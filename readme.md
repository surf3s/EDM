# EDMpy (Beta)

The Python version of EDM-Mobile and EDMWin.

This is now a Beta version which means that I am ready for other people to try to use it in field situations.  Beta means that I have eliminated the bugs that I know of but a) there are still bugs and b) users should proceed with some caution.  I would also recommend that if you do not have time to test extensively before going into the field, you should also have a backup option (e.g. EDM-Mobile or EDMWin).  By summer 2023 I will know better how the program is working.

If you want to work with the source code rather than the Windows distributable provided here (see Windows folder), you can clone this repository, setup a virtual environment, and install the required packages (pip -r requirements.txt).  I don't advise doing this for now unless you are keen in part because I will be making modifications a lot leading up to the summer of 2023.  If you are Mac user (or Linux), then the fastest way to start using the program is by installing it from PyPi (see below).

#### Installation

##### Windows

A Windows exe file can be found in the Windows folder listed above or [click here to download directly](https://github.com/surf3s/EDM/raw/master/Windows/dist/edm.exe).  Download this file, place it in a folder where you want to start your data entry, and launch the program.

I have tested EDMpy thus far on several Windows 10 and 11 computers.  I also have it running on an ARM ChromeBook (non-ARM ChromeBooks should work as well).  One user has reported that it runs on a Microsoft tablet running Windows 11.  Another  user is running it on Topcon tablets without issues.  I doubt it works on Windows 7 and it almost certainly does not work on Windows XP, but you really, really should not be using computers with either of those operating systems.

If you get a Windows error telling you that the program is incompatible with Windows 10 or 11, be sure that you have downloaded the complete program.  I have found that you can run a partially downloaded exe, in which case Windows will give an incompatability error.

##### Mac OS

These instructions are similar to what is required for Linux.  Let me know if these instructions do not work.  I am not sure about python3-pip versus pip.  You may need to install pip instead of python3-pip with sudo apt install pip.  If python3 does not work, then try typing just python.  This will put you into python and tell you the version number.  Exit python with quit().  If the version is 3.0 or above, then you can replace python3 below with python.

```
pip install edm-arch --user
python3 -m edmpy
```

If you already have edm-arch installed, you can upgrade it as follows.

```
pip install --upgrade edm-arch
```

##### Android

I am not sure I will do an Android version or not.  I have look into how to connect a phone to a total station, and it doesn't look straightforward even with BlueTooth.  I will keep looking at this option.  Better will be to use a ChromeBook I think.

##### Linux (and ChromeBook)

I have run the program on Linux and on the Linux subsystem for ChromeBooks (I will provide more information on this soon).  However, I have not tried to connect either to a total station (coming soon).

```
pip install edm-arch
python -m edmpy
```

If you already have edm-arch installed, you can upgrade it as follows.

```
pip install --upgrade edm-arch
```

#### What total station should I use?

Currently EDM is tested on Topcon and Leica.  For Topcon, I tested (in January of 2023) a model GM-55/EBL.  Topcon has kept their communication protocols very consistent over the last forty years.  The first version of this program was written for a Topcon GTS-3B, and I didn't change the code at all to work on the brand new GM-55.  My guess is that EDM will work on virtually any basic model of Topcon total station.  For Leica, I have tested an older Builder R200M, an older TCR403, a newer TS13 and a newer TS07.  Over the years, Leica introduced a new communications protocol called GeoCOM.  For a while I think some stations supported both the old protocol and the new GeoCOM.  Now I think they only support GeoCOM.  EDM supports both.

In the past EDM also worked with Sokkia stations.  I think I could make it work again with Sokkia stations, but I need someone to help me test them.  The same is true for Nokkia stations, though here I think I never had a successful test.  If someone wants to work with me on it, I am willing to try again.  If you are a programmer, make the code work with these types, place a pull request, and I will put the code into the main program here.

This version of EDM also works with Microscribes.  These are instruments built for taking 3D coordinates from objects.  However, we adapted them to excavate sediment blocks in the laboratory.  EDM will allow you to georeference these blocks so that as you record points, the XYZ coordinates are excavation grid coordinates rather than coordinates local to the Microscribe only.

#### What computer should I use?

Currently EDM is only fully tested on Windows 10 and 11.  However, the libraries used here are specifically designed to work on Windows, Linux, MacOS and even Android.  The only issue I see is serial port drivers (but see also below BlueTooth).  In the coming months, I will be testing EDM on a variety of platforms including ChromeOS.  If you have experience running it on other platforms, please let me know.  For Android, I will have to produce a separate installation that I hope to work on soon.

The main issues with a field computer are battery life and durability.  Now that the new program is written, I am looking for good field computers.  I have run both EDMWin and this version of EDM on a Topcon FC-6000 Geo Cell CE 128GB tablet with Windows 10.  This tablet is ruggized and comes with an exchangeable battery.  I will know better how they work in a few months, but it seems like a good solution.

#### How should I connect a computer to a total station?

There are two ways to connect to a total station: serial and BlueTooth.  Up to now, I only have experience with serial.  However, serial is not easy these days, and one of the main reasons I rewrote the program was to provide better support for BlueTooth.  Serial on a modern computer really means USB.  By far the easiest solution is to purchase a USB cable designed to work with your total station (by two - cables can fail - and don't buy cheap cables).  In the past, these cables sometimes also required a driver.  Alternatively, if you already have a serial cable for your total station, you can buy a serial to USB converter cable.  These are inexpensive and relatively easy to find.  You can have them in both USB Type A and C formats.  It may be less of an issue today, but in the past some serial to USB cables used chipsets that were not compatible with some computers.  Solving this problem will just take a bit of Internet research.  When the total station and computer are cabled, you will need to set the communications parameters in the station and in the EDM program.  I suggest using something slow and simple like 2400 (or 1200), E, 7, 1 (I have used 1200 baud, 7 databits, 1 stopbit and even parity since 1987).  If it works and you want to experiment with higher speeds, you can.  But start slow.  You will need to put the same settings into EDM and you will need to specify the COM port.  This latter can be a bit tricky, but EDM will scan your system to find available COM ports and from there you can test them.  If you are good with Windows device manager, you can typically find the COM port assigned to the USB cable there.  You can also use the Setup Test COM screen to see what is being sent to and received from the total station.

BlueTooth is also an option, and it works better and better these days.  First, of course, you need a BlueTooth equipped total station.  Enable BlueTooth in your station.  On the Leica TS07 there is no option to enter communications parameteres.  On the TS13 you could (but I am not sure it matters).  If you can set parameters, set them to something simple like 2400 baud, 7 databits, 1 stopbit, and even parity.  Second, enable BlueTooth on your computer and pair with the station.  For Leica, you might see more than one option for pairing.  When I tested it, the total station appeared as TS followed by a string of 7 digits (rather than an option like TPS radio LR BT).  Connecting to it might mean entering a code (it is 0000 for Leica).  Third, you will need to specify the COM port and the same protocol information (2400, E, 7, 1) in EDM (note: you don't need to set this in the Windows device manager - EDM will override these).  Trying to work out which COM port is the correct one can be challenging.  EDM will scan the available ports and report back.  Then you can try each.  To test the connection, use the Measure button on the main screen.  You can also use the Setup Test COM screen to see what is being sent to and received from the total station.

I don't have a lot of experience yet with BlueTooth but I know others that do use it with older version of this program.  For both BlueTooth and serial, making it work the first time can be a bit of a challenge, but once it works, it tends to work thereafter.  Note that BlueTooth will draw more power than serial.  If battery life is an issue, you might want to consider serial.  It is also good to have a serial option as a backup.

#### What data format does EDM use?

This new EDM program uses a plain text JSON database.  The advantage to this is that the program easily runs on multiple platforms (i.e. Windows, MacOS, Linux) and the data are not locked in a proprietary format.  The main downside I see to this format is that it is not as easy to view and repair the database as it was with Microsoft Access which gave a nice grid view of the data (like in spreadsheet program).  However, as of version 1.0.31, I made an important change that makes the JSON files easy to read in a text editor (i.e. they are formatted nicely).  It should now be easy to search for cases and view the data associated with each point.  Changes made in the JSON file are reflected in the program.  Still, while I understand that sometimes you need to edit your data this way, I still encourage doing it from within the program.  Note that EDM will also export the data in CSV format.  From there the data are easily imported into a number of different programs.  However, changes made to the CSV file are not reflected in the program (you could re-import the CSV but I have not tested this and would not recommend it for now).  CSV export is intended for when you want to move the data into another database.

#### How many points can I store in the database?

Short answer, I don't know.  I have simulated having 1000 points in the database and it is still reasonably fast and responsive on my laptop.  As you add more points, you can expect certain parts of the program to slow (e.g. opening the data grid to view all points).  I never intended my programs to be the main database a person uses.  I always envisioned doing some data entry with these programs (E5 and EDM) before moving the data into a real database.  However, I know lots of people who keep their entire dataset in these programs.  I think that is okay, but remember to always keep backups.

#### Why can't I plot the points with this program?

I am working on this.  Once this program is working smoothly, I will add plot functionality.


##### Update (March 2, 2023)
1.   Added and debugged Topcon stations
2.   Added and debugged Leica and Leica GeoCom stations
3.   Stopped program from exiting when escape is pressed
4.   Fixed default locations for ini, log, and data
5.   Program remembers last size and location of the screen
6.   Repeat button added to measure screen
7.   Flag to not prompt for prism each point added to options screen
10.  Misc. prism height issues addressed
11.  X box added to text boxes to help clearing values on touchscreen computers
12.  Prism menu added to edit record with update of Z on prism height change
13.  Improved text sizing in buttons to include word wrapping and dynamic sizing
14.  Improved the default CFG and carry and increment issues
15.  Fixed button font size on open dialog
16.  Length checking implemented (length in CFG is enforced during data entry)
17.  Prompt values (from CFG when provided) are used in Edit last record and New Record instead of the field name
18.  Empty entries in MENUs are removed
19.  Better error trapping of mistakes in the CFG
20.  First shot on empty data table put 1 in increment fields
21.  Fields shown in CFG order on delete record in gridview
22.  Can do offsets in the datagrid using +-
23.  Added save and revert buttons to case saving in datagrid (i.e. no longer saves immediately)
24.  Basic editing shortcuts (like cntl-c etc.) work in text boxes
25.  BlueTooth working on Leica GeoCOM stations
26.  Multiple UI fixes

##### Update (July 21, 2022)
1. Bugs in datagrid
2. Bugs in data filter in edit last record
3. Bug in starting path that meant a first CFG could not be opened

##### Update (July 18, 2022)
1. Bugs in editing that converted numeric values to string values

##### Update (July 16, 2022)
1. Microscribe setup asked for prism
2. Manual XYZ or VDH didn't work for setups
3. Welcome screen kept reappearing

##### Update (July 6, 2022)
1. Improvements in CSV file import
2. Some misc. bug fixing
3. Added CSV export to EDMWin (see oldstoneage.com website)

##### Update (July 1, 2022)
1. Tweaked the default CFG to carry unit and increment ID
2. Changed how increment works a bit (should work properly now)
3. Disabled multitouch to disable red dot on right mouse click
4. Check to see if mdf or sdf file is specified (from EDMWin and EDM-Mobile).
5. Change to json format and give warning#$
6. Check to see if json file can be found
7.   If not, new empty file is created and warning given
8. Prism height - whether menu or manual - carries between shots
9. Prism height menu - works better with keyboard (enter key and arrow keys)
10. A number of issues with using the program before opening a CFG fixed

##### Update (June 21, 2022)
1. Fix a number of bugs (some of them important)
2. Added a screen called Test COM to help test serial connections to the total station
3. Started adding support for Sokkia.  I need someone who can help me debug this.
4. Made the logging actual log something useful.
5. Create a PyPi project called edm-py so that Linux and MacOS users can easily install the program

