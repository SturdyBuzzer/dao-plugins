import mobase

from .DAOUtils import DAOUtils

#######################
### Mod Data Checks ###
#######################
class DAOModDataChecker(mobase.ModDataChecker): 

    def __init__(self, organizer: mobase.IOrganizer):
        super().__init__()
        DAOModDataChecker._organizer = organizer

    def dataLooksValid(self, filetree: mobase.IFileTree) -> mobase.ModDataChecker.CheckReturn:    
        #Fix: Single root folders getting traversed by Simple Installer:
        parent = filetree.parent()
        filetree = parent if parent else filetree
        if DAOModDataChecker.is_data_fixable(filetree): 
            return mobase.ModDataChecker.FIXABLE
        
        #if <case for data being invalid?>:
        #    return mobase.ModDataChecker.INVALID

        return mobase.ModDataChecker.VALID
    
    def fix(self, filetree: mobase.IFileTree) -> mobase.IFileTree:
        fix_queue = DAOModDataChecker.queue_fixes(filetree)
        if fix_queue.__len__():
            return DAOModDataChecker.execute_fixes(filetree, fix_queue)
        return filetree 
       
    _dir_list = (
        "addins", "bin_ship", "docs", "logs", "mo2unpack", "offers", 
        "packages/core/data", "packages/core/override", "settings" 
        )
    
    _archive_extensions = {"dazip", "override"}
    _archive_unpacked = ("contents/", "bioware/")   
    
    _bin_exceptions = {"daoriginsconfig.ini", "dragonage.ini", "keybindings.ini"}
    _bin_extensions = {"asi", "conf", "dll", "exe", "ini"}

    _docs_exceptions = {"addins.xml", "chargenmorphcfg.xml", "manifest.xml", "offers.xml", "overrideconfig.xml", "systeminformation.xml"}
    _docs_extensions = {"jpg", "pdf", "png", "txt", "xml"}
    
    @staticmethod
    def is_data_fixable(filetree: mobase.IFileTree) -> bool:
        """Check if mod data filetree needs fixing."""
        for entry in DAOUtils.walk_tree(filetree): 
            if entry.isDir():
                continue
            name = entry.name().casefold()
            if name == "meta.ini":
                continue
            path = entry.pathFrom(filetree, '/').casefold()
            suffix = entry.suffix().casefold()
            if suffix == "mo2unpack":
                continue
            if (
                # File is .dazip or .override archive
                (suffix in DAOModDataChecker._archive_extensions)
                or
                # File is part of unpacked .dazip or .override archive
                (path.startswith(DAOModDataChecker._archive_unpacked))
                or 
                # File is a binary and not already in bin_ship/
                (suffix in DAOModDataChecker._bin_extensions and name not in DAOModDataChecker._bin_exceptions and path != f"bin_ship/{name}")
                or
                # File is a docs type and not already in docs/ (excluding chargenmorphcfg.xml and manifest.xml)
                (suffix in DAOModDataChecker._docs_extensions and name not in DAOModDataChecker._docs_exceptions and path != f"docs/{name}")
                or
                # File is otherwise not in a valid directory (move to packages/core/override)
                (not path.startswith(DAOModDataChecker._dir_list) and name != "systeminformation.xml")
            ): return True
        return False
    
    @staticmethod
    def queue_fixes(filetree: mobase.IFileTree) -> dict[str, mobase.FileTreeEntry]:
        """Queue filetree fixes without modifying the tree."""
        fix_queue: dict[str, mobase.FileTreeEntry] = {}
        flatten = DAOModDataChecker._organizer.pluginSetting(
            "Dragon Age Origins Support Plugin",
            "flatten_override",
        )
        for entry in DAOUtils.walk_tree(filetree):
            if entry.isDir():
                continue
            name = entry.name()
            lower_name = name.casefold()
            path = entry.pathFrom(filetree, '/')
            lower_path = path.casefold()
            suffix = entry.suffix().casefold()
            if suffix == "mo2unpack":
                continue
            # File is .dazip or .override archive
            if suffix in DAOModDataChecker._archive_extensions:
                new_path = f"{name}.mo2unpack"
            # File is part of unpacked .dazip or .override archive
            elif lower_path.startswith(DAOModDataChecker._archive_unpacked):
                new_path = f"mo2unpack/{path}"
            elif lower_name == "manifest.xml":
                new_path = f"mo2unpack/{name}"
            # File is a binary type   
            elif suffix in DAOModDataChecker._bin_extensions:
                new_path = f"bin_ship/{name}"
            # File is a docs type (excluding chargenmorphcfg.xml and manifest.xml)
            elif suffix in DAOModDataChecker._docs_extensions and name not in DAOModDataChecker._docs_exceptions:
                new_path = f"docs/{name}"
            # File is otherwise not in a valid directory (move to packages/core/override)
            elif not lower_path.startswith(DAOModDataChecker._dir_list):
                new_path = f"packages/core/override_mo2flatten/{path}" if flatten else f"packages/core/override/{path}"
            else: continue         
            fix_queue[new_path] = entry
        return fix_queue
    
    @staticmethod
    def execute_fixes(filetree: mobase.IFileTree, fix_queue: dict[str, mobase.FileTreeEntry]) -> mobase.IFileTree:
        """Execute filetree fixes.""" 
        for new_path, entry in fix_queue.items():
            parent = entry.parent()
            filetree.move(entry, new_path, mobase.IFileTree.InsertPolicy.REPLACE)
            if parent is not None:
                DAOUtils.trim_branch(parent)
        return filetree  