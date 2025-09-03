import hashlib
import mobase
import os
import urllib.request

from PyQt6.QtCore import QCoreApplication, QPoint, Qt
from PyQt6.QtGui import QFontMetrics, QIcon, QAction
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, 
    QListWidgetItem, QMenu, QMessageBox,
    QProgressDialog, QPushButton, QVBoxLayout, QWidget, 
)


from typing import Callable, Generator

from xml.etree import ElementTree as ET

from .dao_utils import DAOUtils

class DAODLCManager(mobase.IPluginTool):
    
    #################
    ## Plugin Meta ##
    #################
    AUTHOR = "SturdyBuzzer"
    DESCRIPTION = "Manage Official Dragon Age: Origins DLC"
    DISPLAYNAME = "Dragon Age: Origins - DLC Manager"
    GAMENAME = "dragonage"
    ICON_PATH = "plugins/dao_plugins/dao.ico"
    NAME = "DAO DLC-Manager"
    TOOLTIP = (
        "Manage Official Dragon Age: Origins DLC:<br>"
        "Download and install DLC.<br>"
        "Convert DLC to MO2 managed mods.<br>"
    )
    VERSION = "1.0.0"
    SUPPORTURL = "https://www.nexusmods.com/dragonage/mods/6725"

    ##################################
    ## IPluginTool Method Overrides ##
    ##################################
    def __init__(self):
        super().__init__()

    def init(self, organizer: mobase.IOrganizer) -> bool:
        self._organizer = organizer
        return True

    def author(self) -> str:
        return self.AUTHOR
    
    def description(self) -> str:
        return self.tr(self.DESCRIPTION)

    # **Main: Called when plugin selected from tools menu** #
    def display(self):
        game = self._organizer.managedGame()
        if not game.gameShortName() == self.gameName():
            return
        self._run_plugin_tool()

    def displayName(self) -> str:
        return self.tr(self.DISPLAYNAME)
         
    def gameName(self) -> str:
        return self.GAMENAME
       
    def icon(self) -> QIcon:
        game = self._organizer.managedGame()
        if not game.gameShortName() == self.gameName():
            return QIcon()
        return QIcon(self.ICON_PATH)
    
    def isActive(self) -> bool:
        game = self._organizer.managedGame()
        return game.gameShortName() == self.gameName()

    def name(self) -> str:
        return self.NAME
    
    # Get main MO2 window (not used) #
    def setParentWidget(self, parent: QWidget):
        self._parent_widget = parent  

    def settings(self) -> list[mobase.PluginSetting]:
        return [
            mobase.PluginSetting(
                "enable_logging",
                f"Toggles message logging to console/mo_interface.log.<br>",
                True,
            ),
            mobase.PluginSetting(
                "delete_archives",
                (
                    f"Toggles whether to save or remove installed DLC archives.<br>"
                    f"Warning: Setting to \"True\" will delete all downloaded archives.<br>"
                ),
                False,
            ),
            mobase.PluginSetting(
                "dlc_location",
                (
                    f"Choose the directory location for DLC files.<br>"
                    f"Valid options are \"Game\", \"Data\", or \"Mods\".<br>"
                ),
                "Game",
            ),
        ]
    
    def tooltip(self) -> str:
        return self.tr(self.TOOLTIP)
    
    def tr(self, string: str) -> str:
        return QCoreApplication.translate(self.name(), string)

    def version(self) -> mobase.VersionInfo:
        major, minor, subminor = map(int, self.VERSION.split("."))
        return mobase.VersionInfo(major, minor, subminor, mobase.ReleaseType.FINAL)

    ####################
    ### Helper Utils ###
    ####################
    def _get_data_dir(self) -> str:
        """Get current games data directory"""
        game = self._organizer.managedGame()
        data_dir = game.dataDirectory().absolutePath()
        return data_dir

    def _get_game_dir(self) -> str:
        """Get current games game directory"""
        game = self._organizer.managedGame()
        game_dir = game.gameDirectory().absolutePath()
        return game_dir
    
    def _get_setting(self, key: str) -> mobase.MoVariant:
        return self._organizer.pluginSetting(self.name(), key)
       
    def _set_setting(self, key: str, value: mobase.MoVariant):
        self._organizer.setPluginSetting(self.name(), key, value)

    def _handle_plugin_setting_changed(self, plugin: str, setting: str, old: mobase.MoVariant, new: mobase.MoVariant):
        """Event Handler for onPluginSettingChanged"""
        if self.name() != plugin or old == new:
            return
        DAOUtils.log_message(f"Setting: {setting} changed from {old} to {new}")
        if setting == "delete_archives":
            path = self._get_download_path()
            DAOUtils.remove_dir(path)
    
    def _get_dlc_loc(self) -> str:
        setting = str(self._get_setting("dlc_location"))
        return setting if setting in ("Game", "Data", "Mods") else "Game"
    
    def _read_dlc_list(self) -> None:
        """Parse the dao_dlc_data.xml file into memory."""
        xml_path = self._get_xml_path()
        self._dlc_list = ET.parse(xml_path).getroot()
    
    def _get_dlc_list(self) -> ET.Element:
        return self._dlc_list

    def _get_download_path(self) -> str:
        return "plugins/dao_plugins/dlc_archive"
    
    def _get_xml_path(self) -> str:
        return "plugins/dao_plugins/dao_dlc_data.xml"
        
    ######################################
    ## Main runners for dao_dlc_manager ##
    ######################################
    def _run_plugin_tool(self):
        """"Main plugin workflow"""
        # Init dao_utils for logging
        DAOUtils.setup_utils(self._organizer, self.name())

        self._organizer.onPluginSettingChanged(self._handle_plugin_setting_changed)

        # Select which features to run
        option_one = "Download and Install DLC"
        option_two = "Manage DLC Install Location"
        option_three = "Fix DLC Item Transfer To Awakening"
        selected = self._show_check_list(
            self.displayName(),
            "Please select which actions to take:",
            {
                option_one   : True,
                option_two   : True,
                option_three : False,
            }        
        )
        if not selected:
            return
     
        # Read in the dlc data
        self._read_dlc_list()

        # Update current DLC status
        self._update_dlc_status()
        
        if option_one in selected:
            self._run_installer_tool()
        
        if option_two in selected:
            self._run_relocation_tool()

        if option_three in selected:
            self._run_dlc_fix_tool()

    def _run_installer_tool(self):
        """"Select DLC archives to download and install."""
        # Show dlc installer checklist and return selected items
        selected = self._show_check_list(
            self.displayName(),
            "Choose which DLC to download and install:",
            # Get DLC checklist based on install status
            self._get_dlc_check_list()     
        )
        if not selected:
            return
        
        # Download selected DLC archives
        result = self._download_dlc_archives(selected)
            
        # Install downloaded DLC archives to dlc_loc
        self._install_dlc_archives(result)

        # Update current DLC status
        self._update_dlc_status()

        # Remove incomplete DLC installs
        self._remove_incomplete_dlc_installs()

        # Update addins.xml and offers.xml
        self._build_addins_offers_xml()

        # Show results
        msg = self._show_results(selected, result)
        DAOUtils.log_message(f"Installer Results: {msg}")

    def _run_relocation_tool(self):
        """Move all dlc installs to chosen location."""
        options = {
            "Game Directory" : "Game",
            "Data Directory" : "Data",
            "Mods Directory" : "Mods",
        }
        dlc_loc = str(self._get_setting("dlc_location"))
        current = list(options.values()).index(dlc_loc)
        selected = self._show_combo_box(
            self.displayName(),
            (
                "Choose which directory to keep installed DLC:<br><br>"
                "1. Game Directory<br><br>"
                "2. Data Directory<br><br>"
                "3. Mods Directory (Manage DLC as MO2 Mods)<br><br>"
            ),
            list(options.keys()),
            current,
        )
        if not selected:
            return
        
        # Update dlc_location setting
        self._set_setting("dlc_location", options[selected])

        # Move files
        failures = self._move_all_dlc_installs()

        # Update current DLC status
        self._update_dlc_status()

        # Remove incomplete DLC installs
        self._remove_incomplete_dlc_installs()

        # Update addins.xml and offers.xml
        self._build_addins_offers_xml()

        # Show results
        msg = self._show_results(failures, set())
        DAOUtils.log_message(f"Relocation Results: {msg}")

    def _run_dlc_fix_tool(self):
        """Run dlc item transfer fix tool."""

        if not DAOUtils.show_message_box(
            self.displayName(),
            [
                "DLC Transfer To Awakening Patch:<br>",
                "Patches all the DLC items so that they transfer to Awakenings.",
                "Does <b>not</b> gaurantee items will actually <b>work</b> in Awakenings...",
                "Consider this a <b>work in progress</b>. More info below:<br>"

            ],
            "https://www.nexusmods.com/dragonage/mods/5354?tab=posts",
            "DLC Transfer To Awakening Patch (UPDATED)/POSTS",
            cancel = True    
        ): return

        results = self._fix_dlc_item_transfer()

        attempt = results["attempt"]
        success = results["success"]
        msg = self._show_results(attempt, success)
        DAOUtils.log_message(f"DLC Transfer Fix Results: {msg}")

    ##################
    ## Core Methods ##
    ##################
    def _get_dlc_item_paths(self, dlc_item: ET.Element) -> list[str]:
        """Returns a list of relative paths for the DLC package"""
        manifest = dlc_item.find("Manifest")
        return [] if manifest is None else [file.get("Path", "") for file in manifest]
    
    def _walk_dlc_item_dirs(self) -> Generator[tuple[ET.Element, str, dict[str, str],  list[str]], None, None]:
        """Walk through game_dir, data_dir, mods_path for each dlc_item"""
        # Get file paths
        data_dir = self._get_data_dir()
        game_dir = self._get_game_dir()
        mods_path = self._organizer.modsPath()
        # Read in the dlc data
        dlc_list = self._get_dlc_list()
        # Iterrate through dirs for each dlc_items
        for dlc_item in dlc_list:
            uid = dlc_item.get("UID", "")
            name = dlc_item.get("Name", "")
            mod_name = f"{uid} - {name}"
            mod_dir = DAOUtils.os_path(mods_path, mod_name)
            dirs_dict = {
                "Game" : game_dir,
                "Data" : data_dir,
                "Mods"  : mod_dir,
            }
            paths = self._get_dlc_item_paths(dlc_item)
            yield dlc_item, mod_dir, dirs_dict, paths

    def _update_dlc_status(self) -> None:
        """Searches for currently installed DLC"""
        for dlc_item, _mod_dir, dirs_dict, paths in self._walk_dlc_item_dirs():        
            for attrib, dir in dirs_dict.items():
                if not os.path.exists(dir):
                    dlc_item.set(f"{attrib}_Status", "Missing")
                    continue
                found = False
                missing = False
                for path in paths:
                    file_path = DAOUtils.os_path(dir,path)
                    if not os.path.exists(file_path):
                        missing = True
                        continue
                    found = True
                status = "Installed" if found and not missing else "Incomplete" if found else "Missing"
                dlc_item.set(f"{attrib}_Status", status) 

    def _remove_incomplete_dlc_installs(self) -> None:
        """Removes all incomplete DLC installs"""
        for dlc_item, mod_dir, dirs_dict, paths in self._walk_dlc_item_dirs():
            for attrib, dir in dirs_dict.items():
                if dlc_item.get(f"{attrib}_Status", "") != "Incomplete":
                    continue
                if dir == mod_dir:
                    DAOUtils.remove_dir(mod_dir)
                    dlc_item.set(f"{attrib}_Status", "Missing")
                    continue
                for path in paths:
                    file_path = DAOUtils.os_path(dir,path)
                    DAOUtils.remove_file(file_path)
                dlc_item.set(f"{attrib}_Status", "Missing")
        self._organizer.refresh(save_changes=True)

    ##############################
    ## Download and Install DLC ##
    ##############################
    def _get_dlc_check_list(self) -> dict[str, bool]:
        """Get the dlc checklist to display in the UI"""
        check_list: dict[str, bool] = {}
        locs = ("Game", "Data", "Mods")
        for dlc_item in self._get_dlc_list():
            name = dlc_item.get("Name", "")
            if name == "Dragon Age Awakening":
                continue
            if any("Installed" == dlc_item.get(f"{status}_Status", "") for status in locs): 
                check_list.update({name : False})
                continue
            check_list.update({name : True})
        return check_list

    def _show_check_list(self, title: str, label: str, check_list: dict[str, bool]) -> set[str]:
        """show UI checklist and return selected items"""
        dialog = ChecklistDialog(
            title,
            label,
            check_list,
        )
        if not dialog.exec():
            return set()
        return dialog.get_selected_items()

    def _download_dlc_archives(self, selected: set[str]) -> set[str]:
        """Download the DLC dazip archives"""
        result = selected.copy()
        download_path = self._get_download_path()
        DAOUtils.make_dirs(download_path)
        dlc_list = self._get_dlc_list()
        for dlc_item in dlc_list:
            name = dlc_item.get("Name", "")
            if not name in selected:
                continue
            uid = dlc_item.get("UID", "")
            checksum = dlc_item.get("Checksum", "")
            target_name =f"{uid}.zip"
            target_path = DAOUtils.os_path(download_path, target_name)
            # Check if file already downloaded
            if os.path.exists(target_path) and self._validate_checksum(target_path, checksum):
                DAOUtils.log_message(f"File already exists: {target_name}.")
                continue
            url = dlc_item.get("URL", "")
            # PC_GAMER_TALE requires manual input of Mediafire URL
            if uid == "PC_GAMER_TALE":
                url = self._prompt_for_url_input(url)
            # Download file
            if not self._download_file(target_path, url):
                result.remove(name)
                continue  
            # Validate downloaded file          
            if not self._validate_checksum(target_path, checksum):
                result.remove(name)
        return result

    def _prompt_for_url_input(self, url: str) -> str:
        """Request user input for DLC file download link"""
        dialog = QDialog()
        dialog.setWindowTitle("PC_GAMER_TALE - Manual Download Required.")
        # Instructions label (rich text for hyperURL)
        instructions = (f"Attempting to download DLC: 'A Tale of Orzammar'.<br><br>"
                        f"This file is hosted on 'Mediafire' and accessed via a <i>dynamically generated</i> link.<br><br>"
                        f"The link must be input manually...<br><br>"
                        f"Please open the following page in your browser:<br>"
                        f'<a href="{url}">{url}</a><br><br>'
                        f"1: Right click the 'DOWNLOAD' button.<br>"
                        f"2: Select 'Copy Link'.<br>"
                        f"3: Paste the copied link below.<br>"
                        f"4: Click OK.<br>"
                        )
        instructions_label = QLabel(instructions)
        instructions_label.setOpenExternalLinks(True)
        instructions_label.setWordWrap(True)
        # Input box
        input_box = QLineEdit()
        input_box.setPlaceholderText("Paste the direct download link here")
        # Buttons
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(instructions_label)
        layout.addWidget(input_box)
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        # Execute dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return input_box.text().strip()
        return ""
    
    def _download_file(self, target_path: str, url: str) -> bool:
        """Downloads the file at url to target_path"""
        file_name = os.path.basename(target_path)      
        timer = 10
        canceled  = False
        try:
            with urllib.request.urlopen(url, timeout=timer) as response:
                total_size = response.getheader("Content-Length")
                total_size = int(total_size) if total_size else 0
                progress = QProgressDialog(f"Downloading {file_name}", "Cancel", 0, total_size)
                progress.setWindowTitle("Downloading DLC Files:")
                progress.setWindowModality(Qt.WindowModality.ApplicationModal)
                progress.setAutoClose(True)
                progress.setMinimumDuration(0)

                downloaded = 0
                chunk_size = 8192

                with open(target_path, "wb") as out_file:
                    while True:
                        if progress.wasCanceled():
                            DAOUtils.log_message(f"Download canceled for {file_name}.")
                            canceled  = True
                            break
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            progress.setValue(downloaded)
                        QApplication.processEvents()
            if canceled :
                DAOUtils.remove_file(target_path)
                return False
            return True           
        except Exception as e:
            DAOUtils.log_message(f"Failed to download {file_name}: {e}")
            return False
            
    def _validate_checksum(self, target_path: str, checksum: str) -> bool:
        """Uses file checksum to validate file"""
        sha256 = hashlib.sha256()
        try:
            with open(target_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            if sha256.hexdigest() != checksum:
                DAOUtils.log_message(f"Failed to validate: {target_path}")
                return False
            return True
        except Exception as e:
            DAOUtils.log_message(f"Failed to validate: {target_path}: {e}")
            return False  
                    
    def _install_dlc_archives(self, result: set[str]) -> set[str]:
        """Install the downloaded DLC archives to dlc_location"""
        dlc_loc = self._get_dlc_loc()
        download_path = self._get_download_path()
        for dlc_item, mod_dir, dirs_dict, _paths in self._walk_dlc_item_dirs(): 
            name = dlc_item.get("Name", "")
            if name not in result:
                continue
            for attrib, dir in dirs_dict.items():
                if attrib != dlc_loc:
                    continue
                uid = dlc_item.get("UID", "")
                dlc_type = dlc_item.get("Type", "")
                # Create file paths
                archive_name =f"{uid}.zip"
                archive_path = DAOUtils.os_path(download_path, archive_name)
                temp_path = DAOUtils.os_path(dir, "mo2_temp")
                contents_path = DAOUtils.os_path(temp_path, "contents")
                manifest_src = DAOUtils.os_path(temp_path,"manifest.xml")
                manifest_dst = DAOUtils.os_path(dir, dlc_type, uid, "Manifest.xml")
                # Install DLC archive
                success = False
                delete_archives = bool(self._get_setting("delete_archives"))
                if DAOUtils.extract_archive(archive_path, temp_path, delete_archives):
                    if DAOUtils.merge_dirs(contents_path, dir):
                        if DAOUtils.move_file_overwrite_dirs(manifest_src, manifest_dst):
                            success = True
                if not success:
                    result.remove(name)
                    DAOUtils.remove_dir(mod_dir)
                DAOUtils.remove_dir(temp_path)
        return result  
    
    def _show_results(self, selected:set[str], result: set[str]) -> str:
        """Show dialog with results of install tasks"""
        success: list[str] = []
        failed: list[str] = []
        for name in selected:
            if name in result:
                success.append(f"Success - {name}")
            else:
                failed.append(f"Failed - {name}")
        main_msg = "Complete Success." if not failed else "Some tasks may have failed, please see logs."
        failed_msg = f"\n\n{'\n'.join(failed)}" if failed else ""
        success_msg = f"\n\n{'\n'.join(success)}" if success else ""
        summary = (
            f"{main_msg}"
            f"{failed_msg}"
            f"{success_msg}"
        )
        QMessageBox.information(None,"DLC Installer Results:" ,summary)
        return main_msg

    #######################################
    ### Build Addins.xml and Offers.xml ###
    #######################################
    _xml_tags = {
        "Addins" : ("AddInItem","AddInsList"),
        "Offers" : ("OfferItem","OfferList"),
    }
    def _build_addins_offers_xml(self) -> bool:
        """Build Addins.xml and Offers.xml""" 
        for mod_type in self._xml_tags.keys():
            DAOUtils.log_message(f"Building {mod_type}.xml...")
            path_list = self._get_manifest_paths(mod_type)

            item_tag, list_tag = self._xml_tags[mod_type]
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
            data_dir = self._get_data_dir()
            xml_path = DAOUtils.os_path(data_dir, "Settings", f"{mod_type}.xml")
            if not DAOUtils.write_file_bytes(xml_path, xml_bytes):
                return False
        return True

    def _get_manifest_paths(self, search_path: str,) -> list[str]:
        """Return list of paths to all manifest files"""
        file_paths: list[str] = []
        for current_dir in {self._get_game_dir(), self._get_data_dir()}:
            dir_name = DAOUtils.os_path(current_dir, search_path)
            temp_paths = DAOUtils.search_dir(dir_name, "Manifest.xml")
            temp_paths.sort(key = DAOUtils.natural_sort_key)
            file_paths.extend(temp_paths)
        return file_paths
    
    #########################
    ## Manage DLC Location ##
    #########################
    def _show_combo_box(self, title: str, label: str, items: list[str], current: int) -> str:
        """Show message box with dropdown list"""
        dialog = ComboBoxDialog(
            title,
            label,
            items,
            current,
        )
        if not dialog.exec():
            return ""
        return dialog.get_selection()
    
    def _move_all_dlc_installs(self) -> set[str]:
        """Moves all installed DLC to the destination directory (Game, Data, Mods)"""
        dlc_loc = self._get_dlc_loc()
        failures: set[str] = set()
        for dlc_item, mod_dir, dirs_dict, paths in self._walk_dlc_item_dirs():   
            for attrib, src_dir in dirs_dict.items():
                dst_dir = dirs_dict[dlc_loc]
                if src_dir == dst_dir or dlc_item.get(f"{attrib}_Status", "") != "Installed":
                    continue
                uid = dlc_item.get("UID", "")
                if not self._move_dlc_files(uid, paths, src_dir, dst_dir):
                    failures.add(uid)
                    continue
                if mod_dir == dst_dir:
                    self._create_dlc_mod_meta_ini(mod_dir, dlc_item)
                else:
                    DAOUtils.remove_dir(mod_dir)
                DAOUtils.remove_empty_subdirs(src_dir)
                dlc_item.set(f"{attrib}_Status", "Missing")
                dlc_item.set(f"{dlc_loc}_Status", "Installed")
        if not dlc_loc == "Mods":
            self._remove_dlc_separator()
        else:
            self._create_dlc_separator()
            self._update_modlist()
        self._organizer.refresh(save_changes=True)
        return failures

    def _move_dlc_files(self, uid: str, paths: list[str], src_dir: str, dst_dir: str) -> bool:
        """Moves all DLC files with UI progress bar."""
        file_moves: list[tuple[str, str]] = []
        for path in paths:
            src = DAOUtils.os_path(src_dir, path)
            dst = DAOUtils.os_path(dst_dir, path)
            file_moves.append((src, dst))
        total_files = len(file_moves)

        # Set up the progress dialog
        progress = QProgressDialog(f"Moving {uid}", None, 0, total_files)
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        #progress.setMinimumWidth(len(uid)+10)
        progress.setAutoClose(True)
        progress.setMinimumDuration(500) # Epilepsy warning...
        progress.setValue(0)
        
        for i, (src, dst) in enumerate(file_moves, 1):
            if not DAOUtils.move_file_overwrite_dirs(src, dst):
                return False
            progress.setValue(i)
            QApplication.processEvents()
        return True

    def _create_dlc_mod_meta_ini(self, mod_dir: str, dlc_item: ET.Element) -> bool:
        """Create mo2 meta.ini for dlc mod"""
        meta_path = DAOUtils.os_path(mod_dir, "meta.ini")
        uid = dlc_item.get("UID", "")
        url = dlc_item.get("URL", "")
        version = dlc_item.get("Version", "")
        try:
            with open(meta_path, 'w', encoding="utf-8") as f:
                f.write(
                    "[General]"
                    f"version={version}"
                    f"installationFile={uid}.zip"
                    "gameName=dragonage"
                    f"url={url}"
                    "hasCustomURL=true"
                    ""
                    "[installedFiles]"
                    "size=0"
                ) 
            return True
        except Exception as e:
            DAOUtils.log_message(f"Failed to create meta file {meta_path}: {e}")
            return False

    def _create_dlc_separator(self) -> bool:
        """Create mo2 separator"""
        sep_name = "Dragon Age Origins - Official DLC_separator"
        sep_path = DAOUtils.os_path(self._organizer.modsPath(), sep_name)
        meta_path = DAOUtils.os_path(sep_path, "meta.ini")
        if os.path.exists(meta_path):
            return True
        if not DAOUtils.make_dirs(sep_path):
            return False
        try:
            with open(meta_path, 'w', encoding="utf-8") as f:
                f.write(
                    "[General]"
                    "modid=0"
                    "version="
                    "newestVersion="
                    "category=0"
                    "installationFile="
                    ""
                    "[installedFiles]"
                    "size=0"
                )
            return True
        except Exception as e:
            DAOUtils.log_message(f"Failed to create meta file {meta_path}: {e}")
            return False

    def _remove_dlc_separator(self) -> bool:
        """Remove mo2 separator"""
        sep_name = "Dragon Age Origins - Official DLC_separator"
        sep_path = DAOUtils.os_path(self._organizer.modsPath(), sep_name)
        return DAOUtils.remove_dir(sep_path)

    def _update_modlist(self) -> bool:
        profile_path = self._organizer.profilePath()
        modlist_path = DAOUtils.os_path(profile_path, "modlist.txt")
        modlist = [
            f"{dlc_item.get('UID', '')} - {dlc_item.get('Name', '')}"
            for dlc_item in self._get_dlc_list()
        ]
        modlist.reverse()
        try:
            with open(modlist_path, 'a', encoding="utf-8") as f:
                f.write(
                    f"+{'\n+'.join(modlist)}"
                    f"\n-Dragon Age Origins - Official DLC_separator"
                )
            return True
        except Exception as e:
            DAOUtils.log_message(f"Failed to update modlist.txt: {e}")
            return False

    #################################
    ## DLC item transfer fix tool. ##
    #################################
    def _fix_dlc_item_transfer(self) -> dict[str, set[str]]:
        """Patches all installed DLC items so they transfer properly to Awakenings"""
        results: dict[str, set[str]] ={
            "attempt" : set(),
            "success" : set(),
        }
        mods_path = self._organizer.modsPath()
        dlc_fix_path = DAOUtils.os_path(mods_path, "DLC Transfer To Awakening Patch")
        for dlc_item, _mod_dir, dirs_dict, _paths in self._walk_dlc_item_dirs():
            for attrib, dir in dirs_dict.items():
                dlc_type = dlc_item.get("Type", "")
                if dlc_type != "Addins" or dlc_item.get(f"{attrib}_Status", "") != "Installed":
                    continue
                uid = dlc_item.get("UID", "")
                # Define paths
                mod_fix_path = DAOUtils.os_path(dlc_fix_path, dlc_type, uid, "core", "override", "DLC_FIX")
                mod_path = DAOUtils.os_path(dir, dlc_type, uid)
                results["attempt"].add(f"{uid} in {attrib}_Dir")
                # Copy files
                if self._copy_files_to_dlc_fix(
                    mod_path, "data", mod_fix_path, "",
                    name_transform = lambda file: f"{(parts := file.rsplit('.', 1))[0]}_fix.{parts[1]}"
                ):
                    if self._copy_files_to_dlc_fix(
                        mod_path, "data/talktables", mod_fix_path, "talktables",
                        name_transform = lambda file: file if "promo" in uid or "cp" in uid else f"{uid}_c_{file}"
                    ):
                        if self._copy_files_to_dlc_fix(mod_path, "audio/sound", mod_fix_path, "sound"):
                            results["success"].add(f"{uid} in {attrib}_Dir")     
        meta_path = DAOUtils.os_path(dlc_fix_path, "meta.ini")
        try:
            with open(meta_path, 'w', encoding="utf-8") as f:
                f.write(
                    "[General]"
                    f"version={self.version()}"
                    f"installationFile="
                    "gameName=dragonage"
                    f"url={self.SUPPORTURL}"
                    "hasCustomURL=false"
                    ""
                    "[installedFiles]"
                    "size=0"
                ) 
        except Exception as e:
            DAOUtils.log_message(f"Failed to create meta file {meta_path}: {e}")
        self._organizer.refresh(save_changes=True)
        return results

    def _copy_files_to_dlc_fix(
            self, mod_path: str, src_dir: str,
            mod_fix_path: str, dst_dir:str,
            name_transform: Callable[[str], str] = lambda x: x,
        ) -> bool:
        """Copy files to dlc_fix, changing file names as needed"""
        module_path = DAOUtils.os_path(mod_path, "module")
        src_path = DAOUtils.os_path(module_path, src_dir)
        if not os.path.isdir(src_path): 
            return True
        for file in os.listdir(src_path):
            src = DAOUtils.os_path(src_path, file)
            if not os.path.isfile(src):
                continue
            dst_name = name_transform(file)
            dst = DAOUtils.os_path(mod_fix_path, dst_dir, dst_name)
            DAOUtils.log_message(f"Copying {src} to {dst}")
            if not DAOUtils.copy_file(src, dst):
                return False
        return True
                
#####################################
## UI Check-List for DLC Selection ##
#####################################
class ChecklistDialog(QDialog):

    def __init__(self, title: str, label: str, check_list: dict[str, bool]):
        super().__init__()

        self._check_list = check_list.copy()
        self.setWindowTitle(title)
        self.label = QLabel(label)
        self.set_buttons()
        self.set_list_widget()
        self.set_layout()
        self.set_list_widget_state()
        self._locked = True

    def set_buttons(self) -> None:
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def set_list_widget(self) -> None:

        self.list_widget = QListWidget()

        font_metrics = QFontMetrics(self.list_widget.font())
        self.max_width: int = 300

        for name in self._check_list:
            item = QListWidgetItem(name)
            self.max_width = max(self.max_width, 80+font_metrics.horizontalAdvance(name))
            self.list_widget.addItem(item)

        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

    def set_list_widget_state(self) -> None:
        
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not item:
                continue
            if self._check_list[item.text()]:
                item.setCheckState(Qt.CheckState.Checked)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)   
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
                item.setFlags(Qt.ItemFlag.ItemIsSelectable)
                item.setFlags(Qt.ItemFlag.ItemIsUserCheckable)

    def set_layout(self) -> None:
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.buttons)
        self.setLayout(layout)
                
        w = self.max_width
        h = 2*(w//16*9)
        self.resize(w, h)

    def get_selected_items(self) -> set[str]:
        res: set[str] = set()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                res.add(item.text())
        return res

    def show_context_menu(self, position: QPoint) -> None:
        menu = QMenu()
        select_all = QAction("Select All")
        select_none = QAction("Select None")
        invert = QAction("Invert Selection")
        unlock = QAction("Unlock")
        lock = QAction("Lock")
        menu.addActions([select_all, select_none, invert])
        menu.addActions([unlock,]) if self._locked else menu.addActions([lock,])
        vp = self.list_widget.viewport()
        if not vp:
            return
        action = menu.exec(vp.mapToGlobal(position))
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not item:
                continue
            if action == unlock:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)
                self._locked = False
            elif action == lock:
                if not self._check_list[item.text()]:
                    item.setCheckState(Qt.CheckState.Unchecked)
                    item.setFlags(Qt.ItemFlag.ItemIsSelectable)
                    item.setFlags(Qt.ItemFlag.ItemIsUserCheckable)
                self._locked = True
            elif Qt.ItemFlag.ItemIsEnabled in item.flags():
                if action == select_all:
                    item.setCheckState(Qt.CheckState.Checked)
                elif action == select_none:
                    item.setCheckState(Qt.CheckState.Unchecked)
                elif action == invert:
                    if item.checkState() == Qt.CheckState.Checked:
                        item.setCheckState(Qt.CheckState.Unchecked)
                    else:
                        item.setCheckState(Qt.CheckState.Checked)  

###################################
## DLC Location Selection Dialog ##
###################################
class ComboBoxDialog(QDialog):
    def __init__(self, title: str, label: str, items: list[str], current: int):
        super().__init__()
        self.setWindowTitle(title)
        self.selection = None

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(label))

        self.combo = QComboBox()
        self.combo.addItems(items)
        self.combo.setCurrentIndex(current)
        layout.addWidget(self.combo)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

    def get_selection(self):
        return self.combo.currentText()                        