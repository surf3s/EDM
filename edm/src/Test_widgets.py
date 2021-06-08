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

from e5_widgets import *
from main import *

sm = ScreenManager(id = 'screen_manager')

class micro_test(Screen):
    def __init__(self, **kwargs):
        super(micro_test, self).__init__(**kwargs)

        tester = DataGridTextBox(title = 'EDM',
                                    label = 'Datum1' + '.  Waiting on Microscribe...',
                                    button_text = ['Cancel', 'Next'],
                                    call_back = self.next)
        self.add_widget(tester)
    
    def next(self, instance):
        print('next')

class EDM(App):

    def build(self):
        a = 0
        if a == 0 :
            sm.add_widget(micro_test(name = 'test', id = 'test'))
            return(sm)
    
        elif a == 1:
            self.colors = ColorScheme()
            self.ini = INI()
            self.cfg = CFG()
            self.data = DB()
            self.station = totalstation()

            tester = Screen()

            self.content = BoxLayout(orientation = 'vertical',
                                    size_hint_y = .9,
                                    size_hint_x = .8,
                                    pos_hint={'center_x': .5},
                                    id = 'content',
                                    padding = 20,
                                    spacing = 20)
            tester.add_widget(self.content)

            setup_type_box = GridLayout(cols = 2, size_hint = (1, .2))
            setup_type_box.add_widget(e5_label('Setup type', colors = self.colors))
            self.setup_type = Spinner(text = '',
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
            self.content.add_widget(setup_type_box)

            self.scroll_content = BoxLayout(orientation = 'vertical', size_hint = (1, .8),
                                            spacing = 5, padding = 5)
            self.content.add_widget(self.scroll_content)

            test = setups(data = self.data, ini = self.ini, station = self.station, setup_type = 'Three datum shift', )

            self.scroll_content.add_widget(test)

            return(tester)


if __name__ == '__main__':
    EDM().run()

