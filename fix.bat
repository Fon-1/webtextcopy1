@echo off
python fixed_request.py
if %ERRORLEVEL% EQU 0 (
    echo Fix completed successfully.
    echo Now replacing the original file with the fixed version...
    copy /Y a_fixed.py a.py
    echo Done!
) else (
    echo Fix failed. Please check the error messages above.
)
pause  
