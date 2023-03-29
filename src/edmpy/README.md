# EDMpy (Beta)

[in progess - manual for CFG design and program use - please refer also to sample CFG files]

This manual has two main sections.  The first section covers the operation of the program itself.  The second section covers configutation files.  Configuration files are key to EDMpy, but you can start using the program with the default
configation file that the program offers.

This manual does not cover program installation.  For that refer to the notes on the main page.

## A note about updating the program
I am actively working on this program.  I am currently fixing issues rather than adding new features.  Fixes are happening frequently enough that I recommend that you download the latest version before getting ready to go into the field.  However, once things are working, do not update (meaning especially not during a season).  I try very hard not to break the program when I fix it, but you never know.  So, if it is working, leave it alone.  If it is not working, let me know.  This is still a Beta program.  This means that it works (I have already been using it for several years), but there are still bugs/issues.  When I stop finding bugs, I will take it out of Beta (probably fall of 2023 after summer fieldwork experiences).  After this, I will keep debugging as things come up and add features as needed.

## Program Options

### File - Default CFG
This program option creates a basic CFG file that you can use to start recording points.  It includes some basic and some required fields that most archaeologists use.  You can use this CFG as a template to then modify to your specific needs.  Note that before you start using a total station, you will need to connect it (see Station Setup below).  Note that the name of the data file is specified in the CFG and can be viewed with Help - Status (see below).

### File - Open CFG
This program option opens a CFG for use.  It will likewise open the data file specified in the CFG.  The program will do its best to detect any errors in the configutation file and report them.

### File - Import
This option allows data from older versions of the EDM program to be migrated into this version.  It also allows data from other EDMpy data files to be imported.  This later option is useful, for instance, for moving datums, prisms, and units into a new data file.

### File - Export CSVs
This option exports points, prism, datums and units to a CSV file.

### File - Export GeoJSON
This option converts the data file (a JSON file) into a GeoJSON file.  The idea here was to make the data more easily readable in programs like qGIS.  However, GeoJSON is not a very flexible format and accepts only latitude/longitude.  So if you are recording normal total station data, you can convert it to GeoJSON and view it in qGIS, but the coordinate system will be wrong (if you know a correction for this, please let me know).  I am working on better solutions to this problem.  Also note that edits made to the GeoJSON file are not made to the main data file of EDMpy.

### File - Exit
Leave the program.  It is strongly recommended that you leave the program in this way before changing the configuration file or the data files to avoid conflicts.

### Setup - Configure Station
This option is where you tell EDMpy what survey instrument (if any) is connected to the computer and how.  Currently the program works with Topcon and Leica total stations.  It also works with Microscribes.  If you want to hand enter data, it accepts data as XYZ coordinates or as horizontal angle, vertical angle, and slope distance.  Handy entry can provide a useful back system when there is a connection issue with the total station during survey.

Two connection types are supported: serial and BlueTooth.  Note that for serial, you do not actually need a serial connection on your computer.  Instead, these days, you need either a USB cable from the total station manufacturer or a serial to USB converter cable if you are still using an older serial cable provided by your total station manufacturer.  In either case, when you connect the USB cable to your computer, a driver will normally be installed (on Windows anyway) that makes the USB connection look like a serial port.  This is what EDMpy needs.

I have less experience with BlueTooth, but I have successfully connected this program via BlueTooth to two Leica stations and a Topcon station.  To do this, you need to first connect your computer via BlueTooth to the total station (do this in your operating system and not in EDMpy).  Once connected, you may have to tell your operating system to treat this connection as a serial connection (more will be written on this later).  In some instances, this will just happen automatically.  Once this is done, the program will communicate with the station as if it were a serial connection (similar to what is described above for USB connections).

Serial connections require a number of parameters.  These include the speed (baud rate), parity, number of data bits, and the number of stop bits.  The available options for these paramaters are listed in dropdown menus within the program.  I have, since 1987, always used 1200 baud, 7 data bits, 1 stop bit, and even parity (1200,7,E,1).  Together these are known as Topcon settings (you will see this option listed in some Leica stations).  I strongly recommend that you start with these settings in the program and on the station.  If you want to later increase the speed, you can.  Probably most computers today can handle faster speeds, but I have seen some handheld computers fail at speeds like 9600 baud.  The time you save transfering what little data comes across is not worth the headache communication issues can create.

In my experience, getting the station to communicate with a program like EDMpy can take some time the first time you do it.  After that, except for cable failures, it pretty much just works every time.  So do not do it for the first time in the field.  Get it working first in the lab (preferably back at home where you have resources to fix problems).  Note too that if you are using BlueTooth, you can have issues with the connection being dropped.  If you use BlueTooth, I recommend having also a cable backup.  Always take two cables and never buy cheap cables (or cheap batteries for that matter).

### Station - Test COM
This option was added to help me and you debug connection issues and new types of total stations.  It lets you see what data are being send to the station and whether any data are being returned.  Setting the horizontal angle only is useful because it should register on the station's display even if there is a subsequent issue sending a confirmation back to EDMpy.  And recording a point is useful to see whether the shot launches, whether data are returned, and what format the data are in.

### Station - Initialize Station
This option setups of the geometry of the station and places it in your survey or site grid.  There are many ways this can be done, and I can not cover here all of the issues with each.  Normally, in my experience, you will use a two point setup.  This means that you will record two known points and the program will triangulate to calculate its location (see Verify Station as well).  This system is fast and reliable.  There are other ways to initialize.  You can use the over a datum plus record a datum method.  Because you are over a known point and looking at a known point, the program can know what the horizontal angle must be.  Then, once you record the known point, it can use the XYZ distances to calculate where it must be in the grid.  This method is sometimes useful at the start of excavation when first setting up the grid.  The program also lets you simply record a known point.  This case is similar to the one just metioned, however, in this instance the horizontal angle must be set manually prior to recording the point.  Normally one would do this by aligning the station along old excavation trenches or to an arbitrary point (for instance along the axis of the cave) or on north.  I think all stations allow you to set the horizontal angle to zero with a button or menu option on the station, but if you are using a different angle the set horizontal angle option here allows you to quickly upload an angle.  Finally, all of the options just described have the advantage of avoiding having to measure the height of the station above a datum directly under it.  I guess some new stations must do this automatically, but in older or less fancy stations this hand measurement is a source of considerable error in the Z.  Still, if you must do it this way, the program allows for this option.  You can set your horizontal angle, tell the program what point you are setup over, and the height of the station, and the program will calculate the new Z value (XY obviously stay the same as the datum).

There is one other option listed here - three datum shift.  This option is designed for instances when you are excavating a block taken from the site.  If you first record three points on this block while it is still in the site grid, you can then measure these three points again when the block is in the lab and EDMpy will do the math to thereafter place lab points into the site grid.  This conversion is done on the fly meaning that the XYZ that you see in the lab when recording a point will be the equivalent XYZ in the field grid.  We did this while using a Microscribe, and it worked extremely well.  It should work as well if using a total station in the lab while excavating there.

All of the above methods require that datums are first defined (or recorded).  See Station - Record Datums and Edit - Datums to do this.

It is strongly recommended that you verify your setup with an additional datum once you have initialized the station.  The main question I always get is what is an acceptable error.  There is no fixed answer for this question.  In my experience, however, a good setup in a cave site with datums well fixed on the wall can mean an error of only 1 or 2 mm in XY and 0 or 1 mm in Z.  If on the other hand you are setting up in a rain soaked field, then you might be lucky to get errors of 5 to 10 mm on XY.  It is also my experience that in a good setup, the error should not vary more than about 1 mm or 2 day to day.  In other words, you might find that you have an error of 5 or 6 mm and you can't do better than that no matter how hard you try.  I would then accept that error as the normal error for that setup, but I would also expect this error to remain constant throughout the season.  If this error bothers you day to day, I recommend that once you have the best setup you can achieve, you record a new set of datums (at least two plus a verification).  Normally (but not always - it depends on the type of problem you have), future setups on these points will show little to no error (though of course they are still off by the error you had as the start).

Common sources of small (and frustrating) error include not leveling the station, not centering the crosshairs on the prism, recording the point in the wrong mode (i.e. recording a prism but telling the station you are in reflectorless mode), incorrect prism heights, and mixing prisms (prisms each have their own offsets) or a mismatch between the actual prism and the prism the station thinks you are using.  Larger errors are usually something simple like a mismatch between the datum names and the actual points or datum coordinates entered incorrectly at the start.

Here again, as with communication problems, the first day on site can be rough and may take some time.  Thereafter, however, it should work day to day with no issues.

### Station - Verify Station
Use this option to check a setup.  Once you have recorded the verification datum, EDMpy will report back the error (see discuss of errors above).  I strongly recommend verifying each time you setup.  You can also use verify throughout the day to just check that things are okay.

### Station - Record Datums
Use this option to record new datums once the station is setup.  If you want to hand enter datums, use Edit - Datums.

### Station - Options
Currently there is only one option, namely whether the program prompts for a prism after each recorded point.  I normally do this (i.e. prompt each time), but if you are using the same prism each time, then you can save time this way.  You can also change the prism (and recalculate the Z) after a point is recorded.

### Edit - The Last Point
This is the easiest way to edit the last recorded point but it also lets you work your way through the data file point by point and it lets you search for (or filter) for particular points.  Points are displayed one at a time.  Do view the points in a grid view, see Edit - All Points.

### Edit - All Points
Here all points are displayed in a grid view.  The most recent points are at the top of the grid.  The grid scrolls left and right.  Tapping on any field allow that field to be modified.  Tapping on the first field highlights the record.  A highlighted record can then be viewed and modified on the Edit tab.  It can be deleted on the Delete tab.  

### Edit - Datums
This is the same as Edit - All Points except that it is for datums.  With datums you can also add new cases here,

### Edit - Units
This is the same as Edit - All Points except that it is for units.  With units you can also add new cases here.

### Edit - Prisms
This is the same as Edit - All Points except that it is for prisms.  With prisms you can also add new cases here.

### Edit - Settings
Here you can change some things about how the program looks and works.  They are pretty much self explainitory.  Some of the color and font options may require you to restart the program (though I am working on this).

### Delete - The last Point
The program offers to delete only the last recorded point.  Note that there is no undo option but you are asked to confirm.

### Delete - The last object
The program offers to delete the last set of points (same Unit-ID but different suffixes).  Note that there is no undo option but you are asked to confirm.

### Delete - All points
The program offers to empty the data file of all recorded points.  You are asked to confirm twice.  There is no undo.

### Delete - All datums
The program offers to empty the data file of all datums.  You are asked to confirm twice.  There is no undo.

### Delete - All units
The program offers to empty the data file of all units.  You are asked to confirm twice.  There is no undo.

### Delete - All prisms
The program offers to empty the data file of all prisms.  You are asked to confirm twice.  There is no undo.

### Help - Status, Log, INI, CFG, About
These screens provide some information about the program.  Status is useful for knowning where files are stored.  The log is useful for viewing what has been done.  The INI is mostly an internal thing to help me debug.  The CFG is a listing of your CFG.  Again, this is useful for understanding what is working and what is not.  However, at present, to change the CFG you need to exit the program.  Finally, about gives information that I might need to know what version of the program you are using.

### Record button, Continue Button and Measure Button
These three buttons are for recording points.  You can also add your own custom buttons (see below) that speed data recording but filling in fields automatically (e.g. a lithic shot).

Record begins a new object.  If there are increment fields (see below), these values will be incremented.  The suffix will be set to 0.

Continue measures a new point but keeps all the optional fields the same except for suffix which is incremented by 1 (the measurement fields of course change).  This option to group sets of points together using suffix is one of the main advantages of using EDMpy.  For instance, if you are recording two points on elongated objects to measure their orientation, you will record the first point with Measure and the second point with Continue.  In this way both points have the same identifying information and only the suffix will change.  Continuation is also useful for sets of topographic points, layer boundaries, large stones, etc.

Measure is used to know the coordinates of a point without recording it in the data file.  Measure is very useful for laying out squares, for checking level heights, for checking square boundaries, for trimming walls to a fix coordinate, etc.  Over the years we have called these points X-shots, but I use Measure here to make it more clear.

## Configuration Files

EDM (like E5) uses configuration files to specify the fields you want to record with each point and to list some basic options (e.g. the name of the database).  Writing a CFG may appear difficult at first, but most of the content is optional.  If you want to start quickly, EDM will make a default CFG for you.  You can then modify this to better suit your work.

In what follows, the basic configuration file options are listed.  A CFG file is organized into blocks with the field name in [brackets].  Field names are not case sensitive (i.e. [Level] is the same as [LEVEL]).  There is one special block called [EDM] where various options are stored.  Most of these are written automatically by EDM.  The main one you might want to modify is the name of the database file and the name of the data table within this database.  The other import one is called UNIQUE_TOGETHER.  This option is required and specifies which field(s) when combined create a unique key for each record (e.g. something like Unit, ID, Suffix).

Note that there are required fields.  These are Unit, ID, Suffix, X, Y and Z.  Internally, that is to say, within the database, these fields must have these names.  However, you can change how they look in the program by adding a prompt (e.g. Unit can become Square).  Note as well that there quite a few default fields that when used will be filled automatically by EDM.  These are detailed below but they include X, Y, Z, SLOPED, VANGLE, HANGLE, STATIONX, STATIONY, STATIONZ, LOCALX, LOCALY, LOCALZ, DATE, and PRISM.

## The database
EDM uses a JSON format database (see option below).  It is important to know that this database contains not only the recorded points but also tables that store the datums, the prisms and any unit definitions you might have.  Therefore, typically you will want to delete points (or prisms, datums and units) using the options within the program rather than by deleting the JSON file entirely.  If you delete the file or if you delete a point or the contents of a table from within the program, it is unrecoverable (i.e. there is no undo).  You can view the contents of a JSON file at any time by opening the file with a text editor (on Windows something like Notepad).

### The EDM block
Every configutation file will have an [EDM] block where general options are listed.  These are as follows.

#### UNIQUE_TOGETHER
Ever record needs to have a unique identifier.  This can be simply a running number or it can be something more complex like Unit, ID, Suffix.  The advantage to this option is that you can avoid duplicate IDs numbers.  The default that I strongly recommend is Unit, ID, Suffix.  You could also replace Unit with Sitename, ID, Suffix if you don't use excavation units or if ID number are unique to a site rather than an excavation unit.  EDM will not allow two records with the same combination of the UNIQUE_TOGETHER fields to be saved.  Note there is one important glitch in this system.  If you empty your data file, then one can duplicate a case coming from a previous data file.  A solution to this glitch is forthcoming.

```
[EDM]
UNIQUE_TOGETHER=UNIT,ID,SUFFIX
```

#### DATABASE
This option specifies the database filename.  EDM will add the path information automatically.  Databases are JSON files and so the extension should always be JSON.

```
[EDM]
UNIQUE_TOGETHER=UNIT,ID,SUFFIX
DATABASE=C:\Users\mcpherro\Local\Source\Python3\edmpy\CFGs\default.json
```

#### TABLE
This option specifies the table within the database where points are recorded.  A database can contain multiple tables of data.  For instance, in addition to the recorded points, EDM stores the prisms, datums and excavation units in this database.  Normally you will want only one set of points in a database table, but you could start a new table at any time by changing this value.

```
[EDM]
UNIQUE_TOGETHER=UNIT,ID,SUFFIX
DATABASE=C:\Users\mcpherro\Local\Source\Python3\edmpy\CFGs\default.json
TABLE=default
```

### Options for fields

A new field is defined by placing its name in brackets [].  A field should only be defined once.  Fields will be presented in the program in the order they appear in the configuration file.  Capitalization does not matter (EDM will capitalize all field names).  Quite a few characters are not allowed in field names.  This list includes most special characters (e.g. &*%$) and spaces.  This is done in part to help ensure field name compatibility with other databases.  You can replace spaces with underscores _.  

The following options help customize a field.  The format here is the option name followed by an equal sign and the option.  Lists, like menu lists, are comma separated.

#### Prompt
Prompt sets how the field will be asked for or listed in the program.  There is no length limit, but longer prompts may not format correctly depending on screen and font sizes.  An example is as follows:

```
[LEVEL]
PROMPT=Level :
```

#### TYPE
The type determines what values can be entered into a field.  Valid types are text, numeric, and menu.  Text allows any type of free format entry.  Numeric limits entry to valid numbers.  Menu allows one to limit entery to a fixed set of choices that will appear in a menu.  This option works in conjunction with the menu option (see next item).  For the default fields (see below) the type is handled automatically.

```
[ID]
PROMPT=ID :
TYPE=TEXT
```

#### Menu
The menu option lists valid menu entries for a menu type field.  These should be separated by a comma.  Empty items are automatically removed by EDM.

```
[CODE]
PROMPT=Code :
TYPE=MENU
MENU=Lithic,Bone,Tooth,Rock,Other
```

#### Length
The length option specifies the maximum length of an entry for that field.  Length is not required for numeric fields.  Length should probably not be used for menu fields.  But length can be useful for text fields.

```
[ID]
PROMPT=ID :
TYPE=TEXT
LENGTH=6
```

#### Required
This option specifies whether a value must be entered for this field.  Valid entries are TRUE and FALSE.  The default is FALSE meaning that if required is not specified as TRUE, then records with empty values for this field can be saved.

```
[CODE]
PROMPT=Code :
TYPE=MENU
MENU=Lithic,Bone,Tooth,Rock,Other
REQUIRED=TRUE
```

#### Increment
This option sets whether the value of this field will be automatically incremented with each new set of points.  Valid entries are TRUE and FALSE.  The default is FALSE.  This option is useful for ID fields to keep a running ID number.

```
[ID]
PROMPT=ID :
TYPE=TEXT
LENGTH=6
REQUIRED=TRUE
INCREMENT=TRUE
```

#### Carry
This option sets whether the field carries from one point to the next (note that all fields except suffix and the measurement fields carry when doing continuation points).  Valid entries are TRUE and FALSE.  The default is FALSE.  Carry is useful for fields that do not often change.  An example might be sitename.

```[SITENAME]
PROMPT=The site :
TYPE=TEXT
REQUIRED=TRUE
CARRY=TRUE
LENGTH=20
```

### Default fields

The following fields will be filled automatically by EDM after each recorded point.

[SLOPED]
Records the slope distance from the station to the recorded point.  The unit is meters.

[HANGLE]
Records the horizontal angle of the recorded point.  The unit is degrees, minutes and seconds.

[VANGLE]
Records the vertical angle of the recorded point.  The unit degrees, minutes and seconds.

[X]
Records the X coordinate.  This value is the local one returned from the station plus the current station coordinates.  Normally this is the value you will want to save.  The unit is meters.

[Y]
Records the Y coordinate.  This value is the local one returned from the station plus the current station coordinates.  Normally this is the value you will want to save.  The unit is meters.

[Z]
Records the Z coordinate.  This value is the local one returned from the station plus the current station coordinates.  Normally this is the value you will want to save.  The unit is meters.

[STATIONX]
Records the X coordinate of the current station location.  This value plus the local value returned from the station result in the X coordinate for each recorded point.  This value normally does not change until the station is setup again, but it can be useful for recovering later from mistakes.  The unit is meters

[STATIONY]
Records the Y coordinate of the current station location.  See STATIONX for more details.

[STATIONZ]
Records the Y coordinate of the current station location.  See STATIONX for more details.

[DATE]
Records the date and time of the recorded points.  The date format is date followed by time with a space between them.  Date is recorded as day, month, year.  Time is recorded on a 24 hour clock to the second.

[SUFFIX]
Records the shot number is a sequence of shots with the same Unit, ID.  The first shot is always SUFFIX 0.  Subsequent shots increase this counter by one.  New sequences are started with the Record button.  To make a sequence (i.e. record the second shot in a series) use the Continue button.  The unit is integer.

