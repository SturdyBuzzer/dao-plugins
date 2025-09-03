@ECHO OFF
SETLOCAL ENABLEEXTENSIONS
SET HOME=%~dp0..

SET ARCHIVE=%HOME%\dao_archive
SET RELEASE=%HOME%\dao_release

SET VERSION=0.1.0

ECHO:
ECHO Building DAO_Support_Plugin:

IF EXIST %ARCHIVE% (
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
COPY /Y basic_games\games\game_dao.py %ARCHIVE%\basic_games\games\game_dao.py >NUL
COPY /Y basic_games\games\dao_game\__init__.py %ARCHIVE%\basic_games\games\dao_game\__init__.py >NUL
COPY /Y basic_games\games\dao_game\DAOChargen.py %ARCHIVE%\basic_games\games\dao_game\DAOChargen.py >NUL
COPY /Y basic_games\games\dao_game\DAOModDataChecker.py %ARCHIVE%\basic_games\games\dao_game\DAOModDataChecker.py >NUL
COPY /Y basic_games\games\dao_game\DAOLaunch.py %ARCHIVE%\basic_games\games\dao_game\DAOLaunch.py >NUL
COPY /Y basic_games\games\dao_game\DAOInstall.py %ARCHIVE%\basic_games\games\dao_game\DAOInstall.py >NUL
COPY /Y basic_games\games\dao_game\DAOUtils.py %ARCHIVE%\basic_games\games\dao_game\DAOUtils.py >NUL

ECHO:
ECHO Copying DAO Tools plugin files.
COPY /Y dao_plugins\__init__.py %ARCHIVE%\dao_plugins\__init__.py >NUL
COPY /Y dao_plugins\dao_conflict_checker.py %ARCHIVE%\dao_plugins\dao_conflict_checker.py >NUL
COPY /Y dao_plugins\dao_dlc_data.xml %ARCHIVE%\dao_plugins\dao_dlc_data.xml >NUL
COPY /Y dao_plugins\dao_dlc_manager.py %ARCHIVE%\dao_plugins\dao_dlc_manager.py >NUL
COPY /Y dao_plugins\dao_utils.py %ARCHIVE%\dao_plugins\dao_utils.py >NUL
COPY /Y dao_plugins\dao.ico %ARCHIVE%\dao_plugins\dao.ico >NUL

ECHO:
ECHO Building zip archive.
MKDIR "%RELEASE%" 2>NUL
tar -a -c -f "%RELEASE%\ModOrganizer-DAO-Plugins.%VERSION%.zip" -C "%ARCHIVE%" .

ECHO:
ECHO Done. DAO_Support_Plugin built.

