'''
As the lib folder is shared between EDM and E5, I place here the only things that are specific to each program.
In this way I can copy the other library code between programs without modifying it.
'''

__SPLASH_HELP__ = "\nEDM is a rewrite of the EDMWin and EDM-Mobile programs that Harold Dibble and I wrote for "
__SPLASH_HELP__ += "using total stations on archaeological sites.  The basic idea is to provide archaeologists with "
__SPLASH_HELP__ += "a tool that makes it easy to setup a grid on a site and piece provenience artifacts. Over time, "
__SPLASH_HELP__ += "because of changes in hardware and operating systems, the above mentioned programs are at risk "
__SPLASH_HELP__ += "of no longer working.\n\n"
__SPLASH_HELP__ += "This rewrite is in Python and uses libraires designed to make it work across Windows, Linux and "
__SPLASH_HELP__ += "MacOS.  The interface is also designed specifically for touch screens, but I am also striving to "
__SPLASH_HELP__ += "make it work well with keyboards too.  Fast, efficient and error-free are the goals.\n\n"
__SPLASH_HELP__ += "EDM uses configuration files that let you specify what kinds of fields you want to record with "
__SPLASH_HELP__ += "each point.  This is one of the main features of the program.  It also makes it easy to create "
__SPLASH_HELP__ += "menus to speed data entry and reduce errors.  This new program will read the previous CFG files. "
__SPLASH_HELP__ += "However, it will not read the previous data files.  To move data from those data files into this "
__SPLASH_HELP__ += "program, see the instructions on the GitHub web site - https://github.com/surf3s/EDM.\n\n"
__SPLASH_HELP__ += "This program is also open access.  My goal is to bring this tool to as many archaeologists as "
__SPLASH_HELP__ += "possible.  If you want to help me or you need help with the program, please contact me.\n\n"
__SPLASH_HELP__ += "Before you can start recording data points, you will need to open a previouus CFG file, create one, "
__SPLASH_HELP__ += "or use the default one provided here (see option in File menu).  Then you will need to configure "
__SPLASH_HELP__ += "your total station and test the connection (see options in Setup menu) or you can simulate a total station "
__SPLASH_HELP__ += "or use manual entry."

APP_NAME = 'EDM'
