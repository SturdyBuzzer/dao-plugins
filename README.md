# Mod Organizer 2 Plugins for Dragon Age: Origins

> A suite of advanced plugins that bring full Mod Organizer 2 (MO2) virtualization to *Dragon Age: Origins (DAO)*, fixing long-standing limitations, and incorporating the best community tools into the MO2 environment.

---

## Features

### 🔁 Full Virtualization of `Documents\BioWare\Dragon Age`

- Virtualizes the *full* DAO user folder — not just `packages/core/override`.
- Allows overriding **any** file `Settings`, `AddIns`, `Offers`, etc.
- Makes full use of Mod Organizer's VFS for mod priority and conflict detection.

---

### DAO Binary Launch Support

- Supports launching all official binaries from MO2:
  - `DAOriginsLauncher.exe`
  - `DAOriginsConfig.exe`
  - `DAUpdater.exe`, etc.

---

### 🧩 Seamless Mod Installation

- Automatically detects `.dazip` and `.override` packages downloaded from Nexus Mods.
- Installation support includes:
  - `.dazip` packages
  - [DAO-Modmanager](https://www.nexusmods.com/dragonage/mods/277) `.override` packages support.
  - (Including support for  `OverrideConfig.xml` install scripts).
- Auto-sorting and mangement for `Docs`, `Binaries`, etc.

---

### Supports mod added binaries.

- Deploys mod added binaries, script extenders, etc. to DAO *bin_ship* directory on game start.
- Restores game bin_ship directory to previous state when game stops.

---

### ⚙️ Configurable Override Modes

**Two override strategies:**

1. **Flattened (default)**  
   - Flattens all subdirectories into `packages/core/override`.
   - Enables full conflict detection and priority handling in MO2.

2. **Old-school**  
   - Keeps override directory structure intact.
   - Allows for manual conflict resolution by alphabetical order (zzz_myFavoritemods...).

---

### Dynamic Configuration File Generation

- **Addins.xml** and **Offers.xml** are dynamically generated at runtime based on enabled mods and DLC.
- No more broken installs or missing DLC!
- **Chargenmorphcfg.xml** is also auto-generated at runtime based on detected cosmetic mods.
- No need to manually merge chargenmorph files again.

---

### ✅ Save game management

- Extends MO2s local, profile-specific, save games feature to DAO saves.
- View game save data via MO2 UI.

---

### Stock Game Compatibility

- Compatible with [Stock Game Method](https://wiki.wabbajack.org/modlist_author_documentation/Keeping%20the%20Game%20Folder%20clean.html#stock-game) for Wabbajack-style modlists.

---

## 🛠 Tools

### 🔧 `DAODLCManager`

1. **Download and Install Official DLC**
   - Detects missing DLC automatically.
   - Handles downloading and installs with correct metadata generation.

2. **Manage DLC Install Location**
   - Choose where to store DLC files.
   - Convert DLC to standalone MO2 mods for better control.
   - Enable/disable DLC like any other mod.

3. **Fix DLC Item Transfer to Awakening**
   - Patches DLC items to appear in Awakening expansion.
   - *Note: Makes items available, does not guarantee items behave correctly.*

---

### `DAOConflictChecker`

- Scans the VFS override directory for filename conflicts.
- Persists results in a **separate window** for reference while editing MO2 load order.
- Context menu allows:
  - Expand/Collapse all
  - Refresh view
- Optionally shows full paths or paths relative to `packages/core/override`.

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