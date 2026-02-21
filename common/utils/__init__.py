"""Common utilities."""

from common.utils.config import get_settings
from common.utils.database import get_db, init_db

__all__ = ["get_db", "init_db", "get_settings"]
