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
        #Skip checks for already installed files
        if filetree.name():
            return mobase.ModDataChecker.VALID
        #Check if fixable
        if DAOModDataChecker.is_data_fixable(filetree): 
            return mobase.ModDataChecker.FIXABLE
        #if <case for data being invalid?>:
        #    return mobase.ModDataChecker.INVALID
        return mobase.ModDataChecker.VALID
    
    def fix(self, filetree: mobase.IFileTree) -> mobase.IFileTree:
        fix_queue = DAOModDataChecker.queue_fixes(filetree)
        if fix_queue.__len__():
            filetree = DAOModDataChecker.execute_fixes(filetree, fix_queue)
        duplicate_warning = DAOModDataChecker.get_setting("duplicate_warning")
        if duplicate_warning:
            DAOModDataChecker.check_duplicates(filetree, True)
        return filetree 
       
    _dir_list = (
        "addins", "bin_ship", "docs", "logs", "modules", "mo2unpack", "offers", 
        "packages/core_ep1","packages/core/data", "packages/core/override", "settings" 
        )
    
    _archive_extensions = {"dazip", "override"}
    _archive_unpacked = ("contents/", "bioware/")   
    
    _bin_exceptions = {"daoriginsconfig.ini", "dragonage.ini", "keybindings.ini"}
    _bin_extensions = {"asi", "conf", "dll", "exe", "ini"}

    _docs_extensions = {"jpg", "pdf", "png", "txt"}

    @staticmethod
    def get_setting(key: str) -> mobase.MoVariant:
        name = DAOModDataChecker._organizer.managedGame().name()
        return DAOModDataChecker._organizer.pluginSetting(name, key)
        
    @staticmethod
    def is_data_fixable(filetree: mobase.IFileTree) -> bool:
        """Check if mod data filetree needs fixing."""
        duplicate_warning = DAOModDataChecker.get_setting("duplicate_warning")
        if duplicate_warning and not filetree.name():
            if DAOModDataChecker.check_duplicates(filetree, False):
                return True
        for entry in DAOUtils.walk_tree_dao(filetree): 
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
                (suffix in DAOModDataChecker._docs_extensions and not path.startswith("docs/"))
                or
                # File is otherwise not in a valid directory (move to packages/core/override)
                (not path.startswith(DAOModDataChecker._dir_list) and name != "systeminformation.xml")
            ): return True
        return False
    
    @staticmethod
    def queue_fixes(filetree: mobase.IFileTree) -> dict[str, mobase.FileTreeEntry]:
        """Queue filetree fixes without modifying the tree."""
        fix_queue: dict[str, mobase.FileTreeEntry] = {}
        flatten = DAOModDataChecker.get_setting("flatten_override")
        for entry in DAOUtils.walk_tree_dao(filetree):
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
            elif suffix in DAOModDataChecker._docs_extensions:
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
    
    @staticmethod
    def check_duplicates(filetree: mobase.IFileTree, ovrd: bool) -> bool:
        """Check for duplicate files in filetree"""
        if ovrd:
            search_tree = filetree.find("packages/core/override",mobase.FileTreeEntry.FileTypes.DIRECTORY)
            if not isinstance(search_tree, mobase.IFileTree):
                search_tree = filetree.find("packages/core/override_mo2flatten",mobase.FileTreeEntry.FileTypes.DIRECTORY)
        else:
            search_tree = filetree
        if not isinstance(search_tree, mobase.IFileTree):
            return False
        seen: dict[str, str] = {}
        duplicates: dict[str, list[str]] = {}
        for entry in DAOUtils.walk_tree_dao(search_tree):
            if entry.isDir():
                continue
            name = entry.name().casefold()
            rel_path = entry.pathFrom(search_tree, "/").casefold()
            if name not in seen:
                seen[name] = rel_path
                continue
            if name not in duplicates:
                duplicates[name] = [seen[name]]
            duplicates[name].append(rel_path)
        if duplicates:
            if ovrd:
                DAOUtils.log_message(f"Logging duplicate files...")
                for name, paths in duplicates.items():
                    msg = f"Duplicate File:\n -- {name.upper()} --\n -> {"\n -> ".join(paths)}"
                    DAOUtils.log_message(msg)
                DAOModDataChecker.show_duplicate_warning()
            return True
        return False

    @staticmethod
    def show_duplicate_warning():
        DAOUtils.log_message("Warning: Mod override directroy contains duplicate files!")
        DAOUtils.show_message_box(
            header = "Warning: Duplicate files in override",
            message = [
                "This mod contains duplicate file entries in the override directory.<br>",
                "There are likely options that require the users attention.<br>",
                "Please read the mod-page description carefully!<br>",
            ],
            link = f"file:///{DAOModDataChecker._organizer.basePath()}/logs/mo_interface.log",
            link_name = "-- Click here to view logs. --",
            warning = True
            )    