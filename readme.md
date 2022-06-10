# EDMpy (Alpha)
The Python version of EDM-Mobile and EDMWin.

This is an Alpha version which I am making public so that some colleagues can test the program.  For me, Alpha means there are bugs and unfinished features.  The core functionality should be there (i.e. setup the total station, record and edit points, and export the data).  However, it is strongly recommended that you use this version with caution and that you have an alternative plan should it not work (e.g. EDM-Mobile or EDMWin).  What I am looking for here is feedback.  Note that I will be pushing bug and feature fixes to this site throughout the summer.  My hope is that I can reach Beta version by the end of the summer (i.e. I can find no bugs).

If you want to work with the source code rather than the Windows distributable provided here (see Windows folder), you will need to clone this repository, setup a virtual environment, and install the required packages (pip -r requirements.txt).  I don't advise doing this unless you are keen.  Rather, if you give me some time, I will turn this program into a Python package on PyPi so that it can be easily installed and updated with pip install edmpy.

![Tests](https://github.com/surf3s/EDM/actions/workflows/tests.yaml/badge.svg)