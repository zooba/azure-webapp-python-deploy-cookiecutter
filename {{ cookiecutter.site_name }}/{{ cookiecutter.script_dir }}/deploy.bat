@echo off
setlocal
pushd "%~dp0"
if not exist "%PYTHON%" where /q python && set PYTHON=python || where /q py && set PYTHON=py || echo Unable to find python.exe or py.exe && exit /B 1
if not exist site %PYTHON% -m pip install --target site -r deploy_requirements.txt
"%PYTHON%" deploy.py %*
popd
