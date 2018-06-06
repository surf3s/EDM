# need to move read_ini and write_ini over before much else can be done on the read cfg routines

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.popup import Popup
from kivy.properties import ListProperty, StringProperty, ObjectProperty, BooleanProperty, NumericProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel

import os
import string
import random
import numpy as np
import datetime
import pandas as pd 


from collections import OrderedDict




# get anglr.py library
# or get angles.py library (looks maybe better)

# use shelve for nosql database (at least at start)

# use pySerial for serial communications

class points:
    MAX_FIELDS = 30

    class field:
        def __init__(self, name):
            self.name = name
            self.type = 'Text'
            self.menulist = []
            self.prompt = name
            self.maxlen = 10
            self.increment = False
            self.required = False
            self.carry = False 
            self.unique = False

    def __init__(self, filename):
        self.filename = filename
        # check to see if this file exists already and if so read in the data
        # if no file exists are after opening the file there are no fields, insert default fields
        self.fields = []
        self.records = []

    def create_defaults(self):
        self.fields = []
        delete_all()

        unit = field('UNIT')
        unit.prompt = 'Unit'
        unit.maxlen = 6
        unit.required = True
        self.fields.append(unit)

        ID = field('ID')
        ID.prompt = 'ID'
        ID.maxlen = 5
        ID.required = True
        self.fields.append(ID)

        suffix = field('SUFFIX')
        suffix.type = 'Numeric'
        suffix.prompt = 'Suffix'
        suffix.maxlen = 3
        suffix.required = True
        self.fields.append(suffix)

        layer = field('LAYER')
        layer.prompt = 'Layer'
        layer.maxlen = 20
        self.fields.append(layer)

        code = field('CODE')
        code.prompt = 'Code'
        code.maxlen = 20
        self.fields.append(code)

        excavator = field('excavator')
        excavator.prompt = 'Excavator'
        excavator.maxlen = 20
        self.fields.append(excavator)

        prism = fields('PRISM')
        prism.type = 'Numeric'
        prism.required = True
        self.fields.append(prism)

        x = fields('X')
        x.type = 'Numeric'
        x.required = True
        self.fields.append(x)

        y = fields('Y')
        y.type = 'Numeric'
        y.required = True
        self.fields.append(y)

        z = fields('Z')
        z.type = 'Numeric'
        z.required = True
        self.fields.append(z)

        hangle = fields('HANGLE')
        hangle.required = True
        hangle.prompt = 'H-Angle'
        self.fields.append(hangle)

        vangle = fields('VANGLE')
        vangle.required = True
        vangle.prompt = 'V-Angle'
        self.fields.append(vangle)

        sloped = fields('SLOPED')
        sloped.type = 'Numeric'
        sloped.required = True
        sloped.prompt = 'Slope D.'
        self.fields.append(sloped)

        datetime = fields('DATETIME')
        datetime.type = 'Text'
        datetime.required = True
        datetime.prompt = 'Date-Time'
        self.fields.append(datetime)

    def names(self):
        name_list = []
        for field in self.fields:
            name_list.append(field.name)
        return(name_list)

    def field_count(self):
        return(len(self.fields))

    def record_count(self):
        pass
    
    def delete_all(self):
        self.records = []

    def export_csv(self):
        pass

    def delete_record(self):
        pass

    def add_record(self):
        pass

    def initialize(self):
        pass

class datums:
    MAX_DATUMS = 100
    
    class datum:
        def __init__(self, datum_name):
            self.name = datum_name
            self.x = 0
            self.y = 0
            self.z = 0
            self.date_created = ''
    
    def __init__(self, filename):
        self.filename = filename
        if os.path.exists(self.filename):
            self.datums = pd.read_csv(self.filename)
        else:
            self.datums = pd.DataFrame(columns = ['Name','X','Y','Z','Date_Created'])
            self.datums.set_index('Name')
            self.save()

    def save(self):
        self.datums.to_csv(self.filename)

    def count(self):
        return(self.datums.shape[0])

    def names(self):
        return(self.datums.loc[:,'Name'])

    def select(self):
        # need code that build a list of datum names with an add new and cancel button
        # and returns the selected datum
        # if add new is selected the put up edit datum and then save
        pass

    def edit(self):
        # need code that makes input boxes for a datum item
        # needs a name box, XYZ boxes, a record with station and cancel button
        pass

class prisms:
    MAX_PRISMS = 20

    class prism:
        def __init__(self):
            self.name = ''
            self.height = 0
            self.offset = 0

    def __init__(self, filename):
        self.filename = filename
        # check to see if this file exists already and if so read in the prisms
        self.prisms = []

    def count(self):
        return(len(self.prims))

    def names(self):
        name_list = []
        for prism in self.prisms:
            name_list.append(prism.name)
        return(name_list)

    def select(self):
        # need code that build a list of prism names with an add new and cancel button
        # and returns the selected prism
        # if add new is selected the put up edit prism and then save
        pass

    def edit(self):
        # need code that makes input boxes for a prism item
        # needs a name box, height and offset boxes and cancel button
        pass

class units:
    MAX_UNITS = 100

    class unit:
        def __init__(self):
            self.name = ''
            self.x1 = 0
            self.y1 = 0
            self.x2 = 0
            self.y2 = 0
            self.radius = 0

    def __init__(self, filename):
        self.filename = filename
        # check to see if this file exists already and if so read in the unit names
        self.units = []

    def count(self):
        return(len(self.units))

    def names(self):
        name_list = []
        for unit in self.units:
            name_list.append(unit.name)
        return(name_list)

    def select(self):
        # need code that build a list of unit names with an add new and cancel button
        # and returns the selected unit
        # if add new is selected the put up edit unit and then save
        pass

    def edit(self):
        # need code that makes input boxes for a unit item
        # needs a name box, minx, miny, maxx, maxy, and cancel button
        pass

class ini:
    def ini_class(self):
        def __init__(self, name):
            self.name = name
            self.items = []

    def add_value(self, ini_classname, varname, vardata):
        # implement dictionary - add new values and append to existing values using chr(1) as separator
        pass

    def read_ini(self):
        try:
            with open(self.filename) as f:
                for line in f:
                    if line.strip()[0]=="[":
                        ini_classname = ini_class(line.strip()[1:-1].upper())
                    else:
                        if line.find("="):
                            varname = line.split("=")[0].strip().upper()
                            vardata = line.split("=")[1].strip()
                            self.add_value(ini_classname, varname, vardata)
        except:
            pass

    def __init__(self, filename):
        self.filename = filename
        self.classes = []
        self.read_ini()


    def names(self):
        name_list = []
        for ini_class in self.classes:
            name_list.append(ini_class.name)
        return(name_list)
        
    def get_value(self, ini_classname, varname):
        for ini_class in self.classes:
            if ini_class.name==ini_classname:
                return(ini_class[varname])
        return('')                

    def set_value(self, ini_classname, varname, vardata):
        # same as above but without append
        pass


    def write_ini(self):
        try:
            with open('$temp$.ini', mode = 'w') as f:
                pass
                # loop through items in items
                # loop through dictionary for each item

            # when successful - delete current ini
            # rename temp.ini as current ini
        except:
            pass

class cfg:
    def __init__(self, filename):
        self.filename = filename 

    def load(self):
        new_format = False
        with open(self.filename) as f:
            for line in f:
                if line.upper() == '[EDM]':
                    new_format = True

        if not new_format:
            pass
            lineno = 0
            with open(self.filename) as f:
                for line in f:
                    lineno += 1
                    complete_line += line.strip()
                    if complete_line[-1] == '\\':
                        complete_line[-1] = ' '
                    elif len(complete_line)>0 and complete_line[1]!="'":
                        a = complete_line.find(":")
                        if a:
                            key_field = complete_line[:a].upper()
                            data_value = complete_line[a:]
                            if key_field=='FIELD':
                                if data_value == "":
                                    errormessage = "No field name given in line %s." & (lineno)
                                    break 
                                if data_value in points.names(): 
                                    errormessage = "Duplicate FIELD definition for %s in line %s." & (data_value, lineno)
                                    break
                                if points.field_count() == points.MAX_FIELDS:
                                    errormessage = "Too many FIELD definitions with %s.  Limit is %s" & (data_value, points.MAX_FIELDS)
                                    break
                                new_field = points.field
                                new_field.name = data_value
                                points.fields.append(new_field)

                            if key_field == 'POINTSFILE':
                                points.filename = data_value.upper()

                            if key_field == 'COM1':
                                totalstation.com_port_no = 1
                                totalstation.com_port_settings = data_value.upper()

                            if key_field == 'COM2':
                                totalstation.com_port_no = 2
                                totalstation.com_port_settings = data_value.upper()

                            if key_field == 'EDM':
                                data_value = data_value.upper().split(' ')
                                if data_value[0] in ['NONE','MANUAL']:
                                    totalstation.make = 'NONE'
                                if data_value[0] in ["GTS-3B", "GTS-301", "GTS-302", "GTS-303", "GTS-3X", "TOPCON"]:
                                    totalstation.make = 'TOPCON'
                                if data_value[0] in ["TC-500", "WILD"]:
                                    totalstation.make = 'WILD'
                                if data_value[0] in ["SOKKIA"]:
                                    totalstation.make = 'SOKKIA'
                                if totalstation.make == '':
                                    errormessage = "Expected NONE, MANUAL, TOPCON, WILD or SOKKIA instrument in line %s." & (lineno)
                                    break

                            if key_field == "COMPUTER":
                                data_value = data_value.upper()
                                if data_value not in ['WINDOWS','OSX','ANRDOID']:
                                    errormessage = "Expected WINDOWS, OSX or ANDROID for computer type in line %s." & (lineno)
                                    break

                            if key_field == "SQID":
                                pass

                            if key_field == "PRISMDEF":
                                if prisms.count() == prisms.MAX_PRISMS:
                                    errormessage = "The number of prisms is limited to %s." & (prisms.MAX_PRISMS)
                                    break
                                data_value = data_value.split(' ')
                                if len(data_value)<2:
                                    errormessage = 'Prism definitions require a height.  See line %s.' & (lineno)
                                if data_value[0] in prisms.names():
                                    errormessage = 'Duplicate prism name in line %s.' & (lineno)
                                new_prism = prisms.prism
                                new_prism.name = data_value[0].upper()
                                new_prism.height = data_value[1]
                                if len(new_prism)>2:
                                    new_prism.offset = data_value[2]
                                prisms.prisms.append(new_prism)

                            if key_field == "DATUMDEF":
                                if datums.count() == datums.MAX_DATUMS:
                                    errormessage = "The number of datums is limited to %s." & (datums.MAX_DATUMS)
                                    break
                                data_value = data_value.upper().split(' ')
                                if len(data_value) < 4:
                                    errormessage = "Format DATUMDEF as Name X Y Z.  See line %s." & (lineno)
                                    break
                                if data_value[0] in datums.names():
                                    errormessage = "Duplicate datum name in line %s." & (lineno)
                                    break
                                new_datum = datums.datum
                                new_datum.name = data_value[0]
                                new_datum.X = data_value[1]
                                new_datum.Y = data_value[2]
                                new_datum.Z = data_value[3]
                                datums.datums.append(new_datum)

                            if key_field == "UNITFILE":
                                pass

        else:
            ini_data = ini(cfg_file)

            if ini.get_value("EDM", "Sitename"):
                EDM.sitename = ini.get_value("EDM", "Sitename")
            else:
                EDM.sitename = "EDM"
       
            if ini.get_value("EDM", "Database"):
                EDM.database = ini.get_value("EDM", "Database")
            else:
                EDM.database = "EDM"

            if ini.get_value("EDM", "SQID").upper() in ['TRUE', 'YES']:
                EDM.sqid = True
            else:
                EDM.sqid = False

            if ini.get_value("EDM", "Limitchecking").upper() in ['TRUE', 'YES']:
                EDM.limitchecking = True
            else:
                EDM.limitchecking = False

            if ini.get_value("EDM", "WriteLogFile").upper() in ['TRUE', 'YES']:
                EDM.writelogfile = True
            else:
                EDM.writelogfile = False

            if ini.get_value("EDM", "Unitfields"):
                EDM.unitfields = ini.get_value("EDM", "Unitfields").upper()
                # if suffix is a unit field, remove it
                # remove these fields as well "x", "y", "z", "date", "time", "hangle", "vangle"
                unitname = "unit"
            else:
                EDM.unitfields = ""

            for fieldname in ini.names():
                if fieldname not in ["EDM", "BUTTON1", "BUTTON2", "BUTTON3", "BUTTON4", "BUTTON5", "BUTTON6"]:
                    new_field = points.field(fieldname)
                    new_field.type = ini.get_value(fieldname, "Type")
                    new_field.prompt = ini.get_value(fieldname, "Prompt")
                    new_field.menulist = ini.get_value(fieldname, "Menu")
                    new_field.maxlen = ini.get_value(fieldname, "Length")
                    if ini.get_value(fieldname, "Carry").upper() in ['TRUE', 'YES']:
                        new_field.carry = True
                    else:
                        new_field.carry = False
                    if ini.get_value(fieldname, "Unique").upper() in ['TRUE', 'YES']:
                        new_field.unique = True
                    else:
                        new_field.unique = False
                    if ini.get_value(fieldname, "Required").upper() in ['TRUE', 'YES']:
                        new_field.required = True
                    else:
                        new_field.required = False
                    if ini.get_value(fieldname, "Increment").upper() in ['TRUE', 'YES']:
                        new_field.increment = True
                    else:
                        new_field.increment = False

    def save(self):
        pass

class totalstation:
    def __init__(self, make, model):
        if make=='':
            make = "Emulation"
        else:
    	    self.make = make
        self.model = model
        self.com_port_no = 0
        self.com_port_settings = ''
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

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)

class Root(FloatLayout):
    loadfile = ObjectProperty(None)
    savefile = ObjectProperty(None)
    text_input = ObjectProperty(None)

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load_cfg(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Open CFG file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def show_save(self):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def load_cfg(self, path, filename):
        cfg = cfg(os.path.join(path, filename[0]))
        cfg.load()
        self.dismiss_popup()

    def save(self, path, filename):
        with open(os.path.join(path, filename), 'w') as stream:
            stream.write(self.text_input.text)

        self.dismiss_popup()

    def button_action(self, button_name):
        pass

class EditDatums(Screen):
    pass

class MainScreen(Screen):
    pass

class InitializeOnePointHeader(Label):
    pass

class InitializeDirectScreen(Screen):
    def __init__(self,**kwargs):
        super(InitializeDirectScreen, self).__init__(**kwargs)
        self.add_widget(DatumLister())

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


class EditPointsScreen(Screen):
    pass


class EditPrismsScreen(Screen):
    pass


class EditUnitsScreen(Screen):
    pass



class datumlist(RecycleView, Screen):
    def __init__(self, **kwargs):
        super(datumlist, self).__init__(**kwargs)
        self.data = [{'text': str(x)} for x in range(100)]


class MessageBox(Popup):

    def popup_dismiss(self):
        self.dismiss()


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
        MessageBox().open()


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


class AboutScreen(Screen):
    pass

#sm = ScreenManager()
#sm.add_widget(AboutScreen(name='about'))
#sm.add_widget(InitializeDirectScreen(name='InitializeDirect'))
#sm.add_widget(MainScreen(name='main'))

class EditDatumsScreen(Screen):
    def __init__(self,**kwargs):
        super(EditDatumsScreen, self).__init__(**kwargs)
        df = EDMpy.edm_datums.datums 
        self.add_widget(DfguiWidget(df))

class EDMpy(App):
    title = 'EDMpy'
    edm_datums = datums('EDM_datums.csv')
    def build(self):
        self.computer = 'WINDOWS'
        self.printer = False
        self.sitename = ''
        self.database = 'EDM'
        edm_ini = ini('EDM.ini')
        if edm_ini.get_value("EDM", "CFG"):
            self.cfg_file = edm_ini.get_value("EDM", "CFG")
            cfg = cfg(self.cfg_file)
            cfg.load()
        self.edm_points = points(self.database + '_points')
        self.edm_units = units(self.database + '_units')
        self.edm_prisms = prisms(self.database + '_prisms')
        self.edm_datums = datums(self.database + '_datums.csv')
        #sm.current = 'main'
        #df = create_dummy_data(0)
        #df = edm_datums.datums 
        #return(DfguiWidget(df))


# Code from https://github.com/MichaelStott/DataframeGUIKivy/blob/master/dfguik.py

def create_dummy_data(size):

    user_ids = np.random.randint(1, 1000000, 10)
    product_ids = np.random.randint(1, 1000000, 100)

    def choice(*values):
        return np.random.choice(values, size)

    random_dates = [
        datetime.date(2016, 1, 1) + datetime.timedelta(days=int(delta))
        for delta in np.random.randint(1, 50, size)
    ]
    return pd.DataFrame.from_items([
        ("Date", random_dates),
        ("UserID", choice(*user_ids)),
        ("ProductID", choice(*product_ids)),
        ("IntColumn", choice(1, 2, 3)),
        ("FloatColumn", choice(np.nan, 1.0, 2.0, 3.0)),
        ("StringColumn", choice("A", "B", "C")),
        ("Gaussian 1", np.random.normal(0, 1, size)),
        ("Gaussian 2", np.random.normal(0, 1, size)),
        ("Uniform", np.random.uniform(0, 1, size)),
        ("Binomial", np.random.binomial(20, 0.1, size)),
        ("Poisson", np.random.poisson(1.0, size)),
    ])

class HeaderCell(Button):
    pass


class TableHeader(ScrollView):
    """Fixed table header that scrolls x with the data table"""
    header = ObjectProperty(None)

    def __init__(self, titles = None, *args, **kwargs):
        super(TableHeader, self).__init__(*args, **kwargs)

        for title in titles:
            self.header.add_widget(HeaderCell(text=title))


class ScrollCell(Label):
    text = StringProperty(None)
    is_even = BooleanProperty(None)


class TableData(RecycleView):
    nrows = NumericProperty(None)
    ncols = NumericProperty(None)
    rgrid = ObjectProperty(None)

    def __init__(self, list_dicts=[], column_names = None, *args, **kwargs):
        self.nrows = len(list_dicts)
        self.ncols = len(column_names)

        super(TableData, self).__init__(*args, **kwargs)

        self.data = []
        for i, ord_dict in enumerate(list_dicts):
            is_even = i % 2 == 0
            row_vals = ord_dict.values()
            for text in row_vals:
                self.data.append({'text': text, 'is_even': is_even})

    def sort_data(self):
        #TODO: Use this to sort table, rather than clearing widget each time.
        pass
        
        
class Table(BoxLayout):

    def __init__(self, list_dicts=[], column_names = None, *args, **kwargs):

        super(Table, self).__init__(*args, **kwargs)
        self.orientation = "vertical"

        self.header = TableHeader(column_names)
        self.table_data = TableData(list_dicts = list_dicts, column_names = column_names)

        self.table_data.fbind('scroll_x', self.scroll_with_header)

        self.add_widget(self.header)
        self.add_widget(self.table_data)

    def scroll_with_header(self, obj, value):
        self.header.scroll_x = value

class DataframePanel(BoxLayout):
    """
    Panel providing the main data frame table view.
    """

    def populate_data(self, df):
        self.df_orig = df
        self.original_columns = self.df_orig.columns[:]
        self.current_columns = self.df_orig.columns[:]
        self._disabled = []
        self.sort_key = None
        self._reset_mask()
        self._generate_table()

    def _generate_table(self, sort_key=None, disabled=None):
        self.clear_widgets()
        df = self.get_filtered_df()
        data = []
        if disabled is not None:
            self._disabled = disabled
        keys = [x for x in df.columns[:] if x not in self._disabled]
        if sort_key is not None:
            self.sort_key = sort_key
        elif self.sort_key is None or self.sort_key in self._disabled:
            self.sort_key = keys[0]
        for i1 in range(len(df.iloc[:, 0])):
            row = OrderedDict.fromkeys(keys)
            for i2 in range(len(keys)):
                row[keys[i2]] = str(df.iloc[i1, i2])
            data.append(row)
        data = sorted(data, key=lambda k: k[self.sort_key]) 
        self.add_widget(Table(list_dicts=data, column_names = df.columns))
        
    def apply_filter(self, conditions):
        """
        External interface to set a filter.
        """
        old_mask = self.mask.copy()

        if len(conditions) == 0:
            self._reset_mask()

        else:
            self._reset_mask()  # set all to True for destructive conjunction

            no_error = True
            for column, condition in conditions:
                if condition.strip() == '':
                    continue
                condition = condition.replace("_", "self.df_orig['{}']".format(column))
                print("Evaluating condition:", condition)
                try:
                    tmp_mask = eval(condition)
                    if isinstance(tmp_mask, pd.Series) and tmp_mask.dtype == np.bool:
                        self.mask &= tmp_mask
                except Exception as e:
                    print("Failed with:", e)
                    no_error = False

        has_changed = any(old_mask != self.mask)

    def get_filtered_df(self):
        return self.df_orig.loc[self.mask, :]

    def _reset_mask(self):
        pass
        self.mask = pd.Series([True] *
                              self.df_orig.shape[0],
                              index=self.df_orig.index)

class FilterPanel(BoxLayout):
    
    def populate(self, columns):            
        self.filter_list.bind(minimum_height=self.filter_list.setter('height'))
        for col in columns:
            self.filter_list.add_widget(FilterOption(columns))

    def get_filters(self):
        result=[]
        for opt_widget in self.filter_list.children:
            if opt_widget.is_option_set():
                result.append(opt_widget.get_filter())
        return [x.get_filter() for x in self.filter_list.children
                if x.is_option_set]

  
class DfguiWidget(TabbedPanel):

    def __init__(self, df, **kwargs):
        super(DfguiWidget, self).__init__(**kwargs)
        self.df = df
        self.panel1.populate_data(df)
        #self.panel2.populate_columns(df.columns[:])
        #self.panel3.populate(df.columns[:])
        #self.panel4.populate_options(df.columns[:])
        #self.panel5.populate_options(df.columns[:])

    # This should be changed so that the table isn't rebuilt
    # each time settings change.
    def open_panel1(self):
        #arr = self.panel3.get_filters()
        #print(str(arr))
        #self.panel1.apply_filter(self.panel3.get_filters())
        self.panel1._generate_table(disabled=
                                    self.panel2.get_disabled_columns())



# End code from https://github.com/MichaelStott/DataframeGUIKivy/blob/master/dfguik.py


Factory.register('Root', cls=Root)
Factory.register('LoadDialog', cls=LoadDialog)
Factory.register('SaveDialog', cls=SaveDialog)
Factory.register('EDMpy', cls=EDMpy)

if __name__ == '__main__':
    EDMpy().run()