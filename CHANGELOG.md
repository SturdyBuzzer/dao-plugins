# Changelog

## v0.2.6
- Hotfix - Offers.xml generation was being skipped on game launch

## v0.2.5
- General cleanup and better error handling
**feature/manage_configs**
- Can now use MO2s ini Editor to manage DAO settings files
**feature/sort_exes**
- Sort executables in alphabetical order
**feature/data_checker_fixes**
- no longer treat .xml files as docs
- no data checking for already installed files, reduce annoying warnings
**feature/bin_ship_recovery**
- improved method of deploying bin_ship files with better backup and recovery
**feature/rootbuilder_warning**
- warns of potential clash between rootbuilder and deploy_bin_ship feature
**feature/repatriot_saves**
- Move any save files in the overwrite dir back to saves dir
**adhoc/bugfixes_2.5**
- Fixed some DLC manager stuff. Other minor fixes.

## v0.2.4
**feature/docs**
- now all docs type files will be placed in a subfolder corresponding to the mod name
- `docs/<mod_name>/*`

## v0.2.3
**feature/addins_fix**
- DLC detection previously overlooked DLC installed with no Manifest.xml (via DAUpdater.exe)
- Now Manifest.xml is not neccessary for DLC to be detected.
- Also, added a "golden" copy of Addins.xml and Offers.xml.
- The plugin will now build from these files and append any additional mods.
- Now no DLC should fail to load if fully installed.

## v0.2.2
**Adhoc/tempfix**
- Temp fix until I add feature to generate missing manifest.xml

## v0.2.1
**Adhoc/readme**
- Update to the README.md

## v0.2.0
**feature/get_erf_paths**
- DAO Conflict Checker now parses ERF archive files for conflicts  
- DAO Conflict Checker can copy file paths to clipboard from the context (right-click) menu
- github actions  

## v0.1.1
**fixes**
- Correct support URL to point to Nexus Mods page  
- Mod data checker now ignores `meta.ini` files  