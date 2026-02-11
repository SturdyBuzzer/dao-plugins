import mobase

from pathlib import Path
from xml.etree import ElementTree as ET

from ..basic_features import BasicLocalSavegames, BasicGameSaveGameInfo
from ..basic_game import BasicGame

from .dao_game import *

########################
### Basic-Game Setup ###
########################
class DAOriginsGame(BasicGame):

    Name = "Dragon Age Origins Support Plugin"
    Author = "SturdyBuzzer"
    Version = "2.0"

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
        
        # Make DAO IOrganizer available to event handlers
        self._organizer = organizer

        # Init DAOUtils for logging
        DAOUtils.setup_utils(organizer, self.name())

        return True   
    
    #################
    ### ini Files ###
    #################   
    def iniFiles(self):
        return ["DragonAge.ini", "KeyBindings.ini",
            "DAOriginsConfig.ini", "Addins.xml",
            "Offers.xml", "Profile.dap"]
    
    ###################
    ### Executables ###
    ###################
    def executables(self) -> list[mobase.ExecutableInfo]:
        """Set up DAO executables."""
        game_dir = self.gameDirectory()
        return [
            mobase.ExecutableInfo(
                self.gameName(),
                game_dir.absoluteFilePath(self.binaryName()),
            ).withArgument("-enabledeveloperconsole"),
            mobase.ExecutableInfo(
                f"{self.gameName()} - Launcher",
                game_dir.absoluteFilePath(self.getLauncherName()),
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

    ################
    ### Settings ###
    ################    
    _setting_descriptions = {
        "enable_logging" : (
            f"Toggles message logging to console (mo_interface.log).<br><br>"
        ),
        "flatten_override" : (
            f"Removes all sub-directories from packages/core/override."
            f"<br><br>Files will be placed directly in the override directory."
            f"<br><br>This improves MO2s conflict detection for override files."
            f"<br><br>(Must re-install mod to reverse this.)<br><br>"
        ),
        "deploy_bin_ship" : (
            f"Deploys all files in mod folder bin_ship to game root bin_ship at game launch."
            f"<br><br>Restores game root to previous state when game stops."
            f"<br><br>Allows for binaries/load libraries to be managed from MO2."
            f"<br><br>(E.g, patched DAOrigins.exe, DXVK, DAFIX )."
        ),
        "build_addins_offers_xml" : (
            f"Dynamically builds Addins.xml and Offers.xml files on game launch."
            f"<br><br>Results based on installed DLC and other dazip mods."
            f"<br><br>Disable to manually manage Addins.xml and Offers.xml.<br><br>"
        ),
        "build_chargenmorphcfg_xml" : (
            f"Dynamically builds Chargenmorphcfg.xml file on game launch.<br><br>"
            f"<br><br>Results based on mods found in packages/core/overrides."
            f"<br><br>Disable to manually manage Chargenmorphcfg.xml.<br><br>"
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
                #"Area"         : root_dict["Area"],
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
        ext = DAOUtils.get_ext(src)
        if not ext.casefold() in {"dazip", "override"}:
            return
        dst = f"{src.removesuffix(f".{ext}")}.zip"
        DAOUtils.move_file_overwrite(f"{src}.meta", f"{dst}.meta")
        DAOUtils.move_file_overwrite(src, dst)

    # Mod Installers:
    # Support for .dazip, 
    # Support for .override (with override config options)
    # Flattens packages/core/override to work with MO2 built in conflict checker
    # Root builder plugin supported
    def _handle_modInstalled(self, mod: mobase.IModInterface) -> None:
        """Event Handler for onModInstalled"""
        mod_name = mod.name()
        filetree = mod.fileTree()
        rootbuilder = self._organizer.isPluginEnabled("RootBuilder")
        install_tasks = DAOInstall.queue_install_tasks(filetree, rootbuilder)
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
        # Move bin_ship files to game root
        if self._get_setting("deploy_bin_ship"):
            bin_ship = DAOUtils.os_path(game_dir, "bin_ship")
            self._bin_list = DAOUtils.list_files(bin_ship)
            if not DAOLaunch.deploy_bin_ship(game_dir, self._organizer, True):
                DAOUtils.log_message(f"Deploy to bin_ship failed.")
        # Build Addins.xml and Offers.xml
        if self._get_setting("build_addins_offers_xml"):
            if not DAOLaunch.build_addins_offers_xml(overwrite, game_dir, self._organizer):
                DAOUtils.log_message(f"Failed to build Addins.xml and/or Offers.xml")
        # Build Chargenmorph.xml
        if self._get_setting("build_chargenmorphcfg_xml"):
            if not DAOLaunch.build_chargenmorph(overwrite, game_dir, self._organizer):
                DAOUtils.log_message(f"Failed to build Chargenmorphcfg.xml")
        DAOUtils.log_message(f"Launching Game...")
        return True

    def _handle_finishedRun(self, app_path: str, exit_code: int) -> None:
        """Event Handler for onFinishedRun"""
        if not self._is_game_triggered(app_path):
            return
        overwrite = self._organizer.overwritePath()
        DAOUtils.log_message(f"Game stop detected: {app_path}")
        # Restore bin_ship
        if self._get_setting("deploy_bin_ship"):
            game_dir = self.gameDirectory().absolutePath()
            if not DAOLaunch.deploy_bin_ship(game_dir, self._organizer, False):
                DAOUtils.log_message(f"Deploy bin_ship (reverse) failed.")
            bin_ship = DAOUtils.os_path(game_dir, "bin_ship")
            bin_list = DAOUtils.list_files(bin_ship)
            if not DAOLaunch.clean_bin_ship(bin_ship, overwrite, self._bin_list, bin_list):
                DAOUtils.log_message(f"Clean bin_ship failed.")
        # Restore Addins.xml and Offers.xml
        if self._get_setting("build_addins_offers_xml"):
            for mod_type in ("Addins", "Offers"):
                xml_path = DAOUtils.os_path(overwrite, "Settings", f"{mod_type}.xml")
                DAOUtils.remove_file(xml_path)
        # Restore Chargenmorph.xml
        if self._get_setting("build_chargenmorphcfg_xml"):
            ovrd_path = "packages/core/override"
            game_dir = self.gameDirectory().absolutePath()
            chargen_path = DAOUtils.os_path(overwrite, ovrd_path, "Chargenmorphcfg.xml")
            DAOLaunch.hide_files("chargenmorphcfg.xml", game_dir, self._organizer, ovrd_path, True)
            DAOUtils.remove_file(chargen_path)
        DAOUtils.remove_empty_subdirs(overwrite)
        
    # Check that the triggered app is the game itself
    def _is_game_triggered(self, app_path: str) -> bool:
        """Check if triggered process is the game."""
        game_dir = self.gameDirectory().absolutePath()
        game_bin = DAOUtils.os_path(game_dir,self.binaryName())
        launcher_bin = DAOUtils.os_path(game_dir,self.getLauncherName())
        return DAOUtils.os_path(app_path) in {game_bin, launcher_bin}