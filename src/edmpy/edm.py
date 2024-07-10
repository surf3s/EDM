"""
EDM by Shannon McPherron

  This is now beta release.  I am still working on bugs but not adding new features.
  It should be backwards compatible with EDM-Mobile and EDMWin (but there are still some issues).

Changes for Version 1.0.30
  Added and debugged Topcon stations
  Added and debugged Leica and Leica GeoCom stations
  Stopped program from exiting when escape is pressed
  Fixed default locations for ini, log, and data
  Program remembers last size and location of the screen
  Repeat button added to measure screen
  Flag to not prompt for prism each point added to options screen
  Misc. prism height issues addressed
  X box added to text boxes to help clearing values on touchscreen computers
  Prism menu added to edit record with update of Z on prism height change
  Improved text sizing in buttons to include word wrapping and dynamic sizing
  Improved the default CFG and carry and increment issues
  Fixed button font size on open dialog
  Length checking implemented (length in CFG is enforced during data entry)
  Prompt values (from CFG when provided) are used in Edit last record and New Record instead of the field name
  Empty entries in MENUs are removed
  Better error trapping of mistakes in the CFG
  First shot on empty data table put 1 in increment fields
  Fields shown in CFG order on delete record in gridview
  Can do offsets in the datagrid using +-
  Added save and revert buttons to case saving in datagrid (i.e. no longer saves immediately)
  Basic editing shortcuts (like cntl-c etc.) work in text boxes

Changes for Version 1.0.31
  BlueTooth tested with Leica GeoCom stations
  UI fixes
  Tested with 1000 records in DB
  Made JSON files better formatted so that they are more human readable
  Made geoJSON files work with QGIS (points and lines are separate layers)
  Substantial refactoring of Python classes and file structure

Changes for Version 1.0.31
  Fixed issue with numeric values saved as text in JSON after initial save
  Added Help JSON to view raw data in JSON file

Changes for Version 1.0.32
  Fixing issues with GeoCom and station setup

Changes for Version 1.0.33
  Fixed installation issues

Changes for Version 1.0.34
  Yet more fixes for Windows/PyPi installations

Changes for Version 1.0.35
  Bug in file import fixed
  Bug in CFG when no field type is specified fixed as well
  Bug in Filter records that crashed program is fixed
  Importing CSV now takes seconds rather than many many minutes (tested on import of 3996 records)
  Saving a point is now faster when record count is high
  Reworked a number of features because JSON files are not in doc_id order
  Add a "SIMULATION mode on" warning to maing screen when simulating points
  Suffix values on import csv are retained as integers
  Tried to improve open CFG so that if a non-EDM CFG is opened, it is not also trashed
  Fixed important bugs in station setup when using Manual XYZ or Manual VHD options
  Error trap continuation shot on an empty data file

Changes for Vesion 1.0.36
  Redid font sizing for buttons and text
  Trapped a bug with units when switching CFGs
  Various bugs having to do with entering/editing data
  Add support for datumx, datumy, datumz (which is now called stationx, stationy, stationz)

Changes for Version 1.0.37
  Fixed a bug in simulation mode
  Fixed very bad bug with popup window sizing that meant that sometimes prism didn't advance to edit screen

Changes for Version 1.0.38
  Recall last setup coordinates and resume with these (are stored in edm.ini now)

Changes for Version 1.0.39
  Fixed issue with Alpha default buttons not working
  Changed the way checking if last two points are the same works

Changes for Version 1.0.40
  GeoMax added by Tim Schueler
  Multiple bugs traps in datagrid
  Brought changes in E5 over and debugged more
  Added message to communication settings to let user know program is trying
  Fixed datum menu in setups (to not have add new)
  Added message when trying to do setups without having added datums
  fixed a logic bug with units when also unit is set to carry

Changes for Version 1.0.41
  fixed crash when Add button is pressed multiple times

Changes for Version 1.0.42
  Fixed bug where default values on speed buttons did not trigger linked fields
  Fixed bug where changing value of a field in edit screen did not trigger linked fields

Changes for Version 1.0.43
  Fixed bug that broke communication with older Leica instruments

Changes for Version 1.0.44
  Fixed major bug with auto finding Unit based on XY
  Fixed other related issues stemming from this

Changes for Version 1.0.45
  Some newer Leica models can return a valid hangle and vangle but a slope distance of 0 when the distance can't be measured.
    This is now error trapped.  If the coordinates are the same as the station coordinates or if slope distance is zero, a message is displayed.

Changes for Version 1.0.46
  Added in form to allow upload of data to cloud running OSA type system

Bugs/To Do
    import CSV files that don't have quotes
    have a toggle for unit checking
    sort filter by docid


  have to click twice on unit to get it to switch units
  add units to menu as you go along
  need to move load_dialog out of kv and into code and error trap bad paths
  could make menus work better with keyboard (at least with tab)
  Do unitchecking after doing an offset shot on suffix 0 points
  Good way to get random hash IDs
  Offer to change Z when prism changes in datagrid edit cases
  Thoroughly test unit checking
  Add home/end page up/page down and control home/control end to datagrid movement
  Add move to top or bottom in Help JSON and others (like Log file)
  Check what gets logged
  Deal more nicely with aftermath of a non-valid CFG being opened
"""


from kivy.config import Config
from kivy.core.clipboard import Clipboard
from kivy.graphics import Color, Rectangle
from kivy.app import App
from kivy.factory import Factory
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.uix.switch import Switch
from kivy import __version__ as __kivy_version__

import os
import sys
from datetime import datetime
import csv
from math import cos
from math import sin
from platform import python_version
import logging
from platformdirs import user_data_dir, user_log_dir, user_documents_dir
from appdata import AppDataPaths

# My libraries for this project
sys.path.append(os.path.join(sys.path[0], 'lib'))
from lib.e5_widgets import e5_label, e5_button, e5_MessageBox, e5_DatagridScreen, e5_RecordEditScreen, e5_side_by_side_buttons, e5_textinput
from lib.e5_widgets import edm_manual, DataGridTextBox, e5_SaveDialog, e5_LoadDialog, e5_PopUpMenu, e5_MainScreen, e5_InfoScreen, e5_scrollview_label
from lib.e5_widgets import e5_LogScreen, e5_CFGScreen, e5_INIScreen, e5_SettingsScreen, e5_scrollview_menu, DataGridMenuList, SpinnerOptions
from lib.e5_widgets import e5_JSONScreen, DataGridLabelAndField, DataUploadScreen
from lib.colorscheme import ColorScheme
from lib.misc import restore_window_size_position, filename_only, platform_name

from geo import point, prism
from db import DB
from ini import INI
from cfg import CFG
from totalstation import totalstation
from constants import APP_NAME
from constants import __SPLASH_HELP__

# The database - pure Python
from tinydb import TinyDB
from tinydb import __version__ as __tinydb_version__

# from plyer import gps
# from plyer import __version__ as __plyer_version__

# from plyer import __version__ as __plyer_version__
__plyer_version__ = 'None'

from angles import d2r

import serial
# import requests

# if os.name == 'nt':  # sys.platform == 'win32':
#     from serial.tools.list_ports_windows import comports
# elif os.name == 'posix':
#     from serial.tools.list_ports_posix import comports
# # ~ elif os.name == 'java':
# else:
#     raise ImportError("Sorry: no implementation for your platform ('{}') available".format(os.name))

"""
The explicit mention of this package here
triggers its inclusions in the pyinstaller spec file.
It is needed for the filechooser widget.
The TimeZoneInfo is just to avoid a flake8 error.
"""
try:
    import win32timezone
    win32timezone.TimeZoneInfo.local()
except ModuleNotFoundError:
    pass

VERSION = '1.0.46'
PRODUCTION_DATE = 'July 10, 2024'
__DEFAULT_FIELDS__ = ['X', 'Y', 'Z', 'SLOPED', 'VANGLE', 'HANGLE', 'STATIONX', 'STATIONY', 'STATIONZ', 'DATUMX', 'DATUMY', 'DATUMZ', 'LOCALX', 'LOCALY', 'LOCALZ', 'DATE', 'PRISM', 'ID']
__BUTTONS__ = 13
__LASTCOMPORT__ = 16
MAX_SCREEN_WIDTH = 400
__program__ = 'EDM'


class MainScreen(e5_MainScreen):

    event = None

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        self.setup_logger()

        self.colors = ColorScheme()
        self.ini = INI()
        self.cfg = CFG()
        self.data = DB()

        self.warnings, self.errors = self.setup_program()

        self.station = totalstation(self.ini.get_value(APP_NAME, 'STATION'))
        self.station.setup(self.ini, self.data)
        self.station.open()
        if self.station.error_message:
            self.warnings.append(self.station.error_message)

        self.cfg_datums = CFG()
        self.cfg_datums.build_datum()
        self.cfg_prisms = CFG()
        self.cfg_prisms.build_prism()
        self.cfg_units = CFG()
        self.cfg_units.build_unit()

        self.layout = BoxLayout(orientation='vertical',
                                size_hint_y=.9,
                                size_hint_x=.8,
                                pos_hint={'center_x': .5},
                                padding=20,
                                spacing=20)
        self.build_mainscreen()
        self.add_widget(self.layout)
        self.add_screens()
        restore_window_size_position(APP_NAME, self.ini)

    def on_enter(self, *args):
        if self.warnings or self.errors:
            self.popup = self.warnings_and_errors_popup(self.warnings, self.errors, auto_dismiss=False)
            self.popup.open()
            self.errors, self.warnings = [], []
        elif self.ini.first_time:
            self.popup = e5_MessageBox('Welcome to EDM', __SPLASH_HELP__, colors=self.colors)
            self.popup.open()
            self.ini.first_time = False
        self.update_info_label()

    def setup_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh = logging.FileHandler(os.path.join(user_log_dir(APP_NAME, 'OSA'), APP_NAME + '.log'))
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.info(__program__ + ' started, logger initialized, and application built.')

    def add_screens(self):
        sm.add_widget(EditLastRecordScreen(name='EditLastRecordScreen',
                                            colors=self.colors,
                                            data=self.data,
                                            doc_id=None,
                                            e5_cfg=self.cfg))

        sm.add_widget(VerifyStationScreen(name='VerifyStationScreen',
                                            id='verify_station',
                                            data=self.data,
                                            station=self.station,
                                            colors=self.colors,
                                            ini=self.ini))

        sm.add_widget(RecordDatumsScreen(name='RecordDatumsScreen',
                                            data=self.data,
                                            station=self.station,
                                            colors=self.colors,
                                            ini=self.ini))

        sm.add_widget(EditPointScreen(name='EditPointScreen',
                                            colors=self.colors,
                                            data=self.data,
                                            # data_table=self.data.table,
                                            doc_id=None,
                                            e5_cfg=self.cfg,
                                            one_record_only=True))

        sm.add_widget(EditPointsScreen(name='EditPointsScreen',
                                            colors=self.colors,
                                            main_data=self.data,
                                            main_tablename=self.data.table,
                                            main_cfg=self.cfg))

        sm.add_widget(EditPointsScreen(name='EditDatumsScreen',
                                            colors=self.colors,
                                            main_data=self.data,
                                            main_tablename='datums',
                                            main_cfg=self.cfg_datums,
                                            addnew=True))

        sm.add_widget(EditPointsScreen(name='EditPrismsScreen',
                                            colors=self.colors,
                                            main_data=self.data,
                                            main_tablename='prisms',
                                            main_cfg=self.cfg_prisms,
                                            addnew=True))

        sm.add_widget(EditPointsScreen(name='EditUnitsScreen',
                                            colors=self.colors,
                                            main_data=self.data,
                                            main_tablename='units',
                                            main_cfg=self.cfg_units,
                                            addnew=True))

        sm.add_widget(StatusScreen(name='StatusScreen',
                                            colors=self.colors,
                                            cfg=self.cfg,
                                            ini=self.ini,
                                            data=self.data,
                                            station=self.station))

        sm.add_widget(e5_LogScreen(name='LogScreen', colors=self.colors, logger=logging.getLogger(__name__)))

        sm.add_widget(e5_CFGScreen(name='CFGScreen', colors=self.colors, cfg=self.cfg))

        sm.add_widget(e5_INIScreen(name='INIScreen', colors=self.colors, ini=self.ini))

        sm.add_widget(e5_JSONScreen(name='JSONScreen', colors=self.colors, data=self.data))

        sm.add_widget(AboutScreen(name='AboutScreen', colors=self.colors))

        sm.add_widget(StationConfigurationScreen(name='StationConfigurationScreen',
                                                    station=self.station,
                                                    ini=self.ini,
                                                    colors=self.colors))

        sm.add_widget(InitializeStationScreen(name='InitializeStationScreen',
                                                    data=self.data,
                                                    station=self.station,
                                                    ini=self.ini,
                                                    colors=self.colors))

        sm.add_widget(e5_SettingsScreen(name='EDMSettingsScreen',
                                        colors=self.colors,
                                        ini=self.ini,
                                        cfg=self.cfg))

        sm.add_widget(ComTestScreen(name='ComTestScreen',
                                        colors=self.colors,
                                        station=self.station,
                                        cfg=self.cfg))

        sm.add_widget(OptionsScreen(name='OptionsScreen',
                                        colors=self.colors,
                                        station=self.station,
                                        cfg=self.cfg))

        sm.add_widget(DataUploadScreen(name='UploadScreen',
                                        data=self.data,
                                        cfg=self.cfg,
                                        colors=self.colors))

    def delete_screens(self):
        for screen in sm.screens[:]:
            if screen.name != 'MainScreen':
                sm.remove_widget(screen)

    def reset_screens(self):
        self.delete_screens()
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

        self.info = e5_label(text='EDM',
                                size_hint=(1, size_hints['info']),
                                color=self.colors.text_color,
                                id='lastshot',
                                halign='center')
        if self.colors:
            if self.colors.text_font_size:
                self.info.font_size = self.colors.text_font_size
        self.layout.add_widget(self.info)
        self.info.bind(texture_size=self.info.setter('size'))
        self.info.bind(size_hint_min_x=self.info.setter('width'))

        # grid = GridLayout(cols = 3, spacing = 10)
        scroll_content = BoxLayout(orientation='horizontal',
                                    size_hint=(1, size_hints['option_buttons']),
                                    spacing=20)
        self.layout.add_widget(scroll_content)

        button_count = 0
        button_text = []
        button_selected = []
        for button_no in range(1, __BUTTONS__):
            title = self.cfg.get_value(f'BUTTON{button_no}', 'TITLE')
            if title:
                button_text.append(title)
                button_selected.append(False)
                button_count += 1

        if button_count > 0:
            self.scroll_menu = e5_scrollview_menu(button_text,
                                                    menu_selected=button_selected,
                                                    widget_id='buttons',
                                                    call_back=[self.take_shot],
                                                    ncols=3,
                                                    colors=self.colors)
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

        shot_buttons = GridLayout(cols=3, size_hint=(1, size_hints['shot_buttons']), spacing=20)

        shot_buttons.add_widget(e5_button(text='Record', id='record',
                                            colors=self.colors, call_back=self.take_shot, selected=True))

        shot_buttons.add_widget(e5_button(text='Continue', id='continue',
                                            colors=self.colors, call_back=self.take_shot, selected=True))

        self.measure_button = e5_button(text='Measure', id='measure',
                                            colors=self.colors, call_back=self.take_shot, selected=True)
        shot_buttons.add_widget(self.measure_button)

        self.layout.add_widget(shot_buttons)

        self.update_title()

        # if self.cfg.filename:
        #     if self.cfg.has_warnings or self.cfg.has_errors:
        #         self.event = Clock.schedule_once(self.show_popup_message, 1)

    def update_title(self):
        for widget in self.walk():
            if hasattr(widget, 'action_previous'):
                widget.action_previous.title = 'EDM'
                if self.cfg is not None:
                    if self.cfg.filename:
                        widget.action_previous.title = filename_only(self.cfg.filename)

    def message_open_cfg_first(self):
        message = '\nBefore you can do this, you need to open a CFG file (see option under File menu).  Opening a CFG file will also open your database. '
        message += 'If you do not have a CFG file already, you can use a default one (see option under File menu).  Later you can alter the default CFG to '
        message += 'add additional options specific to your work.'
        return e5_MessageBox('EDM', message, colors=self.colors)

    def ready_to_use(self):
        return self.cfg is not None and self.data.filename != '' and self.data.filename is not None

    def take_shot(self, instance):
        if not self.ready_to_use() and instance.id != 'measure':
            self.popup = self.message_open_cfg_first()
            self.popup.open()
            return

        if instance.id == 'continue' and len(self.data.db.table(self.data.table)) == 0:
            message = 'Continue works only after you have saved at least one point.  Continue repeats the last point changing only the Suffix field '
            message += 'and the new measured values.  All other values, such as layer, excavator, and so forth, carry over.  Continue is an easy '
            message += 'way to link a series of measures to a single object or into one set of points.'
            self.popup = e5_MessageBox('EDM', message, colors=self.colors)
            self.popup.open()
            return

        self.station.shot_type = instance.id
        self.station.clear_xyz()
        if self.station.make == 'Microscribe':
            self.popup = DataGridTextBox(title='EDM', text='<Microscribe>',
                                            label='Waiting on...',
                                            button_text=['Cancel', 'Next'],
                                            call_back=self.have_shot,
                                            colors=self.colors)
            self.popup.auto_dismiss = False
            self.popup.open()
        elif self.station.make in ['Manual XYZ', 'Manual VHD']:
            self.popup = edm_manual(type=self.station.make, call_back=self.have_shot_manual, colors=self.colors)
            self.popup.open()
        else:
            self.station.take_shot()
            if self.station.prism_prompt:
                self.popup = self.get_prism_height()
                self.popup.auto_dismiss = False
                self.popup.open()
            else:
                self.have_shot(instance)

    def have_shot_manual(self, instance):
        # check that next was pressed and get values
        if self.popup.xcoord and self.popup.ycoord and self.popup.zcoord:
            p = self.station.text_to_point(f'{self.popup.xcoord.textbox.text},{self.popup.ycoord.textbox.text},{self.popup.zcoord.textbox.text}')
            if p:
                self.station.xyz = p
                self.station.make_global()
                self.station.vhd_from_xyz()
        elif self.popup.hangle and self.popup.vangle and self.popup.sloped:
            try:
                self.station.hangle = float(self.popup.hangle.textbox.text)
                self.station.vangle = float(self.popup.vangle.textbox.text)
                self.station.sloped = float(self.popup.sloped.textbox.text)
            except ValueError:
                self.station.xyz = point()
            self.station.vhd_to_xyz()
            self.station.make_global()
        self.station.pnt = None
        self.popup.dismiss()
        if self.station.xyz.x is None or self.station.xyz.y is None or self.station.xyz.z is None:
            self.popup = e5_MessageBox('Recording error', '\nInvalid value(s) were given.  Point not recorded.', call_back=self.close_popup, colors=self.colors)
            self.popup.open()
            self.popup_open = True
        else:
            if self.station.prism_prompt:
                self.popup = self.get_prism_height()
                self.popup.auto_dismiss = False
                self.popup.open()
                self.popup_open = True
            else:
                self.have_shot(instance)

    def get_prism_height(self):
        prism_names = self.data.names('prisms')
        if len(prism_names) > 0:
            return DataGridMenuList(title="Select or Enter a Prism Height",
                                            menu_list=prism_names,
                                            menu_selected=self.station.prism.name,
                                            call_back=self.have_shot,
                                            dismiss_call_back=self.cancel_x_shot,
                                            colors=self.colors)
        else:
            return DataGridTextBox(title='Enter a Prism Height',
                                        text=str(self.station.prism.height) if self.station.prism.height else '0',
                                        call_back=self.have_shot,
                                        dismiss_call_back=self.cancel_x_shot,
                                        button_text=['Back', 'Next'],
                                        colors=self.colors)

    def have_shot(self, instance):
        if self.station.make == 'Microscribe':
            result = self.popup.result
            if result:
                p = self.station.text_to_point(result)
                if p:
                    self.station.xyz = self.station.mm_to_meters(p)
                    self.station.make_global()
        else:
            if self.station.prism_prompt:
                prism_name = instance.text
                if prism_name == 'Add' or prism_name == 'Next':
                    try:
                        self.station.prism = prism(None, float(self.popup.txt.textbox.text), None)
                    except ValueError:
                        self.station.prism = prism()
                else:
                    self.station.prism = self.data.get_prism(prism_name)
            else:
                self.station.prism = prism(None, 0.0, None)
            if self.station.prism.height is None:
                self.popup.dismiss()
                self.popup = e5_MessageBox('Error', '\nInvalid prism height provided.  Shot not recorded.', call_back=self.close_popup, colors=self.colors)
                self.popup.open()
                self.popup_open = True
                return
            if self.station.make in ['Manual XYZ', 'Manual VHD', 'Simulate']:
                self.station.prism_adjust()

        if self.popup:
            self.popup.dismiss()

        if self.station.shot_type == 'measure':
            self.popup = e5_MessageBox('Measurement',
                                        self.make_x_shot_summary(),
                                        response_type="Other",
                                        response_text=['Close', 'Repeat'],
                                        call_back=[self.cancel_x_shot, self.record_another_x_shot],
                                        colors=self.colors)
            if self.station.make not in ['Manual XYZ', 'Manual VHD', 'Simulate', '']:
                self.event = Clock.schedule_interval(self.check_for_station_response_x_shot, .1)
            self.popup.open()
        else:
            self.add_point_record()
            if self.data.db is not None:
                self.data.db.table(self.data.table).on_save = self.on_save
                self.data.db.table(self.data.table).on_cancel = self.on_cancel
            sm.current = 'EditPointScreen'  # Had a crash here with a none type message - need to replicate
            if self.station.make not in ['Manual XYZ', 'Manual VHD', 'Simulate', '']:
                self.event = Clock.schedule_interval(self.check_for_station_response_edit_record, .1)

    def cancel_x_shot(self, instance):
        self.popup.dismiss()
        if self.event:
            self.event.cancel()
        self.station.cancel()

    def check_for_station_response_edit_record(self, dt):
        # print('.', end = "")
        if self.station.data_waiting():
            if self.station.make in ['Leica']:
                self.station.fetch_point()
            elif self.station.make in ['Leica GeoCom']:
                self.station.fetch_point_leica_geocom()
            elif self.station.make in ['GeoMax']:
                self.station.fetch_point_geomax()
            elif self.station.make in ['Topcon']:
                self.station.fetch_point_topcon()
            if self.station.response:
                self.event.cancel()
                self.station.make_global()
                self.station.prism_adjust()

                if self.station.xyz_global.x == self.station.location.x and self.station.xyz_global.y == self.station.location.y and self.station.xyz_global.z == self.station.location.z:
                    self.popup = e5_MessageBox('Error',
                                                 'The measured point is the same as the station coordinates.  This can happen if the slope distance is 0.  Retake the shot.',
                                                 colors=self.colors)
                    self.popup.open()
                elif self.station.sloped == 0:
                    self.popup = e5_MessageBox('Error',
                                                 'The station returned a slope distance of 0.  Retake the shot.',
                                                 colors=self.colors)
                    self.popup.open()

                # Update the XYZ in the current edit screen
                sm.get_screen('EditPointScreen').reset_defaults_from_recorded_point(self.station)

                # Get the unit for these XY coordinates and if it is different than the current
                # then update the linked fields.  And fix other stuff.
                unitname = self.data.point_in_unit(self.station.xyz_global)
                current_unit = sm.get_screen('EditPointScreen').read_widget_text("UNIT")
                if unitname and current_unit != unitname:
                    sm.get_screen('EditPointScreen').add_new_menu_item_to_cfg("UNIT", unitname)
                    sm.get_screen('EditPointScreen').update_widget_text("UNIT", unitname)
                    sm.get_screen('EditPointScreen').refresh_linked_fields("UNIT", unitname)
                    button_values = self.fill_button_defaults({})
                    for field in button_values.keys():
                        if field != "UNIT":
                            sm.get_screen('EditPointScreen').update_widget_text(field, button_values[field])

    def check_for_station_response_x_shot(self, dt):
        # print('.', end = "")
        if self.station.data_waiting():
            if self.station.make in ['Leica']:
                self.station.fetch_point()
            elif self.station.make in ['Leica GeoCom']:
                self.station.fetch_point_leica_geocom()
            elif self.station.make in ['GeoMax']:
                self.station.fetch_point_geomax()
            elif self.station.make in ['Topcon']:
                self.station.fetch_point_topcon()
            if self.station.response:
                self.station.make_global()
                self.station.prism_adjust()
                self.popup.refresh_text(self.make_x_shot_summary())
                if not self.station.xyz.is_none():
                    self.event.cancel()

    def make_x_shot_summary(self):
        if self.station.xyz.is_none():
            return '\n  Waiting....'

        txt = f'\nCoordinates:\n  X:  {self.station.xyz_global.x:.3f}\n  Y:  {self.station.xyz_global.y:.3f}\n  Z:  {self.station.xyz_global.z:.3f}'
        unitname = self.data.point_in_unit(self.station.xyz_global)
        if unitname:
            txt += f'\n\nThe point is in unit {unitname}.'
        if self.station.make != 'Microscribe':
            txt += f'\n\nMeasurement Data:\n  Horizontal angle:  {self.station.decimal_degrees_to_sexa_pretty(self.station.hangle)}\n  ' \
                   f'Vertical angle:  {self.station.decimal_degrees_to_sexa_pretty(self.station.vangle)}\n  ' \
                   f'Slope distance:  {self.station.sloped:.3f}'
            txt += f'\n  X:  {self.station.xyz.x:.3f}\n  Y:  {self.station.xyz.y:.3f}\n  Z:  {self.station.xyz.z:.3f}'
            txt += f'\n\nStation coordinates:\n  X:  {self.station.location.x:.3f}\n  Y:  {self.station.location.y:.3f}\n  Z:  {self.station.location.z:.3f}'
            if self.station.prism_constant:
                txt += f'\n\nPrism constant :  {self.station.prism_constant} m'
            if self.station.received:
                txt += f'\n\nData stream:\n  {self.station.received}'
            if self.station.error_code != 0:
                txt += f'\n{self.station.error_message}'
        return txt

    def record_another_x_shot(self, instance):
        if self.station.make in ['Manual XYZ', 'Manual VHD', 'Simulate', 'Microscribe']:
            self.close_popup(instance)
            self.take_shot(self.measure_button)
        else:
            self.station.take_shot()
            self.popup.refresh_text('\n  Waiting...')
            self.event = Clock.schedule_interval(self.check_for_station_response_x_shot, .1)

    def on_save(self):
        # if self.point_matches_station_coords():
        #     return ['This point matches the station coordinates.  Normally this means that the point was not recorded correctly.  This can happen when the slope distance is 0.  If this is not correct, you will need to delete this point and reshoot it.']
        self.log_the_shot()
        self.update_info_label()
        self.make_backup()
        # self.check_for_duplicate_xyz()
        return []

    def log_the_shot(self):
        logger = logging.getLogger(__name__)
        logger.info(f'{self.get_last_squid()} {self.station.vhd_to_sexa_pretty_compact()} with prism height {self.station.prism.height} '
                        f'from {self.station.location} ')

    def on_cancel(self):
        if self.data.db is not None:
            doc_ids = self.data.get_doc_ids(self.data.table)
            if doc_ids is not None:
                self.data.db.table(self.data.table).remove(doc_ids=[doc_ids[-1]])

    def get_last_squid(self):
        unit = self.get_last_value('UNIT')
        idno = self.get_last_value('ID')
        suffix = self.get_last_value('SUFFIX')
        return f'{unit}-{idno}({suffix})' if all(item is not None for item in [unit, idno, suffix]) else ''

    def update_info_label(self):
        last_squid = self.get_last_squid()
        self.info.text = last_squid if last_squid else 'EDM'
        if self.station.make in ['Simulate']:
            self.info.text += " - SIMULATION mode on"

    def close_popup(self, instance):
        self.popup.dismiss()

    def save_default_cfg(self):
        content = e5_SaveDialog(filename='',
                                start_path=self.cfg.path,
                                save=self.save_default,
                                cancel=self.dismiss_popup)
        self.popup = Popup(title="Create a new default CFG file",
                            content=content,
                            size_hint=(0.9, 0.9), auto_dismiss=False)
        self.popup.open()
        self.popup_open = True

    def save_default(self, *args):
        path = self.popup.content.filesaver.path
        filename = self.popup.content.filename
        if '.cfg' not in filename.lower():
            filename = filename + '.cfg'
        self.do_default_cfg(path, filename)
        self.dismiss_popup()
        self.build_mainscreen()
        self.reset_screens()

    def do_default_cfg(self, path, filename):
        self.data.close()
        self.cfg.initialize()
        self.cfg.build_default()
        self.ini.update_value(APP_NAME, 'CFG', os.path.join(path, filename))
        self.cfg.update_value(APP_NAME, 'DATABASE', os.path.join(path, filename.split('.')[0] + '.json'))
        tbname = filename.split('.')[0]
        tbname = tbname.replace('-', '_')
        tbname = tbname.replace(' ', '_')
        self.cfg.update_value(APP_NAME, 'TABLE', tbname)
        self.data.open(os.path.join(path, filename.split('.')[0] + '.json'))
        self.open_db()
        self.set_new_data_to_true()
        self.cfg.filename = os.path.join(path, filename)
        self.cfg.save()
        self.ini.update(self.colors, self.cfg)

    def set_new_data_to_true(self, table_name=None):
        if table_name is None:
            self.data.new_data['prisms'] = True
            self.data.new_data['units'] = True
            self.data.new_data['datums'] = True
            self.data.new_data[self.data.table] = True
        else:
            self.data.new_data[table_name] = True

    def load_cfg(self, path, filename):
        warnings, errors = [], []
        self.data.close()
        self.dismiss_popup()
        has_errors, errors = self.cfg.load(os.path.join(path, filename[0]))
        if not has_errors:
            if self.cfg.filename:
                warnings, errors = self.open_db()
                if errors == []:
                    self.set_new_data_to_true()
            self.ini.update(self.colors, self.cfg)
        else:
            self.cfg = CFG()
        self.build_mainscreen()
        self.reset_screens()
        if warnings or errors:
            self.popup = self.warnings_and_errors_popup(warnings, errors, auto_dismiss=False)
            self.popup.open()

    def show_import_csv(self):
        if not self.ready_to_use():
            self.popup = self.message_open_cfg_first()
        else:
            instructions = 'EDM can import data from EDM-Mobile, EDMWin, EDM itself, or user prepared data files.'
            instructions += '  The two import formats are CSV and JSON.'
            instructions += '  CSV files should have a csv or txt extension.  JSON files should have a json extension.'
            instructions += '  See our web site for more information on exporting data from EDM-Mobile and EDMWin.'
            instructions += '  The JSON option is for easy importing from EDM data files.'
            instructions += '  Importing points from JSON files is not yet available.'
            instructions += '  IMPORT: Imported data will overwrite existing data in the case of duplicates.'
            self.popup = e5_PopUpMenu(title="Load which kind of data", message=instructions,
                                        menu_list=['Points', 'Datums', 'Prisms', 'Units'],
                                        menu_selected='',
                                        call_back=self.select_csv_file,
                                        colors=self.colors)
        self.popup.auto_dismiss = False
        self.popup.open()

    def show_csv_datatype(self):
        if not self.ready_to_use():
            self.popup = self.message_open_cfg_first()
        else:
            self.popup = e5_PopUpMenu(title="Export which kind of data", message='',
                                            menu_list=['Points', 'Datums', 'Prisms', 'Units'],
                                            menu_selected='',
                                            call_back=self.show_save_csvs,
                                            colors=self.colors)
        self.popup.auto_dismiss = False
        self.popup.open()

    def select_csv_file(self, instance):
        self.csv_data_type = instance.text
        self.popup.dismiss()
        start_path = self.cfg.path if self.cfg.path else self.app_paths.app_data_path
        content = e5_LoadDialog(load=self.load_csv,
                                cancel=self.dismiss_popup,
                                start_path=start_path,
                                button_color=self.colors.button_color,
                                button_background=self.colors.button_background,
                                filters=['*.csv', '*.CSV', '*.txt', '*.TXT', '*.json', '*.JSON'],
                                font_size=self.colors.button_font_size)
        self.popup = Popup(title="Select CSV or JSON file to import from",
                           content=content,
                           size_hint=(0.9, 0.9),
                           auto_dismiss=False)
        self.popup.open()

    def fix_suffix(self, data):
        for record in data:
            if 'SUFFIX' in record:
                try:
                    record['SUFFIX'] = int(record['SUFFIX'])
                except ValueError:
                    pass
        return data

    def read_csv_file(self, full_filename):
        data = []
        with open(full_filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            for row in reader:
                data.append(row)
        return [field.upper() for field in reader.fieldnames], self.fix_suffix(data)

    def read_json_table(self, full_filename, data_type):
        data = []
        if data_type.upper() in ['DATUMS', 'UNITS', 'PRISMS']:
            data = TinyDB(full_filename).table(data_type.lower()).all()
        fields = data[0].keys() if data else []
        return fields, data

    def check_import_fields_against_cfg_fields(self, fields):
        cfg_fields = self.cfg.fields()
        missing_fields = [field for field in fields if field not in cfg_fields]
        missing_fields = [field for field in missing_fields if field not in ['RECNO', 'TIME']]
        if missing_fields:
            return (f"The following field(s) are present in the import data but not in the current CFG: {', '.join(missing_fields)}. "
                    "Importing these data could cause the loss of data.  Please add these missing fields to the CFG before importing "
                    "these data.")
        else:
            return ""

    def get_unique_key(self, data_record):
        unique_key = []
        for field in self.cfg.unique_together:
            unique_key.append("%s" % data_record[field])
        return ",".join(unique_key)

    def check_unique_together(self, data_record):
        if self.data.db is not None:
            if self.cfg.unique_together and len(self.data.db.table(self.data.table)) > 1:
                unique_key = self.get_unique_key(data_record)
                for doc_id in self.data.doc_ids():
                    if unique_key == self.get_unique_key(self.data.db.table(self.data.table).get(doc_id=doc_id)):
                        return doc_id
        return ''

    def error_check_import(self, fields):
        errors = ''
        if self.csv_data_type == 'Datums':
            if len(fields) < 4:
                errors = '\nThese data seem to have fewer than four fields.  To import datums requires a Name, X, Y, and Z field.  '\
                         'If this is a CSV file, the first row in the file should contain these field names separated by commas.  '\
                         f'The fieldnames read were {fields}.'
            if 'X' not in fields or 'Y' not in fields or 'Z' not in fields or 'NAME' not in fields:
                errors = '\nIf these data are coming from a CSV file, the first row must list the field names (comma delimited) and '\
                         f'must include a field called Name, X, Y and Z.  The fields read were {fields}.'
        if self.csv_data_type == 'Prisms':
            if len(fields) < 2:
                errors = '\nThese data seem to have fewer than two fields.  To import prisms requires a Name and height and optionally '\
                         'an offset field.  If this is a csv file, the first row in the file should contain these field names separated '\
                         f'by commas.  The fieldnames read were {fields}.'
            if 'NAME' not in fields or 'HEIGHT' not in fields:
                errors = '\nIf these data are coming from a CSV file, the first row must list the field names (comma delimited) and must '\
                         f'include a field called Name and Height.  The fields read were {fields}.'
        if self.csv_data_type == 'Units':
            if len(fields) < 5:
                errors = '\nThese data seem to have fewer than five fields.  To import units requires a Unit, Minx, Miny, Maxx, Maxy field.  '\
                         'If this is a CSV file, the first row in the file should contain these field names separated by commas.  '\
                         f'The fieldnames read were {fields}.'
            if 'UNIT' not in fields or 'MINX' not in fields or 'MINY' not in fields or 'MAXX' not in fields or 'MAXY' not in fields:
                errors = '\nIf these data are coming from a CSV file, the first row must list the field names (comma delimited) and '\
                         f'must include at least fields called Unit, Minx, Miny, Maxx, Maxy.  The fields read were {fields}.'
        if self.csv_data_type == 'Points':
            errors = self.check_import_fields_against_cfg_fields(fields)
        return errors

    def build_hash_unique_ids(self):
        hash = {}
        if self.data.db is not None:
            for record in self.data.db.table(self.data.table):
                hash[self.get_unique_key(record)] = record.doc_id
        return hash

    def fix_date_time(self, date, time):
        new_date = date[:date.find(' ')] if " " in date else date
        new_time = time[time.find(" "):] if " " in time else time
        return new_date + new_time

    def import_these(self, data):
        record_count = 0
        replacements = 0
        if self.data.db is not None:
            hash_unique_ids = self.build_hash_unique_ids()
            data_to_insert = []
            for item in data:
                insert_record = {}
                for key, value in item.items():
                    if key.upper() == "UNIT" and self.csv_data_type == "Units":
                        insert_record['NAME'] = value
                    elif (key.upper() == "DATE" or key.upper() == "DAY") and "TIME" in item:
                        insert_record['DATE'] = self.fix_date_time(value, item['TIME'])
                    elif (key.upper() == "DATE" or key.upper() == "DAY") and "time" in item:
                        insert_record['DATE'] = self.fix_date_time(value, item['time'])
                    else:
                        insert_record[key.upper()] = value
                if self.csv_data_type in ['Datums', 'Prisms', 'Units']:
                    if insert_record['NAME'].strip():
                        if len(self.data.get_by_name(self.csv_data_type.lower(), insert_record['NAME'])) > 0:
                            self.data.delete_by_name(self.csv_data_type.lower(), insert_record['NAME'])
                            replacements += 1
                        data_to_insert.append(insert_record)
                if self.csv_data_type == 'Points':
                    # new_docid = self.data.db.table(self.data.table).insert(insert_record)
                    hash_key = self.get_unique_key(insert_record)
                    if hash_key in hash_unique_ids:
                        duplicate_doc_id = hash_unique_ids[hash_key]
                        self.data.db.table(self.data.table).remove(doc_ids=[duplicate_doc_id])
                        replacements += 1
                    # hash_unique_ids[hash_key] = new_docid
                    data_to_insert.append(insert_record)
                record_count += 1
            if self.csv_data_type == 'Points':
                self.data.db.table(self.data.table).insert_multiple(data_to_insert)
            else:
                self.data.db.table(self.csv_data_type.lower()).insert_multiple(data_to_insert)
        return (record_count, replacements)

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
            record_count, replacements = self.import_these(data)

        if errors:
            message = errors
        else:
            if replacements == 0:
                message = '%s %s successfully imported.' % (record_count, self.csv_data_type)
            else:
                message = '%s %s successfully imported.  Of these, %s updated an existing record.' % (record_count, self.csv_data_type, replacements)

        self.popup = e5_MessageBox('CSV Import', message, response_type="OK", call_back=self.close_popup, colors=self.colors)
        self.open_popup()
        return errors

    def add_point_record(self):
        new_record = {}
        new_record = self.fill_default_fields(new_record)
        if self.station.shot_type != 'continue':
            new_record = self.find_unit_and_fill_fields(new_record)
            new_record = self.fill_carry_fields(new_record)
            new_record = self.fill_button_defaults(new_record)
            new_record = self.fill_link_fields(new_record)
            new_record = self.do_increments(new_record)
            new_record['SUFFIX'] = 0
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
        return new_record

    def fill_button_defaults(self, new_record):
        for button_no in range(1, __BUTTONS__):
            button = self.cfg.get_block(f'BUTTON{button_no}')
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
        return new_record

    def do_increments(self, new_record):
        fieldnames = self.cfg.fields()
        for fieldname in fieldnames:
            field = self.cfg.get(fieldname)
            if field.increment:
                try:
                    if fieldname in new_record.keys():
                        new_record[fieldname] = int(new_record[fieldname]) + 1
                    elif self.get_last_numeric_value(fieldname):
                        new_record[fieldname] = int(self.get_last_value(fieldname)) + 1
                    else:
                        new_record[fieldname] = '1'
                except (ValueError, TypeError):
                    pass
        return new_record

    def fill_carry_fields(self, new_record):
        fieldnames = self.cfg.fields()
        for fieldname in fieldnames:
            if fieldname not in __DEFAULT_FIELDS__:
                field = self.cfg.get(fieldname)
                if field.carry:
                    carry_value = self.get_last_value(fieldname)
                    if carry_value:
                        if fieldname in new_record:
                            if new_record[fieldname] is None:
                                new_record[fieldname] = carry_value
                        else:
                            new_record[fieldname] = carry_value
        return new_record

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
        return new_record

    def find_unit_and_fill_fields(self, new_record):
        fields = self.cfg.fields()
        unitname = self.data.point_in_unit(self.station.xyz_global)
        if unitname and "UNIT" in fields:
            new_record['UNIT'] = unitname
            unitfields = self.data.get_link_fields('UNIT', unitname)
            if unitfields:
                for field in unitfields.keys():
                    new_record[field] = unitfields[field]
        return new_record

    def fill_default_fields(self, new_record):
        fields = self.cfg.fields()
        for field in fields:
            value = self.station.format_widget_value(field)
            if value != '':
                new_record[field] = value
            if field == 'DATE':
                new_record['DATE'] = f'{datetime.now().replace(microsecond=0)}'
        return new_record

    def get_last_value(self, field_name):
        if self.data.db is not None:
            if len(self.data.db.table(self.data.table)) > 0:
                doc_ids = self.data.get_doc_ids(self.data.table)
                last_record = self.data.db.table(self.data.table).get(doc_id=doc_ids[-1])
                if last_record != []:
                    if field_name in last_record.keys():
                        return last_record[field_name]
        return None

    def get_last_numeric_value(self, field_name):
        if self.data.db is not None:
            if len(self.data.db.table(self.data.table)) > 0:
                doc_ids = self.data.get_doc_ids(self.data.table)
                for doc_id in reversed(doc_ids):
                    record = self.data.db.table(self.data.table).get(doc_id=doc_id)
                    if record != []:
                        if field_name in record.keys():
                            if self.is_numeric(record[field_name]):
                                return record[field_name]
        return None

    def is_numeric(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def exit_program(self):
        logger = logging.getLogger(__name__)
        logger.info(APP_NAME + ' exited.')
        self.save_window_location()
        App.get_running_app().stop()


class OptionsScreen(Screen):

    def __init__(self, station=None, cfg=None, colors=None, **kwargs):
        super(OptionsScreen, self).__init__(**kwargs)

        self.colors = colors if colors else ColorScheme()
        self.station = station
        self.cfg = cfg

        self.clear_widgets()
        self.layout = GridLayout(cols=1,
                                    spacing=5, padding=5,
                                    size_hint_max_x=MAX_SCREEN_WIDTH,
                                    size_hint_y=1,
                                    pos_hint={'center_x': .5, 'center_y': .5})
        self.add_widget(self.layout)
        self.build_screen()

    def build_screen(self):
        prism = GridLayout(cols=2, size_hint_y=None, spacing=5, padding=5)
        prism.add_widget(e5_label('Prompt for prism height after each point', colors=self.colors))
        prism_switch = Switch(active=self.station.prism_prompt)
        prism_switch.bind(active=self.prism_prompt)
        prism.add_widget(prism_switch)
        prism.height = 100
        self.layout.add_widget(prism)

        self.back_button = e5_button('Back', selected=True, call_back=self.go_back, colors=self.colors)
        self.layout.add_widget(self.back_button)

    def prism_prompt(self, instance, value):
        self.station.prism_prompt = value

    def go_back(self, instance):
        sm.current = 'MainScreen'


class ComTestScreen(Screen):

    def __init__(self, station=None, cfg=None, colors=None, **kwargs):
        super(ComTestScreen, self).__init__(**kwargs)

        self.colors = colors if colors else ColorScheme()
        self.station = station
        self.cfg = cfg

        self.clear_widgets()
        self.layout = GridLayout(cols=1, spacing=5, padding=5,
                                    size_hint_max_x=MAX_SCREEN_WIDTH, size_hint_y=1,
                                    pos_hint={'center_x': .5, 'center_y': .5})
        self.add_widget(self.layout)
        self.build_screen()

    def current_settings_pretty(self):
        txt = f'Current settings:\n{self.station.make}\n{self.station.settings_pretty()}'
        txt += '\nCOM port is '
        txt += 'Open' if self.station.serialcom.is_open else 'Closed'
        return txt

    def on_enter(self):
        sm.get_screen('StationConfigurationScreen').call_back = 'MainScreen'
        self.current_settings.text = self.current_settings_pretty()
        self.station.clear_io()
        self.event = Clock.schedule_interval(self.check_io, .2)

    def check_io(self, dt):
        # print('.', end = "")
        if self.station.data_waiting():
            self.station.receive()
        if self.station.io != '' and self.station.io != self.io.scrolling_label.text:
            '''This is a hack to work around an issue I had when changing the content of
            a scrollbox label.  It wouldn't let me go beyond the size of the original content.
            So now I remove it and  rebuild it.
            '''
            self.layout.remove_widget(self.io)
            self.layout.remove_widget(self.buttons)
            self.io = e5_scrollview_label(self.station.io, popup=False, colors=self.colors)
            self.layout.add_widget(self.io)
            self.layout.add_widget(self.buttons)

    def build_screen(self):
        self.settings = GridLayout(cols=2, spacing=5, padding=5, size_hint=(.2, None))
        self.current_settings = e5_label(self.current_settings_pretty(), colors=self.colors)
        self.settings.add_widget(self.current_settings)
        self.change_settings = e5_button("Change Settings", call_back=self.settings_change, colors=self.colors)
        self.settings.add_widget(self.change_settings)
        self.layout.add_widget(self.settings)

        self.horizontal_angle = GridLayout(cols=2, spacing=5, padding=5, size_hint=(.2, None))
        self.leftside = GridLayout(cols=1, spacing=2, padding=0)
        self.leftside.add_widget(e5_label('Enter angle as ddd.mmss', colors=self.colors))
        self.hangle_input = e5_textinput(write_tab=False, colors=self.colors)
        self.hangle_input.bind(minimum_height=self.hangle_input.setter('height'))
        self.leftside.add_widget(self.hangle_input)
        self.horizontal_angle.add_widget(self.leftside)
        self.set_angle = e5_button("Set H-angle", call_back=self.set_hangle, colors=self.colors)
        self.horizontal_angle.add_widget(self.set_angle)
        self.layout.add_widget(self.horizontal_angle)

        self.record = GridLayout(cols=1, spacing=5, padding=5, size_hint=(.2, None))
        self.measure = e5_button("Record Point", call_back=self.record_point, colors=self.colors)
        self.record.add_widget(self.measure)
        self.layout.add_widget(self.record)

        self.io = e5_scrollview_label('Set an angle or record a point and the communication to the station will appear here.  '
                                        'If nothing is received at all, then it might be a COM port number issue.  '
                                        'If what is received is unreadable, then there is a problem with the speed, parity, data bits, and stop bits.  '
                                        'If everything looks fine, but the angle does not change or a point is not taken, '
                                        'then likely Shannon needs to have a look.  '
                                        'Email the results here to him.', popup=False, colors=self.colors)
        self.layout.add_widget(self.io)

        self.buttons = e5_side_by_side_buttons(text=['Back', 'Clear', 'Copy'],
                                                    id=['back', 'clear', 'copy'],
                                                    call_back=[self.close, self.clear_io, self.copy_io],
                                                    selected=[False, False, False],
                                                    colors=self.colors)
        self.layout.add_widget(self.buttons)

    def clear_io(self, instance):
        self.station.clear_io()
        self.station.clear_serial_buffers()
        self.io.scrolling_label.text = ''

    def copy_io(self, instance):
        Clipboard.copy(self.io.scrolling_label.text)

    def set_hangle(self, instance):
        if self.hangle_input.textbox.text:
            self.station.set_horizontal_angle(self.hangle_input.textbox.text)
            # self.io.scrolling_label.text = self.station.io

    def settings_change(self, instance):
        sm.get_screen('StationConfigurationScreen').call_back = 'ComTestScreen'
        self.event.cancel()
        sm.current = 'StationConfigurationScreen'

    def record_point(self, instance):
        self.station.stop_and_clear_geocom()
        self.station.take_shot()

    def close(self, instance):
        self.event.cancel()
        sm.current = 'MainScreen'


class RecordDatumsScreen(Screen):

    def __init__(self, data=None, station=None, ini=None, colors=None, **kwargs):
        super(RecordDatumsScreen, self).__init__(**kwargs)

        self.colors = colors if colors else ColorScheme()
        self.station = station
        self.data = data
        self.ini = ini

        self.content = BoxLayout(orientation='vertical',
                                    size_hint_y=1, size_hint_max_x=400,
                                    pos_hint={'center_x': .5},
                                    padding=5, spacing=20)
        self.add_widget(self.content)

        self.content.add_widget(e5_label('Provide a name and notes (optional), then record and save.', colors=self.colors))

        self.datum_name = DataGridLabelAndField('Name : ', colors=self.colors)
        self.content.add_widget(self.datum_name)
        self.datum_notes = DataGridLabelAndField('Notes : ', colors=self.colors, note_field=True)
        self.content.add_widget(self.datum_notes)

        self.recorder = datum_recorder('Record datum', station=self.station,
                                        colors=self.colors, setup_type='record_new', data=self.data)
        self.content.add_widget(self.recorder)

        self.results = e5_label('', colors=self.colors)
        self.content.add_widget(self.results)

        self.content.add_widget(e5_side_by_side_buttons(text=['Back', 'Save'],
                                                        id=['cancel', 'save'],
                                                        call_back=[self.cancel, self.check_for_duplicate],
                                                        selected=[False, False],
                                                        colors=self.colors))

    def check_for_duplicate(self, instance):
        if self.data.get_datum(self.datum_name.txt.textbox.text).name is not None:
            message = f'\nOverwrite existing datum {self.datum_name.txt.textbox.text}?'
            self.popup = e5_MessageBox('Overwrite?', message,
                                        response_type="YESNO",
                                        call_back=[self.delete_and_save, self.close_popup],
                                        colors=self.colors,
                                        auto_dismiss=False)
            self.popup.open()
        elif self.datum_name.txt.textbox.text == "":
            self.popup = e5_MessageBox('Error', '\nProvide a datum name before saving.', colors=self.colors)
            self.popup.open()
        else:
            self.save_datum()

    def delete_and_save(self, instance):
        self.popup.dismiss()
        self.data.delete_datum(self.datum_name.txt.texbox.text)
        self.save_datum()

    def save_datum(self):
        error_message = ''
        if self.datum_name.txt.textbox.text == '':
            error_message = '\nProvide a datum name.'
        if self.recorder.result.xyz_global.x is None or self.recorder.result.xyz_global.y is None or self.recorder.result.xyz_global.z is None:
            error_message = '\nThe point was not properly recorded.  Try again.'
        if error_message != '':
            self.popup = e5_MessageBox('Error', error_message, colors=self.colors)
            self.popup.open()
            return

        insert_record = {}
        insert_record['NAME'] = self.datum_name.txt.textbox.text
        insert_record['NOTES'] = self.datum_notes.txt.textbox.text
        insert_record['X'] = str(round(self.recorder.result.xyz_global.x, 3))
        insert_record['Y'] = str(round(self.recorder.result.xyz_global.y, 3))
        insert_record['Z'] = str(round(self.recorder.result.xyz_global.z, 3))
        self.data.db.table('datums').insert(insert_record)
        self.datum_name.txt.textbox.text = ''
        self.datum_notes.txt.textbox.text = ''
        self.recorder.result.text = ''
        self.recorder.result.xyz = None
        self.recorder.result.xyz_global = None
        self.data.new_data['datums'] = True

    def close_popup(self, instance):
        self.popup.dismiss()

    def cancel(self, instance):
        sm.current = 'MainScreen'


class VerifyStationScreen(Screen):

    id = ObjectProperty(None)

    def __init__(self, data=None, station=None, ini=None, colors=None, **kwargs):
        super(VerifyStationScreen, self).__init__(**kwargs)

        self.colors = colors if colors else ColorScheme()
        self.station = station
        self.data = data
        self.ini = ini

        self.content = BoxLayout(orientation='vertical',
                                    size_hint_y=1,
                                    size_hint_max_x=400,
                                    pos_hint={'center_x': .5},
                                    padding=5,
                                    spacing=20)
        self.add_widget(self.content)

        # self.content.add_widget(e5_label('Select a datum to use as verification and record it.', colors = self.colors))

        self.datum1 = datum_selector(text='Select\nverification\ndatum',
                                            data=self.data,
                                            colors=self.colors,
                                            default_datum=self.data.get_datum(self.ini.get_value('SETUPS', 'VERIFICATION')))
        self.content.add_widget(self.datum1)

        self.recorder = datum_recorder('Record\nverification\ndatum', station=self.station,
                                        colors=self.colors, setup_type='verify',
                                        on_record=self.compute_error, data=self.data)
        self.content.add_widget(self.recorder)

        self.results = e5_label('', colors=self.colors)
        self.content.add_widget(self.results)

        self.back_button = e5_button(text='Back', size_hint_y=None,
                                        size_hint_x=1,
                                        id='cancel',
                                        colors=self.colors, selected=False)
        self.content.add_widget(self.back_button)
        self.back_button.bind(on_press=self.close_screen)

    def on_enter(self, *args):
        if len(self.data.names('datums')) == 0:
            message = '\nBefore you can use this option, you need to define some datums.  Go to the menu Edit Datums or to Setup Record Datums to add datums.'
            self.popup = e5_MessageBox('Datums', message, call_back=self.close_popup, colors=self.colors)
            self.popup.open()
        return super().on_enter(*args)

    def compute_error(self):
        if not self.datum1.datum.is_none():
            error = self.station.round_point(self.station.vector_subtract(self.datum1.datum, self.recorder.result.xyz_global))
            self.results.text = f'\n  X error: {error.x}\n  Y error: {error.y}\n  Z error: {error.z}'
        else:
            self.results.text = "Select the name of the verification datum before recording the datum."

    def close_popup(self, instance):
        self.popup.dismiss()
        self.close_screen(instance)

    def close_screen(self, instance):
        if not self.datum1.datum.is_none():
            self.ini.update_value('SETUPS', 'VERIFICATION', self.datum1.datum.name)
            self.ini.save()
        sm.current = 'MainScreen'


class record_button(e5_button):

    popup = ObjectProperty(None)
    datum_name = None

    def __init__(self, station=None, result_label=None, setup_type=None, on_record=None,
                        datum1=None, datum2=None, datum3=None, data=None, **kwargs):
        super(record_button, self).__init__(**kwargs)
        # self.colors = colors if colors is not None else ColorScheme()
        self.station = station
        self.bind(on_press=self.record_datum)
        self.result_label = result_label
        self.setup_type = setup_type
        self.on_record = on_record
        self.datum1 = datum1
        self.datum2 = datum2
        self.datum3 = datum3
        self.data = data
        self.default_prism = prism()

    def is_numeric(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def record_datum(self, instance):
        self.set_angle()

    def get_angle(self):
        if self.id == 'datum1':
            if self.setup_type == 'Over a datum + Record a datum':
                if self.datum1.datum.is_none() or self.datum2.datum.is_none():
                    return None
                else:
                    return self.station.angle_between_points(self.datum1.datum, self.datum2.datum)
            elif self.setup_type == 'Record two datums':
                return 0
        else:
            return None

    def set_angle(self):
        angle = self.get_angle()
        if angle is not None:
            if self.station.make in ['Manual XYZ', 'Manual VHD']:
                message = f'\nAim at {self.datum1.datum.name} and set the horizontal angle to {self.station.decimal_degrees_to_sexa_pretty(angle)}.'
                self.popup = e5_MessageBox('Set horizonal angle', message,
                                            call_back=self.now_take_shot, colors=self.colors)
                self.popup.open()
            elif self.station.make in ['Leica', 'Wild', 'Leica GeoCom', 'Sokkia', 'Topcon', 'GeoMax', 'Simulate']:
                self.popup = self.get_prism_height()
                self.popup.auto_dismiss = False
                self.popup.open()
                self.station.set_horizontal_angle(self.station.decimal_degrees_to_dddmmss(angle))
                self.station.take_shot()
        else:
            if self.station.make in ['Microscribe', 'Manual XYZ', 'Manual VHD']:
                self.wait_for_shot()
            else:
                self.popup = self.get_prism_height()
                self.popup.auto_dismiss = False
                self.popup.open()
                self.station.take_shot()

    def now_take_shot(self, instance):
        self.popup.dismiss()
        self.station.take_shot()
        self.wait_for_shot()

    def wait_for_shot(self):
        if self.station.make == 'Microscribe':
            # self.popup = DataGridTextBox(title = self.text + '.  Waiting on Microscribe...', button_text = ['Cancel', 'Next'], call_back = self.microscribe)
            self.popup = DataGridTextBox(title='EDM',
                                            label=self.text + '.  Waiting on...',
                                            text='<Microscribe>',
                                            button_text=['Cancel', 'Next'],
                                            call_back=self.microscribe,
                                            colors=self.colors)
            self.popup.auto_dismiss = False
            self.popup.open()
        elif self.station.make in ['Manual XYZ', 'Manual VHD']:
            self.popup = edm_manual(type=self.station.make, call_back=self.have_shot_manual, colors=self.colors)
            self.popup.open()

    def have_shot_manual(self, instance):
        if self.station.make in ['Manual XYZ']:
            if self.popup.valid_data():
                p = self.station.text_to_point(f'{self.popup.xcoord.textbox.text},{self.popup.ycoord.textbox.text},{self.popup.zcoord.textbox.text}')
                self.station.xyz = p
                self.station.make_global()
                self.station.vhd_from_xyz()
            else:
                self.station.xyz = point()
        else:
            if self.popup.valid_data():
                self.station.hangle = self.station.dms_to_decdeg(self.popup.hangle.textbox.text)
                self.station.vangle = self.station.dms_to_decdeg(self.popup.vangle.textbox.text)
                self.station.sloped = float(self.popup.sloped.textbox.text)
                self.station.vhd_to_xyz()
            else:
                self.station.xyz = point()
        self.popup.dismiss()
        self.popup = self.get_prism_height()
        self.popup.auto_dismiss = False
        self.popup.open()

    def get_prism_height(self):
        prism_names = self.data.names('prisms') if self.data else []
        if len(prism_names) > 0:
            return DataGridMenuList(title="Select or Enter a Prism Height",
                                        menu_list=prism_names,
                                        menu_selected=self.default_prism.name if self.default_prism.name else '',
                                        call_back=self.have_shot)
        else:
            return DataGridTextBox(title='Enter a Prism Height',
                                        text=str(self.default_prism.height) if self.default_prism.height else '',
                                        call_back=self.have_shot,
                                        button_text=['Back', 'Next'],
                                        colors=self.colors)

    def microscribe(self, instance):
        result = self.popup.result
        self.popup.dismiss()
        p = self.station.text_to_point(result)
        if not p:
            self.popup = e5_MessageBox(title='Error',
                                        message='\n Data not formatted correctly.  EDM expects three floating point numbers separated by commas.',
                                        colors=self.colors)
            self.popup.open()
            return
        self.station.xyz = self.station.mm_to_meters(p)
        if self.setup_type == 'verify' or self.setup_type == 'record_new':
            self.station.make_global()
        else:
            self.station.round_xyz()
        self.have_shot()

    def have_shot(self, instance=None):
        self.popup.dismiss()
        # prism_height = instance.text if not instance.id == 'add_button' else self.popup_textbox.text
        # if self.station.make in ['Leica', 'Leica GeoCom']:
        #     self.station.fetch_point()
        #     self.station.make_global()

        if instance:
            prism_name = instance.text
            if prism_name == 'Add' or prism_name == 'Next':
                try:
                    self.station.prism = prism(None, float(self.popup.txt.textbox.text), None)
                except ValueError:
                    self.station.prism = prism()
            else:
                self.station.prism = self.data.get_prism(prism_name)
        else:
            self.station.prism = prism(None, 0.0, None)
        # try:
        #    if instance:
        #        self.station.prism = self.data.get_prism(instance.txt)
        #    else:
        #        self.station.prism = prism(None, float(self.popup.result), None)
        # except ValueError:
        #    self.station.prism = prism(None, 0.0, None)
        self.default_prism = self.station.prism

        self.event = Clock.schedule_interval(self.check_for_station_response, .1)

    def check_for_station_response(self, dt):
        # print('.', end = "")
        if self.station.data_waiting() or self.station.make in ['Manual XYZ', 'Manual VHD', 'Simulate']:
            if self.station.make in ['Leica']:
                self.station.fetch_point()
            elif self.station.make in ['Leica GeoCom']:
                self.station.fetch_point_leica_geocom()
            elif self.station.make in ['GeoMax']:
                self.station.fetch_point_geomax()
            elif self.station.make in ['Topcon']:
                self.station.fetch_point_topcon()
            if self.station.response or self.station.make in ['Manual XYZ', 'Manual VHD', 'Simulate']:
                self.station.prism_adjust()
                if self.station.xyz.x is not None and self.station.xyz.y is not None and self.station.xyz.z is not None:
                    self.station.make_global()
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
                self.event.cancel()


class record_result(e5_label):
    xyz = point()
    xyz_global = point()


class datum_recorder(GridLayout):

    def __init__(self, text='', datum_no=1, station=None,
                        colors=None, setup_type=None,
                        on_record=None, datum1=None, datum2=None, datum3=None,
                        data=None, **kwargs):
        super(datum_recorder, self).__init__(**kwargs)
        self.padding = 10
        self.spacing = 10
        self.colors = colors if colors is not None else ColorScheme()
        self.station = station
        self.cols = 2
        self.results = []
        self.buttons = []
        self.size_hint_y = None
        self.result = record_result('', colors=self.colors, label_height=100)
        self.button = record_button(text=text if text else 'Record datum %s' % (datum_no),
                                    selected=True,
                                    id='datum%s' % (datum_no),
                                    colors=self.colors,
                                    station=self.station,
                                    result_label=self.result,
                                    setup_type=setup_type,
                                    on_record=on_record,
                                    datum1=datum1,
                                    datum2=datum2,
                                    datum3=datum3,
                                    data=data)
        self.add_widget(self.button)
        self.add_widget(self.result)


class datum_selector(GridLayout):

    datum = None
    popup = ObjectProperty(None)
    popup_open = False

    def __init__(self, text='',
                        data=None, colors=None, default_datum=None,
                        call_back=None,
                        id=None,
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
        self.add_widget(e5_button(text=text, selected=True, call_back=self.show_select_datum, colors=self.colors))
        label = f'Datum: {self.datum.name}\nX: {self.datum.x}\nY: {self.datum.y}\nZ: {self.datum.z}' if not self.datum.is_none() else 'Datum:\nX:\nY:\nZ:'
        self.result = e5_label(label, colors=self.colors, label_height=100)
        self.add_widget(self.result)

    def show_select_datum(self, instance):
        if len(self.data.names('datums')) > 0:
            self.popup = e5_PopUpMenu(title="Select Datum", menu_list=self.data.names('datums'), menu_selected='', call_back=self.datum_selected, colors=self.colors)
        else:
            message = '\nBefore you can setup the station you need to first go back and define stations using the Edit Datums menu or Setup Record Datums menu. '
            message += 'The former lets you add them by hand when you already know their coordinates.  The latter lets you use the station to record datums.'
            self.popup = e5_MessageBox('Create Datums', message, call_back=self.datum_selected, colors=self.colors)
        self.popup.auto_dismiss = False
        self.popup.open()

    def datum_selected(self, instance):
        self.popup.dismiss()
        self.datum = self.data.get_datum(instance.text)
        if self.datum.is_none():
            self.result.text = 'Search error'
            return
        self.result.text = f'Datum: {self.datum.name}\nX: {self.datum.x}\nY: {self.datum.y}\nZ: {self.datum.z}'
        if self.call_back:
            self.call_back(self)


class setups(ScrollView):

    id = ObjectProperty(None)
    popup = ObjectProperty(None)
    popup_open = False
    recorder = []

    def __init__(self, setup_type, data=None, ini=None, station=None, colors=None, **kwargs):
        super(setups, self).__init__(**kwargs)

        self.colors = colors if colors is not None else ColorScheme()
        self.data = data
        self.station = station
        self.ini = ini
        self.recorder = []
        self.bar_width = 10

        self.scrollbox = GridLayout(cols=1, size_hint=(1, None), spacing=5)
        self.scrollbox.bind(minimum_height=self.scrollbox.setter('height'))

        instructions = Label(color=self.colors.text_color,
                             size_hint_y=None,
                             font_size=self.colors.text_font_size if self.colors.text_font_size else 12)

        if setup_type == "Horizontal Angle Only":
            instructions.text = '\nEnter the horizontal angle to uploaded to the station.'
            self.scrollbox.add_widget(instructions)

            # content1 = GridLayout(cols = 2, padding = 10, size_hint_y = None)
            # content1.add_widget(e5_label('Angle (ddd.mmss)', colors = self.colors))
            # self.hangle = e5_textinput(text = '', multiline = False)
            # content1.add_widget(self.hangle)
            # self.scrollbox.add_widget(content1)

            widget = DataGridLabelAndField(col='', prompt='Angle (ddd.mmss)', colors=self.colors, text_length=8, padding=5)
            self.hangle = widget.txt.textbox
            self.scrollbox.add_widget(widget)

            content2 = GridLayout(cols=1, padding=5, size_hint_y=None)
            content2.add_widget(e5_button(text='Upload angle', selected=True, call_back=self.set_hangle, colors=self.colors))
            self.scrollbox.add_widget(content2)

        elif setup_type == "Over a datum":
            instructions.text = '\nUse this option when the station is setup over a known point and you can measure the station height '\
                                'or to set the station location directly (with no station height).  Note this option assumes the horizontal '\
                                'angle is already correct or will be otherwise set.'
            self.scrollbox.add_widget(instructions)

            self.over_datum = datum_selector(text='Select a datum',
                                                data=self.data,
                                                colors=self.colors,
                                                default_datum=self.data.get_datum(self.ini.get_value('SETUPS', 'OVERDATUM')))
            self.scrollbox.add_widget(self.over_datum)

            # content2 = GridLayout(cols = 2, padding = 10, size_hint_y = None)
            # content2.add_widget(e5_label('Station height (optional)'))
            # self.station_height = TextInput(text = '', multiline = False,
            #                                 size_hint_max_y = 30)

            widget = DataGridLabelAndField(col='', prompt='Height (optional)',
                                            colors=self.colors,
                                            text_length=8, padding=5, spacing=20)
            self.station_height = widget.txt.textbox
            # content2.add_widget(self.station_height)

            self.scrollbox.add_widget(widget)

        elif setup_type == "Over a datum + Record a datum":
            instructions.text = "\nSelect the datum under the station and a datum to recorded.  "\
                                "EDM will automatically set the correct horizontal angle and compute the station's XYZ coordinates."
            self.scrollbox.add_widget(instructions)

            self.datum1 = datum_selector(text='Select datum\nunder the\nstation',
                                                data=self.data,
                                                colors=self.colors,
                                                default_datum=self.data.get_datum(self.ini.get_value('SETUPS', 'OVERDATUM')))
            self.scrollbox.add_widget(self.datum1)

            self.datum2 = datum_selector(text='Select datum\nto record',
                                                data=self.data,
                                                colors=self.colors,
                                                default_datum=self.data.get_datum(self.ini.get_value('SETUPS', 'RECORDDATUM')),
                                                call_back=self.datum1_selected)
            self.scrollbox.add_widget(self.datum2)

            datum_name = self.data.get_datum(self.ini.get_value('SETUPS', 'RECORDDATUM'))
            datum_name = f'Record\n{datum_name.name}' if datum_name else 'Record datum 1'
            self.recorder.append(datum_recorder(datum_name, station=self.station, colors=self.colors,
                                                setup_type=setup_type, datum1=self.datum1, datum2=self.datum2,
                                                data=self.data))
            self.scrollbox.add_widget(self.recorder[0])

        elif setup_type == "Record two datums":
            instructions.text = "\nSelect two datums to record. EDM will use triangulation to compute the station's XYZ coordinates.  "\
                                "Always record datum one first and then datum two.  When you record datum one, the horizontal angle will "\
                                "be set to 0.0.  When you accept the setup, the horizontal angle will be reset correctly on datum 2."
            self.scrollbox.add_widget(instructions)

            self.datum1 = datum_selector(text='Select\ndatum\none',
                                                data=self.data,
                                                colors=self.colors,
                                                default_datum=self.data.get_datum(self.ini.get_value('SETUPS', '2DATUMS_DATUM_1')),
                                                call_back=self.datum1_selected)
            self.scrollbox.add_widget(self.datum1)

            self.datum2 = datum_selector(text='Select\ndatum\ntwo',
                                                data=self.data,
                                                colors=self.colors,
                                                default_datum=self.data.get_datum(self.ini.get_value('SETUPS', '2DATUMS_DATUM_2')),
                                                call_back=self.datum2_selected)
            self.scrollbox.add_widget(self.datum2)

            for n in range(2):
                datum_name = self.data.get_datum(self.ini.get_value('SETUPS', '2DATUMS_DATUM_%s' % (n + 1)))
                datum_name = f'Record\n{datum_name.name}' if datum_name else f'Record datum {n + 1}'
                self.recorder.append(datum_recorder(datum_name, datum_no=n + 1, station=station, colors=colors,
                                                    setup_type=setup_type, datum1=self.datum1, datum2=self.datum2, data=self.data))
                self.scrollbox.add_widget(self.recorder[n])

        elif setup_type == "Three datum shift":
            instructions.text = "\nThis option is designed to let one grid be rotated into another and is best for when a block of "\
                                "sediment is being excavated in a lab.  It requires three datums points."
            self.scrollbox.add_widget(instructions)

            self.datum1 = datum_selector(text='Select datum 1',
                                                data=self.data,
                                                colors=self.colors,
                                                default_datum=self.data.get_datum(self.ini.get_value('SETUPS', '3DATUM_SHIFT_GLOBAL_1')),
                                                call_back=self.datum1_selected)
            self.scrollbox.add_widget(self.datum1)

            self.datum2 = datum_selector(text='Select datum 2',
                                                data=self.data,
                                                colors=self.colors,
                                                default_datum=self.data.get_datum(self.ini.get_value('SETUPS', '3DATUM_SHIFT_GLOBAL_2')),
                                                call_back=self.datum2_selected)
            self.scrollbox.add_widget(self.datum2)

            self.datum3 = datum_selector(text='Select datum 3',
                                                data=self.data,
                                                colors=self.colors,
                                                default_datum=self.data.get_datum(self.ini.get_value('SETUPS', '3DATUM_SHIFT_GLOBAL_3')),
                                                call_back=self.datum3_selected)
            self.scrollbox.add_widget(self.datum3)

            for n in range(3):
                datum_name = self.data.get_datum(self.ini.get_value('SETUPS', '3DATUM_SHIFT_GLOBAL_%s' % (n + 1)))
                datum_name = f'Record {datum_name.name}' if datum_name else f'Record datum {n + 1}'
                self.recorder.append(datum_recorder(datum_name, datum_no=n + 1, station=station,
                                                                colors=self.colors, setup_type=setup_type))
                self.scrollbox.add_widget(self.recorder[n])

        instructions.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        instructions.bind(width=lambda instance, value: setattr(instance, 'text_size', (value * .95, None)))

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
        self.recorder[0].children[1].text = f'Record\n{instance.datum.name}'
        self.recorder[0].children[1].datum_name = instance.datum.name

    def datum2_selected(self, instance):
        self.recorder[1].children[1].text = f'Record\n{instance.datum.name}'
        self.recorder[1].children[1].datum_name = instance.datum.name

    def datum3_selected(self, instance):
        self.recorder[2].children[1].text = f'Record\n{instance.datum.name}'
        self.recorder[2].children[1].datum_name = instance.datum.name

    def set_hangle(self, instance):
        if self.hangle:
            self.station.set_horizontal_angle(self.hangle.text)
            logger = logging.getLogger(__name__)
            logger.info(f'Horizontal angle set to {self.hangle.text}')


class InitializeStationScreen(Screen):

    def __init__(self, data=None, station=None, ini=None, colors=None, **kwargs):
        super(InitializeStationScreen, self).__init__(**kwargs)

        self.colors = colors if colors else ColorScheme()
        self.station = station
        self.data = data
        self.ini = ini

        lastsetup_type = self.ini.get_value('SETUPS', 'LASTSETUP_TYPE')
        self.setup = lastsetup_type if lastsetup_type else 'Horizontal Angle Only'

        self.content = BoxLayout(orientation='vertical',
                                    size_hint_y=1, size_hint_max_x=MAX_SCREEN_WIDTH,
                                    pos_hint={'center_x': .5, 'center_y': .5},
                                    padding=5, spacing=5)
        self.add_widget(self.content)

        setup_type_box = GridLayout(cols=1, padding=2, spacing=2, size_hint_y=None)

        setup_type_label = e5_label('Select a setup type from this dropdown', colors=self.colors)
        setup_type_box.add_widget(setup_type_label)

        spinner_dropdown_button = SpinnerOptions
        spinner_dropdown_button.font_size = colors.button_font_size.replace("sp", '') if colors.button_font_size else None
        spinner_dropdown_button.background_color = (0, 0, 0, 1)

        self.setup_type = Spinner(text=self.setup,
                                    values=["Horizontal Angle Only",
                                            "Over a datum",
                                            "Over a datum + Record a datum",
                                            "Record two datums",
                                            "Three datum shift"],
                                    option_cls=spinner_dropdown_button)
        if colors.button_font_size:
            self.setup_type.font_size = colors.button_font_size
        setup_type_box.add_widget(self.setup_type)
        self.setup_type.bind(text=self.rebuild)
        self.content.add_widget(setup_type_box)

        self.scroll_content = BoxLayout(orientation='vertical',
                                        size_hint=(1, .9),
                                        spacing=5, padding=5)

        self.content.add_widget(self.scroll_content)

        self.setup_widgets = setups(self.setup_type.text,
                                    data=self.data,
                                    ini=self.ini,
                                    station=self.station,
                                    colors=self.colors)
        self.scroll_content.add_widget(self.setup_widgets)

        self.content.add_widget(e5_side_by_side_buttons(text=['Back', 'Accept Setup'],
                                                        id=['back', 'accept'],
                                                        call_back=[self.go_back, self.accept_setup],
                                                        selected=[False, False],
                                                        colors=self.colors))

    def rebuild(self, instance, value):
        self.setup = value
        self.scroll_content.clear_widgets()
        self.setup_widgets = setups(self.setup_type.text,
                                        data=self.data,
                                        ini=self.ini,
                                        station=self.station,
                                        colors=self.colors)
        self.scroll_content.add_widget(self.setup_widgets)
        if value not in ['Horizontal Angle Only']:
            if len(self.data.names('datums')) == 0:
                message = '\nBefore you can use this option, you need to define some datums.  '
                message += 'Go to the menu Edit Datums or to Setup Record Datums to add datums.'
                self.popup = e5_MessageBox('Datums', message, call_back=self.close_popup, colors=self.colors)
                self.popup.open()

    def go_back(self, instance):
        self.ini.update_value(APP_NAME, 'LASTSETUP_TYPE', self.setup_type.text)
        sm.current = 'MainScreen'

    def accept_setup(self, instance):
        self.new_station = point()
        self.foresight = None
        txt = ''
        error_message = ''

        if self.setup_type.text == 'Horizontal Angle Only':
            if self.station.location.is_none() is True:
                txt = '\nThe location of the station has not been set.'
            else:
                txt = f'\nThe location of the station is at {str(self.station.location)}.  '\
                      'All measured points will be relative to that point and the horizontal angle uploaded here.'

        elif self.setup_type.text == 'Over a datum':
            if self.setup_widgets.over_datum.datum is None:
                error_message = '\nSelect the datum under the total station and optionally provide the station height.'
            else:
                station_height = float(self.setup_widgets.station_height.text) if self.setup_widgets.station_height.text else 0
                self.new_station = self.setup_widgets.over_datum.datum
                self.new_station.z += station_height
                txt = f'\nSet the station coordinates to\nX : {self.new_station.x}\nY : {self.new_station.y}\nZ : {self.new_station.z}'

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
                txt += '\nIf the setup as measured is accepted, the new station coordinates will be \n'\
                        f'X : {self.new_station.x}\nY : {self.new_station.y}\nZ : {self.new_station.z}'

        elif self.setup_type.text == 'Record two datums':
            if self.setup_widgets.datum1.datum is None or self.setup_widgets.datum2.datum is None:
                error_message = '\nSelect two datums to record.'
            elif self.setup_widgets.datum1.datum == self.setup_widgets.datum2.datum:
                error_message = '\nSelect two different datums.'
            elif self.station.subtract_points(self.setup_widgets.datum1.datum, self.setup_widgets.datum2.datum) == point(0, 0, 0):
                error_message = '\nSelect two different datums with different coordinates.'
            elif self.setup_widgets.recorder[0].result.xyz.is_none() or self.setup_widgets.recorder[1].result.xyz.is_none():
                error_message = '\nRecord each datum.  It is important that the first datum is recorded and then the second and not the other way around.  '\
                                'Note that before the first datum is recorded, a horizontal angle of 0.0000 will be uploaded.'
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
                x = round(-1 * self.setup_widgets.recorder[0].result.xyz.y * sin(d2r(angle_difference)) + self.setup_widgets.datum1.datum.x, 3)
                y = round(-1 * self.setup_widgets.recorder[0].result.xyz.y * cos(d2r(angle_difference)) + self.setup_widgets.datum1.datum.y, 3)
                z1 = self.setup_widgets.datum1.datum.z - self.setup_widgets.recorder[0].result.xyz.z
                z2 = self.setup_widgets.datum2.datum.z - self.setup_widgets.recorder[1].result.xyz.z
                z = round((z1 + z2) / 2, 3)
                self.new_station = point(x, y, z)

                # Workout what angle needs to be uploaded to the station
                self.foresight = self.station.angle_between_points(self.new_station, self.setup_widgets.datum2.datum.as_point())
                txt = f'\nThe measured distance between {self.setup_widgets.datum1.datum.name} and {self.setup_widgets.datum2.datum.name} '
                txt += f'was {round(measured_distance, 3)} m.  The distance based on the datum definitions should be {round(actual_distance, 3)} m.  '
                txt += f'The error is {round(error_distance, 3)} m.\n'
                txt += '\nIf the setup as measured is accepted, the new station coordinates will be \n'
                txt += f'X : {self.new_station.x}\nY : {self.new_station.y}\nZ : {self.new_station.z}\n'
                txt += f'\nAn angle of {self.station.decimal_degrees_to_sexa_pretty(self.foresight)} '
                txt += 'will be uploaded (do not turn the station until this angle is set).'
                self.foresight = self.station.decimal_degrees_to_dddmmss(self.foresight)

        elif self.setup_type.text == 'Three datum shift':
            if any([widget.is_none() for widget in [self.setup_widgets.datum1.datum, self.setup_widgets.datum2.datum, self.setup_widgets.datum3.datum]]):
                error_message = '\nSelect three datums to record.'
            elif any([xyz.is_none() for xyz in [self.setup_widgets.recorder[n].result.xyz for n in range(3)]]):
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

                txt = f'\nThe following errors are noted.  The actual distance between datums 1 and 2 is {round(dist_12_datums, 3)} and '
                txt += f'the measured distance was {round(dist_12_measured, 3)}.  '
                txt += f'The actual distance between datums 2 and 3 is {round(dist_23_datums, 3)} and the measured distance was {round(dist_23_measured, 3)}.  '
                txt += f'The actual distance between datums 1 and 3 is {round(dist_13_datums, 3)} and the measured distance was {round(dist_13_measured, 3)}.  '
                txt += f'\n\nThis corresponds to errors of {dist_12_error}, {dist_23_error}, and {dist_13_error}, respectively.'

        if not self.new_station.is_none() or txt:
            self.popup = e5_MessageBox('Accept setup?', txt, response_type="YESNO", call_back=[self.set_and_close, self.close_popup], colors=self.colors)
        else:
            self.popup = e5_MessageBox('Error', error_message, colors=self.colors)

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
                logger.info(f'Setup 3 datum shift using {self.setup_widgets.datum1.datum}, {self.setup_widgets.datum2.datum}, and \
                                {self.setup_widgets.datum3.datum}')
                logger.info(f'Recorded values were respectively {self.setup_widgets.recorder[0].result.xyz}, {self.setup_widgets.recorder[1].result.xyz}, and \
                                {self.setup_widgets.recorder[2].result.xyz}')

        self.popup.dismiss()
        if self.foresight:
            self.station.set_horizontal_angle(self.foresight)
            logger.info(f'Horizontal angle set to {self.foresight}')
        if self.new_station.is_none() is False:
            self.station.location = self.new_station
            logger.info('Station location set to ' + str(self.station.location))
            self.ini.update_value('SETUPS', 'STATIONX', self.station.location.x)
            self.ini.update_value('SETUPS', 'STATIONY', self.station.location.y)
            self.ini.update_value('SETUPS', 'STATIONZ', self.station.location.z)
        self.ini.update_value('SETUPS', 'LASTSETUP_TYPE', self.setup_type.text)
        self.ini.save()
        sm.current = 'MainScreen'


class EditLastRecordScreen(e5_RecordEditScreen):
    pass


class EditPointScreen(e5_RecordEditScreen):

    def reset_defaults_from_recorded_point(self, station):
        for widget in self.layout.walk():
            if hasattr(widget, 'id'):
                value = station.format_widget_value(widget.id)
                if value != '':
                    widget.text = str(value)


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

    def __init__(self, label_text='', spinner_values=(), default='',
                        id=None, call_back=None, colors=None, station=None, **kwargs):
        super(station_setting, self).__init__(**kwargs)

        self.station = station
        self.id = id
        self.cols = 2
        self.pos_hint = {'center_x': .5},
        self.colors = colors
        self.label = e5_label(text=label_text + ' : ', colors=colors, halign='right')
        self.add_widget(self.label)

        # Create a default dropdown button and then modify its properties
        # For some reason, the usual font size specification doesn't work here and sp has to be removed
        spinner_dropdown_button = SpinnerOptions
        spinner_dropdown_button.font_size = colors.button_font_size.replace("sp", '') if colors.button_font_size else None
        spinner_dropdown_button.background_color = (0, 0, 0, 1)

        self.spinner = Spinner(text=default if default is not None else '',
                                values=spinner_values,
                                font_size=colors.button_font_size if colors.button_font_size else None,
                                option_cls=spinner_dropdown_button)
        if label_text == 'Port Number':
            comport = GridLayout(cols=2, spacing=5)
            comport.bind(minimum_height=comport.setter('height'))
            comport.add_widget(self.spinner)
            scan_button = e5_button('Scan', colors=colors, call_back=self.scanner, button_height=comport.height)
            comport.add_widget(scan_button)
            self.add_widget(comport)
        else:
            self.add_widget(self.spinner)
        if call_back:
            self.spinner.bind(text=call_back)

    def scanner(self, instance):
        if self.station:
            ports = self.station.list_comports()
            text = 'Available ports:\n\n'
            for port in ports:
                text += f"{port[0]['port']} - {port[0]['desc'][0:port[0]['desc'].find('(') - 1]}\n"
            self.spinner.values = list([port[0]['port'] for port in ports])
            self.popup = e5_MessageBox('COM Ports', text,
                                        response_type="OK",
                                        call_back=self.close_popup_comports,
                                        colors=self.colors)
            self.popup.open()
            self.popup_open = True
        else:
            self.event1 = Clock.schedule_once(self.show_popup_message, .2)
            self.event2 = Clock.schedule_interval(self.check_comports, .2)

    def show_popup_message(self, dt):
        # print('.', end = "")
        self.popup = e5_MessageBox('COM Ports', '\nLooking for valid COM ports...This can take several seconds...'
                                                    'And the Cancel button might appear non-responsive...',
                                    response_type="CANCEL",
                                    call_back=self.close_popup,
                                    colors=self.colors)
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
            ser = serial.Serial(port=portName)
            ser.close()
            return portName
        except:
            return None

    def check_comports(self, dt):
        # print('.', end = "")
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
            self.valid_comports.append(self.comportIsUsable(f"COM{self.comport_to_test}"))

    def comports(self):
        return list(filter(None.__ne__, [self.comportIsUsable(f"COM{comno}") for comno in range(1, __LASTCOMPORT__ + 1)]))


class StationConfigurationScreen(Screen):

    def __init__(self, station=None, ini=None, colors=None, **kwargs):
        super(StationConfigurationScreen, self).__init__(**kwargs)

        self.station = station
        self.colors = colors
        self.ini = ini
        self.call_back = 'MainScreen'

    def on_enter(self):
        self.clear_widgets()
        self.layout = GridLayout(cols=1, spacing=5, padding=5,
                                    size_hint_max_x=MAX_SCREEN_WIDTH, size_hint_y=1,
                                    pos_hint={'center_x': .5, 'center_y': .5})
        self.add_widget(self.layout)
        self.build_screen()

    def build_screen(self):
        self.station_type = station_setting(label_text='Station type',
                                            spinner_values=("Leica", "Leica GeoCom", "GeoMax", "Wild", "Topcon", "Sokkia", "Microscribe",
                                                                "Manual XYZ", "Manual VHD", "Simulate"),
                                            call_back=self.toggle_buttons,
                                            id='station_type',
                                            colors=self.colors,
                                            default=self.ini.get_value(APP_NAME, 'STATION'))
        self.layout.add_widget(self.station_type)

        self.communications = station_setting(label_text='Communications',
                                                spinner_values=("Serial", "Bluetooth"),
                                                id='communications',
                                                colors=self.colors,
                                                default=self.ini.get_value(APP_NAME, 'COMMUNICATIONS'))
        self.layout.add_widget(self.communications)

        self.comports = station_setting(label_text='Port Number',
                                            spinner_values=[f'COM{n + 1}' for n in range(__LASTCOMPORT__)],
                                            id='comport',
                                            colors=self.colors, station=self.station,
                                            default=self.ini.get_value(APP_NAME, 'COMPORT'))
        self.layout.add_widget(self.comports)

        self.baud_rate = station_setting(label_text='Baud rate',
                                            spinner_values=("1200", "2400", "4800", "9600", "14400", "19200", "38400", "115200"),
                                            id='baudrate',
                                            colors=self.colors,
                                            default=self.ini.get_value(APP_NAME, 'BAUDRATE'))
        self.layout.add_widget(self.baud_rate)

        self.parity = station_setting(label_text='Parity',
                                            spinner_values=("Even", "Odd", "None"),
                                            id='parity',
                                            colors=self.colors,
                                            default=self.ini.get_value(APP_NAME, 'PARITY'))
        self.layout.add_widget(self.parity)

        self.data_bits = station_setting(label_text='Databits',
                                            spinner_values=("7", "8"),
                                            id='databits',
                                            colors=self.colors,
                                            default=self.ini.get_value(APP_NAME, 'DATABITS'))
        self.layout.add_widget(self.data_bits)

        self.stop_bits = station_setting(label_text='Stopbits',
                                            spinner_values=("0", "1", "2"),
                                            id='stopbits',
                                            colors=self.colors,
                                            default=self.ini.get_value(APP_NAME, 'STOPBITS'))
        self.layout.add_widget(self.stop_bits)

        self.buttons = e5_side_by_side_buttons(text=['Back', 'Set'],
                                                id=['Back', 'Set'],
                                                selected=[True, False],
                                                call_back=[self.close_screen, self.update_ini],
                                                colors=self.colors)
        self.layout.add_widget(self.buttons)
        self.toggle_buttons(None, None)
        self.changes = False

    def toggle_buttons(self, instance, value):
        disabled = self.station_type.spinner.text in ['Simulate', 'Microscribe', 'Manual XYZ', 'Manual VHD']
        self.stop_bits.spinner.disabled = disabled
        self.parity.spinner.disabled = disabled
        self.data_bits.spinner.disabled = disabled
        self.baud_rate.spinner.disabled = disabled
        self.comports.spinner.disabled = disabled
        self.communications.spinner.disabled = disabled

    def update_ini(self, instance):
        self.station.make = self.station_type.spinner.text
        self.ini.update_value(APP_NAME, 'STATION', self.station_type.spinner.text)

        self.station.stopbits = self.stop_bits.spinner.text
        self.ini.update_value(APP_NAME, 'STOPBITS', self.stop_bits.spinner.text)

        self.station.baudrate = self.baud_rate.spinner.text
        self.ini.update_value(APP_NAME, 'BAUDRATE', self.baud_rate.spinner.text)

        self.station.databits = self.data_bits.spinner.text
        self.ini.update_value(APP_NAME, 'DATABITS', self.data_bits.spinner.text)

        self.station.comport = self.comports.spinner.text
        self.ini.update_value(APP_NAME, 'COMPORT', self.comports.spinner.text)

        self.station.parity = self.parity.spinner.text
        self.ini.update_value(APP_NAME, 'PARITY', self.parity.spinner.text)

        self.station.communication = self.communications.spinner.text
        self.ini.update_value(APP_NAME, 'COMMUNICATIONS', self.communications.spinner.text)

        self.ini.save()

        if self.station.make in ['Simulate', 'Manual XYZ', 'Manual VHD', 'Microscribe', '']:
            self.close_screen(None)
        else:
            self.popup = e5_MessageBox('EDM', "\nSetting up communications.  Setup will timeout after 30 seconds if communications with these settings fails, and you will receive an error message.", response_type="NONE", colors=self.colors)
            self.popup.open()
            self.event = Clock.schedule_once(self.test_open, 5)

    def test_open(self, instance):
        success = self.station.open()
        self.popup.dismiss()
        if success == '':
            self.close_screen(None)
        else:
            self.popup = e5_MessageBox('Error', success, colors=self.colors)
            self.popup.open()

    def close_screen(self, value):
        sm.current = self.call_back


class AboutScreen(e5_InfoScreen):

    def on_pre_enter(self):
        self.content.text = '\n\nEDM by Shannon P. McPherron\n\nVersion ' + VERSION + ' Cranberry Pie\n\n'
        self.content.text += f'Built using Python 3.8, Kivy {__kivy_version__} and TinyDB {__tinydb_version__}\n\n'
        self.content.text += 'An OldStoneAge.Com Production\n\n' + PRODUCTION_DATE
        self.content.halign = 'center'
        self.content.valign = 'middle'
        self.content.color = self.colors.text_color
        self.back_button.background_color = self.colors.button_background
        self.back_button.color = self.colors.button_color


class StatusScreen(e5_InfoScreen):

    def __init__(self, data=None, ini=None, cfg=None, station=None, **kwargs):
        super(StatusScreen, self).__init__(**kwargs)
        self.data = data
        self.ini = ini
        self.cfg = cfg
        self.station = station

    def on_pre_enter(self):
        app_paths = AppDataPaths(APP_NAME)
        txt = self.data.status() if self.data else 'A data file has not been initialized or opened.\n\n'
        txt += self.cfg.status() if self.cfg else 'A CFG is not open.\n\n'
        txt += self.ini.status() if self.ini else 'An INI file is not available.\n\n'
        txt += self.station.status() if self.station else 'Total station information is not available.\n\n'
        txt += f'\nThe default user path is {app_paths.app_data_path}.\n'
        logger = logging.getLogger(__name__)
        txt += f'\nThe log is written to {logger.handlers[0].baseFilename}\n'
        txt += f'\nThe operating system is {platform_name()}.\n'
        txt += f'\nPython build is {python_version()}.\n'
        txt += f'\nLibraries installed include Kivy {__kivy_version__} and TinyDB {__tinydb_version__}.\n'
        txt += '\nEDM was tested and distributed most recently on Python 3.8.6, Kivy 2.1.0 and TinyDB 4.4.0.\n'
        self.content.text = txt
        self.content.color = self.colors.text_color
        self.back_button.background_color = self.colors.button_background
        self.back_button.color = self.colors.button_color


sm = ScreenManager()


class EDMApp(App):

    def __init__(self, **kwargs):
        super(EDMApp, self).__init__(**kwargs)
        self.setup_paths()

    def setup_paths(self):
        ini_file_path = user_data_dir(APP_NAME, 'OSA')
        self.make_path(ini_file_path)

        log_file_path = user_log_dir(APP_NAME, 'OSA')
        self.make_path(log_file_path)

        doc_file_path = user_documents_dir()
        self.make_path(doc_file_path)

    def make_path(self, pathname):
        if not os.path.isdir(pathname):
            os.makedirs(pathname, exist_ok=True)

    def build(self):
        sm.add_widget(MainScreen(name='MainScreen'))
        sm.current = 'MainScreen'
        self.title = f"{APP_NAME} {VERSION}"
        if 'exit' in sys.argv:
            self.stop()
        return sm


Factory.register(APP_NAME, cls=EDMApp)


if __name__ == '__main__':
    Config.set('input', 'mouse', 'mouse,multitouch_on_demand')      # Removes red dot
    Config.set('kivy', 'exit_on_escape', '0')
    EDMApp().run()
