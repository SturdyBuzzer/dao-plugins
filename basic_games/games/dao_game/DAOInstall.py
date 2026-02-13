import mobase
import os

from PyQt6.QtWidgets import QInputDialog

from xml.etree import ElementTree as ET

from .DAOUtils import DAOUtils

###################
### Mod Install ###
###################
class DAOInstall:

    @staticmethod 
    def queue_install_tasks(filetree: mobase.IFileTree) -> dict[str, list[str]]:  
        """Plan the install tasks without modifying the tree.""" 
        install_path_dict: dict[str, list[str]] = {
            'bioware' : [], 'contents' : [], 'dazip' : [],
            'docs' : [], 'mo2flatten' : [], 'override' : [],
            }              
        for entry in DAOUtils.walk_tree(filetree):
            path = entry.pathFrom(filetree, '/')
            lower_path = path.casefold()
            if entry.isDir():
                if lower_path == "mo2unpack/bioware":
                    path = "mo2unpack"
                    key = 'bioware'
                elif lower_path == "mo2unpack/contents":
                    path = "mo2unpack"
                    key = 'contents'
                elif lower_path == "packages/core/override_mo2flatten":
                    key = 'mo2flatten'
                else: continue  
            else:
                if lower_path.endswith(".dazip.mo2unpack"):
                    key = 'dazip'
                elif lower_path.startswith("docs/"):
                    key = 'docs'
                elif lower_path.endswith(".override.mo2unpack"):
                    key = 'override'
                else: continue
            install_path_dict[key].append(path)
        return install_path_dict
    
    @staticmethod
    def execute_install_tasks(install_path_dict: dict[str, list[str]], mod_path: str) -> bool:
        """Execute the queued install tasks."""
        install_func_dict = {
            "bioware"    : DAOInstall.install_bioware,
            'contents'   : DAOInstall.install_contents,
            'dazip'      : DAOInstall.install_dazip,
            'docs'       : DAOInstall.install_docs,
            'override'   : DAOInstall.install_override,
            'mo2flatten' : DAOInstall.install_mo2flatten,
        }
        result = True
        for key, func in install_func_dict.items():
            paths = install_path_dict.get(key)
            if not paths:
                continue
            paths.sort(key=DAOUtils.natural_sort_key)
            for file_path in paths:
                if not func(file_path, mod_path):
                    DAOUtils.log_message(f"Failed install task: {func.__name__}({file_path}, {mod_path})")
                    result = False
        return result
        
    @staticmethod
    def flatten_override_dir(mod_dir: str) -> bool:
        """Flattens override dir (or moves each file to subdirs based on file suffix)."""
        ovrds_path = DAOUtils.os_path(mod_dir, "packages/core/override")
        if not os.path.isdir(ovrds_path):
            return True
        path_dict: dict[str, str] = {}
        for root, _, files in os.walk(ovrds_path):
            for file in files:
                rel_path = os.path.relpath(root, ovrds_path)
                src = DAOUtils.os_path(ovrds_path, rel_path, file)
                dst = DAOUtils.os_path(ovrds_path, file)
                if src == dst:
                    continue
                path_dict[src] = dst
        move_queue = dict(sorted(path_dict.items(), key=lambda x: DAOUtils.natural_sort_key(x[0])))
        for src, dst in move_queue.items():
            if not DAOUtils.move_file_overwrite_dirs(src, dst):
                DAOUtils.log_message(f"Failed to flatten override directory for: {mod_dir}")
                return False
        return DAOUtils.remove_empty_subdirs(ovrds_path)

    @staticmethod
    def flatten_override_dir_all_mods(mods_path: str) -> bool:
        """Calls flatten_override_dir for all installed mods"""
        if not os.path.isdir(mods_path):
            return False 
        for entry in os.listdir(mods_path):
            mod_dir = DAOUtils.os_path(mods_path, entry)
            if not DAOInstall.flatten_override_dir(mod_dir):
                return False
            DAOUtils.log_message(f"Flattened override for mod : {entry}.")
        return True

    @staticmethod
    def warn_install_failed(mod_name: str) -> None:
        """Show message box warning that install tasks have failed."""
        DAOUtils.show_message_box(
            header = "Mod Install Failed!",
            message = [
                f"Mod: {mod_name}.\n",
                f"Some install tasks were unsuccessful.\n",
                "\nPlease see MO2 logs for more info."
            ],
            warning = True,
        )

    ################################
    ## Install .override archives ##
    ################################
    @staticmethod                   
    def install_bioware(path: str, mod_path: str) -> bool:
        """Install unpacked .override archives (from DAO-Modmanager)"""
        temp_path = DAOUtils.os_path(mod_path, path)
        return DAOInstall.install_override_files(temp_path, mod_path)
    
    @staticmethod   
    def install_override(file_path:str, mod_path: str) -> bool:
        """Install .override archives (from DAO-Modmanager)"""    
        archive_path = DAOUtils.os_path(mod_path, file_path)
        temp_path = DAOUtils.os_path(mod_path, "mo2unpack")
        if not DAOUtils.extract_archive(archive_path, temp_path):
            return False
        return DAOInstall.install_override_files(temp_path, mod_path)
        
    @staticmethod   
    def install_override_files(temp_path: str, mod_path: str) -> bool:
        """Move contents of BioWare to override dir and check for OverrideConfig.xml """
        src_dir = DAOUtils.os_path(temp_path, "BioWare", "Dragon Age")
        config_path = ""
        for root, _, files in os.walk(src_dir):
            for file in files:
                if not file.casefold() == "overrideconfig.xml":
                    continue
                rel_path = os.path.relpath(root, src_dir)
                config_path = DAOUtils.os_path(mod_path, rel_path, file)
        if not DAOUtils.merge_dirs(src_dir, mod_path):
            return False
        if not DAOInstall.install_override_config(config_path, mod_path):
            return False
        return DAOUtils.remove_dir(temp_path)
        
    @staticmethod   
    def install_override_config(config_path: str, mod_path: str) -> bool:
        """Install wizard for OverrideConfig.XML files from DAO-Modmanager"""
        if not config_path:
            return True 
        ovrd_dir = os.path.dirname(config_path)
        ovrd_name = os.path.basename(ovrd_dir)
        run_config = DAOUtils.show_message_box(
            header = f"DAO-Modmanager Support:",
            message = [
                f"OverrideConfig.xml file detected:\n\n",
                f"{ovrd_name}\n\n",
                f"Run override-config installer?",
            ],
            cancel = True,
        )
        if not run_config:
            return True
        return DAOInstall.override_config_installer(config_path, mod_path)
   
    #############################
    ## Install .dazip archives ##
    #############################
    @staticmethod                   
    def install_contents(path: str, mod_path: str) -> bool:
        """Perform install tasks on unpacked dazip mod packages"""
        temp_path = DAOUtils.os_path(mod_path, path)
        return DAOInstall.install_dazip_files(temp_path, mod_path)

    @staticmethod                   
    def install_dazip(path: str, mod_path: str) -> bool:
        """Perform install tasks on dazip mod packages"""    
        archive_path = DAOUtils.os_path(mod_path, path)
        temp_path = DAOUtils.os_path(mod_path, "mo2unpack")
        if not DAOUtils.extract_archive(archive_path, temp_path):
            return False
        return DAOInstall.install_dazip_files(temp_path, mod_path)

    @staticmethod
    def install_dazip_files(temp_path: str, mod_path:str) -> bool:
        """Move Contents dir to override dir and prepare Manifest.xml"""
        src_dir = DAOUtils.os_path(temp_path, "Contents")
        if not DAOUtils.merge_dirs(src_dir, mod_path):
            return False
        if not DAOInstall.install_dazip_manifest(temp_path, mod_path):
            return False
        return DAOUtils.remove_dir(temp_path)
      
    @staticmethod   
    def install_dazip_manifest(temp_path: str, mod_path:str) -> bool:
        """Rename and format Manifest.xml."""
        src_path = DAOUtils.os_path(temp_path, "Manifest.xml")
        if not DAOUtils.file_exists(src_path):
            DAOUtils.log_message(f"Failed to install Manifest - File not found: {src_path}")
            return False
        manifest = ET.parse(src_path).getroot()
        type = manifest.get("Type", "")
        if type.casefold() == "addin":
            tag = "AddInsList/AddInItem"
        elif type.casefold() == "offer":
            tag = "OfferList/OfferItem"
        else:
            DAOUtils.log_message(f"Failed to install Manifest - No valid Type: {src_path}")
            return False
        item = manifest.find(tag)
        uid = item.get("UID", "") if item else ""
        if not uid:
            DAOUtils.log_message(f"Failed to install Manifest - No UID found: {src_path}")
            return False
        dst_path = DAOUtils.os_path(mod_path, f"{type}s", uid, "Manifest.xml")
        if not DAOUtils.move_file_overwrite_dirs(src_path, dst_path):
            return False
        return DAOUtils.format_xml_file(dst_path)

    ##################
    ## Install docs ##
    ##################
    @staticmethod
    def install_docs(path: str, mod_path: str) -> bool:
        """Move docs dir to subfolder based on mod name"""
        mod_name = os.path.basename(mod_path)
        src_file = DAOUtils.os_path(mod_path, path)
        dst_file = DAOUtils.os_path(mod_path, f"{path.replace("docs", f"docs/{mod_name}")}")
        return DAOUtils.move_file_overwrite_dirs(src_file, dst_file)


    ########################
    ## Install mo2flatten ##
    ########################
    @staticmethod
    def install_mo2flatten(path: str, mod_path: str) -> bool:
        """Renames temp dir packages/core/override_mo2flatten to packages/core/override"""
        src_dir = DAOUtils.os_path(mod_path, path)
        if not os.path.exists(src_dir):
            return False
        dst_dir = DAOUtils.os_path(mod_path, "packages/core/override")
        return DAOUtils.merge_dirs(src_dir, dst_dir)
        
    ###################################################
    ### DAO Mod Manager - Override Config Installer ###
    ###################################################

    # This is support for the DAO-Modmanager format of OverrideConfig.XML
    # Allows for choosing optional variations during install of .override package files.
    # https://www.nexusmods.com/dragonage/mods/277
    @staticmethod   
    def override_config_installer(xml_path: str, mod_path: str) -> bool:
        """Run override-config installer with user input"""
        DAOUtils.log_message(f"Running override-config installer.")
        root = ET.parse(xml_path).getroot()

        options = DAOInstall.override_config_parse(root)
        if not options:
            return False

        results = DAOInstall.override_config_dialog(options)
        if not results:
            return False

        if not DAOInstall.override_config_action(results, mod_path):
            DAOUtils.log_message(f"Failed override-config install.")
            return False
        
        #DAOUtils.remove_file(xml_path) # Remove OverrideConfig.XML once done?
        DAOUtils.log_message(f"Override-config install complete.")
        return True
    
    @staticmethod   
    def override_config_parse(root: ET.Element) -> list[dict[str,list[str]]]:
        """Read in the values from OverrideConfig.xml"""
        options: list[dict[str,list[str]]] = []

        for section in root:
            section_name = section.attrib.get("Name", "")
            for key in section:
                description = ""
                values: list[dict[str, str]] = []
                for value in key:
                    if value.tag == "Description":
                        description = f"{value.text.strip()}\n\n" if value.text else ""
                    else:    
                        value_dict = {
                            'Value'       : value.attrib.get("Value", ""),
                            'OptionsFile' : value.attrib.get("OptionsFile", ""),
                        }
                        values.append(value_dict)
                optiondict = {
                    'section_name' : [section_name,],
                    'key_name'     : [key.attrib.get("Name", ""),],
                    'key_default'  : [key.attrib.get("DefaultValue", ""),],
                    'key_file'     : [key.attrib.get("OriginalFile", ""),],
                    'value_names'  : [value['Value'] for value in values],
                    'value_files'  : [value['OptionsFile'] for value in values],
                    'description'  : [description,],
                }
                options.append(optiondict)
        return options
    
    @staticmethod   
    def override_config_dialog(options: list[dict[str,list[str]]]) -> list[dict[str, str]]:
        """Prompt the user to select from the list of options""" 
        results: list[dict[str, str]] = []

        for option in options:
            # Dialog Box
            item, ok = QInputDialog.getItem(
                None,
                f"DAO-Modmanager Support:",
                (
                    f"{option['section_name'][0]} - {option['key_name'][0]}.\n\n"
                    f"Choose alternate option:\n"
                    f"(DefaultValue: {option['key_default'][0]})"
                    f"\n{option['description'][0] or ""}"
                ),
                option['value_names'],
                next((i for i, v in enumerate(option['value_names']) if v == option['key_default'][0]), 0),
                False
            )
            if not ok:
                continue
            old = option['key_file'][0]
            i = next((i for i, v in enumerate(option['value_names']) if v == item), 0)
            new = option['value_files'][i]
            DAOUtils.log_message(f"{option['section_name'][0]} - {option['key_name'][0]}: {option['value_names'][i]}")
            res = {
                'old' : old,
                'new' : new,
            }
            results.append(res)
        return results
    
    @staticmethod   
    def override_config_action(results: list[dict[str, str]], mod_path: str) -> bool:
        """Move files based on the user selections"""
        ovrd_path = DAOUtils.os_path(mod_path, "packages", "core", "override")
        for res in results:
            new = res['new']
            old = res['old']
            src_path = DAOInstall.override_config_search(new, ovrd_path)
            dst_path = DAOInstall.override_config_search(old, ovrd_path)
            if not DAOUtils.copy_file(src_path, dst_path):
                return False
        return True

    @staticmethod   
    def override_config_search(file_name: str, ovrd_path: str) -> str:
        """Find the full path of the override file"""
        for root, _, files in os.walk(ovrd_path):
            for file in files:
                if not file.casefold() == file_name.casefold():
                    continue
                rel_path = os.path.relpath(root, ovrd_path)
                return DAOUtils.os_path(ovrd_path, rel_path, file)
        return ""