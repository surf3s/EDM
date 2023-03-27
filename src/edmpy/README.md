# EDMpy (Beta)

[to be written - manual for CFG design and program use - for now refer to sample CFG files]

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

