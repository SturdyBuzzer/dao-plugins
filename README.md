# Mod Organizer 2 Plugins for Dragon Age: Origins

> A suite of advanced plugins that bring full Mod Organizer 2 (MO2) virtualization to *Dragon Age: Origins (DAO)*, fixing long-standing limitations, and incorporating the best community tools into the MO2 environment.

---

# DAO Mod Organizer 2 Plugins

## Table of Contents

1. [Main Features](#main-features)
2. [Extra Tools](#extra-tools)
3. [Installation](#installation)

---

## Main Features

### Full Virtualization of the Dragon Age User Folder

* The *entire* **DAO** user folder at
  `%UserProfile%\Documents\Bioware\Dragon Age` is now included in MO2’s virtualization.
* Previously this was limited to `packages\core\override`.
* Now **any** file (Settings, AddIns, Offers, etc.) can be overridden.
* Makes full use of Mod Organizer’s mod priority and conflict detection systems.

### Full Install Support for DAO Mod Types

* Automatically detects and installs **.dazip** packages.
* Supports **.override** packages (the ones built from [DAO-Modmanager](https://www.nexusmods.com/dragonage/mods/277)).
* Triggers any `OverrideConfig.xml` install scripts included with `.override` packages.
* Auto-sorting and management for Overrides, Docs, Binaries, etc.

### Dynamic `Addins.xml` and `Offers.xml` Generation

*(Settings → Plugins → Dragon Age Origins Support Plugin → `build_addins_offers_xml`)*

* On **game launch**, the plugin detects all installed **DLC** and `.dazip` mods currently active.
* Generates new `Addins.xml` and `Offers.xml` files in the MO2 `%BASE_DIR%/Overwrite` directory.
* Files are fully removed when the game stops.
* Original files in the user directory remain untouched.
* No more worrying about mods and DLC not being loaded into the game!

### Dynamic `Chargenmorphcfg.xml` Generation

*(Settings → Plugins → Dragon Age Origins Support Plugin → `build_chargenmorphcfg_xml`)*

* On **game launch**, detects all installed cosmetic/chargen mods (Hair, Eyes, Beard, etc.).
* Generates a new `Chargenmorphcfg.xml` in the MO2 `%BASE_DIR%/Overwrite` directory.
* Competing `Chargenmorphcfg.xml` files are temporarily hidden.
* Restored when the game stops.
* No more manual consolidation of chargenmorph files!
* Ensures all cosmetic mods show up in character creation.

### Auto-Deploy Mod Added Binaries/Executables

*(Settings → Plugins → Dragon Age Origins Support Plugin → `deploy_bin_ship`)*

* `bin_ship` is now a special sub-folder in your mods.
* On launch, the plugin deploys any files in `%Mods_Path%\<mod name>\bin_ship` into the game’s `%GAME_DIR%\bin_ship`.
* Useful for DXVK, DAFix, script extenders, etc.
* Restores the `bin_ship` directory when the game stops.

### Configurable Override Modes

*(Settings → Plugins → Dragon Age Origins Support Plugin → `flatten_override`)*

1. **Flatten Override (default):**

   * Auto flattens all sub-directories in `packages\core\override`.
   * Select your desired override files at the install mods dialog then click "ok" to auto-flatten.
   * Enables full conflict detection and priority handling via MO2.

2. **Old-school:**

   * Keeps `packages\core\override` directory structure intact.
   * Manual conflict resolution by alphabetical order (e.g., `zzz_myFavoritemod...`).
   * For those who like it the *old fashioned* way.

### Save Game Management

* Extends MO2’s **profile-local save games** to DAO saves.
* View DAO savegame metadata in MO2’s Saves tab.

---

## Extra Tools

*(Accessible from MO2’s **Tools** drop-down → puzzle piece icon)*

### DAODLCManager

*(Tools → Dragon Age: Origins – DLC Manager)*

1. **Download and Install Official DLC**

   * Detects currently installed DLC.
   * Lets you select, download, and install official DAO DLC.
   * Handles downloading, validation, and installation with proper metadata.
   * Archives stored in `%BASE_DIR%\plugins\dao_plugins\dlc_archive`.
   * Configurable option to delete archives after install.
     *(Settings → Plugins → Dragon Age: Origins – DLC Manager → `delete_archives`)*

2. **Manage DLC Install Location**

   * Choose where to store DLC files:

     * Game Directory
     * Data Directory (`%UserProfile%\Documents\Bioware\Dragon Age`)
     * Mods Directory
   * Selecting *Mods Directory* converts DLC into standalone MO2 mods for more control.
   * Enable/disable DLC like any other MO2 mod.
   * Easily revertible back to Game/Data directories.

3. **Fix DLC Item Transfer to Awakening**

   * Patches DLC items so they appear in the Awakening expansion.
   * Scans installed DLC and extracts only required files.
   * Creates a toggleable MO2 mod for the patch.
   * *Note: Items may require further modding for proper behavior.*

---

### DAOConflictChecker

*(Tools → Dragon Age: Origins – Conflict Checker)*

* Scans MO2’s virtual `packages\core\override` directory for file-name conflicts.
* Also checks inside Bioware’s `.erf` archives.
* Displays results in a **separate window** for reference while adjusting load order.
* Auto-refreshes after changes for **real-time conflict resolution**.
* Options to show full or relative paths.
* Paths can be copied to clipboard.
* Customizable font size.
  *(Settings → Plugins → Dragon Age: Origins – Conflict Checker → `font_point_size`)*
* Context menu options:

  * Copy Path
  * Expand All
  * Collapse All
  * Refresh View
  * Toggle Full Paths

---

## Installation

1. Install **Dragon Age: Origins**

   * Follow [Step 00 and Step 01](https://www.nexusmods.com/dragonage/mods/5610).
2. Run the game once to create the `%UserProfile%\Documents\Bioware\Dragon Age` directory.
3. Download the latest [Mod Organizer 2](https://github.com/ModOrganizer2/modorganizer/releases) (e.g. `Mod.Organizer-2.5.2.7z`) and extract it.
4. Download the latest **DAO Mod Organizer 2 Plugins** (from Nexus or [GitHub releases](https://github.com/SturdyBuzzer/dao-plugins/releases)).
5. Extract the `.zip` into your MO2 `%BASE_DIR%/plugins` directory.

   * *Optional:* create a `game` directory inside `%BASE_DIR%` and copy your DAO install files there.
     (See [Wabbajack docs](https://wiki.wabbajack.org/modlist_author_documentation/Keeping%20the%20Game%20Folder%20clean.html#stock-game) for more info.)
6. Start `ModOrganizer.exe` and create a portable instance.
7. Point the instance to your **Dragon Age: Origins** install directory (where `DAOriginsLauncher.exe` is located).

---

## 🧪 Developer Setup

<pre><code># Prerequisites
# - Mod Organizer 2.5.2+ (https://github.com/ModOrganizer2/modorganizer/releases)
# - Python 3.12.3+ (https://www.python.org/downloads/release/python-3123/)

# Clone this repo into your MO2 installation's "plugins" folder

# Enable and configure poetry (only once)
poetry --version
poetry config virtualenvs.in-project true
poetry install

# Open the repo in VSCode
# Select the correct interpreter:
# Ctrl+Shift+P → "Python: Select Interpreter" → Choose ".venv/Scripts/python.exe"
</code></pre>

---

## 📁 File Structure

```
├── basic_games
│   └── games
│       ├── dao_game/
│       │   └── *.py
│       └── game_dao.py
├── dao_plugins/
│   └── *.py
├── dao_tools/
│   └── DEPLOY.BAT
├── .gitignore
├── pyproject.toml
├── README.md
```