[in progress]

# Configuration Files

One of the important aspects of EDM is the configuration file.  While you do not have to use your own configuration file (you can instead use the default configuration file EDM provides), configuration files are what allow you to customize EDM for your survey or excavations.  A configuration file contains a list of the fields you want to attach to each recorded point.  EDM provides many default fields (e.g. X, Y, Z)

## Blocks

The configuration file is made of blocks.  Each block groups a set of like things.  Blocks are identified by brackets.  So, for instance, every file will have an EDM block where defaults for the configuration file are stored.  Here is an example:

```
[EDM]
DATABASE=C:\Users\mcpherro\Local\Source\Python3\edm\CFGs\test_b.json
TABLE=test_b
```

All of the settings stored in the EDM block are normally written by the program itself, but sometimes you may need to modify it as well. The names of the settings do not need to be in uppercase, but EDM will make them uppercase automatically.

In addition to the EDM block, you can define speed buttons with blocks (see below) and fields to record (see next section).

## Data fields

The primary thing you will want to do is make (or modify the default configuration file) to record just the observations you want to make for each points.  Each field is defined as a block with brackets.  After that you can define a number of options as listed here.  The order in which the fields appear in the configuration file is the order in which they will appear on screen in the EDM program.  You can change the order at any time and it will not impact the database.  You can also delete and add fields at any time.

### Default data fields

There are a number of field names that you can use to collect data from the total station automatically.  These are X, Y, Z, SLOPED, HANLGE, VANGLE, STATIONX, STATIONY, STATIONZ, LOCALX, LOCALY, LOCALZ, PRISM and DATE.  X, Y and Z are the points in the global grid.  Normally these are the data you want from the total station.  The X, Y, and Z are computed from the slope distance (SLOPED), horizontal angle (HANGLE), and vertical angle (VANGLE) passed to the program from the station and added to the current station coordinates of STATIONX, STATIONY, and STATIONZ.  LOCALX, LOCALY, and LOCALZ are relative to the station only (i.e. local coordinates as opposed to global coordinates).  The calculated height stored in Z reflects the prism height stored in PRISM.  Additionally the date and time of the record point are automatically stored in DATE.

After a shot is recorded, EDM goes through the list of fields in the configuration file and fills the default data fields with the appropriate data.  While only the X, Y and Z are normally needed, some users also like to record the raw data coming from the station and the current station coordinates in case an error occurs and a later recalculation with these data can fix it.

### User defined fields

In addition to the default fields, you can add your own fields.  Each field name is enclosed in brackets and can include the following settings.  Here is an example definition of a field:

```
[LEVEL]
PROMPT=Level :
TYPE=MENU
LENGTH=20
REQUIRED=TRUE
MENU=4A,4B,5A,5B,5C,SURFACE,BACKDIRT
```

#### PROMPT

Specifies how the field will be prompted on screen within the EDM program.

#### TYPE

There are the following field types: TEXT, NUMERIC, MENU.  A text field accepts any alphanumeric input.  A numeric field accepts only valid numbers.  A menu field prompts a list of menu options (see below).

#### LENGTH

Specifies the maximum length for a field.  Note that this can be changed at any time and it will not effect data already stored in the database.  LENGTH is not required for any field and is not useful for numeric fields.

#### MENU

The menu option lists the menus for a particular field.  You can specify these in advance or you can add them from within the program and they will be recorded here.

#### REQUIRED

When REQUIRED is set to TRUE, a response for this field is required before the record can be saved.

#### INCREMENT

When INCREMENT is set to TRUE, the numeric values in this field are incremented by 1 for each recorded point.  This option is useful for the ID field.

#### LINKED

This option also makes data entry faster.  The format is to list a set of fields linked to the particular field.  Consider this example:

```
[UNIT]
TYPE=TEXT
PROMPT=Unit
LENGTH=6
LINKED=SUFFIX,ID,LEVEL,EXCAVATOR
REQUIRED=TRUE
```

With this example, for every unique value of UNIT, the values of SUFFIX,ID,LEVEL,EXCAVATOR will be remembered as defaults.  So when you switch units, EDM will fill the SUFFIX,ID,LEVEL,EXCAVATOR with the last values used for these fields.  If any of these fields is also an INCREMENT field, then the value will be incremented as well.  Using linked fields with the UNIT field typically makes sense because you may have one person per unit, they will excavate one level at a time, and the ID numbers will be unique per unit.  Because of this, EDM also offers something called UNITCHECKING (see below).  UNITCHECKING allows a unit to be linked to a range of X and Y coordinates.  In this way, the measured coordinates determine what unit is filled into the UNIT field and then the linked fields are pulled in as well based on that unit.

Another way to do something like this is to link to a person.  So you might have a field that looks like this:

```
[EXCAVATOR]
TYPE=TEXT
PROMPT=Excavator
LENGTH=12
LINKED=UNIT,ID,SUFFIX,LEVEL
REQUIRED=TRUE
```

Here, after recording a point, you would first specify the excavator and then EDM will get the last UNIT, ID, SUFFIX and LEVEL.  This reduces errors and saves a lot of time entering values for each point.

## Speed Buttons
If you have common shot types, you can make a button to speed the recording of these shots by automatically filling in certain fields.
To do this, in the configuration file, create a block with the button number and then list the fields and their values.  A button should also have a title.  Here is an example three buttons to record a flint, a bone or a rock (in French).  Note that for the rock, the addition of ID = Alpha.  This tells EDM to fill in the ID field with random letters instead of the next number in the normal sequence.  We do this in our excavations for rocks, topographic points and other points that do not get on official ID number.

```
[BUTTON1]
TITLE=Silex
CODE=Silex

[BUTTON2]
TITLE=Os
CODE=OS

[BUTTON5]
TITLE=Cailloux
CODE=Cailloux
ID=Alpha
```

You can place these lines anywhere in the configuration file, but normally you will place them at the top just under the EDM block.

## UNITCHECKING


## UNITS

Units are specific to a database file, but you can export prisms easily as a CSV file (File Export CSV) and then import them into a different database (File Import).

## PRISMS

EDM keeps a table in the database where the heights of a set of prisms are stored.  Every prism has a name, a height and optionally an offset.  Heights and offsets are recorded in meters.  After each record point, it then becomes faster and easier to select the prism used from the menu of named prisms.  About offsets, prisms come with offsets.  What this means is that the measured distance is not the actual distance and so a correction is applied.  Normally, you want to let the total station do this.  So, for instance, most total stations will allow you to specify which prism type you are using (which normally varies by size).  After a point is recorded, the total station will then automatically apply the correction to the slope distance before passing this value to the EDM program.  This is the recommended way to do things.  However, if you are using prisms not recognized by your station, then EDM allows you to do these adjustments in the software.  In this case, you will have to be sure that the station is not also applying a correction.  A word of warning - this is really not recommended.  This is a last resort solution as the potential to confuse things and, for instance, apply two conflicting offsets at the same time, is very high.  I consider this an advanced user option, and I strongly recommend that you let the total station handle this part of measuring a point.

Prisms are specific to a database file, but you can export prisms easily as a CSV file (File Export CSV) and then import them into a different database (File Import).

## DATUMS

EDM keeps a table of datums to make station initialization easier.  With each datum there is a name and the three coordinates X, Y and Z.  You can add datums by hand in the Edit Datums menu.  You can also record datums with the total station in the Setup-Record Datums menu option.  Datums are specific to a database file, but you can export datums easily as a CSV file (File Export CSV) and then import them into a different database (File Import).