"""Neo4j graph database connection."""
import os
from typing import Optional

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession

# Global driver instance
_driver: Optional[AsyncDriver] = None


def get_driver() -> AsyncDriver:
    """Get the Neo4j driver instance."""
    global _driver
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialized. Call init_driver() first.")
    return _driver


async def init_driver() -> None:
    """Initialize the Neo4j driver."""
    global _driver

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")

    _driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    # Test connection
    try:
        async with _driver.session() as session:
            await session.run("RETURN 1")
        print(f"Connected to Neo4j at {uri}")
    except Exception as e:
        print(f"Warning: Could not connect to Neo4j: {e}")
        raise


async def close_driver() -> None:
    """Close the Neo4j driver."""
    global _driver
    if _driver:
        await _driver.close()
        _driver = None


async def get_session() -> AsyncSession:
    """Get a new Neo4j session."""
    driver = get_driver()
    return driver.session()
