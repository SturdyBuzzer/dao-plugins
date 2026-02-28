import mobase

from PyQt6.QtCore import QCoreApplication, QPoint, Qt
from PyQt6.QtGui import QAction, QColor, QIcon
from PyQt6.QtWidgets import( 
    QApplication, QDialog, QDialogButtonBox, 
    QHBoxLayout, QLabel, QLineEdit, QMenu,
    QScrollArea, QSizePolicy, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .dao_utils import DAOUtils

class DAOConflictChecker(mobase.IPluginTool):
    
    #################
    ## Plugin Meta ##
    #################

    AUTHOR = "SturdyBuzzer"
    DESCRIPTION = f"Detects conflicts in Dragon Age: Origins data directory."
    DISPLAYNAME = "Dragon Age: Origins - Conflict Checker"
    GAMENAME = "dragonage"
    ICON_PATH = "plugins/dao_plugins/dao.ico"
    NAME = "DAO Conflict Checker"
    TOOLTIP = (
        f"Detects conflicts in Dragon Age: Origins data directory.<br>"
    )
    VERSION = "1.0.3"
    SUPPORTURL = "https://www.nexusmods.com/dragonage/mods/6725"

    ##################################
    ## IPluginTool Method Overrides ##
    ##################################
    def __init__(self):
        super().__init__()

    def init(self, organizer: mobase.IOrganizer) -> bool:
        self._organizer = organizer
        self._ignore_mods: set[str] = set()
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
                    f"Default is relative to conflict root dir.<br>"
                ),
                False,
            ),
            mobase.PluginSetting(
                "override_only",
                (
                    f"Toggles whether to only show conflicts between files in override.<br>"
                    f"Default (False) will show conflicts among all relevant data files.<br>"
                ),
                False,
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
        if setting == "font_point_size":
            self._set_font_size()
        elif setting in ("show_full_paths", "override_only"):
            self._fill_conflict_tree()

    def _clear_mod_ignore_list(self):
        """Clear the in-memory list of mods to ignore"""
        if self._ignore_mods:
            DAOUtils.log_message(f"Clearing mod ignore list")
            self._ignore_mods.clear()

    def _refresh_callback(self):
        """Function to be called on next refresh"""
        self._clear_mod_ignore_list()
        self._clear_filters()
        if self._conflict_dialog.isVisible():
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
        self._conflict_dialog.finished.connect(self._on_dialog_finished)
        self._show_conflicts(self._conflict_dialog)
        #self._conflict_dialog.show()
    
    def _on_dialog_finished(self, result: int):
        """Handle dialog finished event"""
        self._clear_filters()
        self._clear_mod_ignore_list()

    def _show_conflicts(self, dialog: QDialog):
        """Display the UI showing any detected file conflicts"""
        # Main Dialog box       
        dialog.setWindowTitle(self.displayName())
        dialog.setMinimumSize(720, 405)
        layout = QVBoxLayout(dialog)

        # Filter UI
        filter_row = QHBoxLayout()

        filter_row.addWidget(QLabel("Filter:"))

        self._filter_file = QLineEdit()
        self._filter_file.setPlaceholderText("File Name contains…")
        self._filter_file.textChanged.connect(self._apply_filters)
        filter_row.addWidget(self._filter_file)

        self._filter_mod = QLineEdit()
        self._filter_mod.setPlaceholderText("Mod Name contains…")
        self._filter_mod.textChanged.connect(self._apply_filters)
        filter_row.addWidget(self._filter_mod)

        self._filter_path = QLineEdit()
        self._filter_path.setPlaceholderText("File Path contains…")
        self._filter_path.textChanged.connect(self._apply_filters)
        filter_row.addWidget(self._filter_path)

        layout.addLayout(filter_row)        

        # QTreeWidget
        self._tree = QTreeWidget()
        tree = self._tree
        tree.setHeaderLabels(["File Name", "Mod Name", "File Path"])
        tree.setColumnCount(3)
        tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tree.setUniformRowHeights(False)

        self._fill_conflict_tree()
    
        header = tree.header()
        if header is not None:
            header.setMinimumSectionSize(180)
            for index in (0, 1, 2):
                header.setSectionResizeMode(index, header.ResizeMode.Interactive)
                
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

    def _get_conflict_root(self) -> str:
        """Set the root dir for conflict detection"""
        res = ""
        setting = bool(self._get_setting("override_only"))
        if setting:
            res = "packages/core/override"
        return res

    def _fill_conflict_tree(self):
        """Checks file paths for conflicts and adds to display tree"""
        tree = self._tree
        tree.clear()
        show_full_paths = self._get_setting("show_full_paths")
        ovrd_only = bool(self._get_setting("override_only"))
        conflict_dict = self._scan_conflict_dir()
        conflict_root = f"{self._get_conflict_root()}"
        if conflict_root not in ("", "."):
            conflict_root = f"{conflict_root}/"
        for file, paths in conflict_dict.items():
            if len(paths) <= 1:
                continue
            header = f"{file} - x{len(paths)}"
            parent = QTreeWidgetItem([header])
            parent.setFirstColumnSpanned(True)
            
            paths.sort(key=lambda p: (
                not (ovrd_only and ("/" in p or "\\" in p)),
                DAOUtils.natural_sort_key(p),
                ))
            
            for i, path in enumerate(paths):
                symbol = "+" if i == len(paths) - 1 else "-"
                if path.find(".erf") < 0:
                    res_path = path
                    erf = ""
                else:
                    res_path, file = path.rsplit(" -> ", 1)
                    erf = f" -> {file}" if bool(show_full_paths) else ""
                full_path = self._organizer.resolvePath(f"{conflict_root}{res_path}").casefold()
                mod_name = self._get_mod_name(full_path)
                path = full_path if bool(show_full_paths) else path
                child = QTreeWidgetItem(["", f"{mod_name}", f"{symbol} {path}{erf}"])
                color = QColor("lightgreen") if symbol == "+" else QColor("red")
                for index in (0, 1, 2):
                    child.setForeground(index, color)
                parent.addChild(child)
            tree.addTopLevelItem(parent)
        tree.expandAll()
        self._apply_filters()
        self._organizer.onNextRefresh(self._refresh_callback, False)

    _ignore_dirs = ("characters", "bin_ship", "docs", "logs", "settings")

    _ignore_files = ("manifest.xml")

    def _scan_conflict_dir(self) -> dict[str, list[str]]:
        """Scans conflict dir for paths by filename"""
        organizer = self._organizer
        vfs_tree = organizer.virtualFileTree()
        isRoot = False
        conflict_root = f"{self._get_conflict_root()}"
        if conflict_root in ("", "."):
            isRoot = True
            conflict_tree = vfs_tree
            conflict_root = ""
        else:
            conflict_tree = vfs_tree.find(conflict_root, mobase.IFileTree.FileTypes.DIRECTORY)
            conflict_root = f"{conflict_root}/"
        if not isinstance(conflict_tree, mobase.IFileTree):
            return {}
        file_dict: dict[str, list[str]] = {}
        for entry in DAOUtils.walk_tree(conflict_tree):
            if entry.isDir():
                continue
            base = entry.path().split('\\')[0]
            if isRoot and base.casefold() in self._ignore_dirs:
                continue
            rel_path = entry.pathFrom(conflict_tree, '/').casefold()
            full_path = self._organizer.resolvePath(f"{conflict_root}{rel_path}").casefold()
            mod_name = self._get_mod_name(full_path)
            if mod_name in self._ignore_mods:
                continue
            name = entry.name().casefold()
            if name in self._ignore_files:
                continue
            if not name.endswith(".erf"):
                file_dict.setdefault(name, []).append(rel_path)
                continue
            erf_list = DAOUtils.get_erf_paths(name, full_path)
            for name in erf_list:
                path = f"{rel_path } -> {name.casefold()}"
                file_dict.setdefault(name, []).append(path)
        return dict(sorted(file_dict.items()))
    
    def _get_mod_name(self, file_path: str) -> str:
        """Get the mod name for the current file"""
        mods_path = self._organizer.modsPath()
        rel_path = DAOUtils.get_rel_path(file_path, mods_path)
        if rel_path in (file_path, None):
            mod_name = "<Unmanaged>"
        else:
            mod_name = rel_path.split('\\')[0]
        return mod_name

    def _set_context_menu(self, point: QPoint):
        """Add right-click menu options"""
        menu = QMenu(self._tree)
        collapse_action = QAction("Collapse All")
        copy_action = QAction("Copy Path")
        expand_action = QAction("Expand All")
        ignore_action = QAction("Ignore Mod")        
        refresh_action = QAction("Refresh")
        paths_action = QAction("Toggle Full Paths")
        ovrd_action = QAction("Toggle Override Only")
        menu.addActions([collapse_action, copy_action, expand_action, ignore_action, refresh_action, paths_action, ovrd_action])
        action = menu.exec(self._tree.mapToGlobal(point))
        if action == copy_action:
            item = self._tree.itemAt(point)
            if item is None:
                return
            path = item.text(2)[2:].rsplit(" -> ", 1)[0]
            clipboard = QApplication.clipboard()
            if path and clipboard is not None:
                DAOUtils.log_message(f"Copy to clipboard: {path}")
                clipboard.setText(path)
        elif action == ignore_action:
            item = self._tree.itemAt(point)
            if item is None:
                return
            name = item.text(1)
            if not name:
                return
            DAOUtils.log_message(f"Adding '{name}' to ignore list.")
            self._ignore_mods.add(name)
            DAOUtils.log_message(f"Ignore list: {self._ignore_mods}")
            self._fill_conflict_tree()
        elif action == expand_action:
            self._tree.expandAll()
        elif action == collapse_action:
            self._tree.collapseAll()
        elif action == refresh_action:
            self._clear_filters()
            self._clear_mod_ignore_list()           
            self._fill_conflict_tree()
        elif action == paths_action:
            full_path = self._get_setting("show_full_paths")
            self._set_setting("show_full_paths", not bool(full_path)) 
        elif action == ovrd_action:
            ovrd_only = self._get_setting("override_only")
            self._set_setting("override_only", not bool(ovrd_only)) 

    def _set_font_size(self):
        """Set the display font size"""
        size = str(self._get_setting("font_point_size"))
        tree = self._tree
        font = tree.font()
        font.setPointSize(int(size))
        tree.setFont(font)

    def _clear_filters(self):
        """Remove current filters"""
        self._filter_file.blockSignals(True)
        self._filter_mod.blockSignals(True)
        self._filter_path.blockSignals(True)
        try:
            self._filter_file.setText("")
            self._filter_mod.setText("")
            self._filter_path.setText("")
        finally:
            self._filter_file.blockSignals(False)
            self._filter_mod.blockSignals(False)
            self._filter_path.blockSignals(False)
        self._apply_filters()

    def _apply_filters(self):
        """Filter conflict files"""
        if not hasattr(self, "_tree"):
            return

        file_q = self._filter_file.text().strip().casefold() if hasattr(self, "_filter_file") else ""
        mod_q = self._filter_mod.text().strip().casefold() if hasattr(self, "_filter_mod") else ""
        path_q = self._filter_path.text().strip().casefold() if hasattr(self, "_filter_path") else ""

        tree = self._tree

        for i in range(tree.topLevelItemCount()):
            parent = tree.topLevelItem(i)
            if parent is None:
                continue
            
            # Do any groups have matching value?
            group_matches = False
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child is None:
                    continue
                
                file_val = parent.text(0).casefold()
                mod_val = child.text(1).casefold()
                path_val = child.text(2).casefold()

                match = True
                if file_q and file_q not in file_val:
                    match = False
                if match and mod_q and mod_q not in mod_val:
                    match = False
                if match and path_q and path_q not in path_val:
                    match = False

                if match:
                    group_matches = True
                    break
            
            # If so hide other groups
            bool_hide = not (group_matches or (not file_q and not mod_q and not path_q))
            parent.setHidden(bool_hide)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child is None:
                    continue              
                child.setHidden(bool_hide)

        tree.expandAll()     