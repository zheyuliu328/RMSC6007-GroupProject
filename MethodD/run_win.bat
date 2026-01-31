@echo off
cd /d %~dp0
if not exist logs mkdir logs
if not exist outputs mkdir outputs
docker compose run --rm -T methodd
echo.
echo DONE. Outputs in .\outputs, logs in .\logs
pause