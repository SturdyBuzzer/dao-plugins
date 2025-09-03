import mobase

from PyQt6.QtCore import QCoreApplication, QPoint, Qt
from PyQt6.QtGui import QAction, QColor, QIcon
from PyQt6.QtWidgets import( 
    QDialog, QDialogButtonBox, QMenu,
    QScrollArea, QSizePolicy, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .dao_utils import DAOUtils

class DAOConflictChecker(mobase.IPluginTool):
    
    #################
    ## Plugin Meta ##
    #################
    AUTHOR = "SturdyBuzzer"
    DESCRIPTION = "Detects conflicts in Dragon Age: Origins packages/core/override directory."
    DISPLAYNAME = "Dragon Age: Origins - Conflict Checker"
    GAMENAME = "dragonage"
    ICON_PATH = "plugins/dao_plugins/dao.ico"
    NAME = "DAO Conflict Checker"
    TOOLTIP = (
        "Detects conflicts in Dragon Age: Origins packages/core/override directory.<br>"
    )
    VERSION = "1.0.0"
    SUPPORTURL = ""

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
                "font_point_size",
                f"Set the font size for the conflict checker display.<br>",
                int(10),
            ),
            mobase.PluginSetting(
                "show_full_paths",
                (
                    f"Toggles display of the full os path for conflicting files.<br>"
                    f"Default is relative to packages/core/override.<br>"
                ),
                False,
            )
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
        if setting == "font_point_size":
            self._set_font_size()
        elif setting == "show_full_paths":
            self._fill_conflict_tree()

    ###########################################
    ## Main runners for dao_conflict_checker ##
    ###########################################
    def _run_plugin_tool(self):
        """"Main plugin workflow"""
        # Init dao_utils for logging
        DAOUtils.setup_utils(self._organizer, self.name())

        self._organizer.onPluginSettingChanged(self._handle_plugin_setting_changed)

        self._conflict_dialog = QDialog()
        self._show_conflicts(self._conflict_dialog)
        #self._conflict_dialog.show()
   
    def _show_conflicts(self, dialog: QDialog):
        """Display the UI showing any detected file conflicts"""
        # Main Dialog box       
        dialog.setWindowTitle(self.displayName())
        dialog.setMinimumSize(720, 405)
        layout = QVBoxLayout(dialog)

        # QTreeWidget
        self._tree = QTreeWidget()
        tree = self._tree
        tree.setHeaderLabels(["Filename", "Conflicting Paths"])
        tree.setColumnCount(2)
        tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tree.setUniformRowHeights(False)

        self._fill_conflict_tree()
    
        header = tree.header()
        if header is not None:
            header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, header.ResizeMode.Interactive)
        
        tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tree.customContextMenuRequested.connect(self._set_context_menu)

        # QScrollArea for long lists
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(tree)

        # font
        self._set_font_size()

        layout.addWidget(scroll_area)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)

        # Make it a separate window (de-coupled)
        dialog.setWindowModality(Qt.WindowModality.NonModal)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowMinMaxButtonsHint)
        dialog.show()

    def _fill_conflict_tree(self):
        """Checks file paths for conflicts and adds to display tree"""
        tree = self._tree
        tree.clear()
        full_path = self._get_setting("show_full_paths")
        conflict_dict = self._scan_override_dir()
        for file, paths in conflict_dict.items():
            if len(paths) <= 1:
                continue
            header = f"{file} - x{len(paths)}"
            parent = QTreeWidgetItem([header])
            parent.setFirstColumnSpanned(True)
            
            paths.sort(key=DAOUtils.natural_sort_key)
            for i, path in enumerate(paths):
                symbol = "+" if i == len(paths) - 1 else "-"
                path = self._organizer.resolvePath(f"packages/core/override/{path}").casefold() if bool(full_path) else path
                child = QTreeWidgetItem(["", f"{symbol} {path}"])
                color = QColor("green") if symbol == "+" else QColor("red")
                child.setForeground(1, color)
                parent.addChild(child)
            tree.addTopLevelItem(parent)
        tree.expandAll()
        self._organizer.onNextRefresh(self._fill_conflict_tree, False)
    
    def _scan_override_dir(self) -> dict[str, list[str]]:
        """Scans override dir for paths by filename"""
        organizer = self._organizer
        vfs_tree = organizer.virtualFileTree()
        ovrd_path = "packages/core/override"
        ovrd_tree = vfs_tree.find(ovrd_path, mobase.IFileTree.FileTypes.DIRECTORY)
        if not isinstance(ovrd_tree, mobase.IFileTree):
            return {}
        file_dict: dict[str, list[str]] = {}
        for entry in DAOUtils.walk_tree(ovrd_tree):
            if entry.isDir():
                continue
            full_path = entry.pathFrom(ovrd_tree, '/').casefold()
            name = entry.name().casefold()
            file_dict.setdefault(name, []).append(full_path)
        
        return dict(sorted(file_dict.items()))
    
    def _set_context_menu(self, point: QPoint):
        """Add right-click menu options"""
        menu = QMenu(self._tree)
        expand_action = QAction("Expand All")
        collapse_action = QAction("Collapse All")
        refresh_action = QAction("Refresh")
        paths_action = QAction("Toggle Full Paths")
        menu.addActions([expand_action, collapse_action, refresh_action, paths_action])
        action = menu.exec(self._tree.mapToGlobal(point))
        if action == expand_action:
            self._tree.expandAll()
        elif action == collapse_action:
            self._tree.collapseAll()
        elif action == refresh_action:               
            self._fill_conflict_tree()
        elif action == paths_action:
            full_path = self._get_setting("show_full_paths")
            self._set_setting("show_full_paths", not bool(full_path)) 

    def _set_font_size(self):
        """Set the display font size"""
        size = str(self._get_setting("font_point_size"))
        tree = self._tree
        font = tree.font()
        font.setPointSize(int(size))
        tree.setFont(font)