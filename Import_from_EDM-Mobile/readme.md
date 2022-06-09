# Importing data from EDM-Mobile

EDMpy cannot directly read from the EDM-Mobile data file (.sdf).  Instead, to move your points, datums, units, and prisms from EDM-Mobile to EDMpy, you will need to follow these steps.  It is recommended that you make a backup of your existing EDMpy data file and CFG before importing data (see point 4 below).

1. Open EDM-Mobile, open the CFG file for the data to be exported, and select the Export ASCII option from the File menu.  Provide a name and a save location. EDM-Mobile will then write four CSV files with the points, units, datums and prisms.
2. Move these four files into a folder on the computer with EDMpy.  Start EDMpy, make sure you have the CFG you want to use open (normally the same CFG you were using with EDM-Mobile) and select the Import option from the File menu.
3. You will be asked which type of data you want to import. Only one type can be done at a time.  Select one of points, units, datums and prisms. Then you will be asked to point to the file on your computer containing these data (refer to point 2 above).
4. The data will then be added to the existing data file. IMPORTANT: Note that when the data already exist in your database, they will be overwritten by the import data without prompting. So, for instance, if you have a prism called Blue in your existing data file and you import a prism called Blue, the imported Blue prism will overwrite the existing one.

Two examples are given in the examples folder. In both cases, it is possible to first open the CFG file (e.g. BachoKiro.cfg) and then import the various points, units, prisms, and datums files to create a test data file.

Note that when importing points, there must be a field in the CFG for every field in the import data.  If you plan on dropping some fields, you will first need to import the data with the fields all present in the CFG, and then after the data are imported, you can delete these fields from the CFG (the data are not removed from the data file at that point but all new points will be recorded without those fields).

Note also that while EDMpy allows you to import points from EDM-Mobile, EDMpy (and EDM-Mobile) are not intended to be databases.  Rather, it is intended that periodically (even daily) you will export the data from EDMpy into a proper database and then erase the data from EDMpy.  If the the number of data points managed by EDMpy becomes too large, the program may become less responsive.