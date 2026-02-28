"""Graph database queries for KGCFP."""
from typing import Optional
from neo4j import AsyncSession
import json


class GraphQueries:
    """Graph database query operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_person_node(self, person_data: dict) -> dict:
        """Create a Person node in Neo4j."""
        query = """
        MERGE (p:Person {id: $id})
        SET p.primary_role = $primary_role,
            p.name = $name,
            p.courtesy_name = $courtesy_name,
            p.pseudonym = $pseudonym,
            p.other_names = $other_names,
            p.choronym = $choronym,
            p.birth_death = $birth_death,
            p.period_ref = $period_ref,
            p.biography = $biography,
            p.source_book = $source_book
        RETURN p
        """
        result = await self.session.run(query, person_data)
        record = await result.single()
        return dict(record["p"]) if record else None

    async def create_work_node(self, work_data: dict) -> dict:
        """Create a Work node in Neo4j."""
        query = """
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
        RETURN w
        """
        result = await self.session.run(query, work_data)
        record = await result.single()
        return dict(record["w"]) if record else None

    async def create_relationship(
        self, source_id: str, target_id: str, rel_type: str, description: Optional[str] = None
    ) -> dict:
        """Create a relationship between two nodes."""
        query = f"""
        MATCH (a {{id: $source_id}})
        MATCH (b {{id: $target_id}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r.description = $description
        RETURN a, r, b
        """
        result = await self.session.run(
            query, {"source_id": source_id, "target_id": target_id, "description": description}
        )
        record = await result.single()
        return dict(record["r"]) if record else None

    def _extract_display_name(self, label: str, node: dict) -> str:
        """Extract a human-readable name for a node based on its label."""
        if label == "Person":
            return node.get("name") or node.get("id", "")
        if label == "Work":
            return node.get("title") or node.get("id", "")
        if label == "Period":
            return node.get("name") or node.get("id", "")
        if label == "Iconography":
            name = node.get("name")
            if isinstance(name, str):
                try:
                    name_dict = json.loads(name)
                    return name_dict.get("zh") or name_dict.get("en") or node.get("id", "")
                except Exception:
                    return name
            if isinstance(name, dict):
                return name.get("zh") or name.get("en") or node.get("id", "")
            return node.get("id", "")

        return node.get("id", "")

    async def get_all_nodes(self, limit: int = 100) -> list[dict]:
        """Get all nodes from the graph."""
        query = """
        MATCH (n)
        RETURN n
        LIMIT $limit
        """
        result = await self.session.run(query, {"limit": limit})
        records = await result.data()
        return [dict(r["n"]) for r in records]

    async def get_all_edges(self, limit: int = 200) -> list[dict]:
        """Get all edges from the graph."""
        query = """
        MATCH (a)-[r]->(b)
        RETURN a.id AS source, b.id AS target, type(r) AS type, r.description AS description
        LIMIT $limit
        """
        result = await self.session.run(query, {"limit": limit})
        records = await result.data()
        return records

    async def get_graph_data(self) -> dict:
        """Get complete graph data (nodes and edges)."""
        # Get nodes
        nodes_query = """
        MATCH (n)
        RETURN n.id AS id, labels(n)[0] AS label, n.id AS raw_id
        """
        nodes_result = await self.session.run(nodes_query)
        raw_nodes = await nodes_result.data()

        # Process nodes to extract display names
        nodes = []
        for n in raw_nodes:
            node_id = n.get('id', '')
            label = n.get('label', '')

            # Get name based on label
            name_query = f"""
            MATCH (n {{id: $id}})
            RETURN n
            """
            name_result = await self.session.run(name_query, {"id": node_id})
            name_record = await name_result.single()

            if name_record:
                node_data = dict(name_record['n'])
                display_name = self._extract_display_name(label, node_data)
                nodes.append({
                    'id': node_id,
                    'label': label,
                    'name': display_name,
                    'role': node_data.get('primary_role', node_data.get('status', '')),
                    'dynasty': ''
                })

        # Get edges
        edges_result = await self.session.run("""
        MATCH (a)-[r]->(b)
        RETURN a.id AS source, b.id AS target, type(r) AS type
        """)
        edges = await edges_result.data()

        return {"nodes": nodes, "edges": edges}

    async def search_nodes(self, query: str) -> list[dict]:
        """Search nodes by name or title."""
        search_query = """
        MATCH (n)
        WHERE n.id CONTAINS $query
        RETURN n.id AS id, labels(n)[0] AS label, n.id AS name
        LIMIT 20
        """
        result = await self.session.run(search_query, {"query": query})
        return await result.data()

    async def get_node_details(self, node_id: str) -> Optional[dict]:
        """Get detailed information about a node."""
        query = """
        MATCH (n {id: $id})
        RETURN n
        """
        result = await self.session.run(query, {"id": node_id})
        record = await result.single()
        return dict(record["n"]) if record else None

    async def get_node_relationships(self, node_id: str) -> list[dict]:
        """Get all relationships for a node."""
        query = """
        MATCH (n {id: $id})-[r]->(m)
        RETURN m.id AS target_id,
               m.id AS target_name,
               labels(m)[0] AS target_label,
               type(r) AS relationship_type,
               r.description AS description
        """
        result = await self.session.run(query, {"id": node_id})
        return await result.data()

    async def delete_all(self) -> int:
        """Delete all nodes and relationships."""
        result = await self.session.run("""
        MATCH (n)
        DETACH DELETE n
        RETURN count(n) AS deleted
        """)
        record = await result.single()
        return record["deleted"] if record else 0
