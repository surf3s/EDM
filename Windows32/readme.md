# Windows distribution without installing Python (32-bit test area)

The dist folder here contains a one file executable of the EDMpy program (edm.exe).  On Windows, download this file to a folder for the program, and it should run without the need to install Python or Python packages.  It works fine on my own Windows 10 computer and apparently works as well on Windows 11.

At times the source code might get ahead of this executable, but I will do my best to update it when major changes occur.

If you are developer, you can use the edmpy.spec file included here to rebuild a distribution of edm.exe.  The file build_windows.bat contains the proper syntax (python -m PyInstaller edmpy.spec).  Note that this command assumes that your are in a virtual environment with all the packages installed to run edmpy.  Note also that I was unable to make it work with the latest version of PyInstaller.  I recommend instead using pip install pyinstaller==4.10.  This version of PyInstaller worked fine for me.