"""
Legacy-compatible database manager shim.

`run_complete_assessment.py` and other development utilities historically
depended on a small `DatabaseManager` helper. During the production hardening
work the implementation moved to `src/infra_mind/core/database.py`, but the
compatibility shim was never re-introduced which caused imports to fail.

This module wraps the production `init_database`/`close_database` helpers and
exposes the minimal interface expected by the scripts:

    manager = DatabaseManager()
    await manager.initialize()
    await manager.shutdown()
    db = manager.get_db()
"""

from __future__ import annotations

from typing import Optional
from loguru import logger

from .database import db as production_db
from .database import init_database, close_database


class DatabaseManager:
    """
    Thin wrapper around the production database utilities.

    The manager keeps track of whether initialization already happened so that
    repeated calls from scripts (or tests) don’t trigger multiple connections.
    """

    def __init__(self) -> None:
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the production database connection if needed."""
        if self._initialized:
            logger.debug("DatabaseManager already initialized – skipping re-init")
            return

        await init_database()
        self._initialized = True
        logger.info("DatabaseManager initialized successfully")

    async def shutdown(self) -> None:
        """Close the database connection if it was opened by initialize()."""
        if not self._initialized:
            return

        await close_database()
        self._initialized = False
        logger.info("DatabaseManager shutdown complete")

    def get_database(self):
        """Return the underlying Motor database reference."""
        return production_db.database

    @property
    def database(self):
        """Convenience alias for code that expects `.database`."""
        return self.get_database()


__all__ = ["DatabaseManager"]
