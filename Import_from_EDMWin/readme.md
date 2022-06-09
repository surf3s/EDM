# Importing data from EDMWin

EDMpy cannot directly read from the EDMWin data file (a Microsoft Access .mdb file).  Additionaly, EDMWin does not have an export option (I will add this).  Instead, to move your datums, units, and prisms from EDMWin to EDMpy, you will need to follow these steps.  It is recommended that you make a backup of your existing EDMpy data file and CFG before importing data (see point 4 below).

1. Open the EDMWin mdb file in Microsoft Access.  Open one of edm_poles, edm_units, or edm_datums in the standard grid view.
2. Click in the upper left corner to highlight the entire grid of data.
3. Right click on a data cell to have the menu of options, and select copy.
4. Open Excel.  right click in cell A1, select Paste (or Paste Special) and paste the data into a worksheet.
5. Select Save As from the File menu.  For Save as Type, select CSV (either MS-DOS or Mac depending on your system), provide a filename appropriate for the data type, and save the data. Ignore messages about potential data loss.
6. Start EDMpy, make sure you have the CFG you want to use open (normally the same CFG you were using with EDMWin) and select the Import option from the File menu.
7. You will be asked which type of data you want to import. Only one type can be done at a time.  Select one of points, units, datums and prisms. Then you will be asked to point to the file on your computer containing these data (refer to point 5 above).
8. The data will then be added to the existing data file. IMPORTANT: Note that when the data already exist in your database, they will be overwritten by the import data without prompting. So, for instance, if you have a prism called Blue in your existing data file and you import a prism called Blue, the imported Blue prism will overwrite the existing one.

An example is given in the examples folder. It is possible to first open the CFG file (e.g. lf.cfg) and then import the various points, units, prisms, and datums files to create a test data file.

Note that when importing points, there must be a field in the CFG for every field in the import data.  If you plan on dropping some fields, you will first need to import the data with the fields all present in the CFG, and then after the data are imported, you can delete these fields from the CFG (the data are not removed from the data file at that point but all new points will be recorded without those fields).

Note also that while EDMpy allows you to import points from EDMWin, EDMpy (and EDMWin) are not intended to be databases.  Rather, it is intended that periodically (even daily) you will export the data from EDMpy into a proper database and then erase the data from EDMpy.  If the the number of data points managed by EDMpy becomes too large, the program may become less responsive.