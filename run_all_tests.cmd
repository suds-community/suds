::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::
:: Development script used on Windows to run the full suds-jurko test suite
:: using multiple Python interpreter versions.
::
:: Intended to be used as a general 'all tests passed' check. To see more
:: detailed information on specific failures, run the failed test group
:: manually, configured for greater verbosity that is done here.
::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
@setlocal

:: Commands for running specific Python interpreter versions.
@set PY243_X32=call py243
@set PY244_X32=call py244
@set PY276_X64=call py276
@set PY325_X64=call py325
@set PY333_X86=call py333_x86
@set PY333_X64=call py333

:: Python command-line options used for running specific scripts.
@set PYTEST_OPTIONS=-m pytest -q -x --tb=short
@set SETUP_OPTIONS=setup.py -q develop

@for %%i in ("%~f0\..") do @set SCRIPT_FOLDER=%%~fi
@cd /d "%SCRIPT_FOLDER%"

@echo ------------------------
@echo --- Python 3.3.3 x64 ---
@echo ------------------------
@if exist "build\" (rd /s /q build || goto :fail)
@%PY333_X64% %SETUP_OPTIONS% || goto :fail
@%PY333_X64% %PYTEST_OPTIONS% build || goto :fail
@echo.
@echo ----------------------------------------
@echo --- Python 3.3.3 x64 - no assertions ---
@echo ----------------------------------------
::Reuse the project built for the previous 'assertions enabled' test run.
::@if exist "build\" (rd /s /q build || goto :fail)
::@%PY333_X64% %SETUP_OPTIONS% || goto :fail
@%PY333_X64% -O %PYTEST_OPTIONS% build || goto :fail
@echo.

@echo ------------------------
@echo --- Python 2.4.3 x32 ---
@echo ------------------------
@%PY243_X32% %PYTEST_OPTIONS% || goto :fail
@echo.
@echo ----------------------------------------
@echo --- Python 2.4.3 x32 - no assertions ---
@echo ----------------------------------------
@%PY243_X32% -O %PYTEST_OPTIONS% || goto :fail
@echo.

@echo ------------------------
@echo --- Python 3.3.3 x86 ---
@echo ------------------------
@if exist "build\" (rd /s /q build || goto :fail)
@%PY333_X86% %SETUP_OPTIONS% || goto :fail
@%PY333_X86% %PYTEST_OPTIONS% build || goto :fail
@echo.
@echo ----------------------------------------
@echo --- Python 3.3.3 x86 - no assertions ---
@echo ----------------------------------------
::Reuse the project built for the previous 'assertions enabled' test run.
::@if exist "build\" (rd /s /q build || goto :fail)
::@%PY333_X86% %SETUP_OPTIONS% || goto :fail
@%PY333_X86% -O %PYTEST_OPTIONS% build || goto :fail
@echo.

@echo ------------------------
@echo --- Python 3.2.5 x64 ---
@echo ------------------------
@if exist "build\" (rd /s /q build || goto :fail)
@%PY325_X64% %SETUP_OPTIONS% || goto :fail
@%PY325_X64% %PYTEST_OPTIONS% build || goto :fail
@echo.
@echo ----------------------------------------
@echo --- Python 3.2.5 x64 - no assertions ---
@echo ----------------------------------------
::Reuse the project built for the previous 'assertions enabled' test run.
::@if exist "build\" (rd /s /q build || goto :fail)
::@%PY325_X64% %SETUP_OPTIONS% || goto :fail
@%PY325_X64% -O %PYTEST_OPTIONS% build || goto :fail
@echo.

@echo ------------------------
@echo --- Python 2.7.6 x64 ---
@echo ------------------------
@%PY276_X64% %PYTEST_OPTIONS% || goto :fail
@echo.
@echo ----------------------------------------
@echo --- Python 2.7.6 x64 - no assertions ---
@echo ----------------------------------------
@%PY276_X64% -O %PYTEST_OPTIONS% || goto :fail
@echo.

@echo ------------------------
@echo --- Python 2.4.4 x32 ---
@echo ------------------------
@%PY244_X32% %PYTEST_OPTIONS% || goto :fail
@echo.
@echo ----------------------------------------
@echo --- Python 2.4.4 x32 - no assertions ---
@echo ----------------------------------------
@%PY244_X32% -O %PYTEST_OPTIONS% || goto :fail
@echo.

@echo All tests passed.
@exit /b 0


:fail
    @echo.
    @echo Test failed.
    @exit /b -2
