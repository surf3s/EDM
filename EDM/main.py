### EDM by Shannon McPherron
#
#   This is an alpha release.  I am still working on bugs and I am still implementing some features.
#   It should be backwards compatible with EDM-Mobile and EDMWin (but there are still some issues).

# ToDo
#   After XYZ are obtained, check units file, populate and maintain units file after save
#   Need to make prism menu after shot work
#   Make copy and paste work

#   A text field can be linked to another table. [future feature]
#   Think through making a field link to a database table (unique value is a table record)

# ToDo NewPlot
#   Read JSON file

# ToDo More Longterm
#   Add serial port communications
#   Add bluetooth communications

# ToDo Serial Communications with TS
#   Add maybe a simulate station type and a manual station type (maybe with VHD vs XYZ)
#   Debug with Dave's station

# Immediate To DO
#   arrow keys (and or tab keys) to move between fields in edit last record

__version__ = '1.0.15'
__date__ = 'August, 2021'
from serial.win32 import ERROR_INVALID_USER_BUFFER
from src.constants import __program__ 

__DEFAULT_FIELDS__ = ['X','Y','Z','SLOPED','VANGLE','HANGLE','STATIONX','STATIONY','STATIONZ','DATE','PRISM','ID']
__BUTTONS__ = 13
__LASTCOMPORT__ = 16

#Region Imports
from kivy.graphics import Color, Rectangle
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.factory import Factory
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.textinput import TextInput
from kivy.lang import Builder
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ListProperty, StringProperty, ObjectProperty, BooleanProperty, NumericProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.core.window import Window
from kivy import __version__ as __kivy_version__

# The explicit mention of this package here
# triggers its inclusions in the pyinstaller spec file.
# It is needed for the filechooser widget.
try:
    import win32timezone
except:
    pass

import os 
import random
import datetime
from math import sqrt
from math import pi
from math import cos
from math import sin

import re
import string
from platform import python_version

import logging
import logging.handlers as handlers

#import serial

# My libraries for this project
from src.blockdata import blockdata
from src.dbs import dbs
from src.e5_widgets import *
from src.constants import *
from src.colorscheme import *
from src.misc import *

# The database - pure Python
from tinydb import TinyDB, Query, where
from tinydb import __version__ as __tinydb_version__

#from plyer import gps
#from plyer import __version__ as __plyer_version__

from collections import OrderedDict

#from plyer import __version__ as __plyer_version__
__plyer_version__ = 'None'

#endregion

# get anglr.py library
# or get angles.py library (looks maybe better)

# use pySerial for serial communications
# io is used for input/output on the serial port
import serial
from time import sleep

if os.name == 'nt':  # sys.platform == 'win32':
    from serial.tools.list_ports_windows import comports
elif os.name == 'posix':
    from serial.tools.list_ports_posix import comports
#~ elif os.name == 'java':
else:
    raise ImportError("Sorry: no implementation for your platform ('{}') available".format(os.name))

#Region Data Classes
class point:
    def __init__(self, x = None, y = None, z = None):
        self.x = x
        self.y = y
        self.z = z

class datum:
    def __init__(self, name = None, x = None, y = None, z = None, notes = ''):
        self.name = name if name else None
        self.x = x 
        self.y = y 
        self.z = z 
        self.notes = notes

    def as_point(self):
        return(point(self.x, self.y, self.z))

class prism:
    def __init__(self, name = None, height = None, offset = None):
        self.name = name
        self.height = height if height else 0
        self.offset = offset if offset else 0

    def valid(self, data_record):
        if data_record['name'] == '':
            return('A name field is required.')
        if len(data_record['name']) > 20:
            return('Prism names should be 20 characters or less.')
        if data_record['height'] == '':
            return('A prism height is required.')
        if float(data_record['height'])>10:
            return('Prism height looks to large.  Prism heights are in meters.')
        if data_record['offset'] == '':
            data_record['offset'] == '0.0'
        if float(data_record['offset']) > .2:
            return('Prism offset looks to be too large.  Prism offsets are expressed in meters.')
        return(None)

class unit:
    def __init__(self, name = None, x1 = None, y1 = None, x2 = None, y2 = None, radius = None):
        self.name = name
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.radius = radius

    # This represents a dramatic change made to generalize the concept of linking fields
    # The idea is that the linked fields are listed in the CFG as an attribute of a field
    # And now any field can be a link driven field.
    # The issue is where to store the data - I think I try in the CFG as well.
    def update_linked_fields(self, new_record):
        for field_name in edm_cfg.fields():
            field = edm_cfg.get(field_name)
            if field.link_fields:
                defaults = {}
                for link_field in field.link_fields:
                    defaults[link_field] = new_record[link_field]
                field.defaults = defaults
                #edm_cfg.put(field)
                # Need a database for each of these
                # The name field in the database should be the key with is the fieldname 

class DB(dbs):
    MAX_FIELDS = 30
    db = None
    filename = None
    db_name = 'points'

    def __init__(self, filename = ''):
        self.filename = filename
        if self.filename:
            self.db = TinyDB(self.filename)

    def open(self, filename):
        try:
            self.db = TinyDB(filename)
            self.filename = filename
            self.prisms = self.db.table('prisms')
            self.units = self.db.table('units')
            self.datums = self.db.table('datums')
            return(True)
        except:
            return(False)

    def create_defaults(self):
        pass

    def get_unitid(self, unitid):
        unit, id = unitid.split('-')
        p = self.db.search( (where('unit')==unit) & (where('id')==id) )
        if p:
            return(p)
        else:
            return(None)

    def get_datum(self, name = ''):
        if name and self.db:
            a_datum = Query()
            p = self.db.table('datums').search(a_datum.NAME.matches('^' + name + '$', flags = re.IGNORECASE))
            #p = self.db.table('datums').search( (where('NAME') == name, flags = re.IGNORECASE) )
            if p != []:
                p = p[0]
                return(datum(p['NAME'] if 'NAME' in p.keys() else None,
                            float(p['X']) if 'X' in p.keys() else None,
                            float(p['Y']) if 'Y' in p.keys() else None,
                            float(p['Z']) if 'Z' in p.keys() else None,
                            p['NOTES'] if 'NOTES' in p.keys() else None))
        return(None)

    def delete_datum(self, name = ''):
        if name:
            a_datum = Query()
            self.db.table('datums').remove(a_datum.NAME.matches('^' + name + '$', flags = re.IGNORECASE))

    def get_unit(self, name):
        pass

    def get_prism(self, name):
        pass

    def unit_ids(self):
        name_list = []
        for row in self.db.table(self.table):
            name_list.append(row['UNIT'] + '-' + row['ID'])
        return(name_list)

    def names(self, table_name):
        name_list = []
        for row in self.db.table(table_name):
            if 'NAME' in row:
                name_list.append(row['NAME'])
        return(name_list)

    def fields(self):
        pass

    def delete_all(self, table_name = None):
        if table_name is None:
            self.db.drop_tables()
        else:
            self.db.table(table_name).truncate()

    def export_csv(self):
        pass

    def delete_record(self):
        pass

    def add_record(self):
        pass

    def point_in_unit(self, xyz = None):
        if xyz:
            for a_unit in self.db.table('units'):
                if 'XMAX' in a_unit.keys() and 'YMAX' in a_unit.keys() and 'XMIN' in a_unit.keys() and 'YMIN' in a_unit.keys():
                    if xyz.x <= float(a_unit['XMAX']) and xyz.x >= float(a_unit['XMIN']) and xyz.y <= float(a_unit['YMAX']) and xyz.y >= float(a_unit['YMIN']):
                        return(a_unit['NAME'])
        return(None)

    def get_link_fields(self, name = None, value = None):
        if name is not None and value is not None:
            try:
                q = Query()
                r = self.db.table(name).search(q[name].matches('^' + value + '$', re.IGNORECASE))
                if r is not []:
                    return(r[0])
                else:
                    return(None)
            except:
                return(None)
        return(None)

class INI(blockdata):

    def __init__(self, filename = ''):
        if filename=='':
            filename = __program__ + '.ini'
        self.filename = filename
        self.incremental_backups = False
        self.backup_interval = 0
        self.first_time = True
        self.debug = False

    def open(self, filename = ''):
        if filename:
            self.filename = filename
        self.blocks = self.read_blocks()
        self.first_time = (self.blocks == [])
        self.is_valid()
        self.incremental_backups = self.get_value(__program__,'IncrementalBackups').upper() == 'TRUE'
        self.backup_interval = int(self.get_value(__program__,'BackupInterval'))
        self.debug = self.get_value(__program__,'Debug').upper() == 'TRUE'

    def is_valid(self):
        for field_option in ['DARKMODE','INCREMENTALBACKUPS']:
            if self.get_value(__program__,field_option):
                if self.get_value(__program__,field_option).upper() == 'YES':
                    self.update_value(__program__,field_option,'TRUE')
            else:
                self.update_value(__program__,field_option,'FALSE')

        if self.get_value(__program__, "BACKUPINTERVAL"):
            test = False
            try:
                test = int(self.get_value(__program__, "BACKUPINTERVAL"))
                if test < 0:
                    test = 0
                elif test > 200:
                    test = 200
                self.update_value(__program__, 'BACKUPINTERVAL', test)
            except:
                self.update_value(__program__, 'BACKUPINTERVAL', 0)
        else:
            self.update_value(__program__, 'BACKUPINTERVAL', 0)

    def update(self, colors, cfg):
        self.update_value(__program__,'CFG', cfg.filename)
        self.update_value(__program__,'ColorScheme', colors.color_scheme)
        self.update_value(__program__,'ButtonFontSize', colors.button_font_size)
        self.update_value(__program__,'TextFontSize', colors.text_font_size)
        self.update_value(__program__,'DarkMode', 'TRUE' if colors.darkmode else 'FALSE')
        self.update_value(__program__,'IncrementalBackups', self.incremental_backups)
        self.update_value(__program__,'BackupInterval', self.backup_interval)
        self.save()

    def save(self):
        self.write_blocks()

    def status(self):
        txt = '\nThe INI file is %s.\n' % self.filename
        return(txt)

class CFG(blockdata):

    class field:
        name = ''
        inputtype = ''
        prompt = ''
        length = 0
        menu = ''
        increment = False
        required = False
        carry = False 
        unique = False
        link_fields = []
        def __init__(self, name):
            self.name = name

    def __init__(self, filename = ''):
        self.initialize()
        if filename:
            self.filename = filename

    def initialize(self):
        self.blocks = []
        self.filename = ""
        self.path = ""
        self.current_field = None
        self.current_record = {}
        self.BOF = True
        self.EOF = False
        self.has_errors = False
        self.has_warnings = False
        self.key_field = None   # not implimented yet
        self.description = ''   # not implimented yet
        self.gps = False
        self.link_fields = []
        self.errors = []
        self.unique_together = []

    def open(self, filename = ''):
        if filename:
            self.filename = filename
        return(self.load())

    def valid_datarecord(self, data_record):
        for field in data_record:
            f = self.get(field)
            value = data_record[field]
            if f.required and not value:
                return('Required field %s is empty.  Please provide a value.' % field)
            if f.length!=0 and len(value) > f.length:
                return('Maximum length for %s is set to %s.  Please shorten your response.  Field lengths can be set in the CFG file.  A value of 0 means no length limit.')
        if self.unique_together:
            pass
        
        return(True)

    def get(self, field_name):
        f = self.field(field_name)
        f.inputtype = self.get_value(field_name, 'TYPE')
        f.prompt = self.get_value(field_name, 'PROMPT')
        f.length = self.get_value(field_name, 'LENGTH')
        f.menu = self.get_value(field_name, 'MENU').split(",")
        link_fields = self.get_value(field_name, 'LINKED')
        if link_fields:
            f.link_fields = link_fields.upper().split(",")
        f.carry = self.get_value(field_name, 'CARRY').upper() == 'TRUE'
        f.required = self.get_value(field_name, 'REQUIRED').upper() == 'TRUE'
        f.increment = self.get_value(field_name, 'INCREMENT').upper() == 'TRUE'
        return(f)

    def put(self, field_name, f):
        self.update_value(field_name, 'PROMPT', f.prompt)
        self.update_value(field_name, 'LENGTH', f.length)
        self.update_value(field_name, 'TYPE', f.inputtype)

    def fields(self):
        field_names = self.names()
        del_fields = ['EDM','TIME']
        for n in range(1, __BUTTONS__):
            del_fields.append('BUTTON%s' % n)
        for del_field in del_fields:
            if del_field in field_names:
                field_names.remove(del_field)
        return(field_names)

    def clean_menu(self, menulist):
        menulist = [item.strip() for item in menulist]
        menulist = list(filter(('').__ne__, menulist))
        return(menulist)

    def build_prism(self):
        self.update_value('NAME', 'Prompt', 'Name :')
        self.update_value('NAME', 'Type', 'Text')
        self.update_value('NAME', 'Length', 20)

        self.update_value('HEIGHT', 'Prompt', 'Height :')
        self.update_value('HEIGHT', 'Type', 'Numeric')

        self.update_value('OFFSET', 'Prompt', 'Offset :')
        self.update_value('OFFSET', 'Type', 'Numeric')

    def build_unit(self):
        self.update_value('NAME', 'Prompt', 'Name :')
        self.update_value('NAME', 'Type', 'Text')
        self.update_value('NAME', 'Length', 20)

        self.update_value('XMIN', 'Prompt', 'X Minimum :')
        self.update_value('XMIN', 'Type', 'Numeric')

        self.update_value('YMIN', 'Prompt', 'Y Minimum :')
        self.update_value('YMIN', 'Type', 'Numeric')

        self.update_value('XMAX', 'Prompt', 'X Maximum :')
        self.update_value('XMAX', 'Type', 'Numeric')

        self.update_value('YMAX', 'Prompt', 'Y Maximum :')
        self.update_value('YMAX', 'Type', 'Numeric')

        self.update_value('RADIUS', 'Prompt', 'or enter a Radius :')
        self.update_value('RADIUS', 'Type', 'Text')
        self.update_value('RADIUS', 'Length', 20)

        self.update_value('CENTERX', 'Prompt', 'and a Center X :')
        self.update_value('CENTERX', 'Type', 'Numeric')

        self.update_value('CENTERY', 'Prompt', 'and Center Y :')
        self.update_value('CENTERY', 'Type', 'Numeric')

    def build_datum(self):
        self.update_value('NAME', 'Prompt', 'Name :')
        self.update_value('NAME', 'Type', 'Text')
        self.update_value('NAME', 'Length', 20)

        self.update_value('X', 'Prompt', 'X :')
        self.update_value('X', 'Type', 'Numeric')

        self.update_value('Y', 'Prompt', 'Y :')
        self.update_value('Y', 'Type', 'Numeric')

        self.update_value('Z', 'Prompt', 'Z :')
        self.update_value('Z', 'Type', 'Numeric')

        self.update_value('NOTES', 'Prompt', 'Note :')
        self.update_value('NOTES', 'Type', 'Note')

    def build_default(self):
        self.update_value('UNIT', 'Prompt', 'Unit :')
        self.update_value('UNIT', 'Type', 'Text')
        self.update_value('UNIT', 'Length', 6)

        self.update_value('ID', 'Prompt', 'ID :')
        self.update_value('ID', 'Type', 'Text')
        self.update_value('ID', 'Length', 6)

        self.update_value('SUFFIX', 'Prompt', 'Suffix :')
        self.update_value('SUFFIX', 'Type', 'Numeric')

        self.update_value('LEVEL', 'Prompt', 'Level :')
        self.update_value('LEVEL', 'Type', 'Menu')
        self.update_value('LEVEL', 'Length', 20)

        self.update_value('CODE', 'Prompt', 'Code :')
        self.update_value('CODE', 'Type', 'Menu')
        self.update_value('CODE', 'Length', 20)

        self.update_value('EXCAVATOR', 'Prompt', 'Excavator :')
        self.update_value('EXCAVATOR', 'Type', 'Menu')
        self.update_value('EXCAVATOR', 'Length', 20)

        self.update_value('PRISM', 'Prompt', 'Prism :')
        self.update_value('PRISM', 'Type', 'Numeric')

        self.update_value('X', 'Prompt', 'X :')
        self.update_value('X', 'Type', 'Numeric')

        self.update_value('Y', 'Prompt', 'Y :')
        self.update_value('Y', 'Type', 'Numeric')

        self.update_value('Z', 'Prompt', 'Z :')
        self.update_value('Z', 'Type', 'Numeric')

        self.update_value('DATE', 'Prompt', 'Date :')
        self.update_value('DATE', 'Type', 'Text')
        self.update_value('DATE', 'Length', 24)

        # should add hangle, vangle, sloped 

    def validate(self):

        self.errors = []
        self.has_errors = False
        self.has_warnings = False
        field_names = self.fields()
        self.link_fields = []

        # This is a legacy issue.  Linked fields are now listed with each field.
        unit_fields = self.get_value('EDM', 'UNITFIELDS')
        if unit_fields:
            unit_fields = unit_fields.upper().split(',')
            unit_fields.remove('UNIT')
            unit_fields = ','.join(unit_fields)
            self.update_value('UNIT', 'LINKED', unit_fields)
            self.delete_key('EDM', 'UNITFIELDS')

        table_name = self.get_value('EDM','TABLE')
        if table_name:
            if any((c in set(r' !@#$%^&*()?/\{}<.,.|+=~`-')) for c in table_name):
                self.errors.append("Error: The table name '%s' has non-standard characters in it that cause a problem in JSON files.  Do not use any of these '%s' characters.  Change the name before collecting data." % (table_name, r' !@#$%^&*()?/\{}<.,.|+=~`-'))
                self.has_errors = True
    
        unique_together = self.get_value('EDM','UNIQUE_TOGETHER')
        if unique_together:
            no_errors = True
            for field_name in unique_together.split(','):
                if not field_name in field_names:
                    self.errors.append("Error: The field '%s' is listed in UNIQUE_TOGETHER but does not appear as a field in the CFG file.")
                    self.has_errors = True
                    no_errors = False
                    break
            if no_errors:
                self.unique_together = unique_together.split(',')
            else:
                self.unique_together = ''

        for field_name in field_names:
            if any((c in set(r' !@#$%^&*()?/\{}<.,.|+=~`-')) for c in field_name):
                self.errors.append("Error: The field name '%s' has non-standard characters in it that cause a problem in JSON files.  Do not use any of these '%s' characters.  Change the name before collecting data." % (table_name, r' !@#$%^&*()?/\{}<.,.|+=~`-'))
                self.has_errors = True
            f = self.get(field_name)
            if f.prompt == '':
                f.prompt = field_name
            f.inputtype = f.inputtype.upper()
            if field_name in ['UNIT','ID','SUFFIX','X','Y','Z']:
                self.update_value(field_name, 'REQUIRED', 'TRUE')
            if field_name == 'ID':
                self.update_value(field_name, 'INCREMENT', 'TRUE')
            if f.link_fields:
                self.link_fields.append(field_name)
                # uppercase the link fields
                for link_field_name in f.link_fields:
                    if link_field_name not in field_names:
                        self.errors.append("Warning: The field %s is set to link to %s but the field %s does not exist in the CFG." % (field_name, link_field_name, link_field_name))
            self.put(field_name, f)

            for field_option in ['UNIQUE','CARRY','INCREMENT','REQUIRED','SORTED']:
                if self.get_value(field_name, field_option):
                    if self.get_value(field_name, field_option).upper() == 'YES':
                        self.update_value(field_name, field_option, 'TRUE')

        return(self.has_errors)

    def save(self):
        self.write_blocks()

    def load(self, filename = ''):
        if filename:
            self.filename = filename
        self.path = ntpath.split(self.filename)[0]

        self.blocks = []
        if os.path.isfile(self.filename):
            self.blocks = self.read_blocks()
            errors = self.validate()
            if errors == []:
                self.save()
            else:
                return(errors)
        else:
            self.filename = 'default.cfg'
            self.build_default()
    
    def status(self):
        txt = '\nCFG file is %s\n' % self.filename
        return(txt)

    def write_csvs(self, filename, table):
        try:
            cfg_fields = self.fields()
            f = open(filename, 'w')
            csv_row = ''
            for fieldname in cfg_fields:
                csv_row += ',"%s"' % fieldname if csv_row else '"%s"' % fieldname 
            f.write(csv_row + '\n')
            for row in table:
                csv_row = ''
                for fieldname in cfg_fields:
                    if fieldname in row.keys():
                        if row[fieldname] is not None:
                            if self.get(fieldname).inputtype in ['NUMERIC','INSTRUMENT']:
                                csv_row += ',%s' % row[fieldname] if csv_row else "%s" % row[fieldname]   
                            else:
                                csv_row += ',"%s"' % row[fieldname] if csv_row else '"%s"' % row[fieldname]
                        else:
                            if self.get(fieldname).inputtype in ['NUMERIC','INSTRUMENT']:
                                if csv_row:
                                    csv_row = csv_row + ','     # Not sure this works if there is an entirely empty row of numeric values
                            else:
                                if csv_row:
                                    csv_row = csv_row + ',""'
                                else: 
                                    csv_row = '""'
                    else:
                        if self.get(fieldname).inputtype in ['NUMERIC','INSTRUMENT']:
                            if csv_row:
                                csv_row = csv_row + ','     # Not sure this works if there is an entirely empty row of numeric values
                        else:
                            if csv_row:
                                csv_row = csv_row + ',""'
                            else: 
                                csv_row = '""'
                f.write(csv_row + '\n')
            f.close()
            return(None)
        except:
            return('\nCould not write data to %s.' % (filename))

class totalstation(object):

    popup = ObjectProperty(None)
    popup_open = False
    rotate_source = []
    rotate_destination = []

    def __init__(self, make = "Simulate", model = ''):
        self.make = make
        self.model = model
        self.communication = 'Serial'
        self.comport = 'COM1'
        self.baudrate = '1200'
        self.parity = 'EVEN'
        self.databits = 7
        self.stopbits = 1
        self.comport_settings = ''
        self.serialcom = serial.Serial()
        self.input_string = ''
        self.output_string = ''
        self.port_open = False
        self.location = point(0, 0, 0)
        self.xyz = point()
        self.prism_constant = 0
        self.hangle = ''
        self.vangle = ''
        self.sloped = 0
        self.suffix = 0
        self.prism = 0
        self.xyz_global = point()
        self.rotate_local = []
        self.rotate_global = []
        self.last_setup_type = ''
        self.open()

    def text_to_point(self, txt):
        if len(txt.split(',')) == 3:
            x, y, z = txt.split(',')
            try:
                return(point(float(x), float(y), float(z)))
            except:
                return(None)
        else:
            return(None)


    def setup(self, ini, data):
        if ini.get_value(__program__,'STATION'):
            self.make = ini.get_value(__program__,'STATION')
        if ini.get_value(__program__,'COMMUNICATIONS'):
            self.communication = ini.get_value(__program__,'COMMUNICATIONS')
        if ini.get_value(__program__,'COMPORT'):
            self.commport = ini.get_value(__program__,'COMPORT')
        if ini.get_value(__program__,'BAUDRATE'):
            self.baudrate = ini.get_value(__program__,'BAUDRATE')
        if ini.get_value(__program__,'PARITY'):
            self.parity = ini.get_value(__program__,'PARITY')
        if ini.get_value(__program__,'DATABITS'):
            self.databits = ini.get_value(__program__,'DATABITS')
        if ini.get_value(__program__,'STOPBITS'):
            self.stopbits = ini.get_value(__program__,'STOPBITS')

        self.last_setup_type = ini.get_value('SETUPS','LASTSETUP_TYPE')

        if ini.get_value('SETUPS','3DATUM_SHIFT_LOCAL_1'):
            point1 = self.text_to_point(ini.get_value('SETUPS','3DATUM_SHIFT_LOCAL_1'))
            point2 = self.text_to_point(ini.get_value('SETUPS','3DATUM_SHIFT_LOCAL_2'))
            point3 = self.text_to_point(ini.get_value('SETUPS','3DATUM_SHIFT_LOCAL_3'))
            if point1 is not None and point2 is not None and point3 is not None:
                self.rotate_local = [point1, point2, point3]
        if ini.get_value('SETUPS','3DATUM_SHIFT_GLOBAL_1'):
            point1 = data.get_datum(ini.get_value('SETUPS','3DATUM_SHIFT_GLOBAL_1'))
            point2 = data.get_datum(ini.get_value('SETUPS','3DATUM_SHIFT_GLOBAL_2'))
            point3 = data.get_datum(ini.get_value('SETUPS','3DATUM_SHIFT_GLOBAL_3'))
            if point1 is not None and point2 is not None and point3 is not None:
                self.rotate_global = [point1.as_point(), point2.as_point(), point3.as_point()]

    def status(self):
        txt = '\nTotal Station:\n'
        txt += '  Make is %s\n' % self.make
        if self.make not in ['Microscribe']:
            txt += '  Communication type is %s\n' % self.communication
            txt += '  COM Port is %s\n' % self.comport
            txt += '  Com settings are %s, %s, %s, %s\n' % (self.baudrate, self.parity, self.databits, self.stopbits)
            if self.serialcom.is_open:
                txt += 'COM Port is open\n'
            else:
                txt += 'COM port is closed\n'
            txt += '  Station was initialized with %s\n' % self.last_setup_type
            txt += '  Station X : %s\n' % self.location.x
            txt += '  Station Y : %s\n' % self.location.y
            txt += '  Station Z : %s\n' % self.location.z
        else:
            if self.last_setup_type:
                txt += '  Station was initialized with %s\n' % self.last_setup_type
                n = 1
                for coordinates in self.rotate_local:
                    txt += '    Datum %s locally is %s, %s, %s\n' % (n, coordinates.x, coordinates.y, coordinates.z)
                    n += 1
                n = 1
                for coordinates in self.rotate_global:
                    txt += '    Datum %s globally is %s, %s, %s\n' % (n, coordinates.x, coordinates.y, coordinates.z)
                    n += 1
        return(txt)

    def parseangle(self, hangle):
        hangle = str(hangle)
        if hangle.find("."): 
            angle = int(hangle) 
            minutes = 0
            seconds = 0
        else:
            hangle = hangle + "0000"
            angle = hangle.split(".")[0]
            minutes = hangle.split(".")[1][0:2]
            seconds = hangle.split(".")[1][2:4]

        return([angle, minutes, seconds])

    def hash(self, hashlen = 5):
        hash = ""
        for a in range(0, hashlen):
            hash += random.choice(string.ascii_uppercase)
        return(hash)

    def take_shot(self):

        self.clear_xyz()

        if self.make=='TOPCON':
            self.clearcom()
            self.edm_output("Z34")   # Slope angle mode
            self.edm_input
            #delay(0.5)

            self.edm_output("C")     # Take the shot
            self.edm_input()
            #delay(0.5)

        elif self.make == "WILD" or self.make == "Leica":
            self.launch_point_leica()

        elif self.make=="SOKKIA":
            self.edm_output(chr(17))

        elif self.make == 'Simulate':
            self.xyz = point(round(random.uniform(1000, 1010), 3),
                                round(random.uniform(1000, 1010), 3),
                                round(random.uniform(0, 1), 3 ))
            self.make_global()
    
    def fetch_point(self):
        if self.make in ['WILD','Leica']:
            self.fetch_point_leica()

    def make_global(self):
        if self.xyz:
            if self.make == 'Microscribe':
                if len(self.rotate_local) == 3 and len(self.rotate_global) == 3:
                    self.xyz_global = self.rotate_point(self.xyz)
                else:
                    self.xyz_global = self.xyz
                self.round_xyz()
            elif self.location:
                self.xyz_global = point(self.xyz.x + self.location.x,
                                        self.xyz.y + self.location.y,
                                        self.xyz.z + self.location.z,)

    def round_xyz(self):
        if self.xyz_global.x is not None:
            self.xyz_global = self.round_point(self.xyz_global)

        if self.xyz.x is not None:
            self.xyz = self.round_point(self.xyz)

    def round_point(self, p):
        return(point(round(p.x, 3), round(p.y, 3), round(p.z, 3)))

    def clear_xyz(self):
        self.xyz = point()
        self.xyz_global = point()

    def vhd_to_nez(self):
        pass

    def parse_nez(self):
        pass

    def comport_nos(self):
        ports = self.list_comports()
        return(list([port[0]['port'] for port in ports]))

    def list_comports(self):
        ports = []
        for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
            ports.append([{'port': port, 'desc': desc}])
        return(ports)

    def send(self, text):
        if self.serialcom.is_open:
            self.serialcom.write(text)
            print(text)
            #sleep(0.1) 

    def receive(self):
        if self.serialcom.is_open:
            return(self.serialcom.readline().decode())
            
    def close(self):
        if self.serialcom.is_open:
            self.serialcom.close()

    def open(self):
        self.close()
        if self.baudrate and self.comport and self.parity and self.databits and self.stopbits:
            if self.comport in self.comport_nos():
                self.serialcom.port = self.comport
                self.serialcom.baudrate = int(self.baudrate)
                if self.parity == 'Even':
                    self.serialcom.parity = serial.PARITY_EVEN
                elif self.parity == 'Odd':
                    self.serialcom.parity = serial.PARITY_ODD
                elif self.parity == 'None':
                    self.serialcom.parity = serial.PARITY_NONE
                self.serialcom.stopbits = int(self.stopbits)
                self.serialcom.bytesize = int(self.databits)
                self.serialcom.timeout = 30
                self.serialcom.open()
        
    def clear_com(self):
        if self.serialcom.is_open:
            self.serialcom.reset_input_buffer()
            self.serialcom.reset_output_buffer()

    def distance(self, p1, p2):
        return(sqrt( (p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2 ))

    def dms_to_decdeg(self, angle):
        angle = str(angle)
        degrees = int(angle.split(".")[0])        
        minutes = int(angle.split(".")[1][0:2])
        seconds = int(angle.split(".")[1][2:4])
        return(degrees + minutes / 60.0 + seconds / 3600.0)

    def decdeg_to_radians(self, angle):
        return(angle / 360 * (2 * pi))

    # The following functions are needed by the rotation function at the end of this list.
    # Note too that all of the dependent routines are self written
    # rather than pulled from existing libraries (like numpy) to avoid dependencies.  Dependencies make porting to
    # Apple and Android more difficult.
    def dot_product(self, a, b):
        return(a.x * b.x + a.y * b.y + a.z * b.z)
        
    def normalize_vector(self, a):
        if sqrt(self.dot_product(a, a)) == 0:
            return(a)
        else:
            return(self.scale_vector( 1 / sqrt(self.dot_product(a, a)), a))

    def vector_subtract(self, p2, p1):
        return(point(p2.x - p1.x, p2.y - p1.y, p2.z - p1.z))        

    def surface_normal(self, a):
        u = self.vector_subtract(a[1], a[0])
        v = self.vector_subtract(a[2], a[0])
        return(self.normalize_vector(self.cross_product(u, v)))

    def vector_magnitude(self, a):
        return(sqrt(self.dot_product(a, a)))

    def cross_product(self, v1, v2):
        return(point(v1.y * v2.z - v1.z * v2.y,
                    v1.z * v2.x - v1.x * v2.z,
                    v1.x * v2.y - v1.y * v2.x))

    def scale_vector(self, scalar, a):
        return(point(scalar * a.x,
                        scalar * a.y,
                        scalar * a.z))

    def empty_matrix(self):
        return([[0.0 for x in range(3)] for y in range(3)])

    def identity_matrix(self):
        i = self.empty_matrix()
        for n in range(3):
            i[n][n] = 1.0
        return(i)

    def matrix_product(self, a, b):
        result = self.empty_matrix()
        for row in range(3):
            for col in range(3):
                for index in range(3):
                    result[row][col] = result[row][col] + a[row][index] * b[index][col]
        return(result)

    def scale_matrix(self, scalar, m):
        result = self.empty_matrix()
        for row in range(3):
            for col in range(3):
                result[row][col] = scalar * m[row][col]
        return(result)

    def matrix_add(self, m1, m2):
        result = self.empty_matrix()
        for row in range(3):
            for col in range(3):
                result[row][col] = m1[row][col] + m2[row][col]
        return(result)

    def translate_point(self, translation, p):
        return(point(p.x + translation.x,
                        p.y + translation.y,
                        p.z + translation.z))

    def rotate_point_2d(self, local_vector, global_vector, p):
        # local coodinate system and global coordinate system vectors that will be made to align with each other.
        # p is a point to be rotated along with this vector alignment.
        # This is in essence a 2D rotation in the plane formed by the two vectors and around the perpendicular to this plane.
        # (Two vectors have the origin in common and thus make three points altogether and this is a plane)
        # (The surface normal is the rotation axis and the angle of rotation is the angle between the two vectors in this plane)

        i = self.identity_matrix()

        v = self.cross_product(local_vector, global_vector)
        s = self.vector_magnitude(v)
        c = self.dot_product(local_vector, global_vector)

        vx = self.empty_matrix()
        vx[0][0] = 0.0
        vx[0][1] = -1.0 * v.z
        vx[0][2] = v.y

        vx[1][0] = v.z
        vx[1][1] = 0.0
        vx[1][2] = -1.0 * v.x

        vx[2][0] = -1.0 * v.y
        vx[2][1] = v.x
        vx[2][2] = 0.0

        v2x = self.scale_matrix(1 / (1 + c), self.matrix_product(vx, vx))

        # Now create the rotation matrix by adding these components
        r = self.matrix_add( self.matrix_add(i, vx), v2x)

        # Now do the rotation by multiplying this rotation matrix by the individual points (or vectors)
        return(point((p.x * r[0][0]) + (p.y * r[1][0]) + (p.z * r[2][0]),
                        (p.x * r[0][1]) + (p.y * r[1][1]) + (p.z * r[2][1]),
                        (p.x * r[0][2]) + (p.y * r[1][2]) + (p.z * r[2][2])))                        

    def rotate_point_2d_2(self, rotation_vector, local_vector, global_vector, p):
        # local coodinate system and global coordinate system vectors that will be made to align with each other.
        # p is a point to be rotated along with this vector alignment.
        # This is in essence a 2D rotation in the plane formed by the two vectors and around the perpendicular to this plane.
        # (Two vectors have the origin in common and thus make three points altogether and this is a plane)
        # (The surface normal is the rotation axis and the angle of rotation is the angle between the two vectors in this plane)

        i = self.identity_matrix()

        v = rotation_vector
        s = self.vector_magnitude(v)
        c = self.dot_product(local_vector, global_vector)

        vx = self.empty_matrix()
        vx[0][0] = 0.0
        vx[0][1] = -1.0 * v.z
        vx[0][2] = v.y

        vx[1][0] = v.z
        vx[1][1] = 0.0
        vx[1][2] = -1.0 * v.x

        vx[2][0] = -1.0 * v.y
        vx[2][1] = v.x
        vx[2][2] = 0.0

        v2x = self.scale_matrix(1 / (1 + c), self.matrix_product(vx, vx))

        # Now create the rotation matrix by adding these components
        r = self.matrix_add( self.matrix_add(i, vx), v2x)

        # Now do the rotation by multiplying this rotation matrix by the individual points (or vectors)
        return(point((p.x * r[0][0]) + (p.y * r[1][0]) + (p.z * r[2][0]),
                        (p.x * r[0][1]) + (p.y * r[1][1]) + (p.z * r[2][1]),
                        (p.x * r[0][2]) + (p.y * r[1][2]) + (p.z * r[2][2])))                        


    # This routine takes two sets of datums (local and global) and converts a newly recorded point
    # from the local coordinate system (e.g. Microscribe) to the global coordinate system.
    # It does this by performing a rotation around first one leg and then another of the triangle formed by the datums.
    # It is written to be readable.  Much efficiency could be gained but as points are only rotated as recorded,
    # the routine does not need to be fast.  Note too that all of the dependent routines are self written
    # rather than pulled from existing libraries (like numpy) to avoid dependencies.  Dependencies make porting to
    # Apple and Android more difficult.
    def rotate_point(self, p = None):
        # p is a point to be rotated

        if p is None:
            p = self.xyz

        if len(self.rotate_local) == 3 and len(self.rotate_global) == 3 and p:
            rotated_local = []

            # Shift point to relative to the origin
            p = self.vector_subtract(p, self.rotate_local[0])

            # Shift local set relative to origin
            local = []
            local.append(point(0,0,0))
            local.append(self.vector_subtract(self.rotate_local[1], self.rotate_local[0]))
            local.append(self.vector_subtract(self.rotate_local[2], self.rotate_local[0]))
          
            # First line up one side of the triangle formed by the three datum points
            local_vector = self.normalize_vector(local[1])
            global_vector = self.normalize_vector(self.vector_subtract(self.rotate_global[1], self.rotate_global[0]))
            p_out = self.rotate_point_2d(global_vector, local_vector, p)

            # Put the local datums in this new space as well
            rotated_local.append(self.rotate_point_2d(global_vector, local_vector, local[0]))
            rotated_local.append(self.rotate_point_2d(global_vector, local_vector, local[1]))
            rotated_local.append(self.rotate_point_2d(global_vector, local_vector, local[2]))

            # Now line up on the other side of the triangle formed by the three datum points
            # by computing the surface normal of each and rotating on the first already rotated side
            local_datums_normal = self.normalize_vector(self.cross_product(self.normalize_vector(rotated_local[1]),
                                                    self.normalize_vector(rotated_local[2])))
            global_datums_normal = self.normalize_vector(self.cross_product(self.normalize_vector(self.vector_subtract(self.rotate_global[1], self.rotate_global[0])),
                                                        self.normalize_vector(self.vector_subtract(self.rotate_global[2], self.rotate_global[0]))))
            p_out2 = self.rotate_point_2d(global_datums_normal, local_datums_normal, p_out)

            # Finish the rotation for the local datums as well (not strictly needed for points 2 and 3)
            rotated_local[0] = self.rotate_point_2d(global_vector, local_vector, rotated_local[0])
            rotated_local[1] = self.rotate_point_2d(global_vector, local_vector, rotated_local[1])
            rotated_local[2] = self.rotate_point_2d(global_vector, local_vector, rotated_local[2])

            # Now align the starting points of each grid systems by shifting the first datum points onto each other
            result = self.translate_point(self.rotate_global[0], p_out2)

            return(result)

        else:
            return(None)

    def rotate_initialize(self, local_datums, global_datums):
        # local and global datums are two lists of three corresponding points in the two grid systems

        self.rotate_local = local_datums
        self.rotate_global = global_datums


    ### Function specific to Topcon ###
    def make_bcc_topcon(self, itext):
        #Dim b As Integer = 0
        #Dim i As Integer
        #Dim q As Integer
        #Dim b1 As Integer
        #Dim b2 As Integer

        b = 0 
        for i in range(0,len(itext)):
            #q = asc(itext[i:i+1])
            #b1 = q and (Not b) # this is not at all ready
            #b2 = b and (Not q)
            #b = b1 or b2
            pass

        bcc = "000" + str(b).strip()
        return(bcc[-3])

    def horizontal_topcon(self):
        self.send("Z10")
        return(self.receive())

    def initialize_topcon(self):
        self.send("ST0")
    ### end Topcon

    ### Leica functions ###
    def pad_dms_leica(self, angle):
        degrees = ('000' + angle.split('.')[0])[-3:]
        minutes_seconds = (angle.split('.')[1] + '0000')[0:4]
        return( degrees + minutes_seconds)

    def set_horizontal_angle_leica(self, angle):
        # function expects angle as ddd.mmss input
        self.send("PUT/21...4+" + self.pad_dms(angle) + "0 ")
        return(self.receive())

    def launch_point_leica(self):
        self.send(b"GET/M/WI21/WI22/WI31/WI51\r\n")

    def fetch_point_leica(self):
        self.pnt = self.receive()
        if self.pnt:
            self.parce_leica()
            self.vhd_to_nez()

    def vhd_to_xyz(self):
        if self.vangle and self.hangle and self.sloped:
            angle_decdeg = self.dms_to_decdeg(self.vangle)
            z = self.sloped * cos(self.decdeg_to_radians(angle_decdeg))
            actual_distance = sqrt(self.sloped**2 - z**2)

            angle_decdeg = self.dms_to_decdeg(self.hangle)
            angle_decdeg = 450 - angle_decdeg
            x = cos(self.decdeg_to_radians(angle_decdeg)) * actual_distance
            y = sin(self.decdeg_to_radians(angle_decdeg)) * actual_distance
            self.xyz = point(x, y, z)

    def parce_leica(self):
        if self.pnt:
            if self.pnt.startswith('*'):
                pnt = self.pnt[1:]
            for component in pnt.split(' '):
                if component.startswith('21.'):
                    self.hangle = float(component[6:]) / 100000
                elif component.startswith('22.'):
                    self.vangle = float(component[6:]) / 100000
                elif component.startswith('31.'):
                    self.sloped = float(component[6:]) / 1000
                elif component.startswith('51.'):
                    component = component[7:]
                    component = component[component.find('+') + 1 :]
                    self.prism_constant = float(component)
                

    def initialize_leica(self):
        self.send("SET/41/0")
        acknow1 = self.receive()
        self.send("SET/149/2")
        acknow2 = self.receive()
        return(acknow1 + acknow2)
    ### Leica functions ###

    ### Leica geocom functions ###
    def initialize_geocom(self):
        pass
        
    def set_horizontal_angle_geocom(self, angle):
        # function expects angle as ddd.mmss as input
        # %R1Q,2113:HzOrientation[double]
        output = "%R1Q,2113:{:10.8f}".format(self.decdeg_to_radians(self.dms_to_decdeg(angle)))
        errorcode = self.send(output)
        returncode = self.receive()

    def record_point_geocom(self):
        self.clear_com()
        self.send("%R1Q,2008:1,1")          # Use the defaults with 1 and 1
        errorcode = self.receive()
        if not errorcode:
            # %R1Q,2108:WaitTime[long],Mode[long]
            # Waittime is in ms
            # Mode 1 = automatic
            self.clear_com()
            self.send("%R1Q,2108:10000,1")  # Wait for the measurements and return the angles + sloped
            result = self.receive()
        self.clear_com()    
        self.send("%R1Q,2008:3,1")          # Empty the measurement buffer as a precaution
        returncode = self.receive()
    ### Leica geocom functions ###

#endregion

class MainScreen(e5_MainScreen):

    popup = ObjectProperty(None)
    popup_open = False
    text_color = (0, 0, 0, 1)
    title = __program__

    def __init__(self, data = None, cfg = None, ini = None, colors = None, station = None, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        self.colors = colors if colors else ColorScheme()
        self.ini = ini if ini else INI()
        self.data = data if data else DB()
        self.cfg = cfg 
        self.station = station if station else totalstation()
        self.cfg_datums = CFG()
        self.cfg_datums.build_datum()
        self.cfg_prisms = CFG().build_prism()
        self.cfg_units = CFG().build_unit()

        self.layout = BoxLayout(orientation = 'vertical',
                                size_hint_y = .9,
                                size_hint_x = .8,
                                pos_hint={'center_x': .5},
#                                id = 'mainscreen',
                                padding = 20,
                                spacing = 20)
        self.build_mainscreen()
        self.add_widget(self.layout)

    def build_mainscreen(self):

        if platform_name() == 'Android':
            size_hints = {  'info': .13, 
                            'option_buttons': .8 - .13 - .2,
                            'shot_buttons': .2}
        else:
            size_hints = {  'info': .13, 
                            'option_buttons': .8 - .13 - .2,
                            'shot_buttons': .2}

        self.layout.clear_widgets()

        self.info = e5_label(text = 'EDM',
                    size_hint = (1, size_hints['info']),
                    color = self.colors.text_color,
                    id = 'lastshot',
                    halign = 'center')
        if self.colors:
            if self.colors.text_font_size:
                self.info.font_size = self.colors.text_font_size 
        self.layout.add_widget(self.info)
        self.info.bind(texture_size = self.info.setter('size'))
        self.info.bind(size_hint_min_x = self.info.setter('width'))

        #grid = GridLayout(cols = 3, spacing = 10)
        scroll_content = BoxLayout(orientation = 'horizontal',
                                    size_hint = (1, size_hints['option_buttons']),
#                                    id = 'option_buttons',
                                    spacing = 20)
        self.layout.add_widget(scroll_content)

        button_count = 0
        button_text = []
        button_selected = []
        for button_no in range(1, __BUTTONS__):
            if self.cfg.get_value('BUTTON' + str(button_no), 'TITLE'):
                button_text.append(self.cfg.get_value('BUTTON' + str(button_no), 'TITLE'))
                button_selected.append(False)
                button_count += 1

        if button_count > 0:
            self.scroll_menu = e5_scrollview_menu(button_text,
                                                        menu_selected = button_selected,
                                                        widget_id = 'buttons',
                                                        call_back = [self.take_shot],
                                                        ncols = 3,
                                                        colors = self.colors)
            scroll_content.add_widget(self.scroll_menu)


        #if button_count % 3 !=0:
        #    button_empty = Button(text = '', size_hint_y = None, id = '',
        #                    color = self.colors.window_background,
        #                    background_color = self.colors.window_background,
        #                    background_normal = '')
        #    scroll_content.add_widget(button_empty)

        #if button_count % 3 == 2:
        #    scroll_content.add_widget(button_empty)

        #self.layout.add_widget(scroll_content)

        shot_buttons = GridLayout(cols = 3, size_hint = (1, size_hints['shot_buttons']), spacing = 20)
        
        shot_buttons.add_widget(e5_button(text = 'Record',
                        id = 'record',
                        colors = self.colors, call_back = self.take_shot, selected = True))

        shot_buttons.add_widget(e5_button(text = 'Continue',
                        id = 'continue',
                        colors = self.colors, call_back = self.take_shot, selected = True))

        shot_buttons.add_widget(e5_button(text = 'Measure',
                        id = 'measure',
                        colors = self.colors, call_back = self.take_shot, selected = True))

        self.layout.add_widget(shot_buttons)

        self.update_title()

        if self.cfg.filename:
            if self.cfg.has_warnings or self.cfg.has_errors:
                self.event = Clock.schedule_once(self.show_popup_message, 1)

    def update_title(self):
        self.children[-1].children[0].children[0].action_previous.title = 'EDM'
        if self.cfg is not None:
            if self.cfg.filename:
                self.children[-1].children[0].children[0].action_previous.title = filename_only(self.cfg.filename)

    def take_shot(self, instance):
        
        self.station.shot_type = instance.id
        self.station.clear_xyz()
        if self.station.make == 'Microscribe':
            self.popup = DataGridTextBox(title = 'EDM', text = '<Microscribe>',
                                            label = 'Waiting on...',
                                            button_text = ['Cancel', 'Next'],
                                            call_back = self.have_shot,
                                            colors = self.colors)
        else:
            self.station.take_shot()
            prism_names = self.data.names('prisms')
            if len(prism_names) > 0 :
                self.popup = DataGridMenuList(title = "Select or Enter a Prism Height",
                                                menu_list = prism_names,
                                                menu_selected = '',
                                                call_back = self.have_shot)
            else:
                self.popup = DataGridTextBox(title = 'Enter a Prism Height',
                                            call_back = self.have_shot,
                                            button_text = ['Back','Next'])
        self.popup.open()

    def have_shot(self, instance):
        if self.station.make == 'Microscribe':
            result = self.popup.result
            if result:
                p = self.station.text_to_point(result)
                if p:
                    p.x = p.x / 1000
                    p.y = p.y / 1000
                    p.z = p.z / 1000
                    self.station.xyz = p
                    self.station.make_global()
        if self.station.make in ['Leica']:
            self.station.fetch_point()
            self.station.make_global()

        self.popup.dismiss()

        if self.station.xyz.x is not None:
            if self.station.shot_type == 'measure':
                txt = 'Local coordinates:\n  X: %s\n  Y: %s\n  Z: %s' % (self.station.xyz.x, self.station.xyz.y, self.station.xyz.z)
                txt += '\n\nGlobal coordinates:\n  X: %s\n  Y: %s\n  Z: %s' % (self.station.xyz_global.x, self.station.xyz_global.y, self.station.xyz_global.z)
                if self.station.make != 'Microscribe':
                    txt += '\n\nRaw Data:\n  Horizontal angle: %s\n  Vertical angle: %s\n  Slope distance: %s' % (self.station.hangle, self.station.vangle, self.station.sloped)
                    txt += '\n\nStation coordinates:\n  X:  %s\n  Y:  %s\n  Z:  %s' % (self.station.location.x, self.station.location.y, self.station.location.z)
                self.popup = e5_MessageBox('Measurement', txt,
                                        response_type = "OK",
                                        call_back = self.close_popup,
                                        colors = self.colors)
                self.popup.open()
            else:
                self.add_record()
                ### self.station.prism = self.data.prisms.get(value.text).height 
                self.data.db.table(self.data.table).on_save = self.on_save
                self.data.db.table(self.data.table).on_cancel = self.on_cancel
                self.parent.current = 'EditPointScreen'
        else:
            self.popup = e5_MessageBox(title = 'Error', message = '\nPointed not recorded.')
            self.popup.open()

    def on_save(self):
        self.update_info_label()
        self.make_backup()
        self.check_for_duplicate_xyz()
        return([])

    def on_cancel(self):
        last_record = self.data.db.table(self.data.table).all()[-1]
        if last_record != []:
            self.data.db.table(self.data.table).remove(doc_ids = [last_record.doc_id])

    def update_info_label(self):
        unit = self.get_last_value('UNIT')
        idno = self.get_last_value('ID')
        suffix = self.get_last_value('SUFFIX')
        if unit is not None and idno is not None and suffix is not None:
            self.info.text = '%s-%s(%s)' % (unit, idno, suffix)
        else:
            self.info = 'EDM'

    def check_for_duplicate_xyz(self):
        if self.station.make == 'Microscribe':
            if len(self.data.db.table(self.data.table)) > 1:
                last_record = self.data.db.table(self.data.table).all()[-1]
                next_to_last_record = self.data.db.table(self.data.table).all()[-2]
                if 'X' in last_record.keys() and 'Y' in last_record.keys() and 'Z' in last_record.keys():
                    if last_record['X'] == next_to_last_record['X'] and last_record['Y'] == next_to_last_record['Y'] and last_record['Z'] == next_to_last_record['Z']:
                        self.popup = e5_MessageBox(title = 'Warning', message = '\nThe last two recorded points have the exact same XYZ coordinates (%s, %s, %s).  Verify that the Microscribe is still properly recording points (green light is on).  If the red light is on, you need to re-initialize (Setup - Initialize Station) and re-shoot the last two points.' % (last_record['X'], last_record['Y'], last_record['Z']))
                        self.popup.open()

    def close_popup(self, instance):
        self.popup.dismiss()

    def show_load_cfg(self):
        if self.cfg.filename and self.cfg.path:
            start_path = self.cfg.path
        else:
            start_path = self.ini.get_value('EDM','APP_PATH')
        content = e5_LoadDialog(load = self.load_cfg, 
                            cancel = self.dismiss_popup,
                            start_path = start_path,
                            button_color = self.colors.button_color,
                            button_background = self.colors.button_background)
        self.popup = Popup(title = "Load CFG file", content = content,
                            size_hint = (0.9, 0.9))
        self.popup.open()

    def load_cfg(self, path, filename):
        self.dismiss_popup()
        self.cfg.load(os.path.join(path, filename[0]))
        if self.cfg.filename:
            self.open_db()
        self.ini.update(self.colors, self.cfg)
        self.build_mainscreen()

    def show_import_csv(self):
        self.popup = e5_PopUpMenu(title = "Load which kind of data",
                                        menu_list = ['Datums','Prisms','Units'],
                                        menu_selected = '',
                                        call_back = self.select_csv_file,
                                        colors = self.colors)
        self.popup.open()

    def show_csv_datatype(self):
        self.popup = e5_PopUpMenu(title = "Export which kind of data",
                                        menu_list = ['Points','Datums','Prisms','Units'],
                                        menu_selected = '',
                                        call_back = self.show_save_csvs,
                                        colors = self.colors)
        self.popup.open()

    def select_csv_file(self, instance):
        self.csv_data_type = instance.text
        self.popup.dismiss()
        if self.cfg.filename and self.cfg.path:
            start_path = self.cfg.path
        else:
            start_path = self.ini.get_value('EDM','APP_PATH')
        content = e5_LoadDialog(load = self.load_csv, 
                            cancel = self.dismiss_popup,
                            start_path = start_path,
                            button_color = self.colors.button_color,
                            button_background = self.colors.button_background,
                            filters = ['*.csv','*.CSV'])
        self.popup = Popup(title = "Select CSV file to import",
                            content = content,
                            size_hint = (0.9, 0.9))
        self.popup.open()

    def load_csv(self, path, filename):
        csv_file = os.path.join(path, filename[0])
        errors = ''
        record_count = 0
        self.popup.dismiss()
        try:
            if os.path.isfile(csv_file):
                with open(csv_file) as f:
                    firstline = True
                    for line in f:
                        if firstline:
                            fields = line.upper().split(',')
                            if self.csv_data_type == 'Datums':
                                if len(fields) < 4:
                                    errors = '\nThis CSV file seems to have fewer than four fields.  To import datums requires a Name, X, Y, and Z field.  The first row in the file should contain these field names separated by commas.  The first line was read as "%s".' % line
                                if 'X' not in fields or 'Y' not in fields or 'Z' not in fields or 'NAME' not in fields:
                                    errors = '\nThis CSV file must include a first row of field names (comma delimited) and must include a field called Name, X, Y and Z.  The first line was read as "%s".' % line
                            if errors:
                                break
                            firstline = False
                        else:
                            data = line.split(',')
                            insert_record = {}
                            for field in range(len(fields)):
                                insert_record[fields[field]] = data[field]
                            if self.csv_data_type == 'Datums':
                                if self.data.get_datum(insert_record['NAME']) is not None:
                                    self.data.delete_datum(insert_record['NAME'])
                                self.data.db.table('datums').insert(insert_record)
                            if self.csv_data_type == 'Units':
                                self.data.db.table('units').insert(insert_record)
                            if self.csv_data_type == 'Prisms':
                                self.data.db.table('prisms').insert(insert_record)
                            record_count += 1

        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            error = template.format(type(ex).__name__, ex.args)
            logging.exception(error)
        if errors:
            message = errors
        else:
            message = '%s %s successfully imported.' % (record_count, self.csv_data_type)
        self.popup = e5_MessageBox('CSV Import', message,
                                response_type = "OK",
                                call_back = self.close_popup,
                                colors = self.colors)
        self.popup.open()

    def add_record(self):
        new_record = {}
        new_record = self.fill_default_fields(new_record)
        if not self.station.shot_type == 'continue':
            new_record = self.find_unit_and_fill_fields(new_record)
            new_record = self.fill_carry_fields(new_record)
            new_record = self.fill_link_fields(new_record)
            new_record = self.do_increments(new_record)
            new_record['SUFFIX'] = 0
            new_record = self.fill_button_defaults(new_record)
        else:
            new_record = self.fill_empty_with_last(new_record)
            new_record['SUFFIX'] = int(self.get_last_value('SUFFIX')) + 1
            
        self.data.db.table(self.data.table).insert(new_record)
    
    def fill_empty_with_last(self, new_record):
        for field in self.cfg.fields():
            field_data = self.get_last_value(field)
            if field_data is not None:
                if field not in new_record.keys():
                    new_record[field] = self.get_last_value(field)
                elif new_record[field] == '':
                    new_record[field] = self.get_last_value(field)
        return(new_record)

    def fill_button_defaults(self, new_record):
        for button_no in range(1, __BUTTONS__):
            button = self.cfg.get_block('BUTTON' + str(button_no))
            if button:
                if 'TITLE' in button.keys():
                    if button['TITLE'] == self.station.shot_type:
                        fieldnames = self.cfg.fields()
                        for button_default in button:
                            if button_default in fieldnames:
                                if button[button_default].upper() == 'ALPHA':
                                    ### Should be calibrated to the length of this field
                                    new_record[button_default] = self.station.hash()
                                else:
                                    new_record[button_default] = button[button_default]
        return(new_record)

    def do_increments(self, new_record):
        fieldnames = self.cfg.fields()
        for fieldname in fieldnames:
            field = self.cfg.get(fieldname)
            if field.increment:
                if fieldname in new_record.keys():
                    try:
                        new_record[fieldname] = int(new_record[fieldname]) + 1
                    except:
                        pass
                else:
                    new_record[fieldname] = '1'
        return(new_record)

    def fill_carry_fields(self, new_record):
        fieldnames = self.cfg.fields()
        for fieldname in fieldnames:
            if fieldname not in __DEFAULT_FIELDS__:
                field = self.cfg.get(fieldname)
                if field.carry:
                    carry_value = self.get_last_value(fieldname)
                    if carry_value:
                        new_record[fieldname] = carry_value
        return(new_record)

    def fill_link_fields(self, new_record):
        fieldnames = self.cfg.fields()
        for fieldname in fieldnames:
            if fieldname not in __DEFAULT_FIELDS__:
                field = self.cfg.get(fieldname)
                if field.link_fields:
                    if fieldname in new_record.keys():
                        linkfields = self.data.get_link_fields(fieldname, new_record[fieldname])
                        if linkfields:
                            for link_fieldname in linkfields.keys():
                                new_record[link_fieldname] = linkfields[link_fieldname]
        return(new_record)

    def find_unit_and_fill_fields(self, new_record):
        fields = self.cfg.fields()
        unitname = self.data.point_in_unit(self.station.xyz_global)
        if unitname and "UNIT" in fields:
            new_record['UNIT'] = unitname
            unitfields = self.data.get_link_fields('UNIT', unitname)
            if unitfields:
                for field in unitfields.keys():
                    new_record[field] = unitfields[field]
        return(new_record)

    def fill_default_fields(self, new_record):
        fields = self.cfg.fields()
        for field in fields:
            if field == 'X':
                new_record['X'] = self.station.xyz_global.x
            elif field == 'Y':
                new_record['Y'] = self.station.xyz_global.y
            elif field == 'Z':
                new_record['Z'] = self.station.xyz_global.z
            elif field == 'SLOPED':
                new_record['SLOPED'] = self.station.sloped
            elif field == 'HANGLE':
                new_record['HANGLE'] = self.station.hangle
            elif field == 'VANGLE':
                new_record['VANGLE'] = self.station.vangle
            elif field == 'STATIONX':
                new_record['STATIONX'] = self.station.location.x
            elif field == 'STATIONY':
                new_record['STATIONY'] = self.station.location.y
            elif field == 'STATIONZ':
                new_record['STATIONZ'] = self.station.location.z
            elif field == 'LOCALX':
                new_record['LOCALX'] = self.station.xyz.x
            elif field == 'LOCALY':
                new_record['LOCALY'] = self.station.xyz.y
            elif field == 'LOCALZ':
                new_record['LOCALZ'] = self.station.xyz.z
            elif field == 'PRISM':
                new_record['PRISM'] = self.station.prism
            elif field == 'DATE':
                new_record['DATE'] = '%s' % datetime.now().replace(microsecond=0)
        return(new_record)

    def get_last_value(self, field_name):
        if len(self.data.db.table(self.data.table)) > 0 :
            last_record = self.data.db.table(self.data.table).all()[-1]
            if last_record != []:
                if field_name in last_record.keys():
                    return(last_record[field_name])
        return(None)


    def exit_program(self):
        self.save_window_location()
        App.get_running_app().stop()


class RecordDatumsScreen(Screen):

    def __init__(self, data = None, station = None, ini = None, colors = None, **kwargs):
        super(RecordDatumsScreen, self).__init__(**kwargs)

        self.colors = colors if colors else ColorScheme()
        self.station = station
        self.data = data
        self.ini = ini

        self.content = BoxLayout(orientation = 'vertical',
                                size_hint_y = .9,
                                size_hint_x = .8,
                                pos_hint={'center_x': .5},
#                                id = 'content',
                                padding = 20,
                                spacing = 20)
        self.add_widget(self.content)

        self.content.add_widget(e5_label('Provide a name and notes (optional), then record and save.', colors = self.colors))

        self.datum_name = DataGridLabelAndField('Name', colors = self.colors)
        self.content.add_widget(self.datum_name)
        self.datum_notes = DataGridLabelAndField('Notes', colors = self.colors)
        self.content.add_widget(self.datum_notes)
        
        self.recorder = datum_recorder('Record datum', station = self.station,
                                        colors = self.colors, setup_type = 'record_new')
        self.content.add_widget(self.recorder)

        self.results = e5_label('', colors = self.colors)
        self.content.add_widget(self.results)

        self.content.add_widget(e5_side_by_side_buttons(text = ['Save','Back'],
                                                id = ['save','cancel'],
                                                call_back = [self.check_for_duplicate, self.cancel],
                                                selected = [True, True],
                                                colors = self.colors))

    def check_for_duplicate(self, instance):
        if self.data.get_datum(self.datum_name.txt.text) is not None:
            message = '\nOverwrite existing datum %s?' % self.datum_name.txt.text
            self.popup = e5_MessageBox('Overwrite?', message,
                                        response_type = "YESNO",
                                        call_back = [self.delete_and_save, self.close_popup],
                                        colors = self.colors)
        else:
            self.save_datum()

    def delete_and_save(self, instance):
        self.popup.dismiss()
        self.data.delete_datum(self.datum_name.txt.text)
        self.save_datum()

    def save_datum(self):
        insert_record = {}
        insert_record['NAME'] = self.datum_name.txt.text
        insert_record['NOTES'] = self.datum_notes.txt.text
        insert_record['X'] = str(self.recorder.result.xyz_global.x)
        insert_record['Y'] = str(self.recorder.result.xyz_global.y)
        insert_record['Z'] = str(self.recorder.result.xyz_global.z)
        self.data.db.table('datums').insert(insert_record)
        self.datum_name.txt.text = ''
        self.datum_notes.txt.text = ''
        self.recorder.result.text = ''
        self.recorder.result.xyz = None
        self.recorder.result.xyz_global = None
        self.data.new_data = True

    def close_popup(self, instance):
        self.popup.dismiss()

    def cancel(self, instance):
        self.parent.current = 'MainScreen'

class VerifyStationScreen(Screen):
    id = ObjectProperty(None)
    def __init__(self, data = None, station = None, ini = None, colors = None, **kwargs):
        super(VerifyStationScreen, self).__init__(**kwargs)

        self.colors = colors if colors else ColorScheme()
        self.station = station
        self.data = data
        self.ini = ini

        self.content = BoxLayout(orientation = 'vertical',
                                size_hint_y = .9,
                                size_hint_x = .8,
                                pos_hint={'center_x': .5},
#                                id = 'content',
                                padding = 20,
                                spacing = 20)
        self.add_widget(self.content)

        self.content.add_widget(e5_label('Select a datum to use as verification and record it.', colors = self.colors))

        self.datum1 = datum_selector(text = 'Select\nverification\ndatum',
                                            data = self.data,
                                            colors = self.colors,
                                            default_datum = self.data.get_datum(self.ini.get_value('SETUPS', 'VERIFICATION')))
        self.content.add_widget(self.datum1)

        self.recorder = datum_recorder('Record\nverification\ndatum', station = self.station,
                                        colors = self.colors, setup_type = 'verify',
                                        on_record = self.compute_error)
        self.content.add_widget(self.recorder)

        self.results = e5_label('', colors = self.colors)
        self.content.add_widget(self.results)

        self.back_button = e5_button(text = 'Back', size_hint_y = None,
                                    size_hint_x = 1,
                                    id = 'cancel',
                                    colors = self.colors, selected = True)
        self.content.add_widget(self.back_button)
        self.back_button.bind(on_press = self.close_screen)

    def compute_error(self):
        if self.datum1.datum:
            error = self.station.round_point(self.station.vector_subtract(self.datum1.datum, self.recorder.result.xyz_global))
            self.results.text = '\n  X error: %s\n  Y error: %s\n  Z error: %s' % (error.x, error.y, error.z)
        else:
            self.results.text = "Select the name of the verification datum before recording the datum."

    def close_screen(self, instance):
        if self.datum1.datum:
            self.ini.update_value('SETUPS', 'VERIFICATION',self.datum1.datum.name)
            self.ini.save()
        self.parent.current = 'MainScreen'
        
class record_button(e5_button):

    popup = ObjectProperty(None)

    def __init__(self, station = None, result_label = None, setup_type = None, on_record = None, **kwargs):
        super(record_button, self).__init__(**kwargs)
        #self.colors = colors if colors is not None else ColorScheme()
        self.station = station
        self.bind(on_press = self.record_datum)
        self.result_label = result_label
        self.setup_type = setup_type
        self.on_record = on_record
        
    def record_datum(self, instance):
        if self.id == 'datum1' and self.setup_type in ['Over a datum + Record a datum','Record two datums']:
            self.station.set_horizontal_angle(0)
        self.station.take_shot()
        self.wait_for_shot()

    def wait_for_shot(self):
        if self.station.make == 'Microscribe':
            #self.popup = DataGridTextBox(title = self.text + '.  Waiting on Microscribe...', button_text = ['Cancel', 'Next'], call_back = self.microscribe)
            self.popup = DataGridTextBox(title = 'EDM',
                                            label = self.text + '.  Waiting on...',
                                            text = '<Microscribe>',
                                            button_text = ['Cancel', 'Next'],
                                            call_back = self.microscribe,
                                            colors = self.colors)
            self.popup.open()

    def microscribe(self, instance):
        result = self.popup.result
        self.popup.dismiss()
        if result:
            error = True
            try:
                if len(result.split(',')) == 3:
                    x, y, z = result.split(',')
                    x = round(float(x) / 1000, 3) 
                    y = round(float(y) / 1000, 3) 
                    z = round(float(z) / 1000, 3)
                    self.station.xyz = point(x, y, z)
                    if self.setup_type == 'verify' or self.setup_type == 'record_new':
                        self.station.make_global()
                    else:
                        self.station.round_xyz()
                    self.have_shot()
                    error = False
            except:
                pass
            if error:
                self.popup = e5_MessageBox(title = 'Error', message = '\nData not formatted correctly.  EDM expects three floating point numbers separated by commas.',
                                            colors = self.colors)
                self.popup.open()

    def have_shot(self):
        if self.station.xyz:
            if self.setup_type == 'verify' or self.setup_type == 'record_new':
                self.result_label.text = 'X: %s\nY: %s\nZ: %s' % (self.station.xyz_global.x,
                                                                    self.station.xyz_global.y,
                                                                    self.station.xyz_global.z)
            else:
                self.result_label.text = 'X: %s\nY: %s\nZ: %s' % (self.station.xyz.x,
                                                                    self.station.xyz.y,
                                                                    self.station.xyz.z)

            self.result_label.xyz = self.station.xyz
            self.result_label.xyz_global = self.station.xyz_global
        else:
            self.result_label.text = 'Recording error.'
            self.result_label.xyz = None
            self.result_label.xyz_global = None
        if self.on_record is not None:
            self.on_record()

class record_result(e5_label):
    xyz = None

class datum_recorder(GridLayout):

    def __init__(self, text = '', datum_no = 1, station = None,
                        colors = None, setup_type = None,
                        on_record = None, **kwargs):
        super(datum_recorder, self).__init__(**kwargs)
        self.padding = 10
        self.spacing = 10
        self.colors = colors if colors is not None else ColorScheme()
        self.station = station
        self.cols = 2
        self.results = []
        self.buttons = []
        self.size_hint_y = None
        self.result = record_result('', colors = self.colors)
        self.button = record_button(text = text if text else 'Record datum %s' % (datum_no),
                                    selected = True,
                                    id = 'datum%s' % (datum_no),
                                    colors = self.colors,
                                    station = self.station,
                                    result_label = self.result,
                                    setup_type = setup_type,
                                    on_record = on_record)
        self.add_widget(self.button)
        self.add_widget(self.result)
       
class datum_selector(GridLayout):
    
    datum = None
    popup = ObjectProperty(None)
    popup_open = False

    def __init__(self, text = '',
                        data = None, colors = None, default_datum = None, 
                        call_back = None,
                        id = None,
                        **kwargs):
        super(datum_selector, self).__init__(**kwargs)
        #self.orientation = 'horizontal'
        self.padding = 10
        self.spacing = 10
        self.cols = 2
        self.colors = colors
        self.data = data
        self.datum = default_datum
        self.call_back = call_back
        self.size_hint_y = None
        self.add_widget(e5_button(text = text,
                                    selected = True,
                                    call_back = self.show_select_datum,
                                    colors = self.colors))
        if self.datum is not None:
            self.result = e5_label('Datum: %s\nX: %s\nY: %s\nZ: %s' % (self.datum.name,
                                                                    self.datum.x,
                                                                    self.datum.y,
                                                                    self.datum.z), colors = self.colors)
        else:
            self.result = e5_label('Datum:\nX:\nY:\nZ:', colors = self.colors)
        self.add_widget(self.result)

    def show_select_datum(self, instance):
        self.popup = DataGridMenuList(title = "Datum",
                                        menu_list = self.data.names('datums'),
                                        menu_selected = '',
                                        call_back = self.datum_selected,
                                        colors = self.colors)
        self.popup.open()
    
    def datum_selected(self, instance):
        self.popup.dismiss()
        self.datum = self.data.get_datum(instance.text)
        if self.datum:
            self.result.text = 'Datum: %s\nX: %s\nY: %s\nZ: %s' % (self.datum.name,
                                                                    self.datum.x,
                                                                    self.datum.y,
                                                                    self.datum.z)
            if self.call_back:
                self.call_back(self)
        else:
            self.result.text = 'Search error'

class setups(ScrollView):

    id = ObjectProperty(None)
    popup = ObjectProperty(None)
    popup_open = False
    recorder = []

    def __init__(self, setup_type, data = None, ini = None, station = None, colors = None, **kwargs):
        super(setups, self).__init__(**kwargs)

        self.colors = colors if colors is not None else ColorScheme()
        self.data = data
        self.station = station
        self.ini = ini
        self.recorder = []
        self.bar_width = 10

        y_sizes = {"Horizontal Angle Only" : 3.0,
                    "Over a datum": 1.1,
                    "Over a datum + Record a datum" : 1.6,
                    "Record two datums" : 2.6,
                    "Three datum shift" : 6.0}
        
        self.scrollbox = GridLayout(cols = 1,
                                size_hint = (1, None),
#                                id = 'setups_box',
                                spacing = 5)
        self.scrollbox.bind(minimum_height = self.scrollbox.setter('height'))

        instructions = Label(color = self.colors.text_color, size_hint_y = None)

        if setup_type == "Horizontal Angle Only":
            instructions.text = 'Enter the angle to be uploaded to the station.'
            self.scrollbox.add_widget(instructions)

            content1 = GridLayout(cols = 2, padding = 10, size_hint_y = None)
            content1.add_widget(e5_label('Horizontal angle to the point\n(use ddd.mmss)'))
            self.hangle = TextInput(text = '', multiline = False,
#                                    id = 'h_angle',
                                    size_hint_max_y = 30)
            content1.add_widget(self.hangle)
            self.scrollbox.add_widget(content1)

            content2 = GridLayout(cols = 1, padding = 10, size_hint_y = None)
            content2.add_widget(e5_button(text = 'Upload angle', selected = True, call_back = self.set_hangle))
            self.scrollbox.add_widget(content2)

        elif setup_type == "Over a datum":
            instructions.text = 'Use this option when the station is setup over a known point and you can measure the station height or to set the station location directly (with no station height).  Note this option assumes the horizontal angle is already correct or will be otherwise set.'
            self.scrollbox.add_widget(instructions)

            self.over_datum = datum_selector(text = 'Select a datum',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', 'OVERDATUM')))
            self.scrollbox.add_widget(self.over_datum)

            content2 = GridLayout(cols = 2, padding = 10, size_hint_y = None)
            content2.add_widget(e5_label('Station height (optional)'))
            self.station_height = TextInput(text = '', multiline = False,
#                                            id = 'station_height',
                                            size_hint_max_y = 30)
            content2.add_widget(self.station_height)
            self.scrollbox.add_widget(content2)

        elif setup_type == "Over a datum + Record a datum":
            instructions.text = "Select the datum under the station and a datum to be recorded.  EDM will automatically set the correct horizontal angle and compute the station's XYZ coordinates."
            self.scrollbox.add_widget(instructions)

            self.datum1 = datum_selector(text = 'Select datum\nunder the station',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', 'OVERDATUM')))
            self.scrollbox.add_widget(self.datum1)

            self.datum2 = datum_selector(text = 'Select datum\nto record',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', 'RECORDDATUM')),
                                                call_back = self.datum1_selected)
            self.scrollbox.add_widget(self.datum2)
            
            self.recorder.append(datum_recorder('Record datum', station = self.station, colors = self.colors, setup_type = setup_type))
            self.scrollbox.add_widget(self.recorder[0])

        elif setup_type == "Record two datums":
            instructions.text = "Select two datums to record. EDM will use triangulation to compute the station's XYZ coordinates."
            self.scrollbox.add_widget(instructions)

            self.datum1 = datum_selector(text = 'Select first datum\nto record',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', '2DATUMS_DATUM_1')),
                                                call_back = self.datum1_selected)
            self.scrollbox.add_widget(self.datum1)

            self.datum2 = datum_selector(text = 'Select second datum\nto record',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', '2DATUMS_DATUM_2')),
                                                call_back = self.datum2_selected)
            self.scrollbox.add_widget(self.datum2)

            for n in range(2):
                self.recorder.append(datum_recorder('Record datum', datum_no = n + 1, station = station, colors = colors, setup_type = setup_type))
                self.scrollbox.add_widget(self.recorder[n])

        elif setup_type == "Three datum shift":
            instructions.text = "This option is designed to let one grid be rotated into another and is best for when a block of sediment is being excavated in a lab.  It requires three datums points."
            self.scrollbox.add_widget(instructions)

            self.datum1 = datum_selector(text = 'Select datum 1',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', '3DATUM_SHIFT_GLOBAL_1')),
                                                call_back = self.datum1_selected)
            self.scrollbox.add_widget(self.datum1)

            self.datum2 = datum_selector(text = 'Select datum 2',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', '3DATUM_SHIFT_GLOBAL_2')),
                                                call_back = self.datum2_selected)
            self.scrollbox.add_widget(self.datum2)

            self.datum3 = datum_selector(text = 'Select datum 3',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', '3DATUM_SHIFT_GLOBAL_3')),
                                                call_back = self.datum3_selected)
            self.scrollbox.add_widget(self.datum3)

            for n in range(3):
                datum_name = self.data.get_datum(self.ini.get_value('SETUPS', '3DATUM_SHIFT_GLOBAL_%s' % (n + 1)))
                if datum_name is None:
                    datum_name = 'Record datum %s' % (n + 1)
                else:
                    datum_name = 'Record %s' % datum_name.name
                self.recorder.append(datum_recorder(datum_name, datum_no = n + 1, station = station,
                                                                colors = self.colors, setup_type = setup_type))
                self.scrollbox.add_widget(self.recorder[n])
            
        instructions.bind(texture_size = lambda instance, value: setattr(instance, 'height', value[1]))
        instructions.bind(width = lambda instance, value: setattr(instance, 'text_size', (value * .95, None)))
        
        self.size_hint = (1, .9)
        #self.size = (Window.width, Window.height / 2)
        self.id = 'setup_scroll'
        self.add_widget(self.scrollbox)

        def draw_background(widget, prop):
            with widget.canvas.before:
                Color(0.8, 0.8, 0.8, 1)
                Rectangle(size=self.size, pos=self.pos)

        #self.bind(size = draw_background)
        #self.bind(pos = draw_background)

    def datum1_selected(self, instance):
        self.recorder[0].children[1].text = 'Record ' + instance.datum.name

    def datum2_selected(self, instance):
        self.recorder[1].children[1].text = 'Record ' + instance.datum.name

    def datum3_selected(self, instance):
        self.recorder[2].children[1].text = 'Record ' + instance.datum.name

    def set_hangle(self, instance):
        if self.hangle:
            self.station.set_horizontal_angle(self.hangle.text)

class InitializeStationScreen(Screen):

    def __init__(self, data = None, station = None, ini = None, colors = None, **kwargs):
        super(InitializeStationScreen, self).__init__(**kwargs)

        self.colors = colors if colors else ColorScheme()
        self.station = station
        self.data = data
        self.ini = ini

        lastsetup_type = self.ini.get_value('SETUPS', 'LASTSETUP_TYPE')
        self.setup = lastsetup_type if lastsetup_type else 'Horizontal Angle Only'

        self.content = BoxLayout(orientation = 'vertical',
                                size_hint_y = .9,
                                size_hint_x = width_calculator(.9, 400),
                                pos_hint = {'center_x': .5, 'center_y': .5},
#                                id = 'content',
                                padding = 5,
                                spacing = 5)
        self.add_widget(self.content)

        setup_type_box = GridLayout(cols = 2,
                                    #size_hint = (width_calculator(.9, 400), None),
                                    size_hint_y = None,
                                    pos_hint = {'center_x': .5, 'center_y': .5})
        setup_type_box.add_widget(e5_label('Select a setup type', colors = self.colors, size_hint = (.5, None)))

        spinner_dropdown_button = SpinnerOptions
        spinner_dropdown_button.font_size = colors.button_font_size.replace("sp",'') if colors.button_font_size else None
        spinner_dropdown_button.background_color = (0, 0, 0, 1)

        self.setup_type = Spinner(text = self.setup,
                                    values=["Horizontal Angle Only",
                                            "Over a datum",
                                            "Over a datum + Record a datum",
                                            "Record two datums",
                                            "Three datum shift"],
#                                    id = 'setup_type',
                                    size_hint = (.5, None),
                                    option_cls = spinner_dropdown_button
                                    #pos_hint = {'center_x': .5, 'center_y': .5}
                                    )
        if colors.button_font_size:
            self.setup_type.font_size = colors.button_font_size
        setup_type_box.add_widget(self.setup_type)
        self.setup_type.bind(text = self.rebuild)
        self.content.add_widget(setup_type_box)

        self.scroll_content = BoxLayout(orientation = 'vertical',
                                        size_hint = (1, .9),
                                        spacing = 5, padding = 5)

        self.content.add_widget(self.scroll_content)

        self.setup_widgets = setups(self.setup_type.text,                                                
                                    data = self.data,
                                    ini = self.ini,
                                    station = self.station,
                                    colors = self.colors)
        self.scroll_content.add_widget(self.setup_widgets)

        self.content.add_widget(e5_side_by_side_buttons(text = ['Back','Accept Setup'],
                                                        id = ['back','accept'],
                                                        call_back = [self.go_back, self.accept_setup],
                                                        selected = [True, True],
                                                        colors = self.colors))

    def rebuild(self, instance, value):
        self.setup = value
        self.scroll_content.clear_widgets()
        self.setup_widgets = setups(self.setup_type.text,                                                
                                                data = self.data,
                                                ini = self.ini,
                                                station = self.station,
                                                colors = self.colors)
        self.scroll_content.add_widget(self.setup_widgets)

    def go_back(self, instance):
        self.ini.update_value(__program__, 'LASTSETUP_TYPE', self.setup_type.text)        
        self.parent.current = 'MainScreen'

    def accept_setup(self, instance):

        self.new_station = None
        txt = None

        if self.setup_type.text == 'Horizontal Angle Only':
            pass

        elif self.setup_type.text == 'Over a datum':
            if self.setup_widgets.over_datum.datum is None:
                error_message = '\nSelect the datum under the total station and optionally provide the station height.'
            else:
                station_height = float(self.setup_widgets.station_height.text) if self.setup_widgets.station_height.text  else 0
                self.new_station = self.setup_widgets.over_datum.datum
                self.new_station.z += station_height
                txt = '\nSet the station coordinates to\nX : %s\nY: %s\nZ: %s' % (self.new_station.x, self.new_station.y, self.new_station.z)

        elif self.setup_type.text == 'Over a datum + Record a datum':
            if self.setup_widgets.datum1.datum is None or self.setup_widgets.datum2.datum is None:
                error_message = '\nSelect the datum under the total station and a datum to record.'
            elif self.setup_widgets.recorder.results[1].xyz is None:
                error_message = '\nRecord the datum before accepting the setup.'
            else:
                # compute difference between datums and compare this with station.xyz
                # then report error and offer to upload angle
                # angle is the angle between these two datums
                pass

        elif self.setup_type.text == 'Record two datums':
            if self.setup_widgets.datum1.datum is None or self.setup_widgets.datum2.datum is None:
                error_message = '\nSelect two datums to record.'
            elif self.setup_widgets.recorder.results[1].xyz is None or self.setup_widgets.recorder.results[2].xyz is None:
                error_message = '\nRecord each datum.  It is important that the first datum is recorded and then the second and not the other way around.  Note that before the first datum is recorded, a horizontal angle of 0.0000 will be uploaded.'
            else:
                # do a two shot math thing, report the new location, and if they accept it, upload the angle
                pass

        elif self.setup_type.text == 'Three datum shift':
            if self.setup_widgets.datum1.datum is None or self.setup_widgets.datum2.datum is None or self.setup_widgets.datum3.datum is None:
                error_message = '\nSelect three datums to record.'
            elif self.setup_widgets.recorder[0].result.xyz is None or self.setup_widgets.recorder[1].result.xyz is None or self.setup_widgets.recorder[2].result.xyz is None:
                error_message = '\nRecord each datum.'
            else:
                dist_12_measured = self.station.distance(self.setup_widgets.recorder[0].result.xyz, self.setup_widgets.recorder[1].result.xyz)
                dist_12_datums = self.station.distance(self.setup_widgets.datum1.datum.as_point(), self.setup_widgets.datum2.datum.as_point())
                dist_12_error = round(abs(dist_12_measured - dist_12_datums), 3)
                
                dist_23_measured = self.station.distance(self.setup_widgets.recorder[1].result.xyz, self.setup_widgets.recorder[2].result.xyz)
                dist_23_datums = self.station.distance(self.setup_widgets.datum2.datum.as_point(), self.setup_widgets.datum3.datum.as_point())
                dist_23_error = round(abs(dist_23_measured - dist_23_datums), 3)

                dist_13_measured = self.station.distance(self.setup_widgets.recorder[0].result.xyz, self.setup_widgets.recorder[2].result.xyz)
                dist_13_datums = self.station.distance(self.setup_widgets.datum1.datum.as_point(), self.setup_widgets.datum3.datum.as_point())
                dist_13_error = round(abs(dist_13_measured - dist_13_datums), 3)

                # should also include a mean error by averaging everything

                txt = '\nThe following errors are noted.  The actual distance between datums 1 and 2 is %s and the measured distance was %s.  ' % (round(dist_12_datums,3), round(dist_12_measured, 3))
                txt +=  'The actual distance between datums 2 and 3 is %s and the measured distance was %s.  ' % (round(dist_23_datums,3), round(dist_23_measured, 3))
                txt +=  'The actual distance between datums 1 and 3 is %s and the measured distance was %s.  ' % (round(dist_13_datums,3), round(dist_13_measured, 3))
                txt +=  '\n\nThis corresponds to errors of %s, %s, and %s, respectively.' % (dist_12_error, dist_23_error, dist_13_error)

        if self.new_station or txt:
            self.popup = e5_MessageBox('Accept setup?', txt,
                                        response_type = "YESNO",
                                        call_back = [self.set_and_close, self.close_popup],
                                        colors = self.colors)
        else:
            self.popup = e5_MessageBox('Error', error_message,
                                        colors = self.colors)

        self.popup.open()

    def close_popup(self, instance):
        self.popup.dismiss()

    def set_and_close(self, instance):
        if self.setup_type.text == 'Horizontal Angle Only':
            pass

        elif self.setup_type.text == 'Over a datum':
            self.ini.update_value('SETUPS', 'OVERDATUM', self.setup_widgets.over_datum.datum.name)

        elif self.setup_type.text == 'Over a datum + Record a datum':
            self.ini.update_value('SETUPS', 'OVERDATUM', self.setup_widgets.datum1.datum.name)
            self.ini.update_value('SETUPS', 'RECORDDATUM', self.setup_widgets.datum2.datum.name)

        elif self.setup_type.text == 'Record two datums':
            self.ini.update_value('SETUPS', '2DATUMS_DATUM_1', self.setup_widgets.datum1.datum.name)
            self.ini.update_value('SETUPS', '2DATUMS_DATUM_2', self.setup_widgets.datum2.datum.name)

        elif self.setup_type.text == 'Three datum shift':
            self.station.rotate_local = [self.setup_widgets.recorder[0].result.xyz,
                                            self.setup_widgets.recorder[1].result.xyz,
                                            self.setup_widgets.recorder[2].result.xyz]
            self.station.rotate_global = [self.setup_widgets.datum1.datum.as_point(),
                                                self.setup_widgets.datum2.datum.as_point(),
                                                self.setup_widgets.datum3.datum.as_point()]
            self.ini.update_value('SETUPS', '3DATUM_SHIFT_LOCAL_1', '%s,%s,%s' % (self.setup_widgets.recorder[0].result.xyz.x,
                                                                                        self.setup_widgets.recorder[0].result.xyz.y,
                                                                                        self.setup_widgets.recorder[0].result.xyz.z))
            self.ini.update_value('SETUPS', '3DATUM_SHIFT_LOCAL_2', '%s,%s,%s' % (self.setup_widgets.recorder[1].result.xyz.x,
                                                                                        self.setup_widgets.recorder[1].result.xyz.y,
                                                                                        self.setup_widgets.recorder[1].result.xyz.z))
            self.ini.update_value('SETUPS', '3DATUM_SHIFT_LOCAL_3', '%s,%s,%s' % (self.setup_widgets.recorder[2].result.xyz.x,
                                                                                        self.setup_widgets.recorder[2].result.xyz.y,
                                                                                        self.setup_widgets.recorder[2].result.xyz.z))
            self.ini.update_value('SETUPS', '3DATUM_SHIFT_GLOBAL_1', self.setup_widgets.datum1.datum.name)
            self.ini.update_value('SETUPS', '3DATUM_SHIFT_GLOBAL_2', self.setup_widgets.datum2.datum.name)
            self.ini.update_value('SETUPS', '3DATUM_SHIFT_GLOBAL_3', self.setup_widgets.datum3.datum.name)

        self.popup.dismiss()
        self.station.location = self.new_station
        self.ini.update_value('SETUPS', 'LASTSETUP_TYPE', self.setup_type.text)        
        self.ini.save()
        self.parent.current = 'MainScreen'

class EditLastRecordScreen(e5_RecordEditScreen):

    def on_pre_enter(self):
        if self.data_table is not None and self.e5_cfg is not None:
            try:
                last = self.data.db.table(self.data_table).all()[-1]
                self.doc_id = last.doc_id
            except:
                self.doc_id = None
        self.put_data_in_frame()

class EditPointScreen(e5_RecordEditScreen):

    def on_pre_enter(self):
        if self.data_table is not None and self.e5_cfg is not None:
            try:
                last = self.data.db.table(self.data_table).all()[-1]
                self.doc_id = last.doc_id
            except:
                self.doc_id = None
        self.put_data_in_frame()

class EditDatumScreen(Screen):

    pass

class EditPointsScreen(e5_DatagridScreen):
    pass

class EditPrismsScreen(e5_DatagridScreen):
    pass

class EditUnitsScreen(e5_DatagridScreen):
    pass

class EditDatumsScreen(e5_DatagridScreen):
    pass

class SpinnerOptions(SpinnerOption):
    def __init__(self, **kwargs):
        super(SpinnerOptions, self).__init__(**kwargs)

class station_setting(GridLayout):
    label = ObjectProperty(None)
    spinner = ObjectProperty(None)
    id = ObjectProperty(None)
    comport_to_test = None
    valid_comports = []

    def __init__(self, label_text = '', spinner_values = (), default = '',
                        id = None, call_back = None, colors = None, station = None, **kwargs):
        super(station_setting, self).__init__(**kwargs)

        self.station = station
        self.id = id
        self.cols = 2
        self.pos_hint = {'center_x': .5},
        self.colors = colors
        self.label = e5_label(text = label_text, colors = colors)
        self.add_widget(self.label)

        # Create a default dropdown button and then modify its properties
        # For some reason, the usual font size specification doesn't work here and sp has to be removed
        spinner_dropdown_button = SpinnerOptions
        spinner_dropdown_button.font_size = colors.button_font_size.replace("sp",'') if colors.button_font_size else None
        spinner_dropdown_button.background_color = (0, 0, 0, 1)

        self.spinner = Spinner(text = default if default is not None else '',
                                values = spinner_values,
                                font_size = colors.button_font_size if colors.button_font_size else None,
                                option_cls = spinner_dropdown_button)
        if label_text == 'Port Number':
            comport = GridLayout(cols = 2, spacing = 5)
            comport.add_widget(self.spinner)
            comport.add_widget(e5_button('Scan', colors = colors, call_back = self.scanner))
            self.add_widget(comport)
        else:
            self.add_widget(self.spinner)
        if call_back:
            self.spinner.bind(text = call_back)

    def scanner(self, instance):
        if self.station:
            ports = self.station.list_comports()
            text = 'Available ports:\n\n'
            for port in ports:
                text += '%s - %s\n' % (port[0]['port'], port[0]['desc'])
            self.spinner.values = list([port[0]['port'] for port in ports])
            self.popup = e5_MessageBox('COM Ports', text,
                                        response_type = "OK",
                                        call_back = self.close_popup_comports,
                                        colors = self.colors)
            self.popup.open()
            self.popup_open = True
        else:
            self.event1 = Clock.schedule_once(self.show_popup_message, .2)
            self.event2 = Clock.schedule_interval(self.check_comports, .2)


    def show_popup_message(self, dt):
        self.popup = e5_MessageBox('COM Ports','\nLooking for valid COM ports...This can take several seconds...And the Cancel button might appear non-responsive...',
                                    response_type = "CANCEL",
                                    call_back = self.close_popup,
                                    colors = self.colors)
        self.popup.open()
        self.popup_open = True


    def close_popup(self, value):
        self.popup.dismiss()
        self.popup_open = False
        self.event2.cancel()
        self.comport_to_test = None
       
    def close_popup_comports(self, value):
        self.popup.dismiss()
        self.popup_open = False

    def comportIsUsable(self, portName):
        try:
            ser = serial.Serial(port = portName)
            ser.close()
            return portName
        except:
            return None


    def check_comports(self, dt):
        if self.comport_to_test == None:
            self.comport_to_test = 0
            self.valid_comports = []
        self.comport_to_test += 1
        if self.comport_to_test > __LASTCOMPORT__:
            self.spinner.values = list(filter(None.__ne__, self.valid_comports))
            self.event2.cancel()
            self.close_popup(None)
            self.comport_to_test = None
        else:
            self.valid_comports.append(self.comportIsUsable("COM%s" % self.comport_to_test))

    
    def comports(self):
        return list(filter(None.__ne__, [self.comportIsUsable("COM%s" % comno) for comno in range(1, __LASTCOMPORT__ + 1)]))


class StationConfigurationScreen(Screen):

    def __init__(self, station = None, ini = None, colors = None, **kwargs):
        super(StationConfigurationScreen, self).__init__(**kwargs)

        self.station = station
        self.colors = colors
        self.ini = ini

    def on_enter(self):
        self.clear_widgets()
        self.layout = GridLayout(cols = 1,
                                 spacing = 5,
                                 size_hint_x = width_calculator(.9, 800),
                                 size_hint_y = .9,
                                 pos_hint = {'center_x': .5, 'center_y': .5})
        self.add_widget(self.layout)
        self.build_screen()

    def build_screen(self):
        self.station_type = station_setting(label_text = 'Station type',
                                            spinner_values = ("Leica", "Wild", "Topcon", "Microscribe", "Simulate"),
                                            call_back = self.toggle_buttons,
                                            id = 'station_type',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'STATION'))
        self.layout.add_widget(self.station_type)

        self.communications = station_setting(label_text = 'Communications',
                                            spinner_values = ("Serial", "Bluetooth"),
                                            #call_back = self.update_ini,
                                            id = 'communications',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'COMMUNICATIONS'))
        self.layout.add_widget(self.communications)

        self.comports = station_setting(label_text = 'Port Number',
                                            spinner_values = [],
                                            #call_back = self.update_ini,
                                            id = 'comport',
                                            colors = self.colors, station = self.station,
                                            default = self.ini.get_value(__program__, 'COMPORT'))
        self.layout.add_widget(self.comports)
        
        self.baud_rate = station_setting(label_text = 'Baud rate',
                                            spinner_values = ("1200", "2400", "4800", "9600", "14400", "19200"),
                                            #call_back = self.update_ini,
                                            id = 'baudrate',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'BAUDRATE'))
        self.layout.add_widget(self.baud_rate)

        self.parity = station_setting(label_text = 'Parity',
                                            spinner_values = ("Even", "Odd","None"),
                                            #call_back = self.update_ini,
                                            id = 'parity',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'PARITY'))
        self.layout.add_widget(self.parity)

        self.data_bits = station_setting(label_text = 'Databits',
                                            spinner_values = ("7", "8"),
                                            #call_back = self.update_ini,
                                            id = 'databits',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'DATABITS'))
        self.layout.add_widget(self.data_bits)

        self.stop_bits = station_setting(label_text = 'Stopbits',
                                            spinner_values = ("0","1","2"),
                                            #call_back = self.update_ini,
                                            id = 'stopbits',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'STOPBITS'))
        self.layout.add_widget(self.stop_bits)                                                

        self.buttons = e5_side_by_side_buttons(text = ['Back','Set'],
                                                id = ['Back','Set'],
                                                selected = [True, False],
                                                call_back = [self.close_screen, self.update_ini],
                                                colors = self.colors)
        self.layout.add_widget(self.buttons)
        self.toggle_buttons(None, None)
        self.changes = False

    def toggle_buttons(self, instance, value):
        disabled = self.station_type.spinner.text in ['Simulate', 'Microscribe']
        self.stop_bits.spinner.disabled = disabled
        self.parity.spinner.disabled = disabled
        self.data_bits.spinner.disabled = disabled
        self.baud_rate.spinner.disabled = disabled
        self.comports.spinner.disabled = disabled
        self.communications.spinner.disabled = disabled

    def update_ini(self, instance):
        self.station.make = self.station_type.spinner.text 
        self.ini.update_value(__program__, 'STATION', self.station_type.spinner.text)
        self.station.stopbits = self.stop_bits.spinner.text
        self.ini.update_value(__program__, 'STOPBITS', self.stop_bits.spinner.text)
        self.station.baudrate = self.baud_rate.spinner.text
        self.ini.update_value(__program__, 'BAUDRATE', self.baud_rate.spinner.text)
        self.station.databits = self.data_bits.spinner.text
        self.ini.update_value(__program__, 'DATABITS', self.data_bits.spinner.text)
        self.station.comport = self.comports.spinner.text
        self.ini.update_value(__program__, 'COMPORT', self.comports.spinner.text)
        self.station.parity = self.parity.spinner.text
        self.ini.update_value(__program__, 'PARITY', self.parity.spinner.text)
        self.station.communications = self.communications.spinner.text
        self.ini.update_value(__program__, 'COMMUNICATIONS', self.communications.spinner.text)
        self.ini.save()
        self.station.open()
        self.close_screen(None)
        
    def close_screen(self, value):
        self.parent.current = 'MainScreen'

#Region Help Screens

class AboutScreen(e5_InfoScreen):
    def on_pre_enter(self):
        self.content.text = '\n\nEDM by Shannon P. McPherron\n\nVersion ' + __version__ + ' Alpha\nApple Pie\n\n'
        self.content.text += 'Build using Python 3.6, Kivy 1.10.1 and TinyDB 3.11.1\n\n'
        self.content.text += 'An OldStoneAge.Com Production\n\n' + __date__ 
        self.content.halign = 'center'
        self.content.valign = 'middle'
        self.content.color = self.colors.text_color
        self.back_button.background_color = self.colors.button_background
        self.back_button.color = self.colors.button_color

class StatusScreen(e5_InfoScreen):

    def __init__(self, data = None, ini = None, cfg = None, station = None, **kwargs):
        super(StatusScreen, self).__init__(**kwargs)
        self.data = data
        self.ini = ini
        self.cfg = cfg
        self.station = station

    def on_pre_enter(self):
        txt = self.data.status() if self.data else 'A data file has not been initialized or opened.\n\n'
        txt += self.cfg.status() if self.cfg else 'A CFG is not open.\n\n'
        txt += self.ini.status() if self.ini else 'An INI file is not available.\n\n'
        txt += self.station.status() if self.station else 'Total station information is not available.\n\n'
        txt += '\nThe default user path is %s.\n' % self.ini.get_value(__program__,"APP_PATH")
        txt += '\nThe operating system is %s.\n' % platform_name()
        txt += '\nPython buid is %s.\n' % (python_version())
        txt += '\nLibraries installed include Kivy %s and TinyDB %s.\n' % (__kivy_version__, __tinydb_version__)
        txt += '\nEDM was tested and distributed on Python 3.6, Kivy 1.10.1 and TinyDB 3.11.1.\n'
        self.content.text = txt
        self.content.color = self.colors.text_color
        self.back_button.background_color = self.colors.button_background
        self.back_button.color = self.colors.button_color

#endregion

#sm = ScreenManager(id = 'screen_manager')
sm = ScreenManager()

class EDMApp(e5_Program):

    def __init__(self, **kwargs):
        super(EDMApp, self).__init__(**kwargs)

        self.colors = ColorScheme()
        self.ini = INI()
        self.cfg = CFG()
        self.data = DB()

        self.app_path = self.user_data_dir
        self.setup_logger()
        self.setup_program()

        self.station = totalstation(self.ini.get_value(__program__,'STATION'))
        self.station.setup(self.ini, self.data)

    def setup_logger(self):
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh = logging.FileHandler(os.path.join(self.app_path, __program__ + '.log'))
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    def add_screens(self):
        sm.add_widget(MainScreen(name = 'MainScreen', 
                                 colors = self.colors,
                                 ini = self.ini,
                                 cfg = self.cfg,
                                 data = self.data,
                                 station = self.station))

        sm.add_widget(VerifyStationScreen(name = 'VerifyStationScreen',
                                            id = 'verify_station',
                                            data = self.data,
                                            station = self.station,
                                            colors = self.colors,
                                            ini = self.ini))

        sm.add_widget(RecordDatumsScreen(name = 'RecordDatumsScreen',
#                                            id = 'record_datums',
                                            data = self.data,
                                            station = self.station,
                                            colors = self.colors,
                                            ini = self.ini))

        sm.add_widget(EditLastRecordScreen(name = 'EditLastRecordScreen',
#                                        id = 'editlastrecord_screen',
                                        colors = self.colors,
                                        data = self.data,
                                        data_table = self.data.table,
                                        doc_id = None,
                                        e5_cfg = self.cfg))

        sm.add_widget(EditPointScreen(name = 'EditPointScreen',
                                        colors = self.colors,
#                                        id = 'editpoint_screen',
                                        data = self.data,
                                        data_table = self.data.table,
                                        doc_id = None,
                                        e5_cfg = self.cfg,
                                        one_record_only = True))

        sm.add_widget(EditPointsScreen(name = 'EditPointsScreen',
#                                        id = 'editpoints_screen',
                                        colors = self.colors,
                                        main_data = self.data,
                                        main_tablename = self.data.table,
                                        main_cfg = self.cfg))

        datum_cfg = CFG()
        datum_cfg.build_datum()
        sm.add_widget(EditPointsScreen(name = 'EditDatumsScreen',
#                                        id = 'editdatums_screen',
                                        colors = self.colors,
                                        main_data = self.data,
                                        main_tablename = 'datums',
                                        main_cfg = datum_cfg,
                                        addnew = True))

        prism_cfg = CFG()
        prism_cfg.build_prism()
        sm.add_widget(EditPointsScreen(name = 'EditPrismsScreen',
#                                        id = 'editprisms_screen',
                                        colors = self.colors,
                                        main_data = self.data,
                                        main_tablename = 'prisms',
                                        main_cfg = prism_cfg,
                                        addnew = True))

        units_cfg = CFG()
        units_cfg.build_unit()
        sm.add_widget(EditPointsScreen(name = 'EditUnitsScreen',
#                                        id = 'editunits_screen',
                                        colors = self.colors,
                                        main_data = self.data,
                                        main_tablename = 'units',
                                        main_cfg = units_cfg,
                                        addnew = True))

        sm.add_widget(StatusScreen(name = 'StatusScreen',
#                                    id = 'status_screen',
                                    colors = self.colors,
                                    cfg = self.cfg,
                                    ini = self.ini,
                                    data = self.data,
                                    station = self.station))

        sm.add_widget(e5_LogScreen(name = 'LogScreen',
#                                id = 'log_screen',
                                colors = self.colors,
                                logger = logger))

        sm.add_widget(e5_CFGScreen(name = 'CFGScreen',
#                                id = 'cfg_screen',
                                colors = self.colors,
                                cfg = self.cfg))

        sm.add_widget(e5_INIScreen(name = 'INIScreen',
#                                id = 'ini_screen',
                                colors = self.colors,
                                ini = self.ini))

        sm.add_widget(AboutScreen(name = 'AboutScreen',
#                                    id = 'about_screen',
                                    colors = self.colors))

        sm.add_widget(StationConfigurationScreen(name = 'StationConfigurationScreen',
#                                    id = 'station_configuration_screen',
                                    station = self.station,
                                    ini = self.ini,
                                    colors = self.colors))

        sm.add_widget(InitializeStationScreen(name = 'InitializeStationScreen',
#                                                id = 'initialize_station_screen',
                                                data = self.data,
                                                station = self.station,
                                                ini = self.ini,
                                                colors = self.colors))

        sm.add_widget(e5_SettingsScreen(name = 'EDMSettingsScreen',
#                                        id = 'edmsettings_screen',
                                        colors = self.colors,
                                        ini = self.ini,
                                        cfg = self.cfg))

    def build(self):
        self.add_screens()
        restore_window_size_position(__program__, self.ini)
        #Window.borderless = True
        self.title = __program__ + " " + __version__
        logger.info(__program__ + ' started, logger initialized, and application built.')
        sm.screens[0].build_mainscreen()
        return(sm)

Factory.register(__program__, cls=EDMApp)

if __name__ == '__main__':
    logger = logging.getLogger(__program__)
    EDMApp().run()