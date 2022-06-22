# EDM by Shannon McPherron
#
#   This is an alpha release.  I am still working on bugs and I am still implementing some features.
#   It should be backwards compatible with EDM-Mobile and EDMWin (but there are still some issues).

#   A text field can be linked to another table. [future feature]
#   Think through making a field link to a database table (unique value is a table record)

# ToDo NewPlot
#   Read JSON file

# ToDo More Longterm
#   Add bluetooth communications

# Bugs
#   when you delete records one by one, the last one does not show as deleted (even though it is)
#   could make menus work better with keyboard (at least with tab)
#   there is no error checking on duplicates in datagrid edits
#   when editing pole height after shot, offer to update Z

__version__ = '1.0.18'
__date__ = 'June, 2022'
__program__ = 'EDM'
__DEFAULT_FIELDS__ = ['X', 'Y', 'Z', 'SLOPED', 'VANGLE', 'HANGLE', 'STATIONX', 'STATIONY', 'STATIONZ', 'DATE', 'PRISM', 'ID']
__BUTTONS__ = 13
__LASTCOMPORT__ = 16

# Region Imports
from kivy.core.clipboard import Clipboard
from kivy.graphics import Color, Rectangle
from kivy.app import App
from kivy.factory import Factory
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy import __version__ as __kivy_version__

# The explicit mention of this package here
# triggers its inclusions in the pyinstaller spec file.
# It is needed for the filechooser widget.
# The TimeZoneInfo is just to avoid a flake8 error.
try:
    import win32timezone
    win32timezone.TimeZoneInfo.local()
except ModuleNotFoundError:
    pass

import os
import random
from datetime import datetime
import csv
from math import sqrt
from math import pi
from math import cos
from math import sin
from math import acos

from typing import List, Dict

import re
import string
from platform import python_version

import logging

# My libraries for this project
from edmpy.lib.blockdata import blockdata
from edmpy.lib.dbs import dbs
from edmpy.lib.e5_widgets import e5_label, e5_button, e5_MessageBox, e5_DatagridScreen, e5_RecordEditScreen, e5_side_by_side_buttons, e5_textinput, e5_scrollview_label
from edmpy.lib.e5_widgets import edm_manual, DataGridTextBox, width_calculator, e5_SaveDialog, e5_LoadDialog, e5_PopUpMenu, e5_MainScreen, e5_InfoScreen
from edmpy.lib.e5_widgets import e5_LogScreen, e5_CFGScreen, e5_INIScreen, e5_SettingsScreen, e5_scrollview_menu, DataGridMenuList, SpinnerOptions
from edmpy.lib.e5_widgets import DataGridLabelAndField
from edmpy.lib.colorscheme import ColorScheme
from edmpy.lib.misc import restore_window_size_position, filename_only, platform_name

# The database - pure Python
from tinydb import TinyDB, Query, where
from tinydb import __version__ as __tinydb_version__

# from plyer import gps
# from plyer import __version__ as __plyer_version__

# from plyer import __version__ as __plyer_version__
__plyer_version__ = 'None'

# endregion

from angles import r2d, d2r, deci2sexa, Angle

import serial

if os.name == 'nt':  # sys.platform == 'win32':
    from serial.tools.list_ports_windows import comports
elif os.name == 'posix':
    from serial.tools.list_ports_posix import comports
# ~ elif os.name == 'java':
else:
    raise ImportError("Sorry: no implementation for your platform ('{}') available".format(os.name))

# Region Data Classes


class point:
    def __init__(self, x = None, y = None, z = None):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return(f'X : {round(self.x, 3)}, Y : {round(self.y, 3)}, Z : {round(self.z, 3)}')

    def __repr__(self):
        return(f'X : {round(self.x, 3)}, Y : {round(self.y, 3)}, Z : {round(self.z, 3)}')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.x == other.x and self.y == other.y and self.x == other.z
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_none(self):
        return(self.x is None and self.y is None and self.y is None)

    def round(self):
        self.x = round(self.x, 3)
        self.y = round(self.y, 3)
        self.z = round(self.z, 3)
        return(self)


class datum:
    def __init__(self, name = None, x = None, y = None, z = None, notes = ''):
        self.name = name if name else None
        self.x = x
        self.y = y
        self.z = z
        self.notes = notes

    def as_point(self):
        return(point(self.x, self.y, self.z))

    def __str__(self):
        return(f'Datum: {self.name} of X : {round(self.x, 3)}, Y : {round(self.y, 3)}, Z : {round(self.z, 3)}')

    def __repr__(self):
        return(f'Datum: {self.name} of X : {round(self.x, 3)}, Y : {round(self.y, 3)}, Z : {round(self.z, 3)}')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.x == other.x and self.y == other.y and self.x == other.z and self.name == other.name and self.notes == other.notes
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_none(self):
        return(self.name is None and self.x is None and self.y is None and self.z is None and self.notes == '')


class prism:
    def __init__(self, name = None, height = None, offset = None):
        self.name = name
        self.height = height
        self.offset = offset

    def __str__(self):
        return(f'Prism {self.name} with hieght of {round(self.height, 3)} and offset of {round(self.offset, 3)}')

    def __repr__(self):
        return(f'Prism {self.name} with hieght of {round(self.height, 3)} and offset of {round(self.offset, 3)}')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name and self.height == other.height and self.offset == other.offset
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_none(self):
        return(self.name is None and self.height is None and self.offset is None)

    def valid(self):
        if self.name == '':
            return('A name field is required.')
        if len(self.name) > 20:
            return('A prism name should be 20 characters or less.')
        if self.height == '':
            return('A prism height is required.')
        if float(self.height) > 10:
            return('Prism height looks too large.  Prism heights are in meters.')
        if self.offset == '':
            self.offset == 0.0
        if float(self.offset) > .2:
            return('Prism offset looks to be too large.  Prism offsets are expressed in meters.')
        return(True)


class unit:
    def __init__(self, name = None, minx = None, miny = None, maxx = None, maxy = None, centerx = None, centery = None, radius = None):
        self.name = name
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.radius = radius
        self.centerx = centerx
        self.centery = centery

    def __str__(self):
        if not self.radius:
            return(f'Unit {self.name} with limits ({self.minx},{self.miny})-({self.maxx},{self.maxy})')
        else:
            return(f'Unit {self.name} centered on ({self.centerx},{self.centery}) with a radius of {self.radius}')

    def __repr__(self):
        if not self.radius:
            return(f'Unit {self.name} with limits ({self.minx},{self.miny})-({self.maxx},{self.maxy})')
        else:
            return(f'Unit {self.name} centered on ({self.centerx},{self.centery}) with a radius of {self.radius}')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.name == other.name and self.minx == other.minx and self.miny == other.miny and self.maxx == other.maxx and self.maxy == other.maxy and self.centerx == other.centerx and self.centery == other.centery and self.radius == other.radius)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_none(self):
        return(self.name is None and self.minx is None and self.miny is None and self.maxx is None and self.maxy is None and self.radius is None and self.centerx is None and self.centery is None)

    def is_valid(self):
        if self.name == '' or self.name is None:
            return('A name field is required.')
        if len(self.name) > 20:
            return('A unit name should be 20 characters or less.')
        if self.minx is not None and self.maxx is not None:
            if self.minx >= self.maxx:
                return('The unit X2 coordinate must be larger than the X1 coordinate.')
        if self.miny is not None and self.maxy is not None:
            if self.miny >= self.maxy:
                return('The unit Y2 coordinate must be larger than the Y1 coordinate.')
        return(True)


class DB(dbs):
    MAX_FIELDS = 30
    db = None
    filename = None
    db_name = 'points'
    new_data = {}  # type: Dict[str, bool]

    def __init__(self, filename = ''):
        self.filename = filename
        if self.filename:
            self.db = TinyDB(self.filename)

    def open(self, filename):
        try:
            self.db = TinyDB(filename)
            self.filename = filename
            self.prisms = self.db.table('prisms')
            self.new_data['prisms'] = True
            self.units = self.db.table('units')
            self.new_data['units'] = True
            self.datums = self.db.table('datums')
            self.new_data['datums'] = True
            logger = logging.getLogger(__name__)
            logger.info('Database ' + filename + ' opened.')
            return(True)
        except FileNotFoundError:
            return(False)

    def create_defaults(self):
        pass

    def get_unitid(self, unitid):
        unit, id = unitid.split('-')
        p = self.db.search((where('unit') == unit) & (where('id') == id)) if self.db else None
        if p:
            return(p)
        else:
            return(None)

    def get_datum(self, name = None):
        p = self.get_by_name('datums', name)
        return(datum(p['NAME'] if 'NAME' in p.keys() else None,
                        float(p['X']) if 'X' in p.keys() else None,
                        float(p['Y']) if 'Y' in p.keys() else None,
                        float(p['Z']) if 'Z' in p.keys() else None,
                        p['NOTES'] if 'NOTES' in p.keys() else ''))

    def get_unit(self, name):
        p = self.get_by_name('units', name)
        return(unit(name = p['NAME'] if 'NAME' in p.keys() else None,
                    minx = float(p['MINX']) if 'MINX' in p.keys() else None,
                    miny = float(p['MINY']) if 'MINY' in p.keys() else None,
                    maxx = float(p['MAXX']) if 'MAXX' in p.keys() else None,
                    maxy = float(p['MAXY']) if 'MAXY' in p.keys() else None,
                    centerx = float(p['CENTERX']) if 'CENTERX' in p.keys() else None,
                    centery = float(p['CENTERY']) if 'CENTERY' in p.keys() else None,
                    radius = float(p['RADIUS']) if 'RADIUS' in p.keys() else None))

    def get_prism(self, name):
        p = self.get_by_name('prisms', name)
        return(prism(p['NAME'] if 'NAME' in p.keys() else None,
                        float(p['HEIGHT']) if 'HEIGHT' in p.keys() else None,
                        float(p['OFFSET']) if 'OFFSET' in p.keys() else None))

    def get_by_name(self, table = None, name = None):
        if table is not None and name is not None and self.db is not None:
            item = Query()
            p = self.db.table(table).search(item.NAME.matches('^' + name + '$', flags = re.IGNORECASE))
            if p != []:
                return(p[0])
        return({})

    def delete_unit(self, name = None):
        return(self.delete_by_name('units', name))

    def delete_prism(self, name = None):
        return(self.delete_by_name('prisms', name))

    def delete_datum(self, name = None):
        return(self.delete_by_name('datums', name))

    def delete_by_name(self, table = None, name = None):
        if name is not None and table is not None and self.db is not None:
            item = Query()
            self.db.table(table).remove(item.NAME.matches('^' + name + '$', flags = re.IGNORECASE))
            return(True)
        return(False)

    def unit_ids(self):
        return([row['UNIT'] + '-' + row['ID'] for row in self.db.table(self.table)] if self.db is not None else [])

    def names(self, table_name):
        return([row['NAME'] for row in self.db.table(table_name) if 'NAME' in row] if self.db is not None and table_name is not None else [])

    def export_csv(self):
        pass

    def delete_record(self):
        pass

    def add_record(self):
        pass

    def distance(self, p1, a_unit):
        return(sqrt((p1.x - a_unit.centerx)**2 + (p1.y - a_unit.centery)**2))

    def point_in_unit(self, xyz = None):
        if xyz.x is not None and xyz.y is not None:
            for unitname in self.names('units'):
                a_unit = self.get_unit(unitname)
                if a_unit.is_valid() is True:
                    if a_unit.minx is not None and a_unit.miny is not None and a_unit.maxx is not None and a_unit.maxy is not None:
                        if xyz.x <= a_unit.maxx and xyz.x >= a_unit.minx and xyz.y <= a_unit.maxy and xyz.y >= a_unit.miny:
                            return(a_unit.name)
                    elif a_unit.centerx is not None and a_unit.centery is not None and not a_unit.radius == 0.0:
                        if self.distance(xyz, a_unit) <= a_unit.radius:
                            return(a_unit.name)
        return(None)

    def get_link_fields(self, name = None, value = None):
        if name is not None and value is not None and self.db:
            q = Query()
            r = self.db.table(name).search(q[name].matches('^' + value + '$', re.IGNORECASE))
            if r is not []:
                return(r[0])
        return(None)


class INI(blockdata):

    def __init__(self, filename = ''):
        if filename == '':
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
        self.incremental_backups = self.get_value(__program__, 'IncrementalBackups').upper() == 'TRUE'
        self.backup_interval = int(self.get_value(__program__, 'BackupInterval'))
        self.debug = self.get_value(__program__, 'Debug').upper() == 'TRUE'

    def is_valid(self):
        for field_option in ['DARKMODE', 'INCREMENTALBACKUPS']:
            if self.get_value(__program__, field_option):
                if self.get_value(__program__, field_option).upper() == 'YES':
                    self.update_value(__program__, field_option, 'TRUE')
            else:
                self.update_value(__program__, field_option, 'FALSE')

        if self.get_value(__program__, "BACKUPINTERVAL"):
            try:
                test = int(self.get_value(__program__, "BACKUPINTERVAL"))
                if test < 0:
                    test = 0
                elif test > 200:
                    test = 200
                self.update_value(__program__, 'BACKUPINTERVAL', test)
            except ValueError:
                self.update_value(__program__, 'BACKUPINTERVAL', 0)
        else:
            self.update_value(__program__, 'BACKUPINTERVAL', 0)

    def update(self, colors, cfg):
        self.update_value(__program__, 'CFG', cfg.filename)
        self.update_value(__program__, 'ColorScheme', colors.color_scheme)
        self.update_value(__program__, 'ButtonFontSize', colors.button_font_size)
        self.update_value(__program__, 'TextFontSize', colors.text_font_size)
        self.update_value(__program__, 'DarkMode', 'TRUE' if colors.darkmode else 'FALSE')
        self.update_value(__program__, 'IncrementalBackups', self.incremental_backups)
        self.update_value(__program__, 'BackupInterval', self.backup_interval)
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
        menu = []  # type: List[str]
        increment = False
        required = False
        carry = False
        unique = False
        link_fields = []  # type: List[str]

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
        self.link_fields = []   # I think this is a holdover.  Linked fields are not associated with a particular field
        self.errors = []
        self.unique_together = []

    def open(self, filename = ''):
        if filename:
            self.filename = filename
        return(self.load())

    def validate_datafield(self, data_to_insert, data_table):
        # This just validates one field (e.g. when an existing record is edit)
        if data_to_insert and data_table and len(data_to_insert) == 1:
            for field, value in data_to_insert.items():
                f = self.get(field)
                if f.required and value.strip() == "":
                    error_message = f'\nThe field {field} is set to unique or required.  Enter a value to save this record.'
                    return(error_message)
                if f.inputtype == 'NUMERIC':
                    try:
                        float(value)
                    except ValueError:
                        error_message = f'\nThe field {field} requires a valid number.  Correct to save this record.'
                        return(error_message)
                if f.unique:
                    result = data_table.search(where(field) == value)
                    if result:
                        error_message = f'\nThe field {field} is set to unique and the value {value} already exists for this field in this data table.'
                        return(error_message)
        return(True)

    def validate_datarecord(self, data_to_insert, data_table):
        # This validates one record (e.g. one a record is about to be inserted)
        for field in self.fields():
            f = self.get(field)
            if f.required:
                if field in data_to_insert.keys():
                    if data_to_insert[field].strip() == '':
                        error_message = f'\nThe field {field} is set to unique or required.  Enter a value to save this record.'
                        return(error_message)
                else:
                    error_message = f'\nThe field {field} is set to unique or required.  Enter a value to save this record.'
                    return(error_message)
            if f.inputtype == 'NUMERIC':
                if field in data_to_insert.keys():
                    try:
                        float(data_to_insert[field])
                    except ValueError:
                        error_message = f'\nThe field {field} requires a valid number.  Correct to save this record.'
                        return(error_message)
            if f.unique:
                if field in data_to_insert.keys():
                    result = data_table.search(where(field) == data_to_insert[field])
                    if result:
                        error_message = f'\nThe field {field} is set to unique and the value {data_to_insert[field]} already exists for this field in this data table.'
                        return(error_message)
                else:
                    error_message = f'\nThe field {field} is set to unique and a value was not provided for this field.  Unique fields require a value.'
                    return(error_message)

        # TODO test to see if it is units, prisms or datums
        # TODO create a unit, prism or datum from the dictionary using *data_to_insert
        # TODO run the validator in whichever
        # TODO and return results
        return(True)

    def get(self, field_name):
        f = self.field(field_name)
        f.inputtype = self.get_value(field_name, 'TYPE').upper()
        f.prompt = self.get_value(field_name, 'PROMPT')
        f.length = self.get_value(field_name, 'LENGTH')
        menulist = self.get_value(field_name, 'MENU')
        if menulist:
            f.menu = self.get_value(field_name, 'MENU').split(",")
        link_fields = self.get_value(field_name, 'LINKED')
        if link_fields:
            f.link_fields = link_fields.upper().split(",")
        f.carry = self.get_value(field_name, 'CARRY').upper() == 'TRUE'
        f.required = self.get_value(field_name, 'REQUIRED').upper() == 'TRUE'
        f.increment = self.get_value(field_name, 'INCREMENT').upper() == 'TRUE'
        f.unique = self.get_value(field_name, 'UNIQUE').upper() == 'TRUE'
        if f.unique:
            f.required = True
        return(f)

    def put(self, field_name, f):
        self.update_value(field_name, 'PROMPT', f.prompt)
        self.update_value(field_name, 'LENGTH', f.length)
        self.update_value(field_name, 'TYPE', f.inputtype)

    def fields(self):
        field_names = self.names()
        del_fields = ['EDM', 'TIME']
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
        self.update_value('NAME', 'UNIQUE', 'TRUE')
        self.update_value('NAME', 'REQUIRED', 'TRUE')

        self.update_value('HEIGHT', 'Prompt', 'Height :')
        self.update_value('HEIGHT', 'Type', 'Numeric')
        self.update_value('HEIGHT', 'REQUIRED', 'TRUE')

        self.update_value('OFFSET', 'Prompt', 'Offset :')
        self.update_value('OFFSET', 'Type', 'Numeric')

    def build_unit(self):
        self.update_value('NAME', 'Prompt', 'Name :')
        self.update_value('NAME', 'Type', 'Text')
        self.update_value('NAME', 'Length', 20)
        self.update_value('NAME', 'UNIQUE', 'TRUE')
        self.update_value('NAME', 'REQUIRED', 'TRUE')

        self.update_value('MINX', 'Prompt', 'X Minimum :')
        self.update_value('MINX', 'Type', 'Numeric')

        self.update_value('MINY', 'Prompt', 'Y Minimum :')
        self.update_value('MINY', 'Type', 'Numeric')

        self.update_value('MAXX', 'Prompt', 'X Maximum :')
        self.update_value('MAXX', 'Type', 'Numeric')

        self.update_value('MAXY', 'Prompt', 'Y Maximum :')
        self.update_value('MAXY', 'Type', 'Numeric')

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
        self.update_value('NAME', 'UNIQUE', 'TRUE')
        self.update_value('NAME', 'REQUIRED', 'TRUE')

        self.update_value('X', 'Prompt', 'X :')
        self.update_value('X', 'Type', 'Numeric')
        self.update_value('X', 'REQUIRED', 'TRUE')

        self.update_value('Y', 'Prompt', 'Y :')
        self.update_value('Y', 'Type', 'Numeric')
        self.update_value('Y', 'REQUIRED', 'TRUE')

        self.update_value('Z', 'Prompt', 'Z :')
        self.update_value('Z', 'Type', 'Numeric')
        self.update_value('Z', 'REQUIRED', 'TRUE')

        self.update_value('NOTES', 'Prompt', 'Note :')
        self.update_value('NOTES', 'Type', 'Note')

    def build_default(self):
        self.update_value('UNIT', 'Prompt', 'Unit :')
        self.update_value('UNIT', 'Type', 'Text')
        self.update_value('UNIT', 'Length', 6)
        self.update_value('UNIT', 'REQUIRED', 'TRUE')

        self.update_value('ID', 'Prompt', 'ID :')
        self.update_value('ID', 'Type', 'Text')
        self.update_value('ID', 'Length', 6)
        self.update_value('ID', 'REQUIRED', 'TRUE')

        self.update_value('SUFFIX', 'Prompt', 'Suffix :')
        self.update_value('SUFFIX', 'Type', 'Numeric')
        self.update_value('SUFFIX', 'REQUIRED', 'TRUE')

        self.update_value('LEVEL', 'Prompt', 'Level :')
        self.update_value('LEVEL', 'Type', 'Menu')
        self.update_value('LEVEL', 'Length', 20)
        self.update_value('LEVEL', 'REQUIRED', 'TRUE')

        self.update_value('CODE', 'Prompt', 'Code :')
        self.update_value('CODE', 'Type', 'Menu')
        self.update_value('CODE', 'Length', 20)
        self.update_value('CODE', 'REQUIRED', 'TRUE')

        self.update_value('EXCAVATOR', 'Prompt', 'Excavator :')
        self.update_value('EXCAVATOR', 'Type', 'Menu')
        self.update_value('EXCAVATOR', 'Length', 20)

        self.update_value('PRISM', 'Prompt', 'Prism :')
        self.update_value('PRISM', 'Type', 'Numeric')

        self.update_value('X', 'Prompt', 'X :')
        self.update_value('X', 'Type', 'Numeric')
        self.update_value('X', 'REQUIRED', 'TRUE')

        self.update_value('Y', 'Prompt', 'Y :')
        self.update_value('Y', 'Type', 'Numeric')
        self.update_value('Y', 'REQUIRED', 'TRUE')

        self.update_value('Z', 'Prompt', 'Z :')
        self.update_value('Z', 'Type', 'Numeric')
        self.update_value('Z', 'REQUIRED', 'TRUE')

        self.update_value('DATE', 'Prompt', 'Date :')
        self.update_value('DATE', 'Type', 'Text')
        self.update_value('DATE', 'Length', 24)

        self.update_value('HANGLE', 'Prompt', 'H-angle :')
        self.update_value('HANGLE', 'Type', 'Numeric')
        self.update_value('HANGLE', 'REQUIRED', 'TRUE')

        self.update_value('VANGLE', 'Prompt', 'V-angle :')
        self.update_value('VANGLE', 'Type', 'Numeric')
        self.update_value('VANGLE', 'REQUIRED', 'TRUE')

        self.update_value('SLOPED', 'Prompt', 'Slope Dist. :')
        self.update_value('SLOPED', 'Type', 'Numeric')
        self.update_value('SLOPED', 'REQUIRED', 'TRUE')

        self.update_value('EDM', 'UNIQUE_TOGETHER', 'UNIT,ID,SUFFIX')
        self.unique_together = ['UNIT', 'ID', 'SUFFIX']

    def validate(self):

        self.errors = []
        self.has_errors = False
        self.has_warnings = False
        field_names = self.fields()
        self.link_fields = []
        bad_characters = r' !@#$%^&*()?/\{}<.,.|+=~`-'

        # This is a legacy issue.  Linked fields are now listed with each field.
        unit_fields = self.get_value('EDM', 'UNITFIELDS')
        if unit_fields:
            unit_fields = unit_fields.upper().split(',')
            unit_fields.remove('UNIT')
            unit_fields = ','.join(unit_fields)
            self.update_value('UNIT', 'LINKED', unit_fields)
            self.delete_key('EDM', 'UNITFIELDS')

        table_name = self.get_value('EDM', 'TABLE')
        if table_name:
            if any((c in set(bad_characters)) for c in table_name):
                self.errors.append(f"Error: The table name {table_name} has non-standard characters in it that cause a problem in JSON files.  Do not use any of these '{bad_characters}' characters.  Change the name before collecting data.")
                self.has_errors = True

        unique_together = self.get_value('EDM', 'UNIQUE_TOGETHER')
        if unique_together:
            no_errors = True
            for field_name in unique_together.split(','):
                if field_name not in field_names:
                    self.errors.append(f"Error: The field '{field_name}' is listed in UNIQUE_TOGETHER but does not appear as a field in the CFG file.")
                    self.has_errors = True
                    no_errors = False
                    break
            if no_errors:
                self.unique_together = unique_together.split(',')
            else:
                self.unique_together = []
        else:
            if 'UNIT' in field_names and 'ID' in field_names and 'SUFFIX' in field_names:
                self.update_value('EDM', 'UNIQUE_TOGETHER', 'UNIT,ID,SUFFIX')
                self.unique_together = ['UNIT', 'ID', 'SUFFIX']
            if 'ID' in field_names and 'SUFFIX' in field_names:
                self.update_value('EDM', 'UNIQUE_TOGETHER', 'ID,SUFFIX')
                self.unique_together = ['ID', 'SUFFIX']

        for field_name in field_names:
            if any((c in set(bad_characters)) for c in field_name):
                self.errors.append(f"Error: The field name '{field_name}' has non-standard characters in it that cause a problem in JSON files.  Do not use any of these '{bad_characters}' characters.  Change the name before collecting data.")
                self.has_errors = True
            f = self.get(field_name)
            if f.prompt == '':
                f.prompt = field_name
            f.inputtype = f.inputtype.upper()
            if field_name in ['UNIT', 'ID', 'SUFFIX', 'X', 'Y', 'Z']:
                self.update_value(field_name, 'REQUIRED', 'TRUE')
            if field_name == 'ID':
                self.update_value(field_name, 'INCREMENT', 'TRUE')
            if f.link_fields:
                self.link_fields.append(field_name)
                # uppercase the link fields
                for link_field_name in f.link_fields:
                    if link_field_name not in field_names:
                        self.errors.append(f"Error: The field {field_name} is set to link to {link_field_name} but the field {link_field_name} does not exist in the CFG.")
                        self.has_errors = True
            self.put(field_name, f)

            for field_option in ['UNIQUE', 'CARRY', 'INCREMENT', 'REQUIRED', 'SORTED']:
                if self.get_value(field_name, field_option):
                    if self.get_value(field_name, field_option).upper() == 'YES':
                        self.update_value(field_name, field_option, 'TRUE')

        # Every CFG should have a unique together so that duplicates can be avoided
        if self.unique_together == []:
            for field_name in field_names:
                f = self.get(field_name)
                if f.unique is True:
                    self.unique_together = [f.name]
                    if 'SUFFIX' in field_names:
                        self.unique_together.append('SUFFIX')
                    self.update_value('EDM', 'UNIQUE_TOGETHER', ','.join(self.unique_together))
                    break

        if self.unique_together == []:
            self.errors.append('Every CFG file should contain at least one field or a set of fields that together are unique.  Normally, this will be something like Unit, ID and Suffix together.  Set this value by either setting one field to UNIQUE=TRUE or by adding a UNIQUE_TOGETHER line in the EDM block of the CFG file (e.g. something like UNIQUE_TOGETHER=UNIT,ID,SUFFIX).')
            self.has_errors = True

        return(self.has_errors)

    def save(self):
        self.write_blocks()

    def load(self, filename = ''):
        if filename:
            self.filename = filename
        self.path = os.path.split(self.filename)[0]

        self.blocks = []
        if os.path.isfile(self.filename):
            self.blocks = self.read_blocks()
            errors = self.validate()
            if errors is False:     # This is bad.  Errors returned are not dealt with when starting program
                self.save()
            else:
                return(errors)
        else:
            self.filename = 'default.cfg'
            self.build_default()
        logger = logging.getLogger(__name__)
        logger.info('CFG ' + self.filename + ' opened.')

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
                            if self.get(fieldname).inputtype in ['NUMERIC', 'INSTRUMENT']:
                                csv_row += ',%s' % row[fieldname] if csv_row else "%s" % row[fieldname]
                            else:
                                csv_row += ',"%s"' % row[fieldname] if csv_row else '"%s"' % row[fieldname]
                        else:
                            if self.get(fieldname).inputtype in ['NUMERIC', 'INSTRUMENT']:
                                if csv_row:
                                    csv_row = csv_row + ','     # Not sure this works if there is an entirely empty row of numeric values
                            else:
                                if csv_row:
                                    csv_row = csv_row + ',""'
                                else:
                                    csv_row = '""'
                    else:
                        if self.get(fieldname).inputtype in ['NUMERIC', 'INSTRUMENT']:
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
        except OSError:
            return('\nCould not write data to %s.' % (filename))


class totalstation(object):

    popup = ObjectProperty(None)
    popup_open = False
    # rotate_source = []
    # rotate_destination = []

    def __init__(self, make = None, model = None):
        self.make = make if make else 'Manual XYZ'
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
        self.prism_constant = 0.0
        self.hangle = None              # Decimal degrees
        self.vangle = None              # Decimal degrees
        self.sloped = 0.0
        self.suffix = 0
        self.prism = prism()
        self.xyz_global = point()
        self.rotate_local = []
        self.rotate_global = []
        self.last_setup_type = ''
        self.shot_type = ''
        self.event = None
        self.io = ''
        self.open()

    def text_to_point(self, txt):
        if len(txt.split(',')) == 3:
            x, y, z = txt.split(',')
            try:
                return(point(float(x), float(y), float(z)))
            except Exception:
                return(None)
        else:
            return(None)

    def setup(self, ini, data):
        if ini.get_value(__program__, 'STATION'):
            self.make = ini.get_value(__program__, 'STATION')
        if ini.get_value(__program__, 'COMMUNICATIONS'):
            self.communication = ini.get_value(__program__, 'COMMUNICATIONS')
        if ini.get_value(__program__, 'COMPORT'):
            self.comport = ini.get_value(__program__, 'COMPORT')
        if ini.get_value(__program__, 'BAUDRATE'):
            self.baudrate = ini.get_value(__program__, 'BAUDRATE')
        if ini.get_value(__program__, 'PARITY'):
            self.parity = ini.get_value(__program__, 'PARITY')
        if ini.get_value(__program__, 'DATABITS'):
            self.databits = ini.get_value(__program__, 'DATABITS')
        if ini.get_value(__program__, 'STOPBITS'):
            self.stopbits = ini.get_value(__program__, 'STOPBITS')

        self.last_setup_type = ini.get_value('SETUPS', 'LASTSETUP_TYPE')

        if ini.get_value('SETUPS', '3DATUM_SHIFT_LOCAL_1'):
            point1 = self.text_to_point(ini.get_value('SETUPS', '3DATUM_SHIFT_LOCAL_1'))
            point2 = self.text_to_point(ini.get_value('SETUPS', '3DATUM_SHIFT_LOCAL_2'))
            point3 = self.text_to_point(ini.get_value('SETUPS', '3DATUM_SHIFT_LOCAL_3'))
            if point1 is not None and point2 is not None and point3 is not None:
                self.rotate_local = [point1, point2, point3]
        if ini.get_value('SETUPS', '3DATUM_SHIFT_GLOBAL_1'):
            point1 = data.get_datum(ini.get_value('SETUPS', '3DATUM_SHIFT_GLOBAL_1'))
            point2 = data.get_datum(ini.get_value('SETUPS', '3DATUM_SHIFT_GLOBAL_2'))
            point3 = data.get_datum(ini.get_value('SETUPS', '3DATUM_SHIFT_GLOBAL_3'))
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

    def prism_adjust(self):
        if self.prism.height is not None:
            if self.xyz.z is not None:
                self.xyz.z = round(self.xyz.z - self.prism.height, 3)
            if self.xyz_global.z is not None:
                self.xyz_global.z = round(self.xyz_global.z - self.prism.height, 3)

    def angle_between_points(self, p1, p2):
        return self.angle_between_xy_pairs(p1.x, p1.y, p2.x, p2.y)

    def angle_between_xy_pairs(self, x1, y1, x2, y2):
        # angle is from xy1 to xy2
        # result is in decimal degrees
        # angle is clockwise survey angle with positive y = 90

        # Subtract point 1 from 2 to make 2 relative to the origin
        p = self.subtract_points(point(x2, y2, 0), point(x1, y1, 0))

        # Get the angle between the Y axis and this point
        cos_of_angle = self.dot_product(point(0, 1, 0), self.normalize_vector(p))
        angle = r2d(acos(cos_of_angle))

        if p.x < 0:
            angle = 360 - angle

        return(angle)

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

    def point_pretty(self, point):
        return(f'X: {round(point.x, 3)}\nY: {round(point.y, 3)}\nZ: {round(point.z, 3)}')

    def decimal_degrees_to_dddmmss(self, angle):
        if angle is not None:
            sexa = deci2sexa(angle)
            return(f'{sexa[1]}.{sexa[2]}{sexa[3]}')
        else:
            return('')

    def decimal_degrees_to_sexa_pretty(self, angle):
        if angle is not None:
            sexa = deci2sexa(angle)
            return(f'{sexa[1]}° {sexa[2]}\" {sexa[3]}\'')
        else:
            return('')

    def vhd_to_sexa_pretty_compact(self):
        return(f"hangle : {self.decimal_degrees_to_sexa_pretty(self.hangle)}, vangle : {self.decimal_degrees_to_sexa_pretty(self.vangle)}, sloped : {round(self.sloped, 3) if self.sloped else ''}")

    def add_points(self, p1, p2):
        return point(p1.x + p2.x, p1.y + p2.y, p1.z + p2.z)

    def subtract_points(self, p1, p2):
        return point(p1.x - p2.x, p1.y - p2.y, p1.z - p2.z)

    def hash(self, hashlen = 5):
        hash = ""
        for a in range(0, hashlen):
            hash += random.choice(string.ascii_uppercase)
        return(hash)

    def set_horizontal_angle(self, angle):
        if self.make == 'TOPCON':
            self.set_horizontal_angle_topcon(angle)
        elif self.make in ['WILD', 'Leica']:
            self.set_horizontal_angle_leica(angle)
        elif self.make == 'SOKKIA':
            self.set_horizontal_angle_sokkia(angle)
        elif self.make == 'Simulate':
            pass
        elif self.make in ['Manual XYZ', 'Manual VHD']:
            pass

    def set_horizontal_angle_nikon(self, angle):
        # need to send to station in format dddmmss
        self.send("!HAN" + angle.encode())
        # delay(1)
        self.clear_com()

    def launch_point_simulate(self):
        # Put the points into one of two units
        if random.uniform(0, 1) > 0.5:
            self.xyz = point(round(random.uniform(1000, 1001), 3),
                                round(random.uniform(1000, 1001), 3),
                                round(random.uniform(0, 1), 3))
        else:
            self.xyz = point(round(random.uniform(2000, 2001), 3),
                                round(random.uniform(2000, 2001), 3),
                                round(random.uniform(0, 1), 3))
        self.make_global()
        self.vhd_from_xyz()

    def take_shot(self):

        self.clear_xyz()
        self.clear_com()

        if self.make == 'TOPCON':
            self.launch_point_topcon()

        elif self.make in ['WILD', 'Leica']:
            self.launch_point_leica()

        elif self.make == "SOKKIA":
            self.launch_point_sokkia()

        elif self.make == 'Simulate':
            self.launch_point_simulate()

        else:
            pass

    def fetch_point(self):
        if self.make in ['WILD', 'Leica']:
            self.fetch_point_leica()

    def vhd_from_xyz(self):
        self.hangle = self.angle_between_xy_pairs(self.location.x, self.location.y, self.xyz.x, self.xyz.y)
        level_distance = sqrt((self.xyz.x - self.location.x)**2 + (self.xyz.y - self.location.y)**2)
        self.sloped = self.distance(self.location, self.xyz)
        self.vangle = self.angle_between_xy_pairs(0, 0, level_distance, self.xyz.z)

    def make_global(self):
        if self.xyz.x is not None and self.xyz.y is not None and self.xyz.z is not None:
            if self.make == 'Microscribe':
                if len(self.rotate_local) == 3 and len(self.rotate_global) == 3:
                    self.xyz_global = self.rotate_point(self.xyz)
                else:
                    self.xyz_global = self.xyz
                self.round_xyz()
            else:
                if self.location.x is not None and self.location.y is not None and self.location.z is not None:
                    self.xyz_global = point(self.xyz.x + self.location.x,
                                            self.xyz.y + self.location.y,
                                            self.xyz.z + self.location.z,)
                else:
                    self.xyz_global = self.xyz

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

    def clear_io(self):
        self.io = ''

    def trim_io(self, length = 1024):
        self.io = self.io[:length]

    def add_to_io(self, data):
        self.io = self.io + data
        self.trim_io()

    def data_waiting(self):
        if self.serialcom.is_open:
            if self.serialcom.in_waiting > 0:
                return(True)
        return(False)

    def send(self, data):
        if self.serialcom.is_open:
            self.serialcom.write(data)
            self.add_to_io('Sent -> ' + data.decode())
            # print(data)
            # sleep(0.1)

    def receive(self):
        if self.serialcom.is_open:
            data = self.serialcom.read_until().decode()
            # data = self.serialcom.readline().decode()
            if data:
                if self.event is not None:  # This is for Topcon where the COM has to be monitored
                    self.event.cancel()
                    self.event = None
                self.add_to_io('Received <- ' + data)
            return(data)

    def close(self):
        if self.serialcom.is_open:
            self.serialcom.close()
            self.clear_io()

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
                try:
                    self.serialcom.open()
                    self.clear_io()
                    return(True)
                except OSError:
                    pass
        return(False)

    def settings_pretty(self):
        if self.baudrate and self.comport and self.parity and self.databits and self.stopbits:
            return(f"{self.comport}:{self.baudrate},{self.parity},{self.databits},{self.stopbits}")
        else:
            return("Incomplete Settings")

    def clear_com(self):
        if self.serialcom.is_open:
            self.serialcom.reset_input_buffer()
            self.serialcom.reset_output_buffer()

    def distance(self, p1, p2):
        return(sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2))

    def dms_to_decdeg(self, angle):
        angle = str(angle)
        degrees = int(angle.split(".")[0])
        minutes = int(angle.split(".")[1][0:2])
        seconds = int(angle.split(".")[1][2:])
        return(degrees + minutes / 60.0 + seconds / 3600.0)

    def decdeg_to_radians(self, angle):
        return(angle / 360.0 * (2.0 * pi))

    def vhd_to_xyz(self):
        if self.vangle is not None and self.hangle is not None and self.sloped is not None:
            # angle_decdeg = self.dms_to_decdeg(self.vangle)
            z = self.sloped * cos(self.decdeg_to_radians(self.vangle))
            actual_distance = sqrt(self.sloped**2 - z**2)

            # angle_decdeg = self.dms_to_decdeg(self.hangle)
            angle_decdeg = 450 - self.hangle
            x = cos(self.decdeg_to_radians(angle_decdeg)) * actual_distance
            y = sin(self.decdeg_to_radians(angle_decdeg)) * actual_distance
            self.xyz = point(x, y, z)

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
            return(self.scale_vector(1 / sqrt(self.dot_product(a, a)), a))

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
        r = self.matrix_add(self.matrix_add(i, vx), v2x)

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
        r = self.matrix_add(self.matrix_add(i, vx), v2x)

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
            local.append(point(0, 0, 0))
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

    # Function specific to Topcon #

    def launch_point_topcon(self):
        self.send("Z34")   # Slope angle mode
        self.receive()
        # delay(0.5)

        self.send("C")     # Take the shot
        self.receive()
        # delay(0.5)
        self.event1 = Clock.schedule_interval(self.check_receive_buffer, .2)

    def check_receive_buffer(self):
        # need code here to check for a completed shot
        # and then acknowledge back
        pass

    def make_bcc_topcon(self, itext):
        # Dim b As Integer = 0
        # Dim i As Integer
        # Dim q As Integer
        # Dim b1 As Integer
        # Dim b2 As Integer

        b = 0
        for i in range(0, len(itext)):
            # q = asc(itext[i:i+1])
            # b1 = q and (Not b) # this is not at all ready
            # b2 = b and (Not q)
            # b = b1 or b2
            pass

        bcc = "000" + str(b).strip()
        return(bcc[-3])

    def set_horizontal_angle_topcon(self, angle):
        # angle should be in dddmmss
        self.send("J+" + angle + "d")
        self.receive()
        # delay(1)
        self.clear_com()

    def initialize_topcon(self):
        self.send("ST0")

    # end Topcon

    # Sokkia functions

    def launch_point_sokkia(self):
        self.send(chr(17).encode())

    def set_horizontal_angle_sokkia(self, angle):
        # need to send to station in format ddd.mmss
        set_angle_command = "/Dc " + angle + "\r\n"
        self.send(set_angle_command.encode())
        # delay(5)
        self.clear_com()

    def fetch_point_sokkia(self):
        self.pnt = self.receive()
        if self.pnt:
            self.parce_sokkia()
            self.vhd_to_xyz()

    def parce_sokkia(self):
        if self.pnt:
            vhd = self.pnt.strip().split(" ")
            if len(vhd) == 3:
                try:
                    self.sloped = float(vhd[0]) / 1000.0
                except ValueError:
                    self.sloped = None
            if vhd[1][0] != 'E':
                self.vangle = Angle(f'{vhd[1][:3]}d{vhd[1][3:5]}m{vhd[1][5:7]}').d
            else:
                self.vangle = None
            if vhd[2][0] != 'E':
                self.hangle = Angle(f'{vhd[1][:3]}d{vhd[1][3:5]}m{vhd[1][5:7]}').d
            else:
                self.hangle = None

    def initialize_sokkia(self):
        pass

    # end Sokkia

    # Leica functions ###

    def pad_dms_leica(self, angle):
        degrees = ('000' + angle.split('.')[0])[-3:]
        minutes_seconds = (angle.split('.')[1] + '0000')[0:4]
        return(degrees + minutes_seconds)

    def set_horizontal_angle_leica(self, angle):
        # function expects angle as ddd.mmss input
        # but decimal seconds are possible
        if angle.count('.') == 0:
            angle = angle + '.0000'
        elif angle.count('.') == 2:
            dms = angle.split('.')
            ms = '0000' + str(round(float(dms[1] + '.' + dms[2])))
            ms = ms[-4:]
            angle = str(dms[0] + '.' + ms)
        set_angle_command = "PUT/21...4+%s0 \r\n" % self.pad_dms_leica(angle)
        self.send(set_angle_command.encode())
        return(self.receive())

    def launch_point_leica(self):
        self.send(b"GET/M/WI21/WI22/WI31/WI51\r\n")

    def fetch_point_leica(self):
        self.pnt = self.receive()
        if self.pnt:
            self.parce_leica()
            self.vhd_to_xyz()

    def parce_leica(self):
        if self.pnt:
            if self.pnt.startswith('*'):
                self.pnt = self.pnt[1:]
            for component in self.pnt.split(' '):
                if component.startswith('21.'):
                    data = component[6:]
                    self.hangle = Angle(f'{data[:-5]}d{data[-5:-3]}m{data[-3:-1]}.{data[-1]}').d
                elif component.startswith('22.'):
                    data = component[6:]
                    self.vangle = Angle(f'{data[:-5]}d{data[-5:-3]}m{data[-3:-1]}.{data[-1]}').d
                elif component.startswith('31.'):
                    try:
                        self.sloped = float(component[6:]) / 1000.0
                    except ValueError:
                        self.sloped = None
                elif component.startswith('51.'):
                    try:
                        self.prism_constant = float(component[-4:]) / 1000.0
                    except ValueError:
                        self.prism_constant = None

    def initialize_leica(self):
        self.send("SET/41/0")
        acknow1 = self.receive()
        self.send("SET/149/2")
        acknow2 = self.receive()
        return(acknow1 + acknow2)
    # ## Leica functions ###

    # ## Leica geocom functions ###
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
    # ## Leica geocom functions ###

# endregion


class ComTestScreen(Screen):
    def __init__(self, station = None, cfg = None, colors = None, **kwargs):
        super(ComTestScreen, self).__init__(**kwargs)

        self.colors = colors if colors else ColorScheme()
        self.station = station
        self.cfg = cfg

        self.clear_widgets()
        self.layout = GridLayout(cols = 1,
                                 spacing = 5,
                                 size_hint_x = width_calculator(.9, 400),
                                 size_hint_y = .9,
                                 pos_hint = {'center_x': .5, 'center_y': .5})
        self.add_widget(self.layout)
        self.build_screen()

    def current_settings_pretty(self):
        txt = 'The current settings are:\n' + self.station.make + '\n' + self.station.settings_pretty()
        txt += '\nThe COM port is '
        txt += 'Open' if self.station.serialcom.is_open else 'Close'
        return(txt)

    def on_enter(self):
        sm.get_screen('StationConfigurationScreen').call_back = 'MainScreen'
        self.current_settings.text = self.current_settings_pretty()
        self.station.clear_io()
        self.event = Clock.schedule_interval(self.check_io, .2)

    def check_io(self, dt):
        if self.station.data_waiting():
            self.station.receive()
        if self.station.io != '' and self.station.io != self.io.scrolling_label.text:
            self.io.scrolling_label.text = self.station.io

    def build_screen(self):

        self.settings = GridLayout(cols = 2, spacing = 5, padding = 5, size_hint = (.2, None))
        self.current_settings = e5_label(self.current_settings_pretty(), colors = self.colors, size_hint = (0.75, None))
        self.settings.add_widget(self.current_settings)
        self.change_settings = e5_button("Change Settings", call_back = self.settings_change, colors = self.colors)
        self.settings.add_widget(self.change_settings)
        self.layout.add_widget(self.settings)

        self.horizontal_angle = GridLayout(cols = 2, spacing = 5, padding = 5, size_hint = (.2, None))
        self.leftside = GridLayout(cols = 1, spacing = 5, padding = 5)
        self.leftside.add_widget(e5_label('Enter angle as ddd.mmss', colors = self.colors))
        self.hangle_input = e5_textinput(write_tab = False)
        self.hangle_input.bind(minimum_height = self.hangle_input.setter('height'))
        self.leftside.add_widget(self.hangle_input)
        self.horizontal_angle.add_widget(self.leftside)
        self.set_angle = e5_button("Set H-angle", call_back = self.set_hangle, colors = self.colors)
        self.horizontal_angle.add_widget(self.set_angle)
        self.layout.add_widget(self.horizontal_angle)

        self.record = GridLayout(cols = 1, spacing = 5, padding = 5, size_hint = (.2, None))
        self.measure = e5_button("Record Point", call_back = self.record_point, colors = self.colors)
        self.record.add_widget(self.measure)
        self.layout.add_widget(self.record)

        self.io = e5_scrollview_label('Set an angle or record a point and the communication to the station will appear here.  If nothing is received at all, then it might be a COM port number issue.  If what is received is unreadable, then there is a problem with the speed, parity, data bits, and stop bits.  If everything looks fine, but the angle does not change or a point is not taken, then likely Shannon needs to have a look.  Email the results here to him.', popup = False, colors = self.colors)
        self.layout.add_widget(self.io)

        self.layout.add_widget(e5_side_by_side_buttons(text = ['Clear', 'Copy', 'Close'],
                                                        id = ['clear', 'copy', 'close'],
                                                        call_back = [self.clear_io, self.copy_io, self.close],
                                                        selected = [False, False, False],
                                                        colors = self.colors))

    def clear_io(self, instance):
        self.station.clear_io()
        self.io.scrolling_label.text = ''

    def copy_io(self, instance):
        Clipboard.copy(self.io.scrolling_label.text)

    def set_hangle(self, instance):
        if self.hangle_input.text:
            self.station.set_horizontal_angle(self.hangle_input.text)
            # self.io.scrolling_label.text = self.station.io

    def settings_change(self, instance):
        sm.get_screen('StationConfigurationScreen').call_back = 'ComTestScreen'
        self.event.cancel()
        self.parent.current = 'StationConfigurationScreen'

    def record_point(self, instance):
        self.station.take_shot()

    def close(self, instance):
        self.event.cancel()
        self.parent.current = 'MainScreen'


class MainScreen(e5_MainScreen):

    popup = ObjectProperty(None)
    popup_open = False
    text_color = (0, 0, 0, 1)
    title = __program__

    def __init__(self, user_data_dir, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        self.user_data_dir = user_data_dir
        self.setup_logger()

        self.colors = ColorScheme()
        self.ini = INI()
        self.cfg = CFG()
        self.data = DB()

        self.setup_program()

        self.station = totalstation(self.ini.get_value(__program__, 'STATION'))
        self.station.setup(self.ini, self.data)
        self.station.open()

        self.cfg_datums = CFG()
        self.cfg_datums.build_datum()
        self.cfg_prisms = CFG()
        self.cfg_prisms.build_prism()
        self.cfg_units = CFG()
        self.cfg_units.build_unit()

        self.layout = BoxLayout(orientation = 'vertical',
                                size_hint_y = .9,
                                size_hint_x = .8,
                                pos_hint={'center_x': .5},
                                padding = 20,
                                spacing = 20)
        self.build_mainscreen()
        self.add_widget(self.layout)
        self.add_screens()
        restore_window_size_position(__program__, self.ini)

    def setup_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt = '%Y-%m-%d %H:%M:%S')
        fh = logging.FileHandler(os.path.join(self.user_data_dir, __program__ + '.log'))
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.info(__program__ + ' started, logger initialized, and application built.')

    def add_screens(self):
        sm.add_widget(EditLastRecordScreen(name = 'EditLastRecordScreen',
                                            colors = self.colors,
                                            data = self.data,
                                            doc_id = None,
                                            e5_cfg = self.cfg))

        sm.add_widget(VerifyStationScreen(name = 'VerifyStationScreen',
                                            id = 'verify_station',
                                            data = self.data,
                                            station = self.station,
                                            colors = self.colors,
                                            ini = self.ini))

        sm.add_widget(RecordDatumsScreen(name = 'RecordDatumsScreen',
                                            data = self.data,
                                            station = self.station,
                                            colors = self.colors,
                                            ini = self.ini))

        sm.add_widget(EditPointScreen(name = 'EditPointScreen',
                                            colors = self.colors,
                                            data = self.data,
                                            # data_table = self.data.table,
                                            doc_id = None,
                                            e5_cfg = self.cfg,
                                            one_record_only = True))

        sm.add_widget(EditPointsScreen(name = 'EditPointsScreen',
                                            colors = self.colors,
                                            main_data = self.data,
                                            main_tablename = self.data.table,
                                            main_cfg = self.cfg))

        sm.add_widget(EditPointsScreen(name = 'EditDatumsScreen',
                                            colors = self.colors,
                                            main_data = self.data,
                                            main_tablename = 'datums',
                                            main_cfg = self.cfg_datums,
                                            addnew = True))

        sm.add_widget(EditPointsScreen(name = 'EditPrismsScreen',
                                            colors = self.colors,
                                            main_data = self.data,
                                            main_tablename = 'prisms',
                                            main_cfg = self.cfg_prisms,
                                            addnew = True))

        sm.add_widget(EditPointsScreen(name = 'EditUnitsScreen',
                                            colors = self.colors,
                                            main_data = self.data,
                                            main_tablename = 'units',
                                            main_cfg = self.cfg_units,
                                            addnew = True))

        sm.add_widget(StatusScreen(name = 'StatusScreen',
                                            colors = self.colors,
                                            cfg = self.cfg,
                                            ini = self.ini,
                                            data = self.data,
                                            station = self.station))

        sm.add_widget(e5_LogScreen(name = 'LogScreen',
                                            colors = self.colors,
                                            logger = logging.getLogger(__name__)))

        sm.add_widget(e5_CFGScreen(name = 'CFGScreen',
                                            colors = self.colors,
                                            cfg = self.cfg))

        sm.add_widget(e5_INIScreen(name = 'INIScreen',
                                            colors = self.colors,
                                            ini = self.ini))

        sm.add_widget(AboutScreen(name = 'AboutScreen',
                                            colors = self.colors))

        sm.add_widget(StationConfigurationScreen(name = 'StationConfigurationScreen',
                                                    station = self.station,
                                                    ini = self.ini,
                                                    colors = self.colors))

        sm.add_widget(InitializeStationScreen(name = 'InitializeStationScreen',
                                                    data = self.data,
                                                    station = self.station,
                                                    ini = self.ini,
                                                    colors = self.colors))

        sm.add_widget(e5_SettingsScreen(name = 'EDMSettingsScreen',
                                        colors = self.colors,
                                        ini = self.ini,
                                        cfg = self.cfg))

        sm.add_widget(ComTestScreen(name = 'ComTestScreen',
                                        colors = self.colors,
                                        station = self.station,
                                        cfg = self.cfg))

    def reset_screens(self):
        for screen in sm.screens[:]:
            if screen.name != 'MainScreen':
                sm.remove_widget(screen)
        self.add_screens()

    def build_mainscreen(self):

        if platform_name() == 'Android':
            size_hints = {'info': .13,
                            'option_buttons': .8 - .13 - .2,
                            'shot_buttons': .2}
        else:
            size_hints = {'info': .13,
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

        # grid = GridLayout(cols = 3, spacing = 10)
        scroll_content = BoxLayout(orientation = 'horizontal',
                                    size_hint = (1, size_hints['option_buttons']),
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

        # if button_count % 3 !=0:
        #    button_empty = Button(text = '', size_hint_y = None, id = '',
        #                    color = self.colors.window_background,
        #                    background_color = self.colors.window_background,
        #                    background_normal = '')
        #    scroll_content.add_widget(button_empty)

        # if button_count % 3 == 2:
        #    scroll_content.add_widget(button_empty)

        # self.layout.add_widget(scroll_content)

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
        for widget in self.walk():
            if hasattr(widget, 'action_previous'):
                widget.action_previous.title = 'EDM'
                if self.cfg is not None:
                    if self.cfg.filename:
                        widget.action_previous.title = filename_only(self.cfg.filename)

    def take_shot(self, instance):
        self.station.shot_type = instance.id
        self.station.clear_xyz()
        if self.station.make == 'Microscribe':
            self.popup = DataGridTextBox(title = 'EDM', text = '<Microscribe>',
                                            label = 'Waiting on...',
                                            button_text = ['Cancel', 'Next'],
                                            call_back = self.have_shot,
                                            colors = self.colors)
        elif self.station.make in ['Manual XYZ', 'Manual VHD']:
            self.popup = edm_manual(type = self.station.make, call_back = self.have_shot_manual, colors = self.colors)
        else:
            self.station.take_shot()
            self.popup = self.get_prism_height()
        self.popup.open()

    def have_shot_manual(self, instance):
        # check that next was pressed and get values
        if self.popup.xcoord and self.popup.ycoord and self.popup.zcoord:
            p = self.station.text_to_point(f'{self.popup.xcoord.text},{self.popup.ycoord.text},{self.popup.zcoord.text}')
            if p:
                self.station.xyz = p
                self.station.make_global()
                self.station.vhd_from_xyz()
        elif self.popup.hangle and self.popup.vangle and self.popup.sloped:
            try:
                self.station.hangle = float(self.popup.hangle.text)
                self.station.vangle = float(self.popup.vangle.text)
                self.station.sloped = float(self.popup.sloped.text)
            except ValueError:
                self.station.xyz = point()
            self.station.vhd_to_xyz()
            self.station.make_global()
        self.station.pnt = None
        self.popup.dismiss()
        if self.station.xyz.x is None or self.station.xyz.y is None or self.station.xyz.z is None:
            self.popup = e5_MessageBox('Recording error', '\nInvalid value(s) were given.  Point not recorded.', call_back = self.close_popup)
        else:
            self.popup = self.get_prism_height()
        self.popup.open()
        self.popup_open = True

    def get_prism_height(self):
        prism_names = self.data.names('prisms')
        if len(prism_names) > 0:
            return(DataGridMenuList(title = "Select or Enter a Prism Height",
                                            menu_list = prism_names,
                                            menu_selected = '',
                                            call_back = self.have_shot,
                                            colors = self.colors))
        else:
            return(DataGridTextBox(title = 'Enter a Prism Height',
                                        call_back = self.have_shot,
                                        button_text = ['Back', 'Next'],
                                        colors = self.colors))

    def have_shot(self, instance):
        if self.station.make == 'Microscribe':
            result = self.popup.result
            if result:
                p = self.station.text_to_point(result)
                if p:
                    p.x = p.x / 1000.0
                    p.y = p.y / 1000.0
                    p.z = p.z / 1000.0
                    self.station.xyz = p
                    self.station.make_global()
        else:
            prism_name = instance.text
            if prism_name == 'Add' or prism_name == 'Next':
                try:
                    self.station.prism = prism(None, float(self.popup.txt.text), None)
                except ValueError:
                    self.station.prism = prism()
            else:
                self.station.prism = self.data.get_prism(prism_name)
            if self.station.prism.height is None:
                self.popup.dismiss()
                self.popup = e5_MessageBox('Error', '\nInvalid prism height provided.  Shot not recorded.', call_back = self.close_popup)
                self.popup.open()
                self.popup_open = True
                return
            else:
                if self.station.make in ['Leica']:
                    self.station.fetch_point()
                    self.station.make_global()
                elif self.station.make in ['Simulate']:
                    self.station.pnt = None
                elif self.station.make in ['Manual XYZ', 'Manual VHD']:
                    self.station.pnt = None
                self.station.prism_adjust()
        self.popup.dismiss()

        if self.station.xyz.x and self.station.xyz.y and self.station.xyz.z:
            if self.station.shot_type == 'measure':
                txt = f'\nCoordinates:\n  X:  {self.station.xyz_global.x:.3f}\n  Y:  {self.station.xyz_global.y:.3f}\n  Z:  {self.station.xyz_global.z:.3f}'
                unitname = self.data.point_in_unit(self.station.xyz_global)
                if unitname:
                    txt += f'\n\nThe point is in unit {unitname}.'
                if self.station.make != 'Microscribe':
                    txt += f'\n\nMeasurement Data:\n  Horizontal angle:  {self.station.decimal_degrees_to_sexa_pretty(self.station.hangle)}\n  Vertical angle:  {self.station.decimal_degrees_to_sexa_pretty(self.station.vangle)}\n  Slope distance:  {self.station.sloped:.3f}'
                    txt += f'\n  X:  {self.station.xyz.x:.3f}\n  Y:  {self.station.xyz.y:.3f}\n  Z:  {self.station.xyz.z:.3f}'
                    txt += f'\n\nStation coordinates:\n  X:  {self.station.location.x:.3f}\n  Y:  {self.station.location.y:.3f}\n  Z:  {self.station.location.z:.3f}'
                    if self.station.prism_constant:
                        txt += f'\n\nPrism constant :  {self.station.prism_constant} m'
                    if self.station.pnt:
                        txt += f'\n\nData stream:\n  {self.station.pnt}'
                self.popup = e5_MessageBox('Measurement', txt,
                                            response_type = "OK",
                                            call_back = self.close_popup,
                                            colors = self.colors)
                self.popup.open()
            else:
                self.add_point_record()
                # TODO self.station.prism = self.data.prisms.get(value.text).height
                if self.data.db is not None:
                    self.data.db.table(self.data.table).on_save = self.on_save
                    self.data.db.table(self.data.table).on_cancel = self.on_cancel
                self.parent.current = 'EditPointScreen'
        else:
            self.popup = e5_MessageBox(title = 'Error', message = '\nPointed not recorded.')
            self.popup.open()

    def on_save(self):
        # TODO check for duplicates
        # TODO update linked fields
        self.log_the_shot()
        self.update_info_label()
        self.make_backup()
        self.check_for_duplicate_xyz()
        return([])

    def log_the_shot(self):
        logger = logging.getLogger(__name__)
        logger.info(f'{self.get_last_squid()} {self.station.vhd_to_sexa_pretty_compact()} with prism height {self.station.prism.height} from {self.station.location} ')

    def on_cancel(self):
        if self.data.db is not None:
            last_record = self.data.db.table(self.data.table).all()[-1]
            if last_record != []:
                self.data.db.table(self.data.table).remove(doc_ids = [last_record.doc_id])

    def get_last_squid(self):
        unit = self.get_last_value('UNIT')
        idno = self.get_last_value('ID')
        suffix = self.get_last_value('SUFFIX')
        if unit is not None and idno is not None and suffix is not None:
            return(f'{unit}-{idno}({suffix})')
        else:
            return('')

    def update_info_label(self):
        last_squid = self.get_last_squid()
        self.info.text = last_squid if last_squid else 'EDM'

    def check_for_duplicate_xyz(self):
        if self.station.make == 'Microscribe' and self.data.db:
            if len(self.data.db.table(self.data.table)) > 1:
                last_record = self.data.db.table(self.data.table).all()[-1]
                next_to_last_record = self.data.db.table(self.data.table).all()[-2]
                if 'X' in last_record.keys() and 'Y' in last_record.keys() and 'Z' in last_record.keys():
                    if last_record['X'] == next_to_last_record['X'] and last_record['Y'] == next_to_last_record['Y'] and last_record['Z'] == next_to_last_record['Z']:
                        self.popup = e5_MessageBox(title = 'Warning', message = f"\nThe last two recorded points have the exact same XYZ coordinates ({last_record['X']}, {last_record['Y']}, {last_record['Z']}).  Verify that the Microscribe is still properly recording points (green light is on).  If the red light is on, you need to re-initialize (Setup - Initialize Station) and re-shoot the last two points.")
                        self.popup.open()

    def close_popup(self, instance):
        self.popup.dismiss()

    def save_default_cfg(self):
        content = e5_SaveDialog(filename = '',
                                start_path = self.cfg.path,
                                save = self.save_default,
                                cancel = self.dismiss_popup)
        self.popup = Popup(title = "Create a new default CFG file",
                            content = content,
                            size_hint = (0.9, 0.9))
        self.popup.open()
        self.popup_open = True

    def save_default(self, *args):
        path = self.popup.content.filesaver.path
        filename = self.popup.content.filename
        if '.cfg' not in filename.lower():
            filename = filename + '.cfg'
        self.cfg.initialize()
        self.cfg.build_default()
        self.ini.update_value(__program__, 'CFG', os.path.join(path, filename))
        self.cfg.update_value(__program__, 'DATABASE', os.path.join(path, filename.split('.')[0] + '.json'))
        self.cfg.update_value(__program__, 'TABLE', filename.split('.')[0])
        self.data.open(os.path.join(path, filename.split('.')[0] + '.json'))
        self.open_db()
        self.set_new_data_to_true()
        self.cfg.filename = os.path.join(path, filename)
        self.cfg.save()
        self.ini.update(self.colors, self.cfg)
        self.dismiss_popup()
        self.build_mainscreen()
        self.reset_screens()

    def set_new_data_to_true(self, table_name = None):
        if table_name is None:
            self.data.new_data['prisms'] = True
            self.data.new_data['units'] = True
            self.data.new_data['datums'] = True
            self.data.new_data[self.data.table] = True
        else:
            self.data.new_data[table_name] = True

    def show_load_cfg(self):
        if self.cfg.filename and self.cfg.path:
            start_path = self.cfg.path
        else:
            start_path = self.ini.get_value('EDM', 'APP_PATH')
        content = e5_LoadDialog(load = self.load_cfg,
                                cancel = self.dismiss_popup,
                                start_path = start_path,
                                button_color = self.colors.button_color,
                                button_background = self.colors.button_background)
        self.popup = Popup(title = "Load CFG file", content = content,
                            size_hint = (0.9, 0.9))
        self.popup.open()

    def load_cfg(self, path, filename):
        self.data.close()
        self.dismiss_popup()
        self.cfg.load(os.path.join(path, filename[0]))
        if self.cfg.filename:
            self.open_db()
            self.set_new_data_to_true()
        self.ini.update(self.colors, self.cfg)
        self.build_mainscreen()
        self.reset_screens()

    def reset_screen_defaults(self):
        sm.get_screen('EditPointScreen').e5_cfg = self.cfg
        sm.get_screen('EditPointScreen').data_table = self.data.table
        sm.get_screen('EditPointScreen').data = self.data
        sm.get_screen('EditLastRecordScreen').data_table = self.data.table

    def show_import_csv(self):
        instructions = 'EDM can import data from EDM-Mobile, EDMWin, EDM itself, or user prepared data files.  The two import formats are CSV and JSON.  CSV files should have a csv or txt extension.  JSON files should have a json extension.'
        instructions += ' See our web site for more information on exporting data from EDM-Mobile and EDMWin.  The JSON option is for easy importing from EDM data files.'
        instructions += ' Importing points from JSON files is not yet available. IMPORT: Imported data will overwrite existing data in the case of duplicates.'
        self.popup = e5_PopUpMenu(title = "Load which kind of data", message = instructions,
                                        menu_list = ['Points', 'Datums', 'Prisms', 'Units'],
                                        menu_selected = '',
                                        call_back = self.select_csv_file,
                                        colors = self.colors)
        self.popup.open()

    def show_csv_datatype(self):
        self.popup = e5_PopUpMenu(title = "Export which kind of data", message = '',
                                        menu_list = ['Points', 'Datums', 'Prisms', 'Units'],
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
            start_path = self.ini.get_value('EDM', 'APP_PATH')
        content = e5_LoadDialog(load = self.load_csv,
                                cancel = self.dismiss_popup,
                                start_path = start_path,
                                button_color = self.colors.button_color,
                                button_background = self.colors.button_background,
                                filters = ['*.csv', '*.CSV', '*.txt', '*.TXT', '*.json', '*.JSON'])
        self.popup = Popup(title = "Select CSV or JSON file to import from",
                            content = content,
                            size_hint = (0.9, 0.9))
        self.popup.open()

    def read_csv_file(self, full_filename):
        data = []
        with open(full_filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile, quoting = csv.QUOTE_NONNUMERIC)
            for row in reader:
                data.append(row)
        fields = [field.upper() for field in reader.fieldnames]
        return(fields, data)

    def read_json_table(self, full_filename, data_type):
        data = []
        if data_type.upper() in ['DATUMS', 'UNITS', 'PRISMS']:
            data = TinyDB(full_filename).table(data_type.lower()).all()
        fields = data[0].keys() if data else []
        return(fields, data)

    def check_import_fields_against_cfg_fields(self, fields):
        cfg_fields = self.cfg.fields()
        missing_fields = [field for field in fields if field not in cfg_fields]
        missing_fields = [field for field in missing_fields if field not in ['RECNO', 'TIME']]
        if missing_fields:
            return(f"The following field(s) are present in the import data but not in the current CFG: {', '.join(missing_fields)}. Importing these data could cause the loss of data.  Please add these missing fields to the CFG before importing these data.")
        else:
            return("")

    def get_unique_key(self, data_record):
        unique_key = []
        for field in self.cfg.unique_together:
            unique_key.append("%s" % data_record[field])
        return(",".join(unique_key))

    def check_unique_together(self, data_record):
        if self.data.db is not None:
            if self.cfg.unique_together and len(self.data.db.table(self.data.table)) > 1:
                unique_key = self.get_unique_key(data_record)
                for doc_id in self.data.doc_ids():
                    if unique_key == self.get_unique_key(self.data.db.table(self.data.table).get(doc_id = doc_id)):
                        return(doc_id)
        return('')

    def error_check_import(self, fields):
        errors = ''
        if self.csv_data_type == 'Datums':
            if len(fields) < 4:
                errors = f'\nThese data seem to have fewer than four fields.  To import datums requires a Name, X, Y, and Z field.  If this is a CSV file, the first row in the file should contain these field names separated by commas.  The fieldnames read were {fields}.'
            if 'X' not in fields or 'Y' not in fields or 'Z' not in fields or 'NAME' not in fields:
                errors = f'\nIf these data are coming from a CSV file, the first row must list the field names (comma delimited) and must include a field called Name, X, Y and Z.  The fields read were {fields}.'
        if self.csv_data_type == 'Prisms':
            if len(fields) < 2:
                errors = f'\nThese data seem to have fewer than two fields.  To import prisms requires a Name and height and optionally an offset field.  If this is a csv file, the first row in the file should contain these field names separated by commas.  The fieldnames read were {fields}.'
            if 'NAME' not in fields or 'HEIGHT' not in fields:
                errors = f'\nIf these data are coming from a CSV file, the first row must list the field names (comma delimited) and must include a field called Name and Height.  The fields read were {fields}.'
        if self.csv_data_type == 'Units':
            if len(fields) < 5:
                errors = f'\nThese data seem to have fewer than five fields.  To import units requires a Unit, Minx, Miny, Maxx, Maxy field.  If this is a CSV file, the first row in the file should contain these field names separated by commas.  The fieldnames read were {fields}.'
            if 'UNIT' not in fields or 'MINX' not in fields or 'MINY' not in fields or 'MAXX' not in fields or 'MAXY' not in fields:
                errors = f'\nIf these data are coming from a CSV file, the first row must list the field names (comma delimited) and must include at least fields called Unit, Minx, Miny, Maxx, Maxy.  The fields read were {fields}.'
        if self.csv_data_type == 'Points':
            errors = self.check_import_fields_against_cfg_fields(fields)
        return(errors)

    def import_these(self, data):
        record_count = 0
        if self.data.db is not None:
            for item in data:
                insert_record = {}
                for key, value in item.items():
                    if key.upper() == "UNIT" and self.csv_data_type == "Units":
                        insert_record['NAME'] = value
                    else:
                        insert_record[key.upper()] = value
                if self.csv_data_type in ['Datums', 'Prisms', 'Units']:
                    if insert_record['NAME'].strip():
                        if len(self.data.get_by_name(self.csv_data_type.lower(), insert_record['NAME'])) > 0:
                            self.data.delete_by_name(self.csv_data_type.lower(), insert_record['NAME'])
                        self.data.db.table(self.csv_data_type.lower()).insert(insert_record)
                if self.csv_data_type == 'Points':
                    duplicate_doc_id = self.check_unique_together(insert_record)
                    self.data.db.table(self.data.table).insert(insert_record)
                    if not duplicate_doc_id == '':
                        self.data.db.table(self.data.table).remove(doc_ids = [duplicate_doc_id])
                record_count += 1
        return(record_count)

    def load_csv(self, path, filename):
        # TODO This routine does not properly import Units.  The unitfields need to be put into a separate table
        # TODO Need to write the routine to import actual data
        full_filename = os.path.join(path, filename[0])
        self.dismiss_popup()

        if '.csv' in full_filename.lower() or '.txt' in full_filename.lower():
            fields, data = self.read_csv_file(full_filename)
        else:
            fields, data = self.read_json_table(full_filename, self.csv_data_type)

        errors = self.error_check_import(fields)

        if not errors:
            record_count = self.import_these(data)

        if errors:
            message = errors
        else:
            message = '%s %s successfully imported.' % (record_count, self.csv_data_type)
        self.popup = e5_MessageBox('CSV Import', message,
                                    response_type = "OK",
                                    call_back = self.close_popup,
                                    colors = self.colors)
        self.open_popup()
        return(errors)

    def add_point_record(self):
        new_record = {}
        new_record = self.fill_default_fields(new_record)
        if self.station.shot_type != 'continue':
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
                                    # TODO Should be calibrated to the length of this field
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
                    except ValueError:
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
                new_record['PRISM'] = self.station.prism.height if self.station.prism else 0.0
            elif field == 'DATE':
                new_record['DATE'] = '%s' % datetime.now().replace(microsecond=0)
        return(new_record)

    def get_last_value(self, field_name):
        if self.data.db is not None:
            if len(self.data.db.table(self.data.table)) > 0:
                last_record = self.data.db.table(self.data.table).all()[-1]
                if last_record != []:
                    if field_name in last_record.keys():
                        return(last_record[field_name])
        return(None)

    def exit_program(self):
        logger = logging.getLogger(__name__)
        logger.info(__program__ + ' exited.')
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
                                    size_hint_x = width_calculator(.9, 400),
                                    pos_hint={'center_x': .5},
                                    padding = 20,
                                    spacing = 20)
        self.add_widget(self.content)

        self.content.add_widget(e5_label('Provide a name and notes (optional), then record and save.', colors = self.colors))

        self.datum_name = DataGridLabelAndField('Name', colors = self.colors)
        self.content.add_widget(self.datum_name)
        self.datum_notes = DataGridLabelAndField('Notes', colors = self.colors)
        self.content.add_widget(self.datum_notes)

        self.recorder = datum_recorder('Record datum', station = self.station,
                                        colors = self.colors, setup_type = 'record_new', data = self.data)
        self.content.add_widget(self.recorder)

        self.results = e5_label('', colors = self.colors)
        self.content.add_widget(self.results)

        self.content.add_widget(e5_side_by_side_buttons(text = ['Back', 'Save'],
                                                        id = ['cancel', 'save'],
                                                        call_back = [self.cancel, self.check_for_duplicate],
                                                        selected = [False, False],
                                                        colors = self.colors))

    def check_for_duplicate(self, instance):
        if self.data.get_datum(self.datum_name.txt.text).name is not None:
            message = '\nOverwrite existing datum %s?' % self.datum_name.txt.text
            self.popup = e5_MessageBox('Overwrite?', message,
                                        response_type = "YESNO",
                                        call_back = [self.delete_and_save, self.close_popup],
                                        colors = self.colors)
            self.popup.open()
        elif self.datum_name.txt.text == "":
            self.popup = e5_MessageBox('Error', '\nProvide a datum name before saving.', colors = self.colors)
            self.popup.open()
        else:
            self.save_datum()

    def delete_and_save(self, instance):
        self.popup.dismiss()
        self.data.delete_datum(self.datum_name.txt.text)
        self.save_datum()

    def save_datum(self):
        error_message = ''
        if self.datum_name.txt.text == '':
            error_message = '\nProvide a datum name.'
        if self.recorder.result.xyz_global.x is None or self.recorder.result.xyz_global.y is None or self.recorder.result.xyz_global.z is None:
            error_message = '\nThe point was not properly recorded.  Try again.'
        if error_message == '':
            insert_record = {}
            insert_record['NAME'] = self.datum_name.txt.text
            insert_record['NOTES'] = self.datum_notes.txt.text
            insert_record['X'] = str(round(self.recorder.result.xyz_global.x, 3))
            insert_record['Y'] = str(round(self.recorder.result.xyz_global.y, 3))
            insert_record['Z'] = str(round(self.recorder.result.xyz_global.z, 3))
            self.data.db.table('datums').insert(insert_record)
            self.datum_name.txt.text = ''
            self.datum_notes.txt.text = ''
            self.recorder.result.text = ''
            self.recorder.result.xyz = None
            self.recorder.result.xyz_global = None
            self.data.new_data['datums'] = True
        else:
            self.popup = e5_MessageBox('Error', error_message, colors = self.colors)
            self.popup.open()

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
                                    padding = 20,
                                    spacing = 20)
        self.add_widget(self.content)

        # self.content.add_widget(e5_label('Select a datum to use as verification and record it.', colors = self.colors))

        self.datum1 = datum_selector(text = 'Select\nverification\ndatum',
                                            data = self.data,
                                            colors = self.colors,
                                            default_datum = self.data.get_datum(self.ini.get_value('SETUPS', 'VERIFICATION')))
        self.content.add_widget(self.datum1)

        self.recorder = datum_recorder('Record\nverification\ndatum', station = self.station,
                                        colors = self.colors, setup_type = 'verify',
                                        on_record = self.compute_error, data = self.data)
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
            self.ini.update_value('SETUPS', 'VERIFICATION', self.datum1.datum.name)
            self.ini.save()
        self.parent.current = 'MainScreen'


class record_button(e5_button):

    popup = ObjectProperty(None)
    datum_name = None

    def __init__(self, station = None, result_label = None, setup_type = None, on_record = None, datum1 = None, datum2 = None, datum3 = None, data = None, **kwargs):
        super(record_button, self).__init__(**kwargs)
        # self.colors = colors if colors is not None else ColorScheme()
        self.station = station
        self.bind(on_press = self.record_datum)
        self.result_label = result_label
        self.setup_type = setup_type
        self.on_record = on_record
        self.datum1 = datum1
        self.datum2 = datum2
        self.datum3 = datum3
        self.data = data
        self.default_prism = prism()

    def record_datum(self, instance):
        self.set_angle()

    def get_angle(self):
        if self.id == 'datum1':
            if self.setup_type == 'Over a datum + Record a datum':
                return(self.station.angle_between_points(self.datum1.datum, self.datum2.datum))
            elif self.setup_type == 'Record two datums':
                return(0)
        else:
            return(None)

    def set_angle(self):
        angle = self.get_angle()
        if angle is not None:
            if self.station.make in ['Manual XYZ', 'Manual VHD']:
                self.popup = e5_MessageBox('Set horizonal angle', f'\nAim at {self.datum1.datum.name} and set the horizontal angle to {self.station.decimal_degrees_to_sexastr(angle)}.',
                                            call_back = self.now_take_shot, colors = self.colors)
                self.popup.open()
            elif self.station.make == 'Leica':
                self.station.set_horizontal_angle_leica(self.station.decimal_degrees_to_dddmmss(angle))
                self.station.take_shot()
                self.popup = self.get_prism_height()
                self.popup.open()
        else:
            self.station.take_shot()
            self.popup = self.get_prism_height()
            self.popup.open()

    def now_take_shot(self, instance):
        self.popup.dismiss()
        self.station.take_shot()
        self.wait_for_shot()

    def wait_for_shot(self):
        if self.station.make == 'Microscribe':
            # self.popup = DataGridTextBox(title = self.text + '.  Waiting on Microscribe...', button_text = ['Cancel', 'Next'], call_back = self.microscribe)
            self.popup = DataGridTextBox(title = 'EDM',
                                            label = self.text + '.  Waiting on...',
                                            text = '<Microscribe>',
                                            button_text = ['Cancel', 'Next'],
                                            call_back = self.microscribe,
                                            colors = self.colors)
            self.popup.open()
        elif self.station.make in ['Manual XYZ', 'Manual VHD']:
            self.popup = edm_manual(call_back = self.have_shot_manual, colors = self.colors)
            self.popup.open()

    def have_shot_manual(self, instance):
        # check that next was pressed and get values
        p = self.station.text_to_point(f'{self.popup.xcoord.text},{self.popup.ycoord.text},{self.popup.zcoord.text}')
        if p:
            self.station.xyz = p
            self.station.make_global()
            self.station.vhd_from_xyz()
        else:
            self.station.hangle = self.popup.hangle.text if isinstance(self.popup.hangle.text, int) or isinstance(self.popup.hangle.text, float) else ''
            self.station.vangle = self.popup.vangle.text if isinstance(self.popup.vangle.text, int) or isinstance(self.popup.vangle.text, float) else ''
            self.station.sloped = self.popup.sloped.text if isinstance(self.popup.sloped.text, int) or isinstance(self.popup.sloped.text, float) else ''
            self.station.vhd_to_xyz()
        self.popup.dismiss()
        self.popup = self.get_prism_height()
        self.popup.open()

    def get_prism_height(self):
        prism_names = self.data.names('prisms') if self.data else []
        if len(prism_names) > 0:
            return(DataGridMenuList(title = "Select or Enter a Prism Height",
                                            menu_list = prism_names,
                                            menu_selected = self.default_prism.name if self.default_prism.name else '',
                                            call_back = self.have_shot))
        else:
            return(DataGridTextBox(title = 'Enter a Prism Height',
                                        text = str(self.default_prism.height) if self.default_prism.height else '',
                                        call_back = self.have_shot,
                                        button_text = ['Back', 'Next']))

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
            except ValueError:
                pass
            if error:
                self.popup = e5_MessageBox(title = 'Error', message = '\nData not formatted correctly.  EDM expects three floating point numbers separated by commas.',
                                            colors = self.colors)
                self.popup.open()

    def have_shot(self, instance = None):
        self.popup.dismiss()
        # prism_height = instance.text if not instance.id == 'add_button' else self.popup_textbox.text
        if self.station.make in ['Leica']:
            self.station.fetch_point()
            self.station.make_global()

        prism_name = instance.text
        if prism_name == 'Add' or prism_name == 'Next':
            try:
                self.station.prism = prism(None, float(self.popup.txt.text), None)
            except ValueError:
                self.station.prism = prism()
        else:
            self.station.prism = self.data.get_prism(prism_name)

        # try:
        #    if instance:
        #        self.station.prism = self.data.get_prism(instance.txt)
        #    else:
        #        self.station.prism = prism(None, float(self.popup.result), None)
        # except ValueError:
        #    self.station.prism = prism(None, 0.0, None)
        self.default_prism = self.station.prism
        self.station.prism_adjust()
        if self.station.xyz.x and self.station.xyz.y and self.station.xyz.z:
            if self.setup_type == 'verify' or self.setup_type == 'record_new':
                self.result_label.text = self.station.point_pretty(self.station.xyz_global)
            else:
                self.result_label.text = self.station.point_pretty(self.station.xyz)
            self.result_label.xyz = self.station.xyz
            self.result_label.xyz_global = self.station.xyz_global
            if self.on_record is not None:
                self.on_record()
        else:
            self.result_label.text = 'Recording error.'
            self.result_label.xyz = None
            self.result_label.xyz_global = None


class record_result(e5_label):
    xyz = point()
    xyz_global = point()


class datum_recorder(GridLayout):

    def __init__(self, text = '', datum_no = 1, station = None,
                        colors = None, setup_type = None,
                        on_record = None, datum1 = None, datum2 = None, datum3 = None,
                        data = None, **kwargs):
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
                                    on_record = on_record,
                                    datum1 = datum1,
                                    datum2 = datum2,
                                    datum3 = datum3,
                                    data = data)
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
        # self.orientation = 'horizontal'
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

        self.scrollbox = GridLayout(cols = 1,
                                    size_hint = (1, None),
                                    spacing = 5)
        self.scrollbox.bind(minimum_height = self.scrollbox.setter('height'))

        instructions = Label(color = self.colors.text_color, size_hint_y = None)

        if setup_type == "Horizontal Angle Only":
            instructions.text = '\nEnter the horizontal angle to uploaded to the station.'
            self.scrollbox.add_widget(instructions)

            content1 = GridLayout(cols = 2, padding = 10, size_hint_y = None)
            content1.add_widget(e5_label('Angle (use ddd.mmss)'))
            self.hangle = TextInput(text = '', multiline = False,
                                    size_hint_max_y = 30)
            content1.add_widget(self.hangle)
            self.scrollbox.add_widget(content1)

            content2 = GridLayout(cols = 1, padding = 10, size_hint_y = None)
            content2.add_widget(e5_button(text = 'Upload angle', selected = True, call_back = self.set_hangle, colors = self.colors))
            self.scrollbox.add_widget(content2)

        elif setup_type == "Over a datum":
            instructions.text = '\nUse this option when the station is setup over a known point and you can measure the station height or to set the station location directly (with no station height).  Note this option assumes the horizontal angle is already correct or will be otherwise set.'
            self.scrollbox.add_widget(instructions)

            self.over_datum = datum_selector(text = 'Select a datum',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', 'OVERDATUM')))
            self.scrollbox.add_widget(self.over_datum)

            content2 = GridLayout(cols = 2, padding = 10, size_hint_y = None)
            content2.add_widget(e5_label('Station height (optional)'))
            self.station_height = TextInput(text = '', multiline = False,
                                            size_hint_max_y = 30)
            content2.add_widget(self.station_height)
            self.scrollbox.add_widget(content2)

        elif setup_type == "Over a datum + Record a datum":
            instructions.text = "\nSelect the datum under the station and a datum to recorded.  EDM will automatically set the correct horizontal angle and compute the station's XYZ coordinates."
            self.scrollbox.add_widget(instructions)

            self.datum1 = datum_selector(text = 'Select datum\nunder the\nstation',
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

            datum_name = self.data.get_datum(self.ini.get_value('SETUPS', 'RECORDDATUM'))
            datum_name = f'Record\n{datum_name.name}' if datum_name else 'Record datum 1'
            self.recorder.append(datum_recorder(datum_name, station = self.station, colors = self.colors,
                                                setup_type = setup_type, datum1 = self.datum1, datum2 = self.datum2,
                                                data = self.data))
            self.scrollbox.add_widget(self.recorder[0])

        elif setup_type == "Record two datums":
            instructions.text = "\nSelect two datums to record. EDM will use triangulation to compute the station's XYZ coordinates.  Always record datum one first and then datum two.  When you record datum one, the horizontal angle will be set to 0.0.  When you accept the setup, the horizontal angle will be reset correctly on datum 2."
            self.scrollbox.add_widget(instructions)

            self.datum1 = datum_selector(text = 'Select\ndatum\none',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', '2DATUMS_DATUM_1')),
                                                call_back = self.datum1_selected)
            self.scrollbox.add_widget(self.datum1)

            self.datum2 = datum_selector(text = 'Select\ndatum\ntwo',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', '2DATUMS_DATUM_2')),
                                                call_back = self.datum2_selected)
            self.scrollbox.add_widget(self.datum2)

            for n in range(2):
                datum_name = self.data.get_datum(self.ini.get_value('SETUPS', '2DATUMS_DATUM_%s' % (n + 1)))
                datum_name = f'Record\n{datum_name.name}' if datum_name else f'Record datum {n + 1}'
                self.recorder.append(datum_recorder(datum_name, datum_no = n + 1, station = station, colors = colors,
                                                    setup_type = setup_type, datum1 = self.datum1, datum2 = self.datum2, data = self.data))
                self.scrollbox.add_widget(self.recorder[n])

        elif setup_type == "Three datum shift":
            instructions.text = "\nThis option is designed to let one grid be rotated into another and is best for when a block of sediment is being excavated in a lab.  It requires three datums points."
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
                datum_name = f'Record {datum_name.name}' if datum_name else f'Record datum {n + 1}'
                self.recorder.append(datum_recorder(datum_name, datum_no = n + 1, station = station,
                                                                colors = self.colors, setup_type = setup_type))
                self.scrollbox.add_widget(self.recorder[n])

        instructions.bind(texture_size = lambda instance, value: setattr(instance, 'height', value[1]))
        instructions.bind(width = lambda instance, value: setattr(instance, 'text_size', (value * .95, None)))

        self.size_hint = (1, .9)
        # self.size = (Window.width, Window.height / 2)
        self.id = 'setup_scroll'
        self.add_widget(self.scrollbox)

        def draw_background(widget, prop):
            with widget.canvas.before:
                Color(0.8, 0.8, 0.8, 1)
                Rectangle(size=self.size, pos=self.pos)

        # self.bind(size = draw_background)
        # self.bind(pos = draw_background)

    def datum1_selected(self, instance):
        self.recorder[0].children[1].text = 'Record ' + instance.datum.name
        self.recorder[0].children[1].datum_name = instance.datum.name

    def datum2_selected(self, instance):
        self.recorder[1].children[1].text = 'Record ' + instance.datum.name
        self.recorder[1].children[1].datum_name = instance.datum.name

    def datum3_selected(self, instance):
        self.recorder[2].children[1].text = 'Record ' + instance.datum.name
        self.recorder[2].children[1].datum_name = instance.datum.name

    def set_hangle(self, instance):
        if self.hangle:
            self.station.set_horizontal_angle(self.hangle.text)
            logger = logging.getLogger(__name__)
            logger.info(f'Horizontal angle set to {self.hangle.text}')


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
                                    # size_hint_x = width_calculator(.9, 200),
                                    pos_hint = {'center_x': .5, 'center_y': .5},
                                    padding = 5,
                                    spacing = 5)
        self.add_widget(self.content)

        setup_type_box = GridLayout(cols = 2,
                                    # size_hint = (width_calculator(.9, 400), None),
                                    size_hint_y = None,
                                    pos_hint = {'center_x': .5, 'center_y': .5})

        spinner_dropdown_button = SpinnerOptions
        spinner_dropdown_button.font_size = colors.button_font_size.replace("sp", '') if colors.button_font_size else None
        spinner_dropdown_button.background_color = (0, 0, 0, 1)

        self.setup_type = Spinner(text = self.setup,
                                    values=["Horizontal Angle Only",
                                            "Over a datum",
                                            "Over a datum + Record a datum",
                                            "Record two datums",
                                            "Three datum shift"],
                                    # pos_hint = {'center_x': .5, 'center_y': .5}
                                    size_hint = (.5, None),
                                    option_cls = spinner_dropdown_button)
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

        self.content.add_widget(e5_side_by_side_buttons(text = ['Back', 'Accept Setup'],
                                                        id = ['back', 'accept'],
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

        self.new_station = point()
        self.foresight = None
        txt = ''
        error_message = ''

        if self.setup_type.text == 'Horizontal Angle Only':
            if self.station.location.is_none() is True:
                txt = '\nThe location of the station has not been set.'
            else:
                txt = f'\nThe location of the station is at {str(self.station.location)}.  All measured points will be relative to that point and the horizontal angle uploaded here.'

        elif self.setup_type.text == 'Over a datum':
            if self.setup_widgets.over_datum.datum is None:
                error_message = '\nSelect the datum under the total station and optionally provide the station height.'
            else:
                station_height = float(self.setup_widgets.station_height.text) if self.setup_widgets.station_height.text else 0
                self.new_station = self.setup_widgets.over_datum.datum
                self.new_station.z += station_height
                txt = '\nSet the station coordinates to\nX : %s\nY : %s\nZ : %s' % (self.new_station.x, self.new_station.y, self.new_station.z)

        elif self.setup_type.text == 'Over a datum + Record a datum':
            if self.setup_widgets.datum1.datum is None or self.setup_widgets.datum2.datum is None:
                error_message = '\nSelect the datum under the total station and a datum to record.'
            elif self.setup_widgets.datum1.datum == self.setup_widgets.datum2.datum:
                error_message = '\nSelect two different datums.'
            elif self.station.subtract_points(self.setup_widgets.datum1.datum, self.setup_widgets.datum2.datum) == point(0, 0, 0):
                error_message = '\nSelect two different datums with different coordinates.'
            elif self.setup_widgets.recorder[0].result.xyz is None:
                error_message = '\nRecord the datum before accepting the setup.'
            else:
                self.new_station = self.station.subtract_points(self.setup_widgets.datum2.datum, self.setup_widgets.recorder[0].result.xyz).round()
                datum2 = self.station.add_points(self.setup_widgets.datum1.datum, self.setup_widgets.recorder[0].result.xyz).round()
                station_error = self.station.subtract_points(self.setup_widgets.datum2.datum, datum2).round()
                txt = f'\n{self.setup_widgets.datum2.datum.name} recorded as \nX : {datum2.x}\nY : {datum2.y}\nZ : {datum2.z}\n'
                txt += f'\nThe error in this measurement is \nX : {station_error.x}\nY : {station_error.y}\nZ : {station_error.z}\n'
                txt += '(Note that Z will be off by the station height in most setups)\n'
                txt += f'\nIf the setup as measured is accepted, the new station coordinates will be \nX : {self.new_station.x}\nY : {self.new_station.y}\nZ : {self.new_station.z}'

        elif self.setup_type.text == 'Record two datums':
            if self.setup_widgets.datum1.datum is None or self.setup_widgets.datum2.datum is None:
                error_message = '\nSelect two datums to record.'
            elif self.setup_widgets.datum1.datum == self.setup_widgets.datum2.datum:
                error_message = '\nSelect two different datums.'
            elif self.station.subtract_points(self.setup_widgets.datum1.datum, self.setup_widgets.datum2.datum) == point(0, 0, 0):
                error_message = '\nSelect two different datums with different coordinates.'
            elif self.setup_widgets.recorder[0].result.xyz.is_none() or self.setup_widgets.recorder[1].result.xyz.is_none():
                error_message = '\nRecord each datum.  It is important that the first datum is recorded and then the second and not the other way around.  Note that before the first datum is recorded, a horizontal angle of 0.0000 will be uploaded.'
            else:
                measured_distance = self.station.distance(self.setup_widgets.recorder[0].result.xyz, self.setup_widgets.recorder[1].result.xyz)
                actual_distance = self.station.distance(self.setup_widgets.datum1.datum.as_point(), self.setup_widgets.datum2.datum.as_point())
                error_distance = abs(measured_distance - actual_distance)

                # The following code is ported from EDM-Mobile (and EDMWin).
                # I can't remember exactly how this works, but it does work.
                # And I remember the hot, weekend day at Carsac when Harold
                # and I first figured out how to do this.

                # Workout what the measured angle would be from datum1 to datum2
                y = -1 * self.setup_widgets.recorder[0].result.xyz.y
                y = y + self.setup_widgets.recorder[1].result.xyz.y
                p = point(self.setup_widgets.recorder[1].result.xyz.x, y, 0)
                measured_angle = self.station.angle_between_points(point(0, 0, 0), p)

                # Calculate the actual angle between datum1 and datum2
                defined_angle = self.station.angle_between_points(self.setup_widgets.datum1.datum.as_point(), self.setup_widgets.datum2.datum.as_point())

                # get the difference between these two angles
                angle_difference = defined_angle - measured_angle

                # Based on this, compute the new datum.
                self.new_station = point(round(-1 * self.setup_widgets.recorder[0].result.xyz.y * sin(d2r(angle_difference)) + self.setup_widgets.datum1.datum.x, 3),
                                            round(-1 * self.setup_widgets.recorder[0].result.xyz.y * cos(d2r(angle_difference)) + self.setup_widgets.datum1.datum.y, 3),
                                            round(((self.setup_widgets.datum1.datum.z - self.setup_widgets.recorder[0].result.xyz.z) + (self.setup_widgets.datum2.datum.z - self.setup_widgets.recorder[1].result.xyz.z)) / 2, 3))

                # Workout what angle needs to be uploaded to the station
                self.foresight = self.station.angle_between_points(self.new_station, self.setup_widgets.datum2.datum.as_point())
                txt = f'\nThe measured distance between {self.setup_widgets.datum1.datum.name} and {self.setup_widgets.datum2.datum.name} was {round(measured_distance, 3)} m.  The distance based on the datum definitions should be {round(actual_distance, 3)} m.  The error is {round(error_distance, 3)} m.\n'
                txt += f'\nIf the setup as measured is accepted, the new station coordinates will be \nX : {self.new_station.x}\nY : {self.new_station.y}\nZ : {self.new_station.z}\n'
                txt += f'\nAn angle of {self.station.decimal_degrees_to_sexa_pretty(self.foresight)} will be uploaded (do not turn the station until this angle is set).'
                self.foresight = self.station.decimal_degrees_to_dddmmss(self.foresight)

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

                txt = '\nThe following errors are noted.  The actual distance between datums 1 and 2 is %s and the measured distance was %s.  ' % (round(dist_12_datums, 3), round(dist_12_measured, 3))
                txt += 'The actual distance between datums 2 and 3 is %s and the measured distance was %s.  ' % (round(dist_23_datums, 3), round(dist_23_measured, 3))
                txt += 'The actual distance between datums 1 and 3 is %s and the measured distance was %s.  ' % (round(dist_13_datums, 3), round(dist_13_measured, 3))
                txt += '\n\nThis corresponds to errors of %s, %s, and %s, respectively.' % (dist_12_error, dist_23_error, dist_13_error)

        if not self.new_station.is_none() or txt:
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
        if self.setup_type:

            logger = logging.getLogger(__name__)

            if self.setup_type.text == 'Horizontal Angle Only':
                pass

            elif self.setup_type.text == 'Over a datum':
                self.ini.update_value('SETUPS', 'OVERDATUM', self.setup_widgets.over_datum.datum.name)
                logger.info(f'Setup over {self.setup_widgets.over_datum.datum}')

            elif self.setup_type.text == 'Over a datum + Record a datum':
                self.ini.update_value('SETUPS', 'OVERDATUM', self.setup_widgets.datum1.datum.name)
                self.ini.update_value('SETUPS', 'RECORDDATUM', self.setup_widgets.datum2.datum.name)
                logger.info(f'Setup over {self.setup_widgets.datum1.datum} and recorded {self.setup_widgets.datum2.datum}')

            elif self.setup_type.text == 'Record two datums':
                self.ini.update_value('SETUPS', '2DATUMS_DATUM_1', self.setup_widgets.datum1.datum.name)
                self.ini.update_value('SETUPS', '2DATUMS_DATUM_2', self.setup_widgets.datum2.datum.name)
                logger.info(f'Setup 2-point using {self.setup_widgets.datum1.datum} and {self.setup_widgets.datum2.datum}')

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
                logger.info(f'Setup 3 datum shift using {self.setup_widgets.datum1.datum}, {self.setup_widgets.datum2.datum}, and {self.setup_widgets.datum3.datum}')
                logger.info(f'Recorded values were respectively {self.setup_widgets.recorder[0].result.xyz}, {self.setup_widgets.recorder[1].result.xyz}, and {self.setup_widgets.recorder[2].result.xyz}')

        self.popup.dismiss()
        if self.foresight:
            self.station.set_horizontal_angle(self.foresight)
            logger.info(f'Horizontal angle set to {self.foresight}')
        if self.new_station.is_none() is False:
            self.station.location = self.new_station
            logger.info('Station location set to ' + str(self.station.location))
        self.ini.update_value('SETUPS', 'LASTSETUP_TYPE', self.setup_type.text)
        self.ini.save()
        self.parent.current = 'MainScreen'


class EditLastRecordScreen(e5_RecordEditScreen):
    pass


class EditPointScreen(e5_RecordEditScreen):
    pass


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
        spinner_dropdown_button.font_size = colors.button_font_size.replace("sp", '') if colors.button_font_size else None
        spinner_dropdown_button.background_color = (0, 0, 0, 1)

        self.spinner = Spinner(text = default if default is not None else '',
                                values = spinner_values,
                                font_size = colors.button_font_size if colors.button_font_size else None,
                                option_cls = spinner_dropdown_button)
        if label_text == 'Port Number':
            comport = GridLayout(cols = 2, spacing = 5)
            comport.bind(minimum_height = comport.setter('height'))
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
        self.popup = e5_MessageBox('COM Ports', '\nLooking for valid COM ports...This can take several seconds...And the Cancel button might appear non-responsive...',
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
        if self.comport_to_test is None:
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
        self.call_back = 'MainScreen'

    def on_enter(self):
        self.clear_widgets()
        self.layout = GridLayout(cols = 1,
                                 spacing = 5,
                                 size_hint_x = width_calculator(.9, 400),
                                 size_hint_y = .9,
                                 pos_hint = {'center_x': .5, 'center_y': .5})
        self.add_widget(self.layout)
        self.build_screen()

    def build_screen(self):
        self.station_type = station_setting(label_text = 'Station type',
                                            spinner_values = ("Leica", "Wild", "Topcon", "Sokkia", "Microscribe", "Manual XYZ", "Manual VHD", "Simulate"),
                                            call_back = self.toggle_buttons,
                                            id = 'station_type',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'STATION'))
        self.layout.add_widget(self.station_type)

        self.communications = station_setting(label_text = 'Communications',
                                                spinner_values = ("Serial", "Bluetooth"),
                                                # call_back = self.update_ini,
                                                id = 'communications',
                                                colors = self.colors,
                                                default = self.ini.get_value(__program__, 'COMMUNICATIONS'))
        self.layout.add_widget(self.communications)

        self.comports = station_setting(label_text = 'Port Number',
                                            spinner_values = [],
                                            # call_back = self.update_ini,
                                            id = 'comport',
                                            colors = self.colors, station = self.station,
                                            default = self.ini.get_value(__program__, 'COMPORT'))
        self.layout.add_widget(self.comports)

        self.baud_rate = station_setting(label_text = 'Baud rate',
                                            spinner_values = ("1200", "2400", "4800", "9600", "14400", "19200"),
                                            # call_back = self.update_ini,
                                            id = 'baudrate',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'BAUDRATE'))
        self.layout.add_widget(self.baud_rate)

        self.parity = station_setting(label_text = 'Parity',
                                            spinner_values = ("Even", "Odd", "None"),
                                            # call_back = self.update_ini,
                                            id = 'parity',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'PARITY'))
        self.layout.add_widget(self.parity)

        self.data_bits = station_setting(label_text = 'Databits',
                                            spinner_values = ("7", "8"),
                                            # call_back = self.update_ini,
                                            id = 'databits',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'DATABITS'))
        self.layout.add_widget(self.data_bits)

        self.stop_bits = station_setting(label_text = 'Stopbits',
                                            spinner_values = ("0", "1", "2"),
                                            # call_back = self.update_ini,
                                            id = 'stopbits',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'STOPBITS'))
        self.layout.add_widget(self.stop_bits)

        self.buttons = e5_side_by_side_buttons(text = ['Back', 'Set'],
                                                id = ['Back', 'Set'],
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
        self.parent.current = self.call_back

# Region Help Screens


class AboutScreen(e5_InfoScreen):
    def on_pre_enter(self):
        self.content.text = '\n\nEDM by Shannon P. McPherron\n\nVersion ' + __version__ + ' Alpha\nApple Pie\n\n'
        self.content.text += 'Built using Python 3.8, Kivy 2.0 and TinyDB 4.0\n\n'
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
        txt += '\nThe default user path is %s.\n' % self.ini.get_value(__program__, "APP_PATH")
        logger = logging.getLogger(__name__)
        txt += f'\nThe log is written to {logger.handlers[0].baseFilename}\n'
        txt += '\nThe operating system is %s.\n' % platform_name()
        txt += '\nPython build is %s.\n' % (python_version())
        txt += '\nLibraries installed include Kivy %s and TinyDB %s.\n' % (__kivy_version__, __tinydb_version__)
        txt += '\nEDM was tested and distributed most recently on Python 3.8.1, Kivy 2.0.0 and TinyDB 4.4.0.\n'
        self.content.text = txt
        self.content.color = self.colors.text_color
        self.back_button.background_color = self.colors.button_background
        self.back_button.color = self.colors.button_color

# endregion

# sm = ScreenManager(id = 'screen_manager')


sm = ScreenManager()


class EDMApp(App):

    def __init__(self, **kwargs):
        super(EDMApp, self).__init__(**kwargs)

        self.app_path = self.user_data_dir

    def build(self):
        sm.add_widget(MainScreen(user_data_dir = self.user_data_dir, name = 'MainScreen'))
        sm.current = 'MainScreen'
        # Window.borderless = True
        self.title = __program__ + " " + __version__
        return(sm)


Factory.register(__program__, cls=EDMApp)


if __name__ == '__main__':
    EDMApp().run()
