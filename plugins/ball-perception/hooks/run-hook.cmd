@echo off
setlocal enabledelayedexpansion

set "HOOK_NAME=%~1"
set "PLUGIN_ROOT=%~dp0.."

if "%HOOK_NAME%"=="session-start-ball-perception" (
    echo [ball-perception] Initializing perception development environment...
    echo [ball-perception] Skills available: ball-detector, ball-tracker, ball-state-estimator, ball-geometry
    echo [ball-perception] Agents available: perception-architect, perception-developer, perception-reviewer
    echo [ball-perception] Run 'cat AGENTS.md' for team overview
)

exit /b 0
