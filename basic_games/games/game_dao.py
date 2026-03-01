import mobase

from pathlib import Path
from xml.etree import ElementTree as ET

from PyQt6.QtWidgets import QMainWindow

from ..basic_features import BasicLocalSavegames, BasicGameSaveGameInfo
from ..basic_game import BasicGame

from .dao_game import *

########################
### Basic-Game Setup ###
########################
class DAOriginsGame(BasicGame):

    Name = "Dragon Age Origins Support Plugin"
    Author = "SturdyBuzzer"
    Version = "2.9"

    GameName = "Dragon Age: Origins"
    GameShortName = "dragonage"
    GameBinary = r"bin_ship\DAOrigins.exe"
    GameLauncher = r"DAOriginsLauncher.exe"
    GameDataPath = r"%DOCUMENTS%\BioWare\Dragon Age"
    GameDocumentsDirectory = r"%DOCUMENTS%\BioWare\Dragon Age\Settings"
    GameSavesDirectory = r"%DOCUMENTS%\BioWare\Dragon Age\Characters"
    GameSaveExtension = "das"
    GameSteamId = [17450, 47810]
    GameGogId = 1949616134
    GameEaDesktopId = [70377, 70843]
    GameSupportURL = "https://www.nexusmods.com/dragonage/mods/6725"
    
    def init(self, organizer: mobase.IOrganizer):
        super().init(organizer)

        # Register features
        for feature in (
            BasicLocalSavegames(self.savesDirectory()),
            BasicGameSaveGameInfo(
                self._get_save_preview,
                self._get_save_metadata,
                ),
            DAOModDataChecker(organizer),
        ): self._register_feature(feature)
        
        # Set event handlers
        organizer.onPluginSettingChanged(self._handle_plugin_setting_changed)
        organizer.downloadManager().onDownloadComplete(self._handle_downloadComplete)
        organizer.modList().onModInstalled(self._handle_modInstalled)
        organizer.onAboutToRun(self._handle_aboutToRun)
        organizer.onFinishedRun(self._handle_finishedRun)
        organizer.onUserInterfaceInitialized(self._handle_user_interface_initialized)
        
        # Make DAO IOrganizer available to event handlers
        self._organizer = organizer

        # Make common paths available
        self._path_dict = {
            "base_dir"  : self._organizer.basePath(),
            "data_dir"  : self.dataDirectory().absolutePath(),
            "docs_dir"  : self.documentsDirectory().absolutePath(),
            "game_dir"  : self.gameDirectory().absolutePath(),
            "saves_dir" : self.savesDirectory().absolutePath(),
            "overwrite" : self._organizer.overwritePath(),
            }

        # Init DAOUtils for logging
        DAOUtils.setup_utils(organizer, self.name())

        return True   
       
    #################
    ### ini Files ###
    #################   
    def iniFiles(self):
        return ["DragonAge.ini", "KeyBindings.ini",
            "Addins.xml", "Offers.xml",
            "DAOriginsConfig.ini",]
    
    ###################
    ### Executables ###
    ###################
    def executables(self) -> list[mobase.ExecutableInfo]:
        """Set up DAO executables."""
        base_dir = self._organizer.basePath()
        game_dir = self.gameDirectory()
        exe_list = [
            mobase.ExecutableInfo(
                self.gameName(),
                game_dir.absoluteFilePath(self.binaryName()),
            ).withArgument("-enabledeveloperconsole"),
            mobase.ExecutableInfo(
                f"{self.gameName()} - Launcher",
                game_dir.absoluteFilePath(self.getLauncherName()),
            ),
            mobase.ExecutableInfo(
                "Explore Virtual Folder",
                DAOUtils.os_path(base_dir, "explorer++/Explorer++.exe"),
            ),            
            mobase.ExecutableInfo(
                "Tools: DAO - Config",
                game_dir.absoluteFilePath("bin_ship/DAOriginsConfig.exe"),
            ),
            mobase.ExecutableInfo(
                "Tools: DAO - Updater",
                game_dir.absoluteFilePath("bin_ship/DAUpdater.exe"), 
            ),
        ]
        return sorted(exe_list, key=lambda exe: str(exe.title()))

    ################
    ### Settings ###
    ################    
    _setting_descriptions = {
        "enable_logging" : (
            f"Toggles message logging to console (logs/mo_interface.log).<br><br>"
        ),
        "flatten_override" : (
            f"Removes all sub-directories from packages/core/override."
            f"<br><br>Files will be placed directly in the override directory."
            f"<br><br>This improves MO2s conflict detection for override files."
            f"<br><br>(Must re-install mod to reverse this.)<br><br>"
        ),
        "duplicate_warning" : (
            f"Used when flatten_override mode is active."
            f"<br><br>Detects duplicate files found in the mods override dir during install."
            f"<br><br>Displays a message box warning.<br><br>"
        ),
        "deploy_bin_ship" : (
            f"Deploys all files in mod folder bin_ship to game root bin_ship at game launch."
            f"<br><br>Restores game root to previous state when game stops."
            f"<br><br>Allows for binaries/load libraries to be managed from MO2."
            f"<br><br>(E.g, patched DAOrigins.exe, DXVK, DAFIX ).<br><br>"
        ),
        "build_addins_offers_xml" : (
            f"Dynamically builds Addins.xml and Offers.xml files on game launch."
            f"<br><br>Results based on installed DLC and other dazip mods."
            f"<br><br>Disable to manually manage Addins.xml and Offers.xml.<br><br>"
        ),
        "build_chargenmorphcfg_xml" : (
            f"Dynamically builds Chargenmorphcfg.xml file on game launch."
            f"<br><br>Results based on mods found in packages/core/overrides."
            f"<br><br>Disable to manually manage Chargenmorphcfg.xml.<br><br>"
        ),
        "inject_fomod_scripts" : (
            f"Repackages select mods with fomod install scripts on download."
            f"<br><br>Hopefully coverage will grow over time..."
            f"<br><br>Currently below mods are included:<br>"
            f" - Dain's Fixes"
            f"<br><br>"
        ),        
    }
    
    # Add DAO plugin settings to the settings menu
    def settings(self) -> list[mobase.PluginSetting]:
        return [
            mobase.PluginSetting(
                "enable_logging",
                self._setting_descriptions["enable_logging"],
                True,
            ),
            mobase.PluginSetting(
                "flatten_override",
                self._setting_descriptions["flatten_override"],
                False,
            ),
            mobase.PluginSetting(
                "duplicate_warning",
                self._setting_descriptions["duplicate_warning"],
                True,
            ),            
            mobase.PluginSetting(
                "deploy_bin_ship",
                self._setting_descriptions["deploy_bin_ship"],
                True,
            ),
            mobase.PluginSetting(
                "build_addins_offers_xml",
                self._setting_descriptions["build_addins_offers_xml"],
                True,
            ),
            mobase.PluginSetting(
                "build_chargenmorphcfg_xml",
                self._setting_descriptions["build_chargenmorphcfg_xml"],
                True,
            ),
            mobase.PluginSetting(
                "inject_fomod_scripts",
                self._setting_descriptions["inject_fomod_scripts"],
                True,
            ),            
        ]

    def _get_setting(self, key: str) -> mobase.MoVariant:
        return self._organizer.pluginSetting(self.name(), key)
    
    def _set_setting(self, key: str, value: mobase.MoVariant):
        self._organizer.setPluginSetting(self.name(), key, value)

    ##################
    ### Game Saves ###
    ##################
    _gender_dict = {"1" : "Male", "2" : "Female",}

    _race_dict = {"1" : "Dwarf", "2" : "Elf", "3" : "Human"}

    _class_dict = {"1" : "Warrior", "2" : "Mage", "3" : "Rogue"}

    _origin_dict = {
        "1" : "Dalish Elf", "2" : "Dwarf Commoner", "3" : "City Elf",
        "4" : "Circle Mage", "5" : "Human Noble", "6" : "Dwarf Noble",
        }
    
    _background_dict = {
        "DAO_PRC_EP_1" : "Grey Warden",
        "DAO_PRC_DRK"  : "Darkspawn",
        "DAO_PRC_LEL"  : "Orlesian",
        "DAO_PRC_GIB"  : "Grey Warden",
        "DAO_PRC_STR"  : "Grey Warden",
    }
    
    def _get_save_preview(self, save_path: Path):
        """Get character portrait if available."""
        char_path = save_path.parents[2]
        char_name = char_path.name
        portrait = char_path.joinpath(f"{char_name}_portrait.png")
        if portrait.exists():
            return portrait
        return save_path.parent.joinpath("screen.dds")
        
    def _get_save_metadata(self, save_path: Path, save: mobase.ISaveGame):
        """Get save meta data from character xml if available."""
        time = save.getCreationTime().toString()
        char_path = save_path.parents[2]
        char_xml = f"{char_path.name}.xml"
        char_dict = {"Creation Time" : time, "Name" : char_path.name}

        xml_path = char_path.joinpath(char_xml)
        if xml_path.exists():
            root = ET.parse(xml_path).getroot()
            root_dict = root.attrib
            char_dict.update({
                "Gender"       : self._gender_dict[root_dict["Gender"]],
                "Race"         : self._race_dict[root_dict["Race"]],
                "Class"        : self._class_dict[root_dict["Class"]],
                "Level"        : root_dict["Level"],
                "Origin"       : self._origin_dict[root_dict["Origin"]],
                #"Area"         : root_dict["Area"], # Note: Doesn't work well with DLC, etc.
                })
        
        story_path = save_path.parent.joinpath(f"{char_path.name}_Story.xml")
        if story_path.exists():
            module = ET.parse(story_path).getroot().attrib["Module"]
            if module in list(self._background_dict.keys()):
                char_dict.update({"Background" : self._background_dict[module]})

        return char_dict
    
    ####################
    ## Event Handlers ##
    ####################
    def _handle_plugin_setting_changed(self, plugin: str, setting: str, old: mobase.MoVariant, new: mobase.MoVariant):
        """Event Handler for onPluginSettingChanged"""
        if self.name() != plugin or old == new:
            return
        DAOUtils.log_message(f"Setting: {setting} changed from {old} to {new}")
        setting_desc = self._setting_descriptions[setting]
        if setting == "deploy_bin_ship" and new:
            # Warn of potential clash with root builder
            self._rootbuilder_warning()
        if setting == "flatten_override" and new:
            if not DAOUtils.show_message_box(
                f"Flatten packages/core/override?",
                [
                    f"Flatten packages/core/override for all mods?",
                    setting_desc,
                ],
                cancel = True,
            ): return self._set_setting(setting, False)
            mods_path = self._organizer.modsPath()
            DAOInstall.flatten_override_dir_all_mods(mods_path)         
        
    ## If download file is .dazip, rename to .zip ##
    def _handle_downloadComplete(self, download_id: int) -> None:
        """Event Handler for onDownloadComplete"""
        dm = self._organizer.downloadManager()
        src = dm.downloadPath(download_id)
        name, ext = DAOUtils.get_info(src)
        if ext.casefold() in {"dazip", "override"}:
            DAOInstall.convert_to_zip(src)
        if self._get_setting("inject_fomod_scripts"):
            DAOInstall.check_fomod_script(src, name)

    # Mod Installers:
    # Support for .dazip, 
    # Support for .override (with override config options)
    # Flattens packages/core/override to work with MO2 built in conflict checker
    # Root builder plugin supported
    def _handle_modInstalled(self, mod: mobase.IModInterface) -> None:
        """Event Handler for onModInstalled"""
        mod_name = mod.name()
        filetree = mod.fileTree()
        install_tasks = DAOInstall.queue_install_tasks(filetree)
        if not install_tasks.__len__(): 
            return
        mod_dir = mod.absolutePath()
        if not DAOInstall.execute_install_tasks(install_tasks, mod_dir):
            DAOInstall.warn_install_failed(mod_name)
            return
        if not self._get_setting("flatten_override"):
            return
        if not DAOInstall.flatten_override_dir(mod_dir):
            DAOInstall.warn_install_failed(mod_name)

    # On game launch:
    # - Deploy bin_ship
    # - Build addins.xml 
    # - Build offers.xml 
    # - Build chargenmorphcfg.xml
    # - Reverts changes when game stops.
    def _handle_aboutToRun(self, app_path: str) -> bool:
        """Event Handler for onAboutToRun""" 
        # Return false means game no launch
        if not self._is_game_triggered(app_path):
            return True
        game_dir = self.gameDirectory().absolutePath()
        overwrite = self._organizer.overwritePath()
        DAOUtils.log_message(f"Game launch detected: {app_path}")
        show_warning = False
        # Deploy bin files to game directory
        if self._get_setting("deploy_bin_ship"):
            if not DAOLaunch.deploy_secondary_files(app_path, self._path_dict, self._organizer):
                DAOUtils.log_message(f"Warning: Failed to deploy to bin_ship dir!")
                show_warning = True
        # Build Addins.xml and Offers.xml
        if self._get_setting("build_addins_offers_xml"):        
            if not DAOLaunch.build_addins_offers_xml(overwrite, game_dir, self._organizer):
                DAOUtils.log_message(f"Warning: Failed to build Addins.xml and/or Offers.xml")
                show_warning = True
        # Build Chargenmorph.xml
        if self._get_setting("build_chargenmorphcfg_xml"):
            if not DAOLaunch.build_chargenmorphcfg_xml(overwrite, game_dir, self._organizer):
                ovrd_path = "packages/core/override"
                DAOLaunch.hide_files("chargenmorphcfg.xml", game_dir, self._organizer, ovrd_path, True)
                DAOUtils.log_message(f"Warning: Failed to build Chargenmorphcfg.xml")
                show_warning = True
        # Report any failures                
        if show_warning:
            DAOUtils.show_message_box(
                header = "Warning!", 
                message = [
                    f"Something went wrong during game launch!<br><br>",
                    "Please see MO2 logs for more info.",
                ],
                link = f"file:///{self._path_dict["base_dir"]}/logs",
                link_name = "-- Log Directory --",
                warning = True,
                )
        DAOUtils.log_message(f"Launching Game...")
        return True

    def _handle_finishedRun(self, app_path: str, exit_code: int) -> None:
        """Event Handler for onFinishedRun"""
        if not self._is_game_triggered(app_path):
            return
        overwrite = self._organizer.overwritePath()
        profile = self._organizer.profile()
        profile_dir = profile.absolutePath()
        DAOUtils.log_message(f"Game stop detected: {app_path}")
        show_warning = False
        # Restore bin files in game directory
        if self._get_setting("deploy_bin_ship"):
            DAOUtils.log_message(f"Recovering bin_ship to previous state.")
            if not DAOLaunch.recover_secondary_dirs(app_path, self._path_dict, self._organizer):
                show_warning = True
        # Restore Addins.xml and Offers.xml
        if self._get_setting("build_addins_offers_xml"):
            DAOUtils.log_message(f"Restoring Addins.xml/Offers.xml.")
            for mod_type in ("Addins", "Offers"):
                if profile.localSettingsEnabled():
                    link_path = DAOUtils.os_path(profile_dir, f"{mod_type}.xml")
                    DAOUtils.log_message(f"Removing {mod_type}.xml link.")
                    if not DAOUtils.restore_backup(link_path):
                        if DAOUtils.remove_link(link_path, True):
                            continue
                        DAOUtils.log_message(f"Warning: Failed to restore profile dir: {profile_dir}.")
                        show_warning = True
                xml_path = DAOUtils.os_path(overwrite, "Settings", f"{mod_type}.xml")
                if not DAOUtils.restore_backup(xml_path):
                    if DAOUtils.remove_file(xml_path):
                        continue
                    DAOUtils.log_message(f"Warning: Failed to restore overwrite dir: {overwrite}.")
                    show_warning = True
        # Restore Chargenmorph.xml
        if self._get_setting("build_chargenmorphcfg_xml"):
            ovrd_path = "packages/core/override"
            game_dir = self.gameDirectory().absolutePath()
            chargen_path = DAOUtils.os_path(overwrite, ovrd_path, "Chargenmorphcfg.xml")
            DAOUtils.log_message(f"Restoring chargenmorphcfg.xml.")
            if not DAOLaunch.hide_files("chargenmorphcfg.xml", game_dir, self._organizer, ovrd_path, True):
                show_warning = True
            if not DAOUtils.remove_file(chargen_path):
                show_warning = True
        # Move any files in the overwrite dir back to settings dir
        DAOLaunch.move_save_game_files(profile, self._path_dict)
        # Remove empty sub-dirs from overwrite dir           
        DAOUtils.remove_empty_subdirs(overwrite)
        # Report any failures
        if show_warning:
            DAOUtils.show_message_box(
                header = "Warning!", 
                message = [
                    f"Something went wrong during game launch restore!<br><br>",
                    "Please see MO2 logs for more info:<br><br>",
                ],
                link = f"file:///{self._path_dict["base_dir"]}/logs",
                link_name = "-- Log Directory --",
                warning = True,
                )

    def _handle_user_interface_initialized(self, ui: QMainWindow) -> None:
        """Event Handler for onUserInterfaceInitialized"""
        if self._get_setting("deploy_bin_ship"):
            # Warn of potential clash with root builder
            self._rootbuilder_warning()
            # Recover bin dir if persisted bin list exists
            DAOLaunch.check_secondary_status(self._path_dict, self._organizer)

    # Check that the triggered app is the game itself
    def _is_game_triggered(self, app_path: str) -> bool:
        """Check if triggered process is the game."""
        game_dir = self.gameDirectory().absolutePath()
        game_bin = DAOUtils.os_path(game_dir,self.binaryName())
        launcher_bin = DAOUtils.os_path(game_dir,self.getLauncherName())
        return DAOUtils.os_path(app_path) in {game_bin, launcher_bin}
    
    def _rootbuilder_warning(self):
        """Warn of potential clash with root builder"""
        rootbuilder = self._organizer.isPluginEnabled("RootBuilder")
        if not rootbuilder:
            return
        DAOUtils.log_message("Warning: Rootbuilder plugin detected! Disable 'deploy_bin_ship' feature.")
        DAOUtils.show_message_box(
            header = "Warning: Rootbuilder plugin detected!", 
            message = [
                f"DAO plugin's 'deploy_bin_ship' feature is enabled.<br>",
                f"Rootbuilder is likely not compatible with this feature.<br><br>"
                f"Please remove Rootbuilder, or disable 'deploy_bin_ship'.<br><br>",
            ],
            warning = True,
            )
        self._set_setting("deploy_bin_ship", False)