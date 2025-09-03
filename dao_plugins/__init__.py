import mobase

from .dao_dlc_manager import DAODLCManager
from  .dao_conflict_checker import DAOConflictChecker
from .dao_utils import DAOUtils

__all__ = [
    "DAODLCManager",
    "DAOConflictChecker",
    "DAOUtils",
]

def createPlugins() -> list[mobase.IPlugin]:
    return [
        DAODLCManager(),
        DAOConflictChecker(),
    ]
