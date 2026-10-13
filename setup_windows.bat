@echo off
cd /d "%~dp0"
py -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
.venv\Scripts\python.exe manage.py migrate
if errorlevel 1 goto fail
echo Setup completed. For a new database, create an admin with:
echo .venv\Scripts\python.exe manage.py createsuperuser
pause
exit /b 0
:fail
echo Setup failed. Please copy the error message for troubleshooting.
pause
exit /b 1
