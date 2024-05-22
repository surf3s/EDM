# Windows distribution without installing Python

The [dist folder](https://github.com/surf3s/EDM/tree/master/Windows/dist) here contains a one file executable of the EDMpy program [edm.exe](https://github.com/surf3s/EDM/raw/master/Windows/dist/edm.exe).  On Windows, download this file to a folder for the program, and it should run without the need to install Python or Python packages.  It works fine on my own Windows 10 and 11 computers.

At times the source code might get ahead of this executable, but I will do my best to update it when major changes occur.

If you are developer, you can use the edmpy.spec file included here to rebuild a distribution of edm.exe.  The file build_windows.bat contains the proper syntax (python -m PyInstaller edmpy.spec).  Note that this command assumes that your are in a virtual environment with all the packages installed to run edmpy.  Note also that I was unable to make it work with the latest version of PyInstaller.  I recommend instead using pip install pyinstaller==4.10.  This version of PyInstaller worked fine for me.

#### When it crashes.

For me, this version works without crashing.  But I know that other people using the program in different ways on different computers with different total stations will find bugs that crash the program.  To help me fix these problems, I recommend the following.  

First, send me the output from the program.  If you are on Windows and using the EDM.EXE provided here, the error message appears on a screen that instantly closes and is lost.  In those cases there are two methods to get me the error.  One, you can run the program from the command prompt instead of double-clicking it.  To do this, open a command prompt (cmd on Windows computers), navigate to the folder with the program, and run it by typing edm.exe.  Replicate your error and you should see the output there in your command prompt window.  Send this to me.  Two, there may be log files in a folder that looks something like this -  C:\Users\username\.kivy\logs\ where username is the name you use to log into Windows.  Note that the . before kivy may make the folder invisible.  You can get by that by telling Windows Explorer to show hidden files or by typing the path directly into the navigation box.  Have a look at the txt files in the log folder and the latest one should contain information on the program crash.

Second, when you write me, it is usually best to have the CFG and JSON file as well so I can fully replicate the problem.

Third, recently I have found that using your phone to record a video of what you are doing to crash the program saves a lot of time for you trying to explain to me what happened.  This step is optional though.

I am sorry when the program crashes as I want this to be as stable and useful as possible.  And I am very appreciative when you contact me for help.  While you may be worried about bothering me, at the same time, you will be saving others a lot of wasted time trying to solve a problem.

##### Virus Warning

Recently (May, 2024) I was helping someone put the program on a Windows 10 tablet.  However, the virus protection software (Microsoft) said the Windows exe version was a virus and immediately removed it.  It took a lot of time to find a work around.  Eventually we made exe programs a virus exception.  This is not a great solution.  I can assure you that edm.exe does not contain a virus.  I also personally downloaded the same version and scanned it with my virus detection software.  Nothing.  I will try to find a computer where I can replicate this and see what part of my program is giving this problem.  If you experience this as well, let me know.
