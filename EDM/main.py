
# Need a read and write ini to be able to easily resume the program
# Then start working on the flow for more complex setups
# Add serial port communications
# Add bluetooth communications

__program__ = 'EDM'
__version__ = '1.0.1'
__date__ = 'April, 2019'

#Region Imports
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
class points(dbs):
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

    def status(self):
        txt = 'The points file is %s\n' % self.filename
        txt += '%s points in the data file\n' % len(self.db)
        txt += 'with %s fields per point' % self.field_count()
        return(txt)

    def create_defaults(self):
        pass

    def get(self, name):
        unit, id = name.split('-')
        p = self.db.search( (where('unit')==unit) & (where('id')==id) )
        if p:
            return(p)
        else:
            return(None)

    def names(self):
        name_list = []
        for row in self.db:
            name_list.append(row['unit'] + '-' + row['id'])
        return(name_list)

    def fields(self):
        global edm_cfg 
        return(edm_cfg.fields())

    def delete_all(self):
        self.db.purge()

    def export_csv(self):
        pass

    def delete_record(self):
        pass

    def add_record(self):
        pass

class datums(dbs):
    MAX_DATUMS = 100
    db = None
    db_name = 'datums'

    class datum:
        name = ''
        x = 0
        y = 0
        z = 0
        date_created = ''
        def __init__(self, name, x, y, z, date_created):
            self.name = name
            self.x = x
            self.y = y
            self.z = z
            self.date_created = date_created
    
    def __init__(self, db = None):
        self.db = db

    def open(self, db):
        self.db = db

    def add(self, datum):
        new_data = {}
        new_data['name'] = datum.name
        new_data['x'] = datum.x
        new_data['y'] = datum.y
        new_data['z'] = datum.z
        new_data['date_created'] = datum.date_created
        self.db.insert(new_data)

    def get(self, name):
        d = self.db.search(where('name')==name)
        if d:
            return(self.datum(d[0]['name'], d[0]['x'], d[0]['y'], d[0]['z'], d[0]['date_created']))
        else:
            return(None)

    def delete(self, name):
        pass

    def fields(self):
        return(['name','x','y','z','date_created'])

class prisms(dbs):
    MAX_PRISMS = 20
    db = None
    db_name = 'prisms'

    class prism:
        name = None
        offset = 0
        height = 0
        def __init__(self, name, height, offset = 0):
            self.name = name
            self.height = height
            self.offset = offset

    def __init__(self, db = None):
        self.db = db
    
    def open(self, db):
        self.db = db

    def add(self, prism):
        new_data = {}
        new_data['name'] = prism.name
        new_data['height'] = prism.height
        new_data['offset'] = prism.offset
        self.db.insert(new_data)

    def get(self, name):
        p = self.db.search(where('name')==name)
        if p:
            return(self.prism(p[0]['name'], p[0]['height'], p[0]['offset']))
        else:
            return(None)

    def delete(self, name):
        pass

    def fields(self):
        return(['name','height','offset'])

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

class units(dbs):
    MAX_UNITS = 100
    db = None
    db_name = 'units'

    class unit:
        name = ''
        x1 = 0
        y1 = 0
        x2 = 0
        y2 = 0
        radius = None
        def __init__(self, name, x1, y1, x2, y2, radius = 0):
            self.name = name
            self.x1 = x1
            self.y1 = y1
            self.x2 = x2
            self.y2 = y2
            self.radius = radius
 
    def __init__(self, db = None):
        self.db = db

    def open(self, db):
        self.db = db

    def point_in(self, x, y, z):
        for unit_name in self.db.names():
            unit = self.get(unit_name)
            if x<=unit.x2 and x>=unit.x1 and y<=unit.y2 and y>=unit.y1:
                return(unit)
        return(None)

    def add(self, unit):
        new_data = {}
        new_data['name'] = unit.name
        new_data['x1'] = unit.x1
        new_data['y1'] = unit.y1
        new_data['x2'] = unit.x2
        new_data['y2'] = unit.y2
        new_data['radius'] = unit.radius
        self.db.insert(new_data)

    def put(self, unit):
        new_data = {}
        new_data['x1'] = unit.x1
        new_data['x2'] = unit.x2
        new_data['y1'] = unit.y1
        new_data['y2'] = unit.y2
        new_data['radius'] = unit.radius
        unit_record = Query()
        edm_points.db.update(new_data, (unit_record.name == unit.name))

    def get(self, unit_name):
        u = self.db.search(where('name')==unit_name)
        if u:
            return(self.unit(u[0]['name'],
             u[0]['x1'], u[0]['y1'],
             u[0]['x2'], u[0]['y2'],
             u[0]['radius']))
        else:
            return(None)

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

    def delete(self, unit_name):
        pass

    def fields(self):
        return(['name','x1','y1','x2','y2','radius'])

class ini(blockdata):
    
    blocks = []
    filename = ''

    def __init__(self, filename = ''):
        if filename=='':
            filename = 'E5.ini'
        self.filename = filename
        self.incremental_backups = False
        self.backup_interval = 0
        self.first_time = True

    def open(self, filename = ''):
        if filename:
            self.filename = filename
        self.blocks = self.read_blocks()
        self.first_time = (self.blocks == [])
        self.is_valid()
        self.incremental_backups = self.get_value('EDM','IncrementalBackups').upper() == 'TRUE'
        self.backup_interval = int(self.get_value('EDM','BackupInterval'))

    def is_valid(self):
        for field_option in ['DARKMODE','INCREMENTALBACKUPS']:
            if self.get_value('EDM',field_option):
                if self.get_value('EDM',field_option).upper() == 'YES':
                    self.update_value('EDM',field_option,'TRUE')
            else:
                self.update_value('EDM',field_option,'FALSE')

        if self.get_value('EDM', "BACKUPINTERVAL"):
            test = False
            try:
                test = int(self.get_value('EDM', "BACKUPINTERVAL"))
                if test < 0:
                    test = 0
                elif test > 200:
                    test = 200
                self.update_value('EDM', 'BACKUPINTERVAL', test)
            except:
                self.update_value('EDM', 'BACKUPINTERVAL', 0)
        else:
            self.update_value('EDM', 'BACKUPINTERVAL', 0)

    def update(self, edm_station, edm_cfg):
        self.update_value('STATION','TotalStation', edm_station.make)
        self.update_value('STATION','Communication', edm_station.communication)
        self.update_value('STATION','COMPort', edm_station.comport)
        self.update_value('STATION','BAUD', edm_station.baudrate)
        self.update_value('STATION','Parity', edm_station.parity)
        self.update_value('STATION','DataBits', edm_station.databits)
        self.update_value('STATION','StopBits', edm_station.stopbits)
        self.update_value('EDM','CFG', edm_cfg.filename)
        self.save()

    def save(self):
        self.write_blocks()

class cfg(blockdata):

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

    def load(self, filename):
        self.filename = filename 
        self.blocks = self.read_blocks()
        if self.blocks==[]:
            self.build_default()
    
    def status(self):
        txt = 'CFG file is %s\n' % self.filename
        return(txt)

class totalstation:
    def __init__(self, make = "Emulation", model = ''):
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
        self.current_x = 0
        self.current_y = 0
        self.current_z = 0
        self.x = 0
        self.y = 0
        self.z = 0
        self.prism = 0
        self.hangle = ''
        self.vangle = ''
        self.sloped = 0
        self.suffix = 0
        self.prism = 0

    def status(self):
        txt = 'Total Station:\n'
        txt += 'Make is %s\n' % self.make
        txt += 'Communication type is %s\n' % self.communication
        txt += 'COM Port is %s\n' % self.comport
        txt += 'Com settings are %s, %s, %s, %s\n' % (self.baudrate,self.parity,self.databits,self.stopbits)
        if self.port_open:
            txt += 'COM Port is open\n'
        else:
            txt += 'COM port is closed\n'
        txt += 'Station X : %s\n' % self.current_x
        txt += 'Station Y : %s\n' % self.current_y
        txt += 'Station Z : %s\n' % self.current_z

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
        if self.make=='TOPCON':
            clearcom()
            edm_output("Z34")   # Slope angle mode
            edm_input
            delay(0.5)

            edm_output("C")     # Take the shot
            edm_input()
            delay(0.5)

        if self.make=="WILD" or self.make=="LEICA":
            clear_com()
            edm_output("GET/M/WI11/WI21/WI22/WI31/WI51")

        if self.make=="SOKKIA":
            edm_output(Chr(17))

        if self.make == 'Emulation':
            self.x = random.uniform(1000, 1010)
            self.y = random.uniform(1000, 1010)
            self.z = random.uniform(0, 1)
            
    def set_horizontal_angle(angle):
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

class EditDatums(Screen):
    pass

#endregion

class MainScreen(Screen):

    popup = ObjectProperty(None)
    popup_open = False
    text_color = (0, 0, 0, 1)

    def __init__(self, edm_points = None, edm_cfg = None, edm_ini = None, colors = None, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        self.colors = colors if colors else ColorScheme()
        self.edm_cfg = edm_cfg if edm_cfg else cfg()
        self.edm_ini = edm_ini if edm_ini else ini()
        self.edm_points = edm_points if edm_points else points()

        layout = GridLayout(cols = 3, spacing = 10, size_hint_y = .8)
        button_count = 0

        for button_no in range(1,7):
            if edm_cfg.get_value('BUTTON' + str(button_no), 'TITLE'):
                layout.add_widget(e5_button(text = edm_cfg.get_value('BUTTON' + str(button_no), 'TITLE'),
                                             id = 'button' + str(button_no),
                                             call_back = self.take_shot))
                button_count += 1

        if button_count % 3 !=0:
            button_empty = Button(text = '', size_hint_y = None, id = '',
                            color = self.colors.window_background,
                            background_color = self.colors.window_background,
                            background_normal = '')
            layout.add_widget(button_empty)

        if button_count % 3 == 2:
            layout.add_widget(button_empty)
            
        layout.add_widget(e5_button(text = 'Record', id = 'record',
                        colors = self.colors, call_back = self.take_shot))

        layout.add_widget(e5_button(text = 'Continue', id = 'continue',
                        colors = self.colors, call_back = self.take_shot))

        layout.add_widget(e5_button(text = 'Measure', id = 'measure',
                        colors = self.colors, call_back = self.take_shot))

        self.add_widget(layout)

    def take_shot(self, value):
        
        edm_station.take_shot()

        layout_popup = GridLayout(cols = 1, spacing = 10, size_hint_y = None)
        layout_popup.bind(minimum_height=layout_popup.setter('height'))
        for prism in edm_prisms.names():
            button1 = Button(text = prism, size_hint_y = None, id = prism,
                        color = OPTIONBUTTON_COLOR,
                        background_color = OPTIONBUTTON_BACKGROUND,
                        background_normal = '')
            layout_popup.add_widget(button1)
            button1.bind(on_press = self.show_edit_screen)
        button2 = Button(text = 'Back', size_hint_y = None,
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        layout_popup.add_widget(button2)
        root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height/1.9))
        root.add_widget(layout_popup)
        self._popup = Popup(title = 'Prism Height',
                    content = root,
                    size_hint = (None, None),
                    size = (400, 400),
                    #pos_hint = {None, None},
                    auto_dismiss = False)
        button2.bind(on_press = self._popup.dismiss)
        self._popup.open()

    def show_edit_screen(self, value):
        self._popup.dismiss()
        edm_station.prism = edm_prisms.get(value.text).height 
        self.parent.current = 'EditPointScreen'

    def show_save_csvs(self):
        if self.edm_cfg.filename and self.edm_data.filename:
            content = e5_SaveDialog(start_path = self.edm_cfg.path,
                                save = self.save_csvs, 
                                cancel = self.dismiss_popup,
                                button_color = self.colors.button_color,
                                button_background = self.colors.button_background)
            self.popup = Popup(title = "Select a folder for the  CSV files",
                                content = content,
                                size_hint = (0.9, 0.9))
        else:
            self.popup = e5_MessageBox('EDM', '\nOpen a CFG before exporting to CSV',
                                    call_back = self.dismiss_popup,
                                    colors = self.colors)
        self.popup.open()
        self.popup_open = True
        
    def show_load_cfg(self):
        if self.edm_cfg.filename and self.edm_cfg.path:
            start_path = self.edm_cfg.path
        else:
            start_path = self.edm_ini.get_value('EDM','APP_PATH')
        content = e5_LoadDialog(load = self.load, 
                            cancel = self.dismiss_popup,
                            start_path = start_path,
                            button_color = self.colors.button_color,
                            button_background = self.colors.button_background)
        self.popup = Popup(title = "Load CFG file", content = content,
                            size_hint = (0.9, 0.9))
        self.popup.open()

    def load(self, path, filename):
        self.edm_cfg.load(os.path.join(path, filename[0]))
        self.dismiss_popup()

    def dismiss_popup(self):
        self.popup.dismiss()
        self.parent.current = 'MainScreen'

class InitializeOnePointHeader(Label):
    pass

class InitializeDirectScreen(Screen):

    popup = ObjectProperty(None)

    def datum_list(self):
        layout_popup = GridLayout(cols = 1, spacing = 10, size_hint_y = None)
        layout_popup.bind(minimum_height=layout_popup.setter('height'))
        for datum in datums.names(EDMpy.edm_datums):
            button1 = Button(text = datum, size_hint_y = None, id = datum,
                        color = OPTIONBUTTON_COLOR,
                        background_color = OPTIONBUTTON_BACKGROUND,
                        background_normal = '')
            layout_popup.add_widget(button1)
            button1.bind(on_press = self.initialize_direct)
        button2 = Button(text = 'Cancel', size_hint_y = None,
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        layout_popup.add_widget(button2)
        root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height/1.9))
        root.add_widget(layout_popup)
        self.popup = Popup(title = 'Initial Direct',
                    content = root,
                    size_hint = (None, None),
                    size=(400, 400),
                    #pos_hint = {None, None},
                    auto_dismiss = False)
        button2.bind(on_press = self.popup.dismiss)
        self.popup.open()

    def initialize_direct(self, value):
        EDMpy.edm_station.X = EDMpy.edm_datums.datums[EDMpy.edm_datums.datums.Name==value.id].iloc[0]['X']
        EDMpy.edm_station.Y = EDMpy.edm_datums.datums[EDMpy.edm_datums.datums.Name==value.id].iloc[0]['X']
        EDMpy.edm_station.Z = EDMpy.edm_datums.datums[EDMpy.edm_datums.datums.Name==value.id].iloc[0]['X']
        self.popup.dismiss()
        self.parent.current = 'MainScreen'

class InitializeSetAngleScreen(Screen):
    def set_angle(self, foreshot, backshot):
        if foreshot:
            totalstation.set_horizontal_angle(foreshot)
        elif backshot:
            # flip angle 180
            totalstation.set_horizontal_angle(foreshot)
        self.parent.current = 'MainScreen'

class InitializeOnePointScreen(Screen):
    def __init__(self,**kwargs):
        super(InitializeOnePointScreen, self).__init__(**kwargs)
        self.add_widget(InitializeOnePointHeader())
        self.add_widget(DatumLister())

class InitializeTwoPointScreen(Screen):
    def __init__(self,**kwargs):
        super(InitializeTwoPointScreen, self).__init__(**kwargs)
        self.add_widget(InitializeOnePointHeader())
        self.add_widget(DatumLister())

class InitializeThreePointScreen(Screen):
    def __init__(self,**kwargs):
        super(InitializeThreePointScreen, self).__init__(**kwargs)
        self.add_widget(InitializeOnePointHeader())
        self.add_widget(DatumLister())

class EditPointScreen(Screen):

    global edm_cfg
    global edm_station
    global edm_prisms
    global edm_points

    popup = ObjectProperty(None)

    def on_pre_enter(self):
        #super(Screen, self).__init__(**kwargs)
        self.clear_widgets()
        layout = GridLayout(cols = 2, spacing = 10, size_hint_y = None, id = 'fields')
        layout.bind(minimum_height=layout.setter('height'))
        for field_name in edm_cfg.fields():
            f = edm_cfg.get(field_name)
            layout.add_widget(Label(text = field_name,
                                size_hint_y = None, color = BUTTON_COLOR))
            if field_name in ['SUFFIX','X','Y','Z','PRISM','DATE','VANGLE','HANGLE','SLOPED']:
                if field_name == 'SUFFIX':
                    layout.add_widget(Label(text = str(edm_station.suffix), id = 'SUFFIX',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'X':
                    layout.add_widget(Label(text = str(edm_station.x), id = 'X',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'Y':
                    layout.add_widget(Label(text = str(edm_station.y), id = 'Y',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'Z':
                    layout.add_widget(Label(text = str(edm_station.z), id = 'Z',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'SLOPED':
                    layout.add_widget(Label(text = str(edm_station.sloped), id = 'SLOPED',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'HANGLE':
                    layout.add_widget(Label(text = edm_station.hangle, id = 'HANGLE',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'VANGLE':
                    layout.add_widget(Label(text = edm_station.vangle, id = 'VANGLE',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'DATE':
                    layout.add_widget(Label(text = "%s" % datetime.datetime.now(), id = 'DATE',
                                        size_hint_y = None, color = BUTTON_COLOR))
                if field_name == 'PRISM':
                    prism_button = Button(text = str(edm_station.prism), size_hint_y = None,
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '',
                                    id = field_name)
                    layout.add_widget(prism_button)
                    prism_button.bind(on_press = self.show_menu)
            else:
                if f.inputtype == 'TEXT':
                    layout.add_widget(TextInput(multiline=False, id = field_name))
                if f.inputtype == 'NUMERIC':
                    layout.add_widget(TextInput(id = field_name))
                if f.inputtype == 'MENU':
                    button1 = Button(text = 'MENU', size_hint_y = None,
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '',
                                    id = field_name)
                    layout.add_widget(button1)
                    button1.bind(on_press = self.show_menu)
        button2 = Button(text = 'Save', size_hint_y = None,
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        layout.add_widget(button2)
        button2.bind(on_press = self.save)
        button3 = Button(text = 'Back', size_hint_y = None,
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        layout.add_widget(button3)
        root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        root.add_widget(layout)
        self.add_widget(root)

    def show_menu(self, value):
        if value.id!='PRISM':  
            self.popup = MenuList(value.id, edm_cfg.get(value.id).menu, self.menu_selection)
        else:
            self.popup = MenuList(value.id, edm_prisms.names(), self.prism_change)
        self.popup.open()

    def prism_change(self, value):
        edm_station.z = edm_station.z + edm_station.prism
        edm_station.prism = edm_prisms.get(value.text).height 
        edm_station.z = edm_station.z - edm_station.prism
        for child in self.walk():
            if child.id == value.id:
                child.text = str(edm_station.prism)
            if child.id == 'Z':
                child.text = str(edm_station.z)
        self.popup.dismiss()

    def menu_selection(self, value):
        for child in self.walk():
            if child.id == value.id:
                if value.text == 'Add':
                    for widget in self.popup.walk():
                        if widget.id == 'new_item':
                            child.text = widget.text
                            edm_cfg.update_value(value.id,'MENU',
                                                edm_cfg.get_value(value.id,'MENU') + "," + widget.text) 
                else:
                    child.text = value.text
        self.popup.dismiss()

    def save(self, value):
        new_record = {}
        for widget in self.walk():
            for f in edm_points.fields():
                if widget.id == f:
                    new_record[f] = widget.text
        valid = edm_cfg.valid_datarecord(new_record)
        if valid:
            edm_points.db.insert(new_record)
            edm_units.update_defaults(new_record)
            self.parent.current = 'MainScreen'
        else:
            self.popup = e5_MessageBox('Save Error', valid_record)
            self.popup.open()


class datumlist(RecycleView, Screen):
    def __init__(self, **kwargs):
        super(datumlist, self).__init__(**kwargs)
        self.data = [{'text': str(x)} for x in range(100)]

class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout):
    """ Adds selection and focus behaviour to the view. """
    selected_value = StringProperty('')
    btn_info = ListProperty(['Button 0 Text', 'Button 1 Text', 'Button 2 Text'])

class SelectableButton(RecycleDataViewBehavior, Button):
    """ Add selection support to the Label """
    index = None

    def refresh_view_attrs(self, rv, index, data):
        """ Catch and handle the view changes """
        self.index = index
        return super(SelectableButton, self).refresh_view_attrs(rv, index, data)

    def on_press(self):
        self.parent.selected_value = 'Selected: {}'.format(self.parent.btn_info[int(self.id)])

    def on_release(self):
        e5_MessageBox().open()

class RV(RecycleView):
    rv_layout = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.data = [{'text': "Datum " + str(x), 'id': str(x)} for x in range(30)]

class DatumLister(BoxLayout,Screen):
    def __init__(self, list_dicts=[], *args, **kwargs):

        super(DatumLister, self).__init__(*args, **kwargs)
        self.orientation = "vertical"
        self.add_widget(RV())

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

class StationConfigurationScreen(Screen):
    def __init__(self,**kwargs):
        super(StationConfigurationScreen, self).__init__(**kwargs)
    
        layout = GridLayout(cols = 2, spacing = 5)

        # Station type menu
        self.StationLabel = Label(text="Station type", color = WINDOW_COLOR)
        layout.add_widget(self.StationLabel)
        self.StationMenu = Spinner(text="Simulate", values=("Leica", "Wild", "Topcon", "Simulate"), id = 'station',
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '')
        self.StationMenu.size_hint  = (0.3, 0.2)
        layout.add_widget(self.StationMenu)

        # Communications type menu
        self.CommTypeLabel = Label(text="Communications", color = WINDOW_COLOR)
        layout.add_widget(self.CommTypeLabel)
        self.CommTypeMenu = Spinner(text="None", values=("Serial", "Bluetooth"), id = 'communications',
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '')
        self.CommTypeMenu.size_hint  = (0.3, 0.2)
        layout.add_widget(self.CommTypeMenu)

        # Port number
        self.PortNoLabel = Label(text="Port Number", color = WINDOW_COLOR)
        layout.add_widget(self.PortNoLabel)
        self.PortNoMenu = Spinner(text="COM1", values=("COM1", "COM2","COM3","COM4","COM5","COM6"), id = 'comport',
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '')
        self.PortNoMenu.size_hint  = (0.3, 0.2)
        layout.add_widget(self.PortNoMenu)

        # Speed
        self.SpeedLabel = Label(text="Speed", color = WINDOW_COLOR)
        layout.add_widget(self.SpeedLabel)
        self.SpeedMenu = Spinner(text="1200", values=("1200", "2400","4800","9600"), id = 'baudrate',
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '')
        self.SpeedMenu.size_hint  = (0.3, 0.2)
        layout.add_widget(self.SpeedMenu)

        # Parity
        self.ParityLabel = Label(text="Parity", color = WINDOW_COLOR)
        layout.add_widget(self.ParityLabel)
        self.ParityMenu = Spinner(text="Even", values=("Even", "Odd","None"), id = 'parity',
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '')
        self.ParityMenu.size_hint  = (0.3, 0.2)
        layout.add_widget(self.ParityMenu)

        # Databits
        self.DataBitsLabel = Label(text="Data bits", color = WINDOW_COLOR)
        layout.add_widget(self.DataBitsLabel)
        self.DataBitsMenu = Spinner(text="7", values=("7", "8"), id = 'databits',
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '')
        self.DataBitsMenu.size_hint  = (0.3, 0.2)
        layout.add_widget(self.DataBitsMenu)

        # Stopbits
        self.StopBitsLabel = Label(text="Stop bits", color = WINDOW_COLOR)
        layout.add_widget(self.StopBitsLabel)
        self.StopBitsMenu = Spinner(text="1", values=("0", "1", "2"), id = 'stopbits',
                                    color = OPTIONBUTTON_COLOR,
                                    background_color = OPTIONBUTTON_BACKGROUND,
                                    background_normal = '')
        self.StopBitsMenu.size_hint  = (0.3, 0.2)
        layout.add_widget(self.StopBitsMenu)

        button1 = Button(text = 'Save', size_hint_y = None, id = 'save',
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        layout.add_widget(button1)
        button1.bind(on_press = self.close_screen)
        button2 = Button(text = 'Back', size_hint_y = None, id = 'cancel',
                        color = BUTTON_COLOR,
                        background_color = BUTTON_BACKGROUND,
                        background_normal = '')
        layout.add_widget(button2)
        button2.bind(on_press = self.close_screen)

        self.add_widget(layout)

    def close_screen(self, instance):
        if instance.id=='save':
            for child in self.children[0].children:
                if child.id=='stopbits':
                    EDMpy.edm_station.stopbits = child.text
                if child.id=='baudrate':
                    EDMpy.edm_station.baudrate = child.text
                if child.id=='databits':
                    EDMpy.edm_station.databits = child.text
                if child.id=='comport':
                    EDMpy.edm_station.comport = child.text
                if child.id=='parity':
                    EDMpy.edm_station.parity = child.text
                if child.id=='communications':
                    EDMpy.edm_station.communications = child.text
                if child.id=='station':
                    EDMpy.edm_station.make = child.text
                ## need code to open com port here
        self.parent.current = 'MainScreen'

class EDMSettingsScreen(Screen):
    def __init__(self, edm_cfg = None, edm_ini = None, colors = None, **kwargs):
        super(EDMSettingsScreen, self).__init__(**kwargs)
        self.colors = colors if  colors else ColorScheme()
        self.edm_ini = edm_ini
        self.edm_cfg = edm_cfg

    def on_enter(self):
        self.build_screen()

    def build_screen(self):
        self.clear_widgets()
        layout = GridLayout(cols = 1,
                                size_hint_y = 1,
                                id = 'settings_box',
                                spacing = 5, padding = 5)
        layout.bind(minimum_height = layout.setter('height'))

        darkmode = GridLayout(cols = 2, size_hint_y = .1, spacing = 5, padding = 5)
        darkmode.add_widget(e5_label('Dark Mode', colors = self.colors))
        darkmode_switch = Switch(active = self.colors.darkmode)
        darkmode_switch.bind(active = self.darkmode)
        darkmode.add_widget(darkmode_switch)
        layout.add_widget(darkmode)

        colorscheme = GridLayout(cols = 2, size_hint_y = .6, spacing = 5, padding = 5)
        colorscheme.add_widget(e5_label('Color Scheme', colors = self.colors))
        colorscheme.add_widget(e5_scrollview_menu(self.colors.color_names(),
                                                  menu_selected = '',
                                                  call_back = self.color_scheme_selected))
        temp = ColorScheme()
        for widget in colorscheme.walk():
            if widget.id in self.colors.color_names():
                temp.set_to(widget.text)
                widget.background_color = temp.button_background
        layout.add_widget(colorscheme)
        
        backups = GridLayout(cols = 2, size_hint_y = .3, spacing = 5, padding = 5)
        backups.add_widget(e5_label('Auto-backup after\nevery %s\nrecords entered.' % self.edm_ini.backup_interval,
                                    id = 'label_backup_interval',
                                    colors = self.colors))
        slide = Slider(min = 0, max = 200,
                        value = self.edm_ini.backup_interval,
                        orientation = 'horizontal', id = 'backup_interval',
                        value_track = True, value_track_color= self.colors.button_background)
        backups.add_widget(slide)
        slide.bind(value = self.update_backup_interval)
        backups.add_widget(e5_label('Use incremental backups?', self.colors))
        backups_switch = Switch(active = self.e5_ini.incremental_backups)
        backups_switch.bind(active = self.incremental_backups)
        backups.add_widget(backups_switch)
        layout.add_widget(backups)

        settings_layout = GridLayout(cols = 1, size_hint_y = 1, spacing = 5, padding = 5)
        scrollview = ScrollView(size_hint = (1, 1),
                                 bar_width = SCROLLBAR_WIDTH)
        scrollview.add_widget(layout)
        settings_layout.add_widget(scrollview)

        self.back_button = e5_button('Back', selected = True,
                                             call_back = self.go_back,
                                             colors = self.colors)
        settings_layout.add_widget(self.back_button)
        self.add_widget(settings_layout)

    def update_backup_interval(self, instance, value):
        self.edm_ini.backup_interval = int(value)
        for widget in self.walk():
            if widget.id == 'label_backup_interval':
                widget.text = 'Auto-backup after\nevery %s\nrecords entered.' % self.edm_ini.backup_interval
                break

    def incremental_backups(self, instance, value):
        self.edm_ini.incremental_backups = value

    def darkmode(self, instance, value):
        self.colors.darkmode = value
        self.colors.set_colormode()
        self.build_screen()

    def color_scheme_selected(self, instance):
        self.colors.set_to(instance.text)
        self.back_button.background_color = self.colors.button_background
        self.back_button.color = self.colors.button_color
        
    def go_back(self, instance):
        self.edm_ini.update(self.colors, self.edm_cfg)
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

    def __init__(self, edm_points = None, edm_ini = None, edm_cfg = None, **kwargs):
        super(StatusScreen, self).__init__(**kwargs)
        self.edm_data = edm_points
        self.edm_ini = edm_ini
        self.edm_cfg = edm_cfg

    def on_pre_enter(self):
        txt = self.edm_data.status() if self.edm_data else 'A data file has not been initialized or opened.\n\n'
        txt += self.edm_cfg.status() if self.edm_cfg else 'A CFG is not open.\n\n'
        txt += self.edm_ini.status() if self.edm_ini else 'An INI file is not available.\n\n'
        txt += '\nThe default user path is %s.\n' % self.edm_ini.get_value("E5","APP_PATH")
        txt += '\nThe operating system is %s.\n' % platform_name()
        self.content.text = txt
        self.content.color = self.colors.text_color
        self.back_button.background_color = self.colors.button_background
        self.back_button.color = self.colors.button_color


#endregion

sm = ScreenManager(id = 'screen_manager')

class EDMApp(App):

    def __init__(self, **kwargs):
        super(EDMApp, self).__init__(**kwargs)

        app_path = self.user_data_dir

        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh = logging.FileHandler(os.path.join(app_path, __program__ + '.log'))
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        self.main_colors = ColorScheme()
        self.main_ini = ini()
        self.main_cfg = cfg()

        self.edm_station = totalstation()
        self.edm_points = points()
        self.edm_units = units()
        self.edm_prisms = prisms()
        self.edm_datums = datums()

        self.main_ini.open(os.path.join(app_path, __program__ + '.ini'))

        if not self.main_ini.first_time:
            if self.main_ini.get_value(__program__,'ColorScheme'):
                self.main_colors.set_to(self.main_ini.get_value(__program__,'ColorScheme'))
            if self.main_ini.get_value(__program__,'DarkMode').upper() == 'TRUE':
                self.main_colors.darkmode = True
            else:
                self.main_colors.darkmode = False

            if self.main_ini.get_value(__program__, "CFG"):
                self.main_cfg.open(self.main_ini.get_value(__program__, "CFG"))
                if self.main_cfg.filename:
                    if self.main_cfg.get_value(__program__,'DATABASE'):
                        self.edm_points.open(self.main_cfg.get_value(__program__,'DATABASE'))
                    else:
                        database = os.path.split(self.main_cfg.filename)[1]
                        if "." in database:
                            database = database.split('.')[0]
                        database = database + '.json'
                        self.edm_points.open(os.path.join(self.main_cfg.path, database))
                    if self.main_cfg.get_value(__program__,'TABLE'):    
                        self.edm_points.table = self.main_cfg.get_value(__program__,'TABLE')
                    else:
                        self.edm_points.table = '_default'
                    self.edm_datums.open(self.edm_points.db)
                    self.edm_prisms.open(self.edm_points.db)
                    self.edm_units.open(self.edm_points.db)
                    self.main_cfg.update_value(__program__,'DATABASE', self.edm_points.filename)
                    self.main_cfg.update_value(__program__,'TABLE', self.edm_points.table)
                    self.main_cfg.save()
            self.main_ini.update(self.main_colors, self.main_cfg)
            self.main_ini.save()
        self.main_colors.set_colormode()
        self.main_colors.need_redraw = False    
        self.main_ini.update_value(__program__,'APP_PATH', self.user_data_dir)

        #database = 'EDM'
        #self.edm_cfg = cfg(self.edm_ini.get_value("EDM", "CFG"))
        ##self.edm_points = points(database + '_points.json')
        ##if not self.edm_cfg.filename:
        #    self.edm_cfg.filename = 'EDM.cfg'
        #self.edm_cfg.save()
        #self.edm_ini.update(self.edm_station, self.edm_cfg)
        #self.edm_ini.save()

    def build(self):

        sm.add_widget(MainScreen(name = 'MainScreen', id = 'main_screen',
                                 colors = self.main_colors,
                                 edm_ini = self.main_ini,
                                 edm_cfg = self.main_cfg,
                                 edm_points = self.edm_points))

        sm.add_widget(EditPointsScreen(name = 'EditPointsScreen', id = 'editpoints_screen',
                                        colors = self.main_colors,
                                        main_data = self.edm_points,
                                        main_tablename = '_default',
                                        main_cfg = self.main_cfg))

        sm.add_widget(EditDatumsScreen(name = 'EditDatumsScreen', id = 'editdatums_screen',
                                        colors = self.main_colors,
                                        main_data = self.edm_datums,
                                        main_tablename = 'datums',
                                        main_cfg = self.main_cfg))

        sm.add_widget(EditPrismsScreen(name = 'EditPrismsScreen', id = 'editprisms_screen',
                                        colors = self.main_colors,
                                        main_data = self.edm_prisms,
                                        main_tablename = 'prisms',
                                        main_cfg = self.main_cfg))

        sm.add_widget(EditUnitsScreen(name = 'EditUnitsScreen', id = 'editunits_screen',
                                        colors = self.main_colors,
                                        main_data = self.edm_units,
                                        main_tablename = 'units',
                                        main_cfg = self.main_cfg))

        sm.add_widget(StatusScreen(name = 'StatusScreen', id = 'status_screen',
                                    colors = self.main_colors,
                                    edm_cfg = self.main_cfg,
                                    edm_ini = self.main_ini,
                                    edm_points = self.edm_points))

        sm.add_widget(e5_LogScreen(name = 'LogScreen', id = 'log_screen',
                                colors = self.main_colors,
                                logger = logger))

        sm.add_widget(e5_CFGScreen(name = 'CFGScreen', id = 'cfg_screen',
                                colors = self.main_colors,
                                cfg = self.main_cfg))

        sm.add_widget(e5_INIScreen(name = 'INIScreen', id = 'ini_screen',
                                colors = self.main_colors,
                                ini = self.main_ini))

        sm.add_widget(AboutScreen(name = 'AboutScreen', id = 'about_screen',
                                    colors = self.main_colors))

        sm.add_widget(EDMSettingsScreen(name = 'EDMSettingsScreen', id = 'edmsettings_screen',
                                        colors = self.main_colors,
                                        edm_ini = self.main_ini,
                                        edm_cfg = self.main_cfg))

        restore_window_size_position(__program__, self.main_ini)

        self.title = __program__ + " " + __version__

        logger.info('EDM started, logger initialized, and application built.')

        return(sm)

Factory.register(__program__, cls=EDMApp)

if __name__ == '__main__':
    logger = logging.getLogger('EDM')
    EDMApp().run()