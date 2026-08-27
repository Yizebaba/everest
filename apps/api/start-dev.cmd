@echo off
cd /d D:\Everest\apps\api
if "%EVEREST_DATABASE_URL%"=="" (
  echo EVEREST_DATABASE_URL must be supplied by the caller.
  exit /b 1
)
set EVEREST_API_HOST=127.0.0.1
set EVEREST_API_PORT=52147
echo Starting Everest API on http://127.0.0.1:52147
echo Keep this window open.
python run_dev.py
