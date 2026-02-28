"""Test script for extraction module - M3 Framework v1.4."""
import os
import sys
import json

# Set working directory to project root
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add extraction/src to path
sys.path.insert(0, os.path.join(os.getcwd(), "extraction/src"))

from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv(os.path.join(os.getcwd(), ".env"))

from extractor import EntityExtractor
from parser import TextParser


def main():
    """Test extraction on a sample file with M3 Framework."""
    # Initialize
    parser = TextParser(data_dir="data/books")
    extractor = EntityExtractor()

    # Get first file
    files = parser.list_markdown_files()
    test_file = [f for f in files if "古画品录" in str(f) and "校对" not in str(f)][0]
    print(f"Testing with: {test_file.name}")

    content = parser.read_file(test_file)
    print(f"File size: {len(content)} chars")

    # Test with larger chunk
    test_chunk = content[:5000]
    print(f"\n--- Testing with chunk of {len(test_chunk)} chars ---")

    result = extractor.extract_from_text(test_chunk, test_file.name)

    print(f"\n=== Extraction Results ===")
    print(f"Periods (M1.1): {len(result.periods)}")
    print(f"Locations (M1.2): {len(result.locations)}")
    print(f"Iconographies (M1.3): {len(result.iconographies)}")
    print(f"Persons (M2.1): {len(result.persons)}")
    print(f"CV Records (M2.2): {len(result.cv_records)}")
    print(f"Social Relations (M2.3): {len(result.social_relations)}")
    print(f"Works (M3.1): {len(result.works)}")
    print(f"Literature (M3.2): {len(result.literature)}")

    if result.extraction_notes:
        print(f"\nNotes: {result.extraction_notes}")

    # Save result to JSON for inspection
    output_file = "extraction/test_output_m3.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
    print(f"\nSaved output to {output_file}")

    # Show sample of each type
    if result.periods:
        print(f"\nSample Period: {result.periods[0].model_dump()}")
    if result.persons:
        print(f"\nSample Person: {result.persons[0].model_dump()}")
    if result.works:
        print(f"\nSample Work: {result.works[0].model_dump()}")


if __name__ == "__main__":
    main()
