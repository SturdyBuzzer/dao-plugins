import mobase
import os

from xml.etree import ElementTree as ET

from .DAOChargen import DAOChargen
from .DAOUtils import DAOUtils

###################
### Game Launch ###
###################       
class DAOLaunch:

    ########################################
    ### Move bin_ship files to game root ###
    ########################################

    SECONDARY_DIR_BACKUP = r"plugins\basic_games\games\dao_game\DAO_BinList.xml"

    _secondary_dirs = {
    "bin_ship" : ("game_dir", "bin_ship"),
    }

    @staticmethod
    def deploy_secondary_files(app_path: str, path_dict: dict[str, str], organizer: mobase.IOrganizer) -> bool:
        """Move files to secondary dirs"""
        # Backup snapshot of each secondary dir
        if not DAOLaunch._save_secondary_dir_list(app_path, path_dict):
            return False
        # Move data files to deploy dirs
        dir_dict = DAOLaunch._get_secondary_dirs()
        for key, value in dir_dict.items():
            deploy_dir = DAOLaunch._get_deploy_dir(path_dict, value)
            if deploy_dir is None:
                DAOUtils.log_message(f"No matching dir found for: {value}.")
                continue
            DAOUtils.log_message(f"Deploying {key} files to: {deploy_dir}")
            if not DAOLaunch._move_secondary_files(key, deploy_dir, organizer, True):
                return False      
        return True

    @staticmethod
    def recover_secondary_dirs(app_path: str, path_dict: dict[str, str], organizer: mobase.IOrganizer) -> bool:
        """Recover secondary dirs to original state"""
        # Read in snapshot of each secondary dir
        data = DAOLaunch._read_secondary_dir_list()
        if data is None:
            return False
        app_path_bak = data.get("app_path", "")
        if isinstance(app_path_bak, list) or app_path_bak.casefold() != app_path.casefold():
            DAOUtils.log_message(f"Warning: Backup does not match app: {app_path}")
            return False
        return DAOLaunch._restore_secondary_files(data, path_dict, organizer)

    @staticmethod
    def check_secondary_status( path_dict: dict[str, str], organizer: mobase.IOrganizer) -> bool:
        """Check if secondary dir recovery was incomplete."""
        # Detect and recover bin list
        backup_path = DAOLaunch._get_backup_path()
        if not DAOUtils.file_exists(backup_path):
            return True
        DAOUtils.log_message(f"Warning: Mod Organizer 2 may have crashed while game was running.")
        DAOUtils.show_message_box(
            header = "Warning!", 
            message = [
                f"Mod Organizer 2 may have shutdown during gameplay!<br><br>",
                "Please check bin_ship dir.<br><br>",
                f"Backup file: {backup_path}.<br><br>",
            ],
            link = f"file:///{path_dict["game_dir"]}/bin_ship",
            link_name = "-- bin_ship Directory --",            
            warning = True,
            )
        # Read in snapshot of each secondary dir
        data = DAOLaunch._read_secondary_dir_list()
        if data is None:
            return False
        return DAOLaunch._restore_secondary_files(data, path_dict, organizer)
      
    @staticmethod
    def _restore_secondary_files(data: dict[str, str | list[str]], path_dict: dict[str, str], organizer: mobase.IOrganizer) -> bool:
        """Restore files in secondary dirs"""
        backup_path = DAOLaunch._get_backup_path()
        # Restore data files in deploy dirs
        dir_dict = DAOLaunch._get_secondary_dirs()
        for key, value in dir_dict.items():
            deploy_dir = DAOLaunch._get_deploy_dir(path_dict, value)
            if deploy_dir is None:
                continue
            if DAOLaunch._move_secondary_files(key, deploy_dir, organizer, False):
                file_list_bak = set(data.get(key, []))
                overwrite = organizer.overwritePath()
                if DAOLaunch._clean_secondary_dir(key, deploy_dir, file_list_bak, overwrite):
                    continue
            DAOUtils.log_message(f"Warning: Failed to restore secondary dirs! Please see logs.")
            return False
        # Remove snapshot of each secondary dir
        if not DAOUtils.remove_file(backup_path):
            DAOUtils.log_message(f"Warning: Failed to remove secondary dir list file: {backup_path}.")
            return False        
        return True 

    @staticmethod
    def _clean_secondary_dir(dir_name: str, deploy_dir: str, file_list_bak: set[str], overwrite: str) -> bool:
        """Remove any untracked files from secondary dir."""      
        file_list = DAOUtils.list_files(deploy_dir)
        file_paths = file_list - file_list_bak
        for path in file_paths:
            src_path = DAOUtils.os_path(deploy_dir, path)
            dst_path = DAOUtils.os_path(overwrite, dir_name, path)
            if not DAOUtils.move_file_overwrite_dirs(src_path, dst_path):
                return False
        return True 
       
    @staticmethod
    def _get_secondary_dirs() -> dict[str, tuple[str, str]]:
        return DAOLaunch._secondary_dirs
    
    @staticmethod
    def _save_secondary_dir_list(app_path: str, path_dict: dict[str, str]) -> bool:
        """Save secondary dirs list to xml"""
        backup_path = DAOLaunch._get_backup_path()
        data: dict[str, str | list[str]] = {"app_path": app_path}
        dir_dict = DAOLaunch._get_secondary_dirs()
        for key, value in dir_dict.items():
            deploy_path = DAOLaunch._get_deploy_dir(path_dict, value)
            if deploy_path is None:
                continue
            file_list = DAOUtils.list_files(deploy_path)
            data[key] = list(file_list)
        if not DAOLaunch._write_backup_xml(backup_path, data):
            DAOUtils.log_message(f"Failed to save secondary dir backup to {backup_path}.")
            return False
        return True

    @staticmethod
    def _read_secondary_dir_list() -> dict[str, str | list[str]] | None:
        """Read in the saved dir list from xml"""
        backup_path = DAOLaunch._get_backup_path()           
        root = DAOUtils.read_file_xml(backup_path)
        if root is None:
            DAOUtils.log_message(f"Warning: Failed to read secondary dir backup: {backup_path}")
            return None
        app_path = root.findtext("app_path")
        if app_path is None:
            DAOUtils.log_message(f"Warning: App path missing from secondary dir backup: {backup_path}")
            return None
        data: dict[str, str | list[str]] = {"app_path": app_path}
        for dir_elem in root:
            key = dir_elem.tag
            if key == "app_path":
                continue
            file_list = [f.text for f in dir_elem.findall("file") if f.text]
            data[key] = file_list
        return data 
    
    @staticmethod
    def _get_backup_path() -> str:
        return DAOUtils.os_path(DAOLaunch.SECONDARY_DIR_BACKUP)

    @staticmethod
    def _get_deploy_dir(path_dict: dict[str, str], value: tuple[str, str]) -> str | None:
        path_key = value[0]
        base_path = path_dict[path_key]
        rel_path = value[1]
        deploy_path = DAOUtils.os_path(base_path, rel_path)
        if not os.path.isdir(deploy_path):
            return None
        return deploy_path

    @staticmethod
    def _write_backup_xml(path: str, data: dict[str, str | list[str]]) -> bool:
        """Write a secondary backup to XML."""
        root = ET.Element("SecondaryDirs")
        for key, value in data.items():
            elem = ET.SubElement(root, key)
            # app_path
            if isinstance(value, str):
                elem.text = value
                continue
            # secondary dirs
            for item in value:
                file_elem = ET.SubElement(elem, "file")
                file_elem.text = item
        xml_str = ET.tostring(root, encoding="unicode")
        xml_bytes = DAOUtils.pretty_format_xml(xml_str)
        return DAOUtils.write_file_bytes(path, xml_bytes)
    
    @staticmethod
    def _move_secondary_files(dir_name: str, deploy_dir: str, organizer: mobase.IOrganizer, deploy: bool) -> bool:
        """Move files to and from deploy dir"""
        vfs_tree = organizer.virtualFileTree()
        dir_tree = vfs_tree.find(dir_name, mobase.IFileTree.FileTypes.DIRECTORY)
        if not isinstance(dir_tree, mobase.IFileTree):
            return True
        for entry in DAOUtils.walk_tree(dir_tree):
            if entry.isDir():
                continue
            file_path = entry.pathFrom(vfs_tree)
            src_path = organizer.resolvePath(file_path)
            rel_path = os.path.relpath(file_path, dir_name)
            dst_path = DAOUtils.os_path(deploy_dir, rel_path)
            if deploy:
                backup = False
                if DAOUtils.file_exists(dst_path):
                    if not DAOUtils.create_backup(dst_path):
                        return False
                    backup = True
                if not DAOUtils.copy_file(src_path, dst_path):
                    if backup:
                        DAOUtils.restore_backup(dst_path)
                    return False
            else:
                if DAOUtils.restore_backup(dst_path):
                    continue
                if not DAOUtils.remove_file(dst_path):
                    return False
        return True
       
    #######################################
    ### Build Addins.xml and Offers.xml ###
    #######################################

    _xml_tags = {
        "Addins" : ("AddInItem","AddInsList"),
        "Offers" : ("OfferItem","OfferList"),
    }

    @staticmethod
    def build_addins_offers_xml(target_dir: str, game_dir: str, organizer: mobase.IOrganizer) -> bool:
        """Build Addins.xml and Offers.xml"""
        for mod_type, (item_tag, list_tag) in DAOLaunch._xml_tags.items():
            
            DAOUtils.log_message(f"Building {mod_type}.xml...")
            path_list = DAOLaunch.get_file_paths("Manifest.xml", game_dir, organizer, mod_type)

            item_dict: dict[str, ET.Element] = {} 
            for path in path_list:
                with open(path, encoding="utf-8") as f:
                    raw_xml = f.read()
                root = ET.fromstring(raw_xml)
                item_list = root.find(list_tag)
                if item_list is None:
                    continue
                for item in item_list.findall(item_tag):
                    uid = item.get("UID")
                    if uid:
                        item_dict[uid] = item

            xml_gold = DAOUtils.os_path("plugins/basic_games/games/dao_game", f"DAO_{mod_type}.xml")

            if DAOUtils.file_exists(xml_gold):
                root = ET.parse(xml_gold).getroot()
            else:
                root = ET.Element(list_tag)   
            existing_items = {item.get("UID"): item for item in root.findall(item_tag) if item.get("UID")}

            for uid, new_item in item_dict.items():
                if uid in existing_items:
                    old_item = existing_items[uid]
                    DAOUtils.overwrite_element(old_item, new_item)
                    continue
                root.append(new_item)

            xml_str = ET.tostring(root, encoding="unicode") 
            xml_str = xml_str.replace('RequiresAuthorization="1"','RequiresAuthorization="0"')         
            xml_bytes = DAOUtils.pretty_format_xml(xml_str)
            xml_path = DAOUtils.os_path(target_dir, "Settings", f"{mod_type}.xml")
            backup = False
            if DAOUtils.file_exists(xml_path):
                if not DAOUtils.create_backup(xml_path):
                    return False
                backup = True
            if DAOUtils.write_file_bytes(xml_path, xml_bytes):
                if DAOLaunch._create_profile_links(mod_type, xml_path, organizer):
                    continue
            DAOUtils.restore_backup(xml_path) if backup else DAOUtils.remove_file(xml_path)
            return False
        return True
    
    @staticmethod
    def _create_profile_links(mod_type: str, xml_path: str, organizer: mobase.IOrganizer) -> bool:
        """Creates addins.xml/offers.xml link from profile when profile-specific Game INI is enabled"""
        profile = organizer.profile()
        profile_dir = profile.absolutePath()
        if not profile.localSettingsEnabled():
            return True
        link_path = DAOUtils.os_path(profile_dir, f"{mod_type}.xml")
        link_backup = False
        if DAOUtils.file_exists(link_path):
            if not DAOUtils.create_backup(link_path):
                return False
            link_backup = True
        if DAOUtils.create_link(xml_path, link_path, True):
            return True
        DAOUtils.restore_backup(link_path) if link_backup else DAOUtils.remove_link(link_path, True)
        return False       


    ##################################
    ### Build Chargenmorphcfg.xml  ###
    ##################################
    @staticmethod
    def build_chargenmorphcfg_xml(target_dir: str, game_dir: str, organizer: mobase.IOrganizer) -> bool:
        """Dynamically build Chargenmorphcfg.xml based on contents of override dir"""
        DAOUtils.log_message(f"Building Chargenmorphcfg.xml...")
        ovrd_path = "packages/core/override"
        
        vfs_tree = organizer.virtualFileTree()
        ovrd_tree = vfs_tree.find(ovrd_path, mobase.IFileTree.FileTypes.DIRECTORY)
        if not isinstance(ovrd_tree, mobase.IFileTree):
            return True
        
        # Build vanilla chargenmorph tree
        chargenmorph = DAOChargen.build_vanilla_chargen()

        # Append new chargen files found in overrides
        visited: set[str] = set()
        for entry in DAOUtils.walk_tree(ovrd_tree):
            if entry.isDir():
                continue
            name = entry.name().casefold()
            base_name, ext = name.rsplit(".", 1)
            if name in visited or ext not in {"mop", "mmh", "tnt", "dds"}:
                continue    
            visited.add(name)
            resource_type = DAOChargen.get_resource_type(base_name, ext)
            if not resource_type:
                continue
            DAOChargen.add_resource(chargenmorph, name, resource_type)
        if not visited:
            DAOUtils.log_message(f"No chargen mods detected.")
            return True

        DAOLaunch.hide_files("Chargenmorphcfg.xml", game_dir, organizer, ovrd_path)
        # Write completed tree to chargenmorphcfg.xml
        xml_string = ET.tostring(chargenmorph, encoding="unicode")
        xml_bytes = DAOUtils.pretty_format_xml(xml_string)
        xml_path = DAOUtils.os_path(target_dir, ovrd_path, "chargenmorphcfg.xml")
        if not DAOUtils.write_file_bytes(xml_path, xml_bytes):
            DAOLaunch.hide_files("chargenmorphcfg.xml", game_dir, organizer, ovrd_path, True)
            return False
        return True

    @staticmethod
    def get_file_paths(file_name: str, game_dir: str, organizer: mobase.IOrganizer, search_path: str,) -> list[str]:
        """Return list of paths to all matching files"""
        dir_name = DAOUtils.os_path(game_dir, search_path)
        game_paths = DAOUtils.search_dir(dir_name, file_name)
        game_paths.sort(key = DAOUtils.natural_sort_key)

        vfs_tree = organizer.virtualFileTree()
        search_tree = vfs_tree.find(search_path, mobase.IFileTree.FileTypes.DIRECTORY)
        if not isinstance(search_tree, mobase.IFileTree):
            return game_paths
        
        vfs_paths: list[str] = []
        for path in DAOUtils.search_filetree(search_tree, file_name):
            vfs_paths.append(organizer.resolvePath(path))
        vfs_paths.sort(key = DAOUtils.natural_sort_key)

        return game_paths + vfs_paths
    
    @staticmethod
    def hide_files(search_name: str, game_dir: str, organizer: mobase.IOrganizer, search_path: str, unhide: bool = False) -> bool:
        """Hides (or unhides) all matching files"""
        path_list = DAOLaunch.get_file_paths(search_name, game_dir, organizer, search_path)
        for path in path_list:
            new_path = f"{path}.mohidden"
            if not DAOUtils.move_file(new_path, path) if unhide else DAOUtils.move_file(path, new_path):
                return False
        return True
    
    ############################
    ### Move Save Game Files ###
    ############################

    @staticmethod
    def move_save_game_files(profile: mobase.IProfile, path_dict: dict[str, str]) -> bool:
        """Move any save files in the overwrite dir back to saves dir"""
        overwrite = f"{path_dict["overwrite"]}/Characters"
        if profile.localSavesEnabled():
            saves_dir = f"{profile.absolutePath()}/saves"
        else:
            saves_dir = path_dict["saves_dir"]
        if not os.path.exists(overwrite):
            return True
        DAOUtils.log_message(f"Returning save files.")
        return DAOUtils.merge_dirs(overwrite, saves_dir)