# EDMpy (Alpha)
The Python version of EDM-Mobile and EDMWin.

This is an Alpha version which I am making public so that some colleagues can test the program.  For me, Alpha means there are bugs and unfinished features.  The core functionality should be there (i.e. setup the total station, record and edit points, and export the data).  However, it is strongly recommended that you use this version with caution and that you have an alternative plan should it not work (e.g. EDM-Mobile or EDMWin).  What I am looking for here is feedback.  Note that I will be pushing bug and feature fixes to this site throughout the summer.  My hope is that I can reach Beta version by the end of the summer (i.e. I can find no bugs).

If you want to work with the source code rather than the Windows distributable provided here (see Windows folder), you can clone this repository, setup a virtual environment, and install the required packages (pip -r requirements.txt).  I don't advise doing this for now unless you are keen in part because I will be making modifications a lot through the summer of 2022.

#### Installation

##### Windows

A Windows exe file can be found in the folder [Windows](https://github.com/surf3s/EDM/tree/master/Windows/dist).  Download this file, place it in a folder where you want to start your data entry, and launch the program.

I have tested EDM thus far only on my own Windows 10 computer.  One user has reported that it runs on a Microsoft tablet running Windows 11.  I doubt it works on Windows 7 and it almost certainly does not work on Windows XP, but you really, really should not be using computers with either of those operating systems.

##### Mac OS

These instructions are similar to what is required for Linux.  Let me know if these instructions do not work.  I am not sure about python3-pip versus pip.  You may need to install pip instead of python3-pip with sudo apt install pip.  If python3 does not work, then try typing just python.  This will put you into python and tell you the version number.  Exit python with quit().  If the version is 3.0 or above, then you can replace python3 below with python.

```
pip install edm-arch --user
python3 -m edmpy
```

##### Android

I am not sure I will do an Android version or not.  I have look into how to connect a phone to a total station, and it doesn't look straightforward even with BlueTooth.  I will keep looking at this option.  Better will be to use a ChromeBook I think.

##### Linux

Currently untested, but normally......

```
pip install edm-arch
python -m edmpy
```

##### Update (June 21, 2022)
1. Fix a number of bugs (some of them important)
2. Added a screen called Test COM to help test serial connections to the total station
3. Started adding support for Sokkia.  I need someone who can help me debug this.
4. Made the logging actual log something useful.
5. Create a PyPi project called edm-py so that Linux and MacOS users can easily install the program

##### Update (July 1, 2022)
1. Tweaked the default CFG to carry unit and increment ID
2. Changed how increment works a bit (should work properly now)
3. Disabled multitouch to disable red dot on right mouse click
4. Check to see if mdf or sdf file is specified (from EDMWin and EDM-Mobile).
5. Change to json format and give warning
6. Check to see if json file can be found
7.   If not, new empty file is created and warning given
8.  Prism height - whether menu or manual - carries between shots
9.  Prism height menu - works better with keyboard (enter key and arrow keys)
10. A number of issues with using the program before opening a CFG fixed


Note that support currently only exists for Microscribes and Leica total stations.  Sokkia, Topcon and perhaps Nikon will come as I find people to work with.

