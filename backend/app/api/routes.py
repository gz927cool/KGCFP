"""API routes for KGCFP graph operations."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.graph.connection import get_session
from app.graph.queries import GraphQueries


router = APIRouter()


# Request/Response Models
class ImportRequest(BaseModel):
    """Request model for importing data."""
    data: dict


class GraphNode(BaseModel):
    """Graph node model."""
    id: str
    label: str
    name: str
    dynasty: Optional[str] = None
    role: Optional[str] = None


class GraphEdge(BaseModel):
    """Graph edge model."""
    source: str
    target: str
    type: str


class GraphData(BaseModel):
    """Complete graph data model."""
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class SearchResult(BaseModel):
    """Search result model."""
    id: str
    label: str
    name: str


# Routes
@router.get("/graph", response_model=GraphData)
async def get_graph(limit: int = Query(100, ge=1, le=500)):
    """
    Get the complete knowledge graph data.

    Returns nodes and edges for visualization.
    """
    try:
        session = await get_session()
        queries = GraphQueries(session)

        graph_data = await queries.get_graph_data()

        # Convert to response model
        nodes = [
            GraphNode(
                id=n["id"],
                label=n["label"],
                name=n["name"],
                dynasty=n.get("dynasty"),
                role=n.get("role"),
            )
            for n in graph_data["nodes"]
        ]

        edges = [
            GraphEdge(source=e["source"], target=e["target"], type=e["type"])
            for e in graph_data["edges"]
        ]

        await session.close()

        return GraphData(nodes=nodes, edges=edges)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search(q: str = Query(..., min_length=1)):
    """
    Search for nodes by name.

    Returns matching nodes.
    """
    try:
        session = await get_session()
        queries = GraphQueries(session)

        results = await queries.search_nodes(q)

        await session.close()

        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_id}")
async def get_node(node_id: str):
    """
    Get detailed information about a specific node.
    """
    try:
        session = await get_session()
        queries = GraphQueries(session)

        details = await queries.get_node_details(node_id)
        relationships = await queries.get_node_relationships(node_id)

        await session.close()

        if not details:
            raise HTTPException(status_code=404, detail="Node not found")

        return {"node": details, "relationships": relationships}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_data(request: ImportRequest):
    """
    Import data into the knowledge graph.

    Accepts JSON data with persons, works, and relationships.
    """
    try:
        session = await get_session()
        queries = GraphQueries(session)

        imported_count = 0

        # Import persons
        for person in request.data.get("persons", []):
            await queries.create_person_node(person)
            imported_count += 1

        # Import works
        for work in request.data.get("works", []):
            await queries.create_work_node(work)
            imported_count += 1

        # Import relationships
        for rel in request.data.get("relationships", []):
            await queries.create_relationship(
                rel["source_id"], rel["target_id"], rel["relationship_type"], rel.get("description")
            )
            imported_count += 1

        await session.close()

        return {"message": "Import successful", "imported": imported_count}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_graph():
    """
    Clear all nodes and relationships from the graph.
    """
    try:
        session = await get_session()
        queries = GraphQueries(session)

        deleted = await queries.delete_all()

        await session.close()

        return {"message": "Graph cleared", "deleted": deleted}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """
    Get graph statistics.
    """
    try:
        session = await get_session()
        queries = GraphQueries(session)

        graph_data = await queries.get_graph_data()

        nodes = graph_data["nodes"]
        edges = graph_data["edges"]

        # Count by label
        label_counts = {}
        for node in nodes:
            label = node.get("label", "Unknown")
            label_counts[label] = label_counts.get(label, 0) + 1

        # Count relationship types
        rel_counts = {}
        for edge in edges:
            rel_type = edge.get("type", "Unknown")
            rel_counts[rel_type] = rel_counts.get(rel_type, 0) + 1

        await session.close()

        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes_by_label": label_counts,
            "relationships_by_type": rel_counts,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
