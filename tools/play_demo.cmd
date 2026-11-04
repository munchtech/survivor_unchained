@echo off
rem Survivor Unchained: build the C# once (incremental, seconds when nothing changed), then run the game
rem from the main checkout. The Desktop shortcut "Survivor Unchained" points here.
setlocal
set REPO=C:\Users\munch\Desktop\survivorsunchained
set GODOT=C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe
cd /d "%REPO%\godot"
echo Building Survivor Unchained...
dotnet build "%REPO%\godot\SurvivorUnchained.sln" --nologo -v q -clp:ErrorsOnly
if errorlevel 1 (
  echo.
  echo BUILD FAILED. The game was not started. Tell the coordinator.
  pause
  exit /b 1
)
echo Starting the game...
start "" "%GODOT%" --path "%REPO%\godot"
endlocal
