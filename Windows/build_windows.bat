del dist\*.exe
python -m PyInstaller edmpy.spec
move dist\edmpy.exe dist\edm.exe
dist\edm.exe