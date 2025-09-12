@ECHO OFF
SETLOCAL ENABLEEXTENSIONS
SET HOME=%~dp0..

SET ARCHIVE=%HOME%\dao_archive
SET RELEASE=%HOME%\dao_release

SET /P VERSION=<"%HOME%\VERSION"

ECHO:
ECHO Building DAO_Support_Plugin:

IF EXIST "%ARCHIVE%" (
    ECHO:
    ECHO Removing previous archive.
    RMDIR /S /Q "%ARCHIVE%"
)

ECHO:
ECHO Creating required directories.
MKDIR "%ARCHIVE%\basic_games\games\dao_game"
MKDIR "%ARCHIVE%\dao_plugins"

ECHO:
ECHO Copying Game DAO plugin files.
COPY /Y "%HOME%\basic_games\games\game_dao.py" "%ARCHIVE%\basic_games\games\game_dao.py"
COPY /Y "%HOME%\basic_games\games\dao_game\__init__.py" "%ARCHIVE%\basic_games\games\dao_game\__init__.py"
COPY /Y "%HOME%\basic_games\games\dao_game\DAOChargen.py" "%ARCHIVE%\basic_games\games\dao_game\DAOChargen.py"
COPY /Y "%HOME%\basic_games\games\dao_game\DAOModDataChecker.py" "%ARCHIVE%\basic_games\games\dao_game\DAOModDataChecker.py"
COPY /Y "%HOME%\basic_games\games\dao_game\DAOLaunch.py" "%ARCHIVE%\basic_games\games\dao_game\DAOLaunch.py"
COPY /Y "%HOME%\basic_games\games\dao_game\DAOInstall.py" "%ARCHIVE%\basic_games\games\dao_game\DAOInstall.py"
COPY /Y "%HOME%\basic_games\games\dao_game\DAOUtils.py" "%ARCHIVE%\basic_games\games\dao_game\DAOUtils.py"
COPY /Y "%HOME%\basic_games\games\dao_game\DAO_Addins.xml" "%ARCHIVE%\basic_games\games\dao_game\DAO_Addins.xml"
COPY /Y "%HOME%\basic_games\games\dao_game\DAO_Offers.xml" "%ARCHIVE%\basic_games\games\dao_game\DAO_Offers.xml"

ECHO:
ECHO Copying DAO Tools plugin files.
COPY /Y "%HOME%\dao_plugins\__init__.py" "%ARCHIVE%\dao_plugins\__init__.py"
COPY /Y "%HOME%\dao_plugins\dao_conflict_checker.py" "%ARCHIVE%\dao_plugins\dao_conflict_checker.py"
COPY /Y "%HOME%\dao_plugins\dao_dlc_data.xml" "%ARCHIVE%\dao_plugins\dao_dlc_data.xml"
COPY /Y "%HOME%\dao_plugins\dao_dlc_manager.py" "%ARCHIVE%\dao_plugins\dao_dlc_manager.py"
COPY /Y "%HOME%\dao_plugins\dao_utils.py" "%ARCHIVE%\dao_plugins\dao_utils.py"
COPY /Y "%HOME%\dao_plugins\dao.ico" "%ARCHIVE%\dao_plugins\dao.ico"
COPY /Y "%HOME%\dao_plugins\dao_addins.xml" "%ARCHIVE%\dao_plugins\dao_addins.xml"
COPY /Y "%HOME%\dao_plugins\dao_offers.xml" "%ARCHIVE%\dao_plugins\dao_offers.xml"

ECHO:
ECHO Building zip archive.
MKDIR "%RELEASE%" 2>NUL
tar -a -c -f "%RELEASE%\ModOrganizer-DAO-Plugins.%VERSION%.zip" -C "%ARCHIVE%" basic_games dao_plugins

ECHO:
ECHO Done. DAO_Support_Plugin built.

