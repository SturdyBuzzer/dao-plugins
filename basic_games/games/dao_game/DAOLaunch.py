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
    @staticmethod
    def deploy_bin_ship(game_dir: str, organizer: mobase.IOrganizer, deploy: bool) -> bool:
        """Move bin_ship files to game root"""
        vfs_tree = organizer.virtualFileTree()
        bin_tree = vfs_tree.find("bin_ship", mobase.IFileTree.FileTypes.DIRECTORY)
        if not isinstance(bin_tree, mobase.IFileTree):
            return True
        for entry in bin_tree:
            if entry.isDir():
                continue
            file_path = entry.pathFrom(vfs_tree)
            src_path = organizer.resolvePath(file_path)
            dst_path = DAOUtils.os_path(game_dir, file_path)
            if os.path.exists(dst_path):
                if deploy:
                    if not DAOUtils.create_backup(dst_path):
                        return False
                else:
                    if not DAOUtils.restore_backup(dst_path):
                        if not DAOUtils.remove_file(dst_path):
                            return False
            if deploy and not DAOUtils.copy_file(src_path, dst_path):
                return False       
        return True
    
    @staticmethod
    def clean_bin_ship(bin_ship: str, overwrite: str, before: set[str], after: set[str]) -> bool:
        """Remove any untracked files from bin_ship."""
        paths = after - before
        for path in paths:
            src_path = DAOUtils.os_path(bin_ship, path)
            dst_path = DAOUtils.os_path(overwrite, "bin_ship", path)
            if not DAOUtils.move_file_overwrite_dirs(src_path, dst_path):
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
        for mod_type in DAOLaunch._xml_tags.keys():
            
            DAOUtils.log_message(f"Building {mod_type}.xml...")
            path_list = DAOLaunch.get_file_paths("Manifest.xml", game_dir, organizer, mod_type)

            item_tag, list_tag = DAOLaunch._xml_tags[mod_type]
            item_dict: dict[str, ET.Element] = {} 
            for path in path_list:
                with open(path, encoding="utf-8") as f:
                    raw_xml = f.read()
                raw_xml = raw_xml.replace('RequiresAuthorization="1"','RequiresAuthorization="0"')
                root = ET.fromstring(raw_xml)
                item_list = root.find(list_tag)
                if item_list is None:
                    continue
                for item in item_list.findall(item_tag):
                    uid = item.get("UID")
                    if not uid:
                        continue
                    item_dict[uid] = item
            root = ET.Element(list_tag)
            for item in item_dict.values():
                root.append(item)
            xml_str = ET.tostring(root, encoding="unicode")          
            xml_bytes = DAOUtils.pretty_format_xml(xml_str)
            xml_path = DAOUtils.os_path(target_dir, "Settings", f"{mod_type}.xml")
            if not DAOUtils.write_file_bytes(xml_path, xml_bytes):
                return False
        return True


    ##################################
    ### Build Chargenmorphcfg.xml  ###
    ##################################
    @staticmethod
    def build_chargenmorph(target_dir: str, game_dir: str, organizer: mobase.IOrganizer) -> bool:
        """Dynamically build Chargenmorphcfg.xml based on contents of override dir"""
        DAOUtils.log_message(f"Building Chargenmorphcfg.xml...")
        ovrd_path = "packages/core/override"
        DAOLaunch.hide_files("Chargenmorphcfg.xml", game_dir, organizer, ovrd_path)

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
            return True

        # Write completed tree to chargenmorphcfg.xml
        xml_string = ET.tostring(chargenmorph, encoding="unicode")
        xml_bytes = DAOUtils.pretty_format_xml(xml_string)
        xml_path = DAOUtils.os_path(target_dir, ovrd_path, "chargenmorphcfg.xml")
        return DAOUtils.write_file_bytes(xml_path, xml_bytes)

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