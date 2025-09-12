# Changelog

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