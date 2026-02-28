"""Schema definitions for extracted knowledge graph data - M3 Framework v1.5."""
from typing import Optional, Any
from pydantic import BaseModel, Field


# ============= M1: Macro-Level - Taxonomy & Ontology =============

class Period(BaseModel):
    """1.1 Temporal Ontology - Time periods/dynasties."""
    id: str = Field(..., description="Period unique identifier, e.g., period_tang_high")
    name: str = Field(..., description="Standard name, e.g., '盛唐'")
    time_range: Optional[dict[str, int]] = Field(None, description="Gregorian range, e.g., {'start': 713, 'end': 766}")
    dynastic_info: Optional[str] = Field(None, description="Traditional dating, e.g., '唐·开元天宝'")
    source_book: Optional[str] = Field(None, description="Source book")


class Location(BaseModel):
    """1.2 Spatial Ontology - Geographic locations."""
    id: str = Field(..., description="Location unique identifier, e.g., loc_suzhou")
    historical_names: list[dict[str, str]] = Field(default_factory=list, description="Historical names with periods")
    modern_address: Optional[str] = Field(None, description="Modern address, e.g., '江苏省苏州市'")
    coordinates: Optional[list[float]] = Field(None, description="Latitude and longitude [lat, lon]")
    source_book: Optional[str] = Field(None, description="Source book")


class Iconography(BaseModel):
    """1.3 Iconography Ontology - Subject matter classification."""
    id: str = Field(..., description="Iconography identifier, e.g., icon_lohan")
    name: dict[str, str] = Field(..., description="Subject name, e.g., {'zh': '罗汉', 'en': 'Arhat'}")
    parent_id: Optional[str] = Field(None, description="Parent category ID")
    visual_elements: list[str] = Field(default_factory=list, description="Visual distinguishing features")
    source_book: Optional[str] = Field(None, description="Source book")


# ============= M2: Meso-Level - Historical Figures & Social Networks =============


class Person(BaseModel):
    """2.1 Historical Figure entity."""
    id: str = Field(..., description="Person unique identifier")
    primary_role: str = Field(default="Painter", description="Core identity: Painter, Collector, Connoisseur, Critic, Patron")
    name: str = Field(..., description="Commonly used full name (surname + given name)")
    courtesy_name: Optional[str] = Field(None, description="Courtesy name (字)")
    pseudonym: Optional[str] = Field(None, description="Pseudonym/hao (号/别号)")
    other_names: list[str] = Field(default_factory=list, description="Other titles (temple name, posthumous title, dharma name, etc.)")
    choronym: Optional[str] = Field(None, description="Ancestral home/籍贯, e.g., '吴兴'")
    birth_death: Optional[dict[str, Any]] = Field(None, description="Birth/death info, e.g., {'birth': 1254, 'death': 1322, 'period_ref': 'period_yuan'}")
    period_ref: Optional[str] = Field(None, description="Reference to period_id")
    authority_ids: dict[str, str] = Field(default_factory=dict, description="External authority links (CBDB, Wikidata)")
    biography: Optional[str] = Field(None, description="Biography text")
    source_book: Optional[str] = Field(None, description="Source book for this information")


class CVRecord(BaseModel):
    """2.2 CV & Trajectory - Career and travel records."""
    id: str = Field(..., description="CV record ID, e.g., cv_zhao_001")
    person_ref: str = Field(..., description="Reference to person_id")
    entry_mode: Optional[str] = Field(None, description="Entry method: Recommendation, Examination, Hereditary")
    official_title: Optional[str] = Field(None, description="Official title, e.g., '兵部侍郎'")
    rank: Optional[str] = Field(None, description="Rank/品阶")
    tenure: Optional[dict[str, int]] = Field(None, description="Tenure period, e.g., {'start': 1310, 'end': 1313}")
    location_ref: Optional[str] = Field(None, description="Reference to location_id")
    time_ref: Optional[str] = Field(None, description="Reference to period_id")
    event_type: Optional[str] = Field(None, description="Event type: Official_Post, Travel, Examination")
    source_book: Optional[str] = Field(None, description="Source book")


class SocialRelation(BaseModel):
    """2.3 Social Relations."""
    id: str = Field(..., description="Relation ID, e.g., rel_001")
    source_id: str = Field(..., description="Source person ID")
    target_id: str = Field(..., description="Target person ID")
    relation_type: str = Field(..., description="Relation type: Kinship, Master_Student, Friendship, Colleague")
    formal_name: Optional[str] = Field(None, description="Formal relation description, e.g., '师生'")
    source_book: Optional[str] = Field(None, description="Source book")


# ============= M3: Micro-Level - Art Entities & Visual Evidence =============

class Work(BaseModel):
    """3.1 Artwork entity."""
    id: str = Field(..., description="Work unique identifier")
    title: str = Field(..., description="Title in Chinese, e.g., '洛神赋图'")
    creator_ref: Optional[str] = Field(None, description="Reference to person_id")
    period_ref: Optional[str] = Field(None, description="Reference to period_id (for anonymous works)")
    icon_ref: Optional[str] = Field(None, description="Reference to icon_id")
    status: Optional[str] = Field(None, description="Preservation status: Extant, Lost, Copy")
    support: Optional[str] = Field(None, description="Medium/Support: Silk, Paper, Wall")
    dimensions: Optional[dict[str, Any]] = Field(None, description="Dimensions, e.g., {'height': 27.1, 'width': 572.8, 'unit': 'cm'}")
    repository: Optional[str] = Field(None, description="Current repository, e.g., '故宫博物院'")
    description: Optional[str] = Field(None, description="Description")
    source_book: Optional[str] = Field(None, description="Source book")


class Literature(BaseModel):
    """3.2 Literature & Criticism."""
    id: str = Field(..., description="Literature record ID, e.g., lit_001")
    target_ref: str = Field(..., description="Reference to person_id or work_id")
    source_book: str = Field(..., description="Source book, e.g., '《宣和画谱》'")
    author_ref: Optional[str] = Field(None, description="Reference to person_id (critic)")
    quality_rank: Optional[str] = Field(None, description="Quality rank: 神品, 妙品, 能品, 逸品")
    quote: Optional[str] = Field(None, description="Original text quote")
    source_book_ref: Optional[str] = Field(None, description="Source file")


# ============= Extraction Result =============

class ExtractionResult(BaseModel):
    """Complete extraction result from a single text."""
    source_file: str = Field(..., description="Source file name")
    periods: list[Period] = Field(default_factory=list, description="M1.1 Temporal entities")
    locations: list[Location] = Field(default_factory=list, description="M1.2 Spatial entities")
    iconographies: list[Iconography] = Field(default_factory=list, description="M1.3 Iconography entities")
    persons: list[Person] = Field(default_factory=list, description="M2.1 Person entities")
    cv_records: list[CVRecord] = Field(default_factory=list, description="M2.2 CV/Trajectory entities")
    social_relations: list[SocialRelation] = Field(default_factory=list, description="M2.3 Social relations")
    works: list[Work] = Field(default_factory=list, description="M3.1 Work entities")
    literature: list[Literature] = Field(default_factory=list, description="M3.2 Literature/Criticism")
    extraction_notes: list[str] = Field(default_factory=list, description="Notes about extraction quality")


class ExtractionBatch(BaseModel):
    """Batch of extraction results from multiple files."""
    results: list[ExtractionResult] = Field(default_factory=list)
    total_periods: int = Field(0)
    total_locations: int = Field(0)
    total_iconographies: int = Field(0)
    total_persons: int = Field(0)
    total_cv_records: int = Field(0)
    total_social_relations: int = Field(0)
    total_works: int = Field(0)
    total_literature: int = Field(0)
