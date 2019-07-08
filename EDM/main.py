# ToDo
#   On station verify, do the verify math
#   After XYZ are obtained, check units file, populate and maintain units file after save
#   Think through making a field link to a database table (unique value is a table record)

# ToDo NewPlot
#   Read either CSV or JSON file

# ToDo More Longterm
#   Add serial port communications
#   Add bluetooth communications

__version__ = '1.0.4'
__date__ = 'July, 2019'
from constants import __program__ 

#Region Imports
from kivy.graphics import Color, Rectangle
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
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

import logging
import logging.handlers as handlers

# My libraries for this project
from blockdata import blockdata
from dbs import dbs
from e5_widgets import *
from constants import *
from colorscheme import *
from misc import *

# The database - pure Python
from tinydb import TinyDB, Query, where

from collections import OrderedDict

#endregion

# get anglr.py library
# or get angles.py library (looks maybe better)

# use pySerial for serial communications

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
        self.db = TinyDB(filename)
        self.filename = filename
        self.prisms = self.db.table('prisms')
        self.units = self.db.table('units')
        self.datums = self.db.table('datums')

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
        if name is not '':
            p = self.db.table('datums').search( (where('NAME') == name) )[0]
            if p:
                return(datum(p['NAME'] if 'NAME' in p.keys() else None,
                            float(p['X']) if 'X' in p.keys() else None,
                            float(p['Y']) if 'X' in p.keys() else None,
                            float(p['Z']) if 'X' in p.keys() else None,
                            p['NOTES'] if 'NOTES' in p.keys() else None))
        return(None)

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
            name_list.append(row['NAME'])
        return(name_list)

    def fields(self):
        pass

    def delete_all(self):
        self.db.purge()

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
                    if xyz.x <= a_unit['XMAX'] and xyz.x >= a_unit['XMIN'] and xyz.y <= a_unit['YMAX'] and xyz.y >= a_unit['YMIN']:
                        return(a_unit['NAME'])
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
    
    def open(self, filename = ''):
        if filename:
            self.filename = filename
        self.load()

    def valid_datarecord(self, data_record):
        for field in data_record:
            f = self.get(field)
            value = data_record[field]
            if f.required and not value:
                return('Required field %s is empty.  Please provide a value.' % field)
            if f.length!=0 and len(value) > f.length:
                return('Maximum length for %s is set to %s.  Please shorten your response.  Field lengths can be set in the CFG file.  A value of 0 means no length limit.')
        return(True)

    def get(self, field_name):
        f = self.field(field_name)
        f.inputtype = self.get_value(field_name, 'TYPE')
        f.prompt = self.get_value(field_name, 'PROMPT')
        f.length = self.get_value(field_name, 'LENGTH')
        f.menu = self.get_value(field_name, 'MENU').split(",")
        f.link_fields = self.get_value(field_name, 'LINKED').split(",")
        return(f)

    def put(self, field_name, f):
        self.update_value(field_name, 'PROMPT', f.prompt)
        self.update_value(field_name, 'LENGTH', f.length)
        self.update_value(field_name, 'TYPE', f.inputtype)
        #self.update_value(field_name, 'MENU', f.menu)

    def fields(self):
        field_names = self.names()
        del_fields = ['BUTTON1','BUTTON2','BUTTON3','BUTTON4','BUTTON5','BUTTON6','EDM','TIME']
        for del_field in del_fields:
            if del_field in field_names:
                field_names.remove(del_field)
        return(field_names)

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
        for field_name in self.fields():
            f = self.get(field_name)
            if f.prompt == '':
                f.prompt = field_name
            f.inputtype = f.inputtype.upper()
            if field_name in ['UNIT','ID','SUFFIX','X','Y','Z']:
                f.required = True
            self.put(field_name, f)
        
        # This is a legacy issue.  Linked fields are now listed with each field.
        unit_fields = self.get_value('EDM', 'UNITFIELDS')
        if unit_fields:
            f = self.get('UNIT')
            f.link_fields = unit_fields
            self.put('UNIT', f)
            # Delete UNITIFIELDS from the EDM block of teh CFG

    def save(self):
        self.write_blocks()

    def load(self, filename = ''):
        if filename:
            self.filename = filename
        self.path = ntpath.split(self.filename)[0]

        self.blocks = []
        if os.path.isfile(self.filename):
            self.blocks = self.read_blocks()
        else:
            self.filename = 'default.cfg'
            self.build_default()
    
    def status(self):
        txt = 'CFG file is %s\n' % self.filename
        return(txt)

class totalstation:

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
        self.input_string = ''
        self.output_string = ''
        self.port_open = False
        self.location = point(0, 0, 0)
        self.xyz = point()
        self.prism = 0
        self.hangle = ''
        self.vangle = ''
        self.sloped = 0
        self.suffix = 0
        self.prism = 0
        self.xyz_global = point()
        self.rotate_local = []
        self.rotate_global = []
        self.last_setup_type = ''

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
            point1 = data.get_datum(ini.get_value('SETUPS','3DATUM_SHIFT_GLOBAL_1')).as_point()
            point2 = data.get_datum(ini.get_value('SETUPS','3DATUM_SHIFT_GLOBAL_2')).as_point()
            point3 = data.get_datum(ini.get_value('SETUPS','3DATUM_SHIFT_GLOBAL_3')).as_point()
            if point1 is not None and point2 is not None and point3 is not None:
                self.rotate_global = [point1, point2, point3]

    def text_to_point(self, txt):
        if len(txt.split(',')) == 3:
            x, y, z = txt.split(',')
            return(point(float(x), float(y), float(z)))
        else:
            return(None)

    def status(self):
        txt = '\nTotal Station:\n'
        txt += '  Make is %s\n' % self.make
        if self.make not in ['Microscribe']:
            txt += '  Communication type is %s\n' % self.communication
            txt += '  COM Port is %s\n' % self.comport
            txt += '  Com settings are %s, %s, %s, %s\n' % (self.baudrate, self.parity, self.databits, self.stopbits)
            if self.port_open:
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

    def initialize(self):
        pass

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

    def hash(self, hashlen):
        hash = ""
        for a in range(0, hashlen):
            hash = hash + random.choice(string.ascii_uppercase)
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

        elif self.make=="WILD" or self.make=="LEICA":
            self.clear_com()
            self.edm_output("GET/M/WI11/WI21/WI22/WI31/WI51")   

        elif self.make=="SOKKIA":
            self.edm_output(chr(17))

        elif self.make == 'Simulate':
            self.xyz = point(round(random.uniform(1000, 1010), 3),
                                round(random.uniform(1000, 1010), 3),
                                round(random.uniform(0, 1), 3 ))
            self.make_global()
    
    def make_global(self):
        self.xyz_global = point(self.xyz.x + self.location.x,
                                self.xyz.y + self.location.y,
                                self.xyz.z + self.location.z,)

    def clear_xyz(self):
        self.xyz = point()
        self.xyz_global = point()

    def set_horizontal_angle(self, angle):
        pass

    def vhd_to_nez(self):
        pass

    def parse_nez(self):
        pass

    def make_bcc(self, itext):
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

    def init_edm(self):
        if self.make=='TOPCON':
            edm_output("ST0")
        if self.make=="WILD" or self.make=="LEICA":
            if edm_output("SET/41/0")==0:
                edm_input()
            if edm_output("SET/149/2")==0:
                edm_input()

    def horizontal(self):
        if self.make=='TOPCON':
            edm_output("Z10")
            return(edm_input)

    def edm_output(self, d):
        error_code = 0
        return(error_code)

    def edm_input(self):
        return('')

    def close_com(self):
        pass

    def open_com(self):
        pass

    def clear_com(self):
        pass

    def deg_to_rad(self):
        pass

    def conv_angle_to_degminsec(self):
        pass

    def calculate_angle(self):
        pass

    def distance(self, p1, p2):
        return(sqrt( (p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2 ))


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

        if len(self.rotate_local) is 3 and len(self.rotate_global) is 3 and p is not None:
            rotated_local = []

            # First line up one side of the triangle formed by the three datum points
            local_vector = self.normalize_vector(self.vector_subtract(self.rotate_local[1], self.rotate_local[0]))
            global_vector = self.normalize_vector(self.vector_subtract(self.rotate_global[1], self.rotate_global[0]))
            p_out = self.rotate_point_2d(global_vector, local_vector, p)

            # Put the local datums in this new space as well
            rotated_local.append(self.rotate_point_2d(global_vector, local_vector, self.rotate_local[0]))
            rotated_local.append(self.rotate_point_2d(global_vector, local_vector, self.rotate_local[1]))
            rotated_local.append(self.rotate_point_2d(global_vector, local_vector, self.rotate_local[2]))

            # Now line up on the other side of the triangle formed by the three datum points
            local_vector = self.normalize_vector(self.vector_subtract(rotated_local[2], rotated_local[0]))
            global_vector = self.normalize_vector(self.vector_subtract(self.rotate_global[2], self.rotate_global[0]))
            p_out2 = self.rotate_point_2d(global_vector, local_vector, p_out)

            # Finish the rotation for the local datums as well (not strictly needed for points 2 and 3)
            rotated_local[0] = self.rotate_point_2d(global_vector, local_vector, rotated_local[0])
            rotated_local[1] = self.rotate_point_2d(global_vector, local_vector, rotated_local[1])
            rotated_local[2] = self.rotate_point_2d(global_vector, local_vector, rotated_local[2])

            # Now align the starting points of each grid systems by shifting the first datum points onto each other
            datum_diff = self.vector_subtract(self.rotate_global[0], rotated_local[0])
            result = self.translate_point(datum_diff, p_out2)

            return(result)

        else:
            return(None)

    def rotate_initialize(self, local_datums, global_datums):
        # local and global datums are two lists of three corresponding points in the two grid systems

        self.rotate_local = local_datums
        self.rotate_global = global_datums


#endregion

class MainScreen(e5_MainScreen):

    popup = ObjectProperty(None)
    popup_open = False
    text_color = (0, 0, 0, 1)

    def __init__(self, data = None, cfg = None, ini = None, colors = None, station = None, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        self.colors = colors if colors else ColorScheme()
        self.ini = ini if ini else INI()
        self.data = data if data else DB()
        self.cfg = cfg 
        self.station = station if station else totalstation()

        self.layout = BoxLayout(orientation = 'vertical',
                                size_hint_y = .9,
                                size_hint_x = .8,
                                pos_hint={'center_x': .5},
                                id = 'mainscreen',
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

        self.info = Label(text = 'EDM',
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
                                    id = 'option_buttons',
                                    spacing = 20)
        self.layout.add_widget(scroll_content)

        button_count = 0
        button_text = []
        button_selected = []
        for button_no in range(1,7):
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
        
        shot_buttons.add_widget(e5_button(text = 'Record', id = 'record',
                        colors = self.colors, call_back = self.take_shot, selected = True))

        shot_buttons.add_widget(e5_button(text = 'Continue', id = 'continue',
                        colors = self.colors, call_back = self.take_shot, selected = True))

        shot_buttons.add_widget(e5_button(text = 'Measure', id = 'measure',
                        colors = self.colors, call_back = self.take_shot, selected = True))

        self.layout.add_widget(shot_buttons)

    def take_shot(self, instance):
        
        self.station.shot_type = instance.id
        if self.station.make == 'Microscribe':
            self.popup = DataGridTextBox(title = 'EDM',
                                            label = 'Waiting on Microscribe...',
                                            button_text = ['Cancel', 'Next'],
                                            call_back = self.have_shot)
        else:
            self.station.take_shot()
            self.popup = DataGridMenuList(title = "Prism Height",
                                            menu_list = self.data.names('prisms'),
                                            menu_selected = '',
                                            call_back = self.have_shot)
        self.popup.open()

    def have_shot(self, instance):
        if self.station.shot_type == 'measure':
            result = self.popup.result
            self.popup.dismiss()
            if result:
                p = self.station.text_to_point(result)
                if p:
                    p.x = p.x / 1000
                    p.y = p.y / 1000
                    p.z = p.z / 1000
                    self.station.xyz = p
                    if len(self.station.rotate_local) == 3 and len(self.station.rotate_global) == 3:
                        self.station.xyz_global = self.station.rotate_point(p)
                    else:
                        self.station.xyz_global = p

                    self.station.xyz_global.x = round(self.station.xyz_global.x, 3)
                    self.station.xyz_global.y = round(self.station.xyz_global.y, 3)
                    self.station.xyz_global.z = round(self.station.xyz_global.z, 3)

                    self.station.xyz.x = round(self.station.xyz.x, 3)
                    self.station.xyz.y = round(self.station.xyz.y, 3)
                    self.station.xyz.z = round(self.station.xyz.z, 3)

                    txt = 'Local coordinates:\n  X: %s\n  Y: %s\n  Z: %s' % (self.station.xyz.x, self.station.xyz.y, self.station.xyz.z)
                    txt += '\n\nGlobal coordinates:\n  X: %s\n  Y: %s\n  Z: %s' % (self.station.xyz_global.x, self.station.xyz_global.y, self.station.xyz_global.z)
                    self.popup = e5_MessageBox('Measurement', txt,
                                            response_type = "OK",
                                            call_back = self.close_popup,
                                            colors = self.colors)
                    self.popup.open()
        else:
            self.popup.dismiss()
            self.add_record()
            #self.station.prism = self.data.prisms.get(value.text).height 
            self.parent.current = 'EditPointScreen'

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

    def add_record(self):
        new_record = {}
        fields = self.cfg.fields()
        for field in fields:
            if field == 'X':
                new_record['X'] = self.station.x
            elif field == 'Y':
                new_record['Y'] = self.station.y
            elif field == 'Z':
                new_record['Z'] = self.station.z
            elif field == 'PRISM':
                new_record['PRISM'] = self.station.prism
            elif field == 'DATE':
                new_record['DATE'] = '%s' % datetime.now().replace(microsecond=0)
        unitname = self.data.point_in_unit(self.station.xyz)
        if unitname and "UNIT" in fields:
            new_record['UNIT'] = unitname
        self.data.db.table(self.data.table).insert(new_record)

class VerifyStationScreen(Screen):

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
                                id = 'content',
                                padding = 20,
                                spacing = 20)
        self.add_widget(self.content)

        self.content.add_widget(e5_label('Select a datum to use as verification and record it.', colors = self.colors))

        self.datum1 = datum_selector(text = 'Select\nverification\ndatum',
                                            data = self.data,
                                            colors = self.colors,
                                            default_datum = self.data.get_datum(self.ini.get_value('SETUPS', 'VERIFICATION')))
        self.content.add_widget(self.datum1)

        self.recorder = datum_recorder('Record\nverification\ndatum', station = self.station, colors = self.colors, setup_type = 'verify')
        self.content.add_widget(self.recorder)

        self.results = e5_label('', colors = self.colors)
        self.content.add_widget(self.results)

        self.back_button = e5_button(text = 'Back', size_hint_y = None, size_hint_x = 1, id = 'cancel',
                        colors = self.colors, selected = True)
        self.content.add_widget(self.back_button)
        self.back_button.bind(on_press = self.close_screen)


    def close_screen(self, instance):
        self.parent.current = 'MainScreen'
        
class record_button(e5_button):

    popup = ObjectProperty(None)

    def __init__(self, station = None, result_label = None, setup_type = None, **kwargs):
        super(record_button, self).__init__(**kwargs)
        self.station = station
        self.bind(on_press = self.record_datum)
        self.result_label = result_label
        self.setup_type = setup_type

    def record_datum(self, instance):
        if self.id == 'datum1' and self.setup_type in ['Over a datum + Record a datum','Record two datums']:
            self.station.set_horizontal_angle(0)
        self.station.take_shot()
        self.wait_for_shot()

    def wait_for_shot(self):
        if self.station.make == 'Microscribe':
            #self.popup = DataGridTextBox(title = self.text + '.  Waiting on Microscribe...', button_text = ['Cancel', 'Next'], call_back = self.microscribe)
            self.popup = DataGridTextBox(title = 'EDM',
                                            label = self.text + '.  Waiting on Microscribe...',
                                            button_text = ['Cancel', 'Next'],
                                            call_back = self.microscribe)
            self.popup.open()

    def microscribe(self, instance):
        result = self.popup.result
        self.popup.dismiss()
        if result:
            try:
                if len(result.split(',')) == 3:
                    x, y, z = result.split(',')
                    x = round(float(x) / 1000, 3) 
                    y = round(float(y) / 1000, 3) 
                    z = round(float(z) / 1000, 3)
                    self.station.xyz = point(x, y, z)
                    self.have_shot()
            except:
                self.popup = e5_MessageBox(title = 'Error', message = '\nError.  Data not formatted correctly.  EDM expects three floating point numbers separated by commas.')
                self.popup.open()

    def have_shot(self):
        if self.station.xyz:
            self.result_label.text = 'X: %s\nY: %s\nZ: %s' % (self.station.xyz.x,
                                                        self.station.xyz.y,
                                                        self.station.xyz.z)
            self.result_label.xyz = self.station.xyz
        else:
            self.result_label.text = 'Recording error.'
            self.result_label.xyz = None

class record_result(e5_label):
    xyz = None

class datum_recorder(GridLayout):

    def __init__(self, text = '', datum_no = 1, station = None, colors = None, setup_type = None, **kwargs):
        super(datum_recorder, self).__init__(**kwargs)
        self.padding = 10
        self.spacing = 10
        self.colors = colors
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
                                    setup_type = setup_type)
        self.add_widget(self.button)
        self.add_widget(self.result)
       
class datum_selector(GridLayout):
    
    datum = None
    popup = ObjectProperty(None)
    popup_open = False

    def __init__(self, text = '', data = None, colors = None, default_datum = None, **kwargs):
        super(datum_selector, self).__init__(**kwargs)
        #self.orientation = 'horizontal'
        self.padding = 10
        self.spacing = 10
        self.cols = 2
        self.colors = colors
        self.data = data
        self.datum = default_datum
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
        else:
            self.result.text = 'Search error'

class setups(ScrollView):

    popup = ObjectProperty(None)
    popup_open = False
    recorder = []

    def __init__(self, setup_type, data = None, ini = None, station = None, colors = None, **kwargs):
        super(setups, self).__init__(**kwargs)

        self.colors = colors if colors else ColorScheme()
        self.data = data
        self.station = station
        self.ini = ini

        y_sizes = {"Horizontal Angle Only" : 1.2,
                    "Over a datum": 1.1,
                    "Over a datum + Record a datum" : 1.6,
                    "Record two datums" : 2.6,
                    "Three datum shift" : 6.0}
        
        self.scrollbox = GridLayout(cols = 1,
                                size_hint_y = None,
                                id = 'setups_box',
                                spacing = 5)
        self.scrollbox.bind(minimum_height = self.scrollbox.setter('height'))

        instructions = Label(color = self.colors.text_color, size_hint_y = None)

        if setup_type == "Horizontal Angle Only":
            instructions.text = 'Enter the angle to be uploaded to the station.'
            self.scrollbox.add_widget(instructions)

            content1 = BoxLayout(orientation = 'horizontal', padding = 10)
            content1.add_widget(e5_label('Horizontal angle to the point\n(use ddd.mmss)'))
            self.hangle = TextInput(text = '', multiline = False, id = 'h_angle')
            content1.add_widget(self.hangle)
            self.scrollbox.add_widget(content1)

            content2 = BoxLayout(orientation = 'horizontal', padding = 10)
            content2.add_widget(e5_button(text = 'Upload angle', selected = True, call_back = self.set_hangle))
            self.scrollbox.add_widget(content2)

        elif setup_type == "Over a datum":
            instructions.text = 'Enter select the datum point under the station and enter the station height.  Note this option assumes the horizontal angle is already correct or will be otherwise set.'
            self.scrollbox.add_widget(instructions)

            self.over_datum = datum_selector(text = 'Select the datum\nunder the station',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', 'OVERDATUM')))
            self.scrollbox.add_widget(self.over_datum)

            content2 = BoxLayout(orientation = 'horizontal', padding = 10)
            content2.add_widget(e5_label('Height over datum'))
            self.station_height = TextInput(text = '', multiline = False,
                                            id = 'station_height')
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
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', 'RECORDDATUM')))
            self.scrollbox.add_widget(self.datum2)
            
            self.recorder = datum_recorder('Record datum', station = self.station, colors = self.colors, setup_type = setup_type)
            self.scrollbox.add_widget(self.recorder)

        elif setup_type == "Record two datums":
            instructions.text = "Select two datums to record. EDM will use triangulation to compute the station's XYZ coordinates."
            self.scrollbox.add_widget(instructions)

            self.datum1 = datum_selector(text = 'Select first datum\nto record',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', '2DATUMS_DATUM_1')))
            self.scrollbox.add_widget(self.datum1)

            self.datum2 = datum_selector(text = 'Select second datum\nto record',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', '2DATUMS_DATUM_2')))
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
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', '3DATUM_SHIFT_DATUM_1')))
            self.scrollbox.add_widget(self.datum1)

            self.datum2 = datum_selector(text = 'Select datum 2',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', '3DATUM_SHIFT_DATUM_2')))
            self.scrollbox.add_widget(self.datum2)

            self.datum3 = datum_selector(text = 'Select datum 3',
                                                data = self.data,
                                                colors = self.colors,
                                                default_datum = self.data.get_datum(self.ini.get_value('SETUPS', '3DATUM_SHIFT_DATUM_1')))
            self.scrollbox.add_widget(self.datum3)

            for n in range(3):
                self.recorder.append(datum_recorder('Record datum', datum_no = n + 1, station = station, colors = colors, setup_type = setup_type))
                self.scrollbox.add_widget(self.recorder[n])
            
        instructions.bind(texture_size = lambda instance, value: setattr(instance, 'height', value[1]))
        instructions.bind(width = lambda instance, value: setattr(instance, 'text_size', (value * .95, None)))
        
        self.size_hint = (1, None)
        self.size = (Window.width, Window.height / 2)
        self.id = 'setup_scroll'
        self.add_widget(self.scrollbox)

        def draw_background(widget, prop):
            with widget.canvas.before:
                Color(0.8, 0.8, 0.8, 1)
                Rectangle(size=self.size, pos=self.pos)

        self.bind(size = draw_background)
        self.bind(pos = draw_background)

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
                                size_hint_x = .8,
                                pos_hint={'center_x': .5},
                                id = 'content',
                                padding = 20,
                                spacing = 20)
        self.add_widget(self.content)

        setup_type_box = GridLayout(cols = 2, size_hint = (1, .2))
        setup_type_box.add_widget(e5_label('Setup type', colors = self.colors))
        self.setup_type = Spinner(text = self.setup,
                                    values=["Horizontal Angle Only",
                                            "Over a datum",
                                            "Over a datum + Record a datum",
                                            "Record two datums",
                                            "Three datum shift"],
                                    id = 'setup_type',
                                    size_hint = (.7, None)
                                    #pos_hint = {'center_x': .5, 'center_y': .5},
                                    )
        setup_type_box.add_widget(self.setup_type)
        self.setup_type.bind(text = self.rebuild)
        self.content.add_widget(setup_type_box)

        self.scroll_content = BoxLayout(orientation = 'vertical', size_hint = (1, .6),
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
                                                        selected = [True, True]))

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
                last = self.data_table.all()[-1]
                self.doc_id = last.doc_id
            except:
                self.doc_id = None
        self.put_data_in_frame()

class EditPointScreen(e5_RecordEditScreen):

    def on_pre_enter(self):
        if self.data_table is not None and self.e5_cfg is not None:
            try:
                last = self.data_table.all()[-1]
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

class station_setting(GridLayout):
    def __init__(self, label_text = '', spinner_values = (), default = '',
                        id = None, call_back = None, colors = None, **kwargs):
        super(station_setting, self).__init__(**kwargs)

        self.cols = 2
        self.size_hint_max_x = 300

        label = e5_label(text = label_text, colors = colors)
        self.add_widget(label)
        
        spinner = Spinner(text = default if default is not None else '', values = spinner_values,
                                    id = id)
        self.add_widget(spinner)
        spinner.bind(text = call_back)

class StationConfigurationScreen(Screen):

    def __init__(self, station = None, ini = None, colors = None, **kwargs):
        super(StationConfigurationScreen, self).__init__(**kwargs)

        self.station = station
        self.colors = colors
        self.ini = ini

        self.layout = GridLayout(cols = 1, spacing = 5, col_default_width = 600)
        self.add_widget(self.layout)

        self.build_screen()

    def build_screen(self):
        self.layout.clear_widgets()
        self.layout.add_widget(station_setting(label_text = 'Station type',
                                            spinner_values = ("Leica", "Wild", "Topcon", "Microscribe", "Simulate"),
                                            call_back = self.update_ini,
                                            id = 'station_type',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'STATION')))
        self.layout.add_widget(station_setting(label_text = 'Communications',
                                            spinner_values = ("Serial", "Bluetooth"),
                                            call_back = self.update_ini,
                                            id = 'communications',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'COMMUNICATIONS')))
        self.layout.add_widget(station_setting(label_text = 'Port Number',
                                            spinner_values = ("COM1", "COM2","COM3","COM4","COM5","COM6"),
                                            call_back = self.update_ini,
                                            id = 'comport',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'COMPORT')))
        self.layout.add_widget(station_setting(label_text = 'Baud rate',
                                            spinner_values = ("1200", "2400","4800","9600"),
                                            call_back = self.update_ini,
                                            id = 'baudrate',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'BAUDRATE')))
        self.layout.add_widget(station_setting(label_text = 'Parity',
                                            spinner_values = ("Even", "Odd","None"),
                                            call_back = self.update_ini,
                                            id = 'parity',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'PARITY')))
        self.layout.add_widget(station_setting(label_text = 'Databits',
                                            spinner_values = ("7", "8"),
                                            call_back = self.update_ini,
                                            id = 'databits',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'DATABITS')))
        self.layout.add_widget(station_setting(label_text = 'Stopbits',
                                            spinner_values = ("0","1","2"),
                                            call_back = self.update_ini,
                                            id = 'stopbits',
                                            colors = self.colors,
                                            default = self.ini.get_value(__program__, 'STOPBITS')))

        button2 = e5_button(text = 'Back', size_hint_y = None, size_hint_x = 1, id = 'cancel',
                        colors = self.colors, selected = True)
        self.layout.add_widget(button2)
        button2.bind(on_press = self.close_screen)
        self.changes = False

    def update_ini(self, instance, value):
        if instance.id == 'stopbits':
            self.station.stopbits = value
            self.ini.update_value(__program__, 'STOPBITS', value)
        elif instance.id == 'baudrate':
            self.station.baudrate = value
            self.ini.update_value(__program__, 'BAUDRATE', value)
        elif instance.id == 'databits':
            self.station.databits = value
            self.ini.update_value(__program__, 'DATABITS', value)
        elif instance.id == 'comport':
            self.station.comport = value
            self.ini.update_value(__program__, 'COMPORT', value)
        elif instance.id=='parity':
            self.station.parity = value
            self.ini.update_value(__program__, 'PARITY', value)
        elif instance.id=='communications':
            self.station.communications = value
            self.ini.update_value(__program__, 'COMMUNICATIONS', value)
        elif instance.id=='station_type':
            self.station.make = value
            self.ini.update_value(__program__, 'STATION', value)
        self.changes = True

    def close_screen(self, value):
        if self.changes:
            self.ini.save()
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
        self.content.text = txt
        self.content.color = self.colors.text_color
        self.back_button.background_color = self.colors.button_background
        self.back_button.color = self.colors.button_color


#endregion

sm = ScreenManager(id = 'screen_manager')

class EDMApp(e5_Program):

    def __init__(self, **kwargs):
        super(EDMApp, self).__init__(**kwargs)

        self.colors = ColorScheme()
        self.ini = INI()
        self.cfg = CFG()
        self.data = DB()
        self.station = totalstation()

        self.app_path = self.user_data_dir
        self.setup_logger()
        self.setup_program()
        self.station.setup(self.ini, self.data)

    def setup_logger(self):
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh = logging.FileHandler(os.path.join(self.app_path, __program__ + '.log'))
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    def add_screens(self):
        sm.add_widget(MainScreen(name = 'MainScreen', id = 'main_screen',
                                 colors = self.colors,
                                 ini = self.ini,
                                 cfg = self.cfg,
                                 data = self.data,
                                 station = self.station))

        sm.add_widget(VerifyStationScreen(name = 'VerifyStationScreen', id = 'verify_station',
                                            data = self.data,
                                            station = self.station,
                                            colors = self.colors,
                                            ini = self.ini))

        sm.add_widget(EditLastRecordScreen(name = 'EditLastRecordScreen', id = 'editlastrecord_screen',
                                        data_table = self.data.db.table(self.data.table),
                                        doc_id = None,
                                        e5_cfg = self.cfg))

        sm.add_widget(EditPointScreen(name = 'EditPointScreen', id = 'editpoint_screen',
                                        data_table = self.data.db.table(self.data.table),
                                        doc_id = None,
                                        e5_cfg = self.cfg,
                                        one_record_only = True))

        sm.add_widget(EditPointsScreen(name = 'EditPointsScreen', id = 'editpoints_screen',
                                        colors = self.colors,
                                        main_data = self.data,
                                        main_tablename = self.data.table,
                                        main_cfg = self.cfg))

        datum_cfg = CFG()
        datum_cfg.build_datum()
        sm.add_widget(EditPointsScreen(name = 'EditDatumsScreen', id = 'editdatums_screen',
                                        colors = self.colors,
                                        main_data = self.data,
                                        main_tablename = 'datums',
                                        main_cfg = datum_cfg,
                                        addnew = True))

        prism_cfg = CFG()
        prism_cfg.build_prism()
        sm.add_widget(EditPointsScreen(name = 'EditPrismsScreen', id = 'editprisms_screen',
                                        colors = self.colors,
                                        main_data = self.data,
                                        main_tablename = 'prisms',
                                        main_cfg = prism_cfg,
                                        addnew = True))

        units_cfg = CFG()
        units_cfg.build_unit()
        sm.add_widget(EditPointsScreen(name = 'EditUnitsScreen', id = 'editunits_screen',
                                        colors = self.colors,
                                        main_data = self.data,
                                        main_tablename = 'units',
                                        main_cfg = units_cfg,
                                        addnew = True))

        sm.add_widget(StatusScreen(name = 'StatusScreen', id = 'status_screen',
                                    colors = self.colors,
                                    cfg = self.cfg,
                                    ini = self.ini,
                                    data = self.data,
                                    station = self.station))

        sm.add_widget(e5_LogScreen(name = 'LogScreen', id = 'log_screen',
                                colors = self.colors,
                                logger = logger))

        sm.add_widget(e5_CFGScreen(name = 'CFGScreen', id = 'cfg_screen',
                                colors = self.colors,
                                cfg = self.cfg))

        sm.add_widget(e5_INIScreen(name = 'INIScreen', id = 'ini_screen',
                                colors = self.colors,
                                ini = self.ini))

        sm.add_widget(AboutScreen(name = 'AboutScreen', id = 'about_screen',
                                    colors = self.colors))

        sm.add_widget(StationConfigurationScreen(name = 'StationConfigurationScreen', id = 'station_configuration_screen',
                                    station = self.station,
                                    ini = self.ini,
                                    colors = self.colors))

        sm.add_widget(InitializeStationScreen(name = 'InitializeStationScreen', id = 'initialize_station_screen',
                                                data = self.data,
                                                station = self.station,
                                                ini = self.ini,
                                                colors = self.colors))

        sm.add_widget(e5_SettingsScreen(name = 'EDMSettingsScreen', id = 'edmsettings_screen',
                                        colors = self.colors,
                                        ini = self.ini,
                                        cfg = self.cfg))

    def build(self):
        self.add_screens()
        restore_window_size_position(__program__, self.ini)
        self.title = __program__ + " " + __version__
        logger.info(__program__ + ' started, logger initialized, and application built.')
        sm.screens[0].build_mainscreen()
        return(sm)

Factory.register(__program__, cls=EDMApp)

if __name__ == '__main__':
    logger = logging.getLogger(__program__)
    EDMApp().run()