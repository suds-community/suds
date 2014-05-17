::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::
:: "poor man's tox" development script used on Windows to run the full
:: suds-jurko test suite using multiple Python interpreter versions.
::
:: Intended to be used as a general 'all tests passed' check. To see more
:: detailed information on specific failures, run the failed test group
:: manually, configured for greater verbosity than is done here.
::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
@setlocal

:: Process script environment.
@for %%i in ("%~f0\..\..") do @set PROJECT_FOLDER=%%~fi
@cd /d "%PROJECT_FOLDER%"

:: Used pytest command-line options.
@set PYTEST_OPTIONS=-m pytest -q -x --tb=short

@call :test "3.4.0 x64" "py340"     || goto :fail
@call :test "2.4.3 x86" "py243"     || goto :fail
@call :test "2.7.6 x64" "py276"     || goto :fail
@call :test "3.4.0 x86" "py340_x86" || goto :fail
@call :test "2.4.4 x86" "py244"     || goto :fail
@call :test "3.3.3 x86" "py333_x86" || goto :fail
@call :test "3.2.5 x64" "py325"     || goto :fail
@call :test "3.3.3 x64" "py333"     || goto :fail
@call :test "3.3.5 x64" "py335"     || goto :fail
@call :test "2.5.4 x86" "py254_x86" || goto :fail
@call :test "2.5.4 x64" "py254"     || goto :fail
@call :test "2.6.6 x86" "py266_x86" || goto :fail
@call :test "2.6.6 x64" "py266"     || goto :fail
@call :test "2.7.6 x86" "py276_x86" || goto :fail
@call :test "3.1.3 x64" "py313"     || goto :fail
@call :test "3.2.5 x86" "py325_x86" || goto :fail
@call :test "3.3.5 x86" "py335_x86" || goto :fail

@echo All tests passed.
@exit /b 0


:fail
    @echo.
    @echo Test failed.
    @exit /b -2


:test
    @setlocal
    @set TITLE=%~1
    @set PYTHON="%~2"
    @if "%TITLE:~0,1%" == "2" goto :test__skip_build
        @echo ---------------------------------------------------------------
        @echo --- Building suds for Python %TITLE%
        @echo ---------------------------------------------------------------
        @if exist "build\" (rd /s /q build || exit /b -2)
    :test__skip_build
    :: Install the project into the target Python environment in editable mode.
    :: This will actually build Python 3 sources in case we are using a Python 3
    :: environment.
    @call %PYTHON% setup.py -q develop || exit /b -2
    @cd tests
    @echo.
    @echo ---------------------------------------------------------------
    @echo --- Testing suds with Python %TITLE%
    @echo ---------------------------------------------------------------
    @call %PYTHON% %PYTEST_OPTIONS% %LOCATION% || exit /b -2
    @echo.
    @echo ---------------------------------------------------------------
    @echo --- Testing suds with Python %TITLE% - no assertions
    @echo ---------------------------------------------------------------
    @call %PYTHON% -O %PYTEST_OPTIONS% %LOCATION% || exit /b -2
    @echo.
    @exit /b 0
