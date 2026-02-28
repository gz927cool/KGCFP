"""Neo4j import script for KGCFP - imports extraction results into the graph database."""
import json
import os
import sys
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv(project_root / ".env")

from neo4j import GraphDatabase


def serialize_prop(value: Any) -> str:
    """Serialize a property value to JSON string if it's a dict/list."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


class Neo4jImporter:
    """Import extracted data into Neo4j."""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def clear_database(self):
        """Clear all nodes and relationships."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Database cleared.")

    def create_constraints(self):
        """Create constraints for better performance."""
        with self.driver.session() as session:
            constraints = [
                "CREATE CONSTRAINT period_id_unique IF NOT EXISTS FOR (p:Period) REQUIRE p.id IS UNIQUE",
                "CREATE CONSTRAINT location_id_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE",
                "CREATE CONSTRAINT iconography_id_unique IF NOT EXISTS FOR (i:Iconography) REQUIRE i.id IS UNIQUE",
                "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
                "CREATE CONSTRAINT work_id_unique IF NOT EXISTS FOR (w:Work) REQUIRE w.id IS UNIQUE",
                "CREATE CONSTRAINT literature_id_unique IF NOT EXISTS FOR (l:Literature) REQUIRE l.id IS UNIQUE",
            ]
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    print(f"Constraint: {e}")

    def import_periods(self, periods: list[dict]):
        """Import Period nodes."""
        with self.driver.session() as session:
            for period in periods:
                session.run("""
                    MERGE (p:Period {id: $id})
                    SET p.name = $name,
                        p.time_range = $time_range,
                        p.dynastic_info = $dynastic_info,
                        p.source_book = $source_book
                """, id=period.get("id"),
                   name=period.get("name"),
                   time_range=serialize_prop(period.get("time_range")),
                   dynastic_info=period.get("dynastic_info"),
                   source_book=period.get("source_book"))
        print(f"Imported {len(periods)} periods")

    def import_locations(self, locations: list[dict]):
        """Import Location nodes."""
        with self.driver.session() as session:
            for loc in locations:
                session.run("""
                    MERGE (l:Location {id: $id})
                    SET l.historical_names = $historical_names,
                        l.modern_address = $modern_address,
                        l.coordinates = $coordinates,
                        l.source_book = $source_book
                """, id=loc.get("id"),
                   historical_names=serialize_prop(loc.get("historical_names")),
                   modern_address=loc.get("modern_address"),
                   coordinates=serialize_prop(loc.get("coordinates")),
                   source_book=loc.get("source_book"))
        print(f"Imported {len(locations)} locations")

    def import_iconographies(self, iconographies: list[dict]):
        """Import Iconography nodes."""
        with self.driver.session() as session:
            for icon in iconographies:
                session.run("""
                    MERGE (i:Iconography {id: $id})
                    SET i.name = $name,
                        i.parent_id = $parent_id,
                        i.visual_elements = $visual_elements,
                        i.source_book = $source_book
                """, id=icon.get("id"),
                   name=serialize_prop(icon.get("name")),
                   parent_id=icon.get("parent_id"),
                   visual_elements=serialize_prop(icon.get("visual_elements")),
                   source_book=icon.get("source_book"))
        print(f"Imported {len(iconographies)} iconographies")

    def import_persons(self, persons: list[dict]):
        """Import Person nodes."""
        with self.driver.session() as session:
            for person in persons:
                session.run("""
                    MERGE (p:Person {id: $id})
                    SET p.primary_role = $primary_role,
                        p.name = $name,
                        p.courtesy_name = $courtesy_name,
                        p.pseudonym = $pseudonym,
                        p.other_names = $other_names,
                        p.choronym = $choronym,
                        p.birth_death = $birth_death,
                        p.period_ref = $period_ref,
                        p.authority_ids = $authority_ids,
                        p.biography = $biography,
                        p.source_book = $source_book
                """, id=person.get("id"),
                   primary_role=person.get("primary_role"),
                   name=person.get("name"),
                   courtesy_name=person.get("courtesy_name"),
                   pseudonym=person.get("pseudonym"),
                   other_names=serialize_prop(person.get("other_names")),
                   choronym=person.get("choronym"),
                   birth_death=serialize_prop(person.get("birth_death")),
                   period_ref=person.get("period_ref"),
                   authority_ids=serialize_prop(person.get("authority_ids")),
                   biography=person.get("biography"),
                   source_book=person.get("source_book"))
        print(f"Imported {len(persons)} persons")

    def import_works(self, works: list[dict]):
        """Import Work nodes."""
        with self.driver.session() as session:
            for work in works:
                session.run("""
                    MERGE (w:Work {id: $id})
                    SET w.title = $title,
                        w.creator_ref = $creator_ref,
                        w.period_ref = $period_ref,
                        w.icon_ref = $icon_ref,
                        w.status = $status,
                        w.support = $support,
                        w.dimensions = $dimensions,
                        w.repository = $repository,
                        w.description = $description,
                        w.source_book = $source_book
                """, id=work.get("id"),
                   title=work.get("title"),
                   creator_ref=work.get("creator_ref"),
                   period_ref=work.get("period_ref"),
                   icon_ref=work.get("icon_ref"),
                   status=work.get("status"),
                   support=work.get("support"),
                   dimensions=serialize_prop(work.get("dimensions")),
                   repository=work.get("repository"),
                   description=work.get("description"),
                   source_book=work.get("source_book"))
        print(f"Imported {len(works)} works")

    def import_literature(self, literature: list[dict]):
        """Import Literature nodes."""
        with self.driver.session() as session:
            for lit in literature:
                session.run("""
                    MERGE (l:Literature {id: $id})
                    SET l.target_ref = $target_ref,
                        l.source_book = $source_book,
                        l.author_ref = $author_ref,
                        l.quality_rank = $quality_rank,
                        l.quote = $quote,
                        l.source_book_ref = $source_book_ref
                """, id=lit.get("id"),
                   target_ref=lit.get("target_ref"),
                   source_book=lit.get("source_book"),
                   author_ref=lit.get("author_ref"),
                   quality_rank=lit.get("quality_rank"),
                   quote=lit.get("quote"),
                   source_book_ref=lit.get("source_book_ref"))
        print(f"Imported {len(literature)} literature")

    def import_relationships(self, cv_records: list[dict], social_relations: list[dict]):
        """Import relationships between nodes."""
        with self.driver.session() as session:
            for cv in cv_records:
                if cv.get("location_ref"):
                    session.run("""
                        MATCH (p:Person {id: $person_ref})
                        MATCH (l:Location {id: $location_ref})
                        MERGE (p)-[r:WORKED_AT]->(l)
                        SET r.official_title = $official_title,
                            r.rank = $rank,
                            r.tenure = $tenure,
                            r.event_type = $event_type
                    """, person_ref=cv.get("person_ref"),
                       location_ref=cv.get("location_ref"),
                       official_title=cv.get("official_title"),
                       rank=cv.get("rank"),
                       tenure=serialize_prop(cv.get("tenure")),
                       event_type=cv.get("event_type"))

                if cv.get("time_ref"):
                    session.run("""
                        MATCH (p:Person {id: $person_ref})
                        MATCH (t:Period {id: $time_ref})
                        MERGE (p)-[r:ACTIVE_IN]->(t)
                    """, person_ref=cv.get("person_ref"), time_ref=cv.get("time_ref"))

            for rel in social_relations:
                rel_type = rel.get("relation_type", "RELATED_TO")
                rel_label = rel_type.upper().replace(" ", "_").replace("/", "_")

                session.run(f"""
                    MATCH (a:Person {{id: $source_id}})
                    MATCH (b:Person {{id: $target_id}})
                    MERGE (a)-[r:`{rel_label}`]->(b)
                    SET r.formal_name = $formal_name,
                        r.source_book = $source_book
                """,
                    source_id=rel.get("source_id"),
                    target_id=rel.get("target_id"),
                    formal_name=rel.get("formal_name"),
                    source_book=rel.get("source_book"))

            print(f"Imported {len(cv_records)} CV records and {len(social_relations)} social relations")

    def import_work_relationships(self, works: list[dict]):
        """Create relationships between works and other entities."""
        with self.driver.session() as session:
            for work in works:
                if work.get("creator_ref"):
                    session.run("""
                        MATCH (w:Work {id: $work_id})
                        MATCH (p:Person {id: $creator_ref})
                        MERGE (p)-[r:CREATED]->(w)
                    """, work_id=work.get("id"), creator_ref=work.get("creator_ref"))

                if work.get("period_ref"):
                    session.run("""
                        MATCH (w:Work {id: $work_id})
                        MATCH (p:Period {id: $period_ref})
                        MERGE (w)-[r:DATED_TO]->(p)
                    """, work_id=work.get("id"), period_ref=work.get("period_ref"))

                if work.get("icon_ref"):
                    session.run("""
                        MATCH (w:Work {id: $work_id})
                        MATCH (i:Iconography {id: $icon_ref})
                        MERGE (w)-[r:DEPICTS]->(i)
                    """, work_id=work.get("id"), icon_ref=work.get("icon_ref"))

        print(f"Imported work relationships")

    def import_literature_relationships(self, literature: list[dict]):
        """Create relationships between literature and other entities."""
        with self.driver.session() as session:
            for lit in literature:
                target_ref = lit.get("target_ref")
                if not target_ref:
                    continue

                session.run("""
                    MATCH (l:Literature {id: $lit_id})
                    MATCH (p:Person {id: $target_ref})
                    MERGE (l)-[r:CRITIQUES]->(p)
                """, lit_id=lit.get("id"), target_ref=target_ref)

                session.run("""
                    MATCH (l:Literature {id: $lit_id})
                    MATCH (w:Work {id: $target_ref})
                    MERGE (l)-[r:RECORDS]->(w)
                """, lit_id=lit.get("id"), target_ref=target_ref)

                if lit.get("author_ref"):
                    session.run("""
                        MATCH (l:Literature {id: $lit_id})
                        MATCH (p:Person {id: $author_ref})
                        MERGE (p)-[r:WROTE]->(l)
                    """, lit_id=lit.get("id"), author_ref=lit.get("author_ref"))

        print(f"Imported literature relationships")

    def import_file(self, file_path: str):
        """Import a single extraction result file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.import_periods(data.get("periods", []))
        self.import_locations(data.get("locations", []))
        self.import_iconographies(data.get("iconographies", []))
        self.import_persons(data.get("persons", []))
        self.import_works(data.get("works", []))
        self.import_literature(data.get("literature", []))

        self.import_relationships(
            data.get("cv_records", []),
            data.get("social_relations", [])
        )
        self.import_work_relationships(data.get("works", []))
        self.import_literature_relationships(data.get("literature", []))

    def get_stats(self):
        """Get database statistics."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS label, count(*) AS count
                ORDER BY count DESC
            """)
            print("\n=== Database Statistics ===")
            for record in result:
                print(f"  {record['label']}: {record['count']}")

            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS type, count(*) AS count
                ORDER BY count DESC
            """)
            print("\n=== Relationships ===")
            for record in result:
                print(f"  {record['type']}: {record['count']}")


def main():
    """Main import function."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")

    print(f"Connecting to Neo4j at {uri}...")
    importer = Neo4jImporter(uri, user, password)

    output_dir = project_root / "extraction" / "output"

    if not output_dir.exists():
        print(f"Output directory not found: {output_dir}")
        return

    json_files = list(output_dir.glob("*_extracted.json"))

    if not json_files:
        print("No extraction files found.")
        return

    print(f"Found {len(json_files)} extraction files to import")

    print("\nClearing database...")
    importer.clear_database()

    print("\nCreating constraints...")
    importer.create_constraints()

    for json_file in json_files:
        print(f"\nImporting: {json_file.name}")
        importer.import_file(str(json_file))

    importer.get_stats()
    importer.close()
    print("\nImport complete!")


if __name__ == "__main__":
    main()
