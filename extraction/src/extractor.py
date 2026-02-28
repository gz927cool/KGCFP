"""LangChain-based entity extractor for Chinese painting texts - M3 Framework v1.5."""
import json
import os
import re
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables
load_dotenv()

# Get configuration from environment
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL_NAME = os.getenv("LLM_MODEL", "qt-qwen2.5-14b-vllm-dev")

from schema import (
    Period,
    Location,
    Iconography,
    Person,
    CVRecord,
    SocialRelation,
    Work,
    Literature,
    ExtractionResult,
)


class EntityExtractor:
    """Extract entities from Chinese painting texts using LangChain - M3 Framework."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
    ):
        """Initialize the extractor with LLM configuration."""
        self.api_key = api_key or API_KEY
        self.base_url = base_url or BASE_URL
        self.model_name = model_name or MODEL_NAME

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=temperature,
            max_tokens=4096,
        )

    def _build_extraction_prompt(self) -> ChatPromptTemplate:
        """Build the extraction prompt template for M3 Framework."""
        # Complete M3 Framework v1.5 schema - using doubled curly braces for escaping
        schema_description = """{{
  "source_file": "string",
  "periods": [{{ "id": "string", "name": "string", "time_range": {{"start": 0, "end": 0}}, "dynastic_info": "string" }}],
  "locations": [{{ "id": "string", "historical_names": [{{"name": "string", "period": "string"}}], "modern_address": "string", "coordinates": [0, 0] }}],
  "iconographies": [{{ "id": "string", "name": {{"zh": "string"}}, "parent_id": "string", "visual_elements": ["string"] }}],
  "persons": [{{ "id": "string", "primary_role": "string", "name": "string", "courtesy_name": "string", "pseudonym": "string", "other_names": ["string"], "choronym": "string", "birth_death": {{"birth": 0, "death": 0, "period_ref": "string"}}, "period_ref": "string", "authority_ids": {{"Wikidata": "string", "CBDB": "string"}}, "biography": "string" }}],
  "cv_records": [{{ "id": "string", "person_ref": "string", "entry_mode": "string", "official_title": "string", "rank": "string", "tenure": {{"start": 0, "end": 0}}, "location_ref": "string", "event_type": "string" }}],
  "social_relations": [{{ "id": "string", "source_id": "string", "target_id": "string", "relation_type": "string", "formal_name": "string" }}],
  "works": [{{ "id": "string", "title": "string", "creator_ref": "string", "period_ref": "string", "icon_ref": "string", "status": "string", "support": "string", "dimensions": {{"height": 0, "width": 0, "unit": "cm"}}, "repository": "string", "description": "string" }}],
  "literature": [{{ "id": "string", "target_ref": "string", "source_book": "string", "author_ref": "string", "quality_rank": "string", "quote": "string" }}]
}}"""

        system_prompt = """You are an expert in Chinese art history specializing in extracting structured information from classical Chinese painting texts.

Your task is to extract structured entities following the M3 Framework v1.5 schema.

M3 Framework Entity Types to Extract:

**M1: Macro-Level (Taxonomy)**
1. **Periods (时期)** - Time periods/dynasties with time ranges
2. **Locations (地点)** - Geographic locations, historical/modern names, coordinates
3. **Iconography (题材)** - Subject matter classifications (religious figures, scenes, etc.)

**M2: Meso-Level (Historical Figures & Social Networks)**
4. **Persons (人物)** - Painters, collectors, critics, patrons
   - Extract: names (name, courtesy/字, pseudo/号), role, choronym (籍贯), birth/death years, period reference, authority IDs (Wikidata, CBDB)
5. **CV Records (履历)** - Official posts, career trajectories
   - Extract: entry mode (科举/荐举), official titles, rank, tenure, location
6. **Social Relations (社会关系)** - Teacher-student, kinship, colleague, friendship

**M3: Micro-Level (Art Entities & Evidence)**
7. **Works (作品)** - Paintings, calligraphies
   - Extract: title, creator, period, status (存世), support (媒介), dimensions, repository
8. **Literature (文献著录)** - Criticism and records
   - Extract: source book, quality rank (神品/妙品/能品/逸品), quotes

IMPORTANT:
- Return ONLY valid JSON, no explanations
- Use empty arrays [] for missing entity types
- Link entities via references (period_ref, creator_ref, person_ref, etc.)
- For Chinese dynasty mapping, use: 魏晋=220-420, 南北朝=420-589, 隋=581-618, 唐=618-907, 五代=907-960, 宋=960-1279, 元=1271-1368, 明=1368-1644, 清=1644-1911

Output format (JSON):
""" + schema_description

        human_prompt = """Extract all M3 Framework entities from the following text from "{source_file}":

---TEXT START---
{text}
---TEXT END---

Return ONLY valid JSON."""

        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def extract_from_text(self, text: str, source_file: str) -> ExtractionResult:
        """
        Extract entities from a single text chunk.

        Args:
            text: Text to extract from
            source_file: Source file name for attribution

        Returns:
            ExtractionResult with extracted entities
        """
        prompt = self._build_extraction_prompt()

        # Truncate very long texts to avoid token limits
        if len(text) > 6000:
            text = text[:6000] + "...[truncated]"

        formatted_prompt = prompt.format(
            text=text,
            source_file=source_file
        )

        try:
            response = self.llm.invoke(formatted_prompt)
            content = response.content

            # Try to parse JSON from response
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)

                # Build result with proper schema
                result = ExtractionResult(
                    source_file=source_file,
                    periods=[Period(**p, source_book=source_file) for p in data.get("periods", [])],
                    locations=[Location(**loc, source_book=source_file) for loc in data.get("locations", [])],
                    iconographies=[Iconography(**ic, source_book=source_file) for ic in data.get("iconographies", [])],
                    persons=[Person(**p, source_book=source_file) for p in data.get("persons", [])],
                    cv_records=[CVRecord(**cv, source_book=source_file) for cv in data.get("cv_records", [])],
                    social_relations=[SocialRelation(**sr, source_book=source_file) for sr in data.get("social_relations", [])],
                    works=[Work(**w, source_book=source_file) for w in data.get("works", [])],
                    literature=[Literature(**lit, source_book_ref=source_file) for lit in data.get("literature", [])],
                )
                return result
            else:
                return ExtractionResult(
                    source_file=source_file,
                    extraction_notes=[f"Failed to parse JSON from response: {content[:200]}"]
                )

        except Exception as e:
            return ExtractionResult(
                source_file=source_file,
                extraction_notes=[f"Extraction error: {str(e)}"]
            )


class BatchExtractor:
    """Process multiple files for extraction."""

    def __init__(self, extractor: EntityExtractor, parser):
        self.extractor = extractor
        self.parser = parser

    def process_file(self, file_path: Path) -> ExtractionResult:
        """Process a single file and return combined results."""
        print(f"Processing: {file_path.name}")

        content = self.parser.read_file(file_path)
        file_info = self.parser.get_file_info(file_path)

        # Collect all entities
        all_periods = []
        all_locations = []
        all_iconographies = []
        all_persons = []
        all_cv_records = []
        all_social_relations = []
        all_works = []
        all_literature = []
        all_notes = []

        # Process by sections
        sections = list(self.parser.segment_by_headings(content))

        for heading, section_content in sections:
            if len(section_content) < 100:
                continue

            # Process each chunk
            for chunk in self.parser.chunk_text(section_content, chunk_size=3000):
                result = self.extractor.extract_from_text(
                    chunk,
                    f"{file_info['filename']} - {heading}"
                )

                all_periods.extend(result.periods)
                all_locations.extend(result.locations)
                all_iconographies.extend(result.iconographies)
                all_persons.extend(result.persons)
                all_cv_records.extend(result.cv_records)
                all_social_relations.extend(result.social_relations)
                all_works.extend(result.works)
                all_literature.extend(result.literature)
                all_notes.extend(result.extraction_notes)

        # Deduplicate by ID
        def dedupe_by_id(items):
            seen = set()
            result = []
            for item in items:
                if item.id not in seen:
                    seen.add(item.id)
                    result.append(item)
            return result

        return ExtractionResult(
            source_file=file_path.name,
            periods=dedupe_by_id(all_periods),
            locations=dedupe_by_id(all_locations),
            iconographies=dedupe_by_id(all_iconographies),
            persons=dedupe_by_id(all_persons),
            cv_records=dedupe_by_id(all_cv_records),
            social_relations=dedupe_by_id(all_social_relations),
            works=dedupe_by_id(all_works),
            literature=dedupe_by_id(all_literature),
            extraction_notes=all_notes
        )

    def process_directory(self, data_dir: str = "data/books") -> list[ExtractionResult]:
        """Process all Markdown files in a directory."""
        results = []
        files = self.parser.list_markdown_files()

        print(f"Found {len(files)} Markdown files to process")

        for file_path in files:
            result = self.process_file(file_path)
            results.append(result)
            print(f"  - {file_path.name}: {len(result.persons)} persons, {len(result.works)} works")

        return results


def save_results(results: list[ExtractionResult], output_dir: str = "output"):
    """Save extraction results to JSON files."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Save individual results
    for result in results:
        filename = f"{Path(result.source_file).stem}_extracted.json"
        with open(output_path / filename, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)

    # Save combined result
    combined = {
        "total_files": len(results),
        "total_periods": sum(len(r.periods) for r in results),
        "total_locations": sum(len(r.locations) for r in results),
        "total_iconographies": sum(len(r.iconographies) for r in results),
        "total_persons": sum(len(r.persons) for r in results),
        "total_cv_records": sum(len(r.cv_records) for r in results),
        "total_social_relations": sum(len(r.social_relations) for r in results),
        "total_works": sum(len(r.works) for r in results),
        "total_literature": sum(len(r.literature) for r in results),
        "results": [r.model_dump() for r in results]
    }

    with open(output_path / "combined_extraction.json", "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"\nSaved results to {output_path}/")
    print(f"Total: {combined['total_periods']} periods, {combined['total_locations']} locations, {combined['total_persons']} persons, {combined['total_works']} works, {combined['total_literature']} literature")


if __name__ == "__main__":
    # Test extraction
    parser = TextParser(data_dir="../../data/books")
    extractor = EntityExtractor()
    batch_extractor = BatchExtractor(extractor, parser)

    # Process first file as test
    files = parser.list_markdown_files()
    if files:
        print(f"Testing with: {files[0].name}")
        result = batch_extractor.process_file(files[0])
        print(f"Extracted: {len(result.persons)} persons, {len(result.works)} works")
