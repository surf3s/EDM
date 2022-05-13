class MenuList(Popup):
    def __init__(self, title, menu_list, call_back, **kwargs):
        super(MenuList, self).__init__(**kwargs)
        __content = GridLayout(cols = 1, spacing = 5, size_hint_y = None)
        __content.bind(minimum_height=__content.setter('height'))
        for menu_item in menu_list:
            __button = Button(text = menu_item, size_hint_y = None, id = title,
                        color = OPTIONBUTTON_COLOR,
                        background_color = OPTIONBUTTON_BACKGROUND,
                        background_normal = '')
            __content.add_widget(__button)
            __button.bind(on_press = call_back)
        if title!='PRISM':
            __new_item = GridLayout(cols = 2, spacing = 5, size_hint_y = None)
            __new_item.add_widget(TextInput(size_hint_y = None, id = 'new_item'))
            __add_button = Button(text = 'Add', size_hint_y = None,
                                    color = BUTTON_COLOR,
                                    background_color = BUTTON_BACKGROUND,
                                    background_normal = '', id = title)
            __new_item.add_widget(__add_button)
            __add_button.bind(on_press = call_back)
            __content.add_widget(__new_item)
        __button1 = Button(text = 'Back', size_hint_y = None,
                                color = BUTTON_COLOR,
                                background_color = BUTTON_BACKGROUND,
                                background_normal = '')
        __content.add_widget(__button1)
        __button1.bind(on_press = self.dismiss)
        __root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height/1.9))
        __root.add_widget(__content)
        self.title = title
        self.content = __root
        self.size_hint = (None, None)
        self.size = (400, 400)
        self.auto_dismiss = True

class TextNumericInput(Popup):
    def __init__(self, title, call_back, **kwargs):
        super(TextNumericInput, self).__init__(**kwargs)
        __content = GridLayout(cols = 1, spacing = 5, size_hint_y = None)
        __content.bind(minimum_height=__content.setter('height'))
        __content.add_widget(TextInput(size_hint_y = None, multiline = False, id = 'new_item'))
        __add_button = Button(text = 'Next', size_hint_y = None,
                                    color = BUTTON_COLOR,
                                    background_color = BUTTON_BACKGROUND,
                                    background_normal = '', id = title)
        __content.add_widget(__add_button)
        __add_button.bind(on_press = call_back)
        __button1 = Button(text = 'Back', size_hint_y = None,
                                color = BUTTON_COLOR,
                                background_color = BUTTON_BACKGROUND,
                                background_normal = '')
        __content.add_widget(__button1)
        __button1.bind(on_press = self.dismiss)
        __root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height/1.9))
        __root.add_widget(__content)
        self.title = title
        self.content = __root
        self.size_hint = (None, None)
        self.size = (400, 400)
        self.auto_dismiss = True

class MessageBox(Popup):
    def __init__(self, title, message, **kwargs):
        super(MessageBox, self).__init__(**kwargs)
        __content = BoxLayout(orientation = 'vertical')
        __label = Label(text = message, size_hint=(1, 1), valign='middle', halign='center')
        __label.bind(
            width=lambda *x: __label.setter('text_size')(__label, (__label.width, None)),
            texture_size=lambda *x: __label.setter('height')(__label, __label.texture_size[1]))
        __content.add_widget(__label)
        __button1 = Button(text = 'Back', size_hint_y = .2,
                            color = BUTTON_COLOR,
                            background_color = BUTTON_BACKGROUND,
                            background_normal = '')
        __content.add_widget(__button1)
        __button1.bind(on_press = self.dismiss)
        self.title = title
        self.content = __content
        self.size_hint = (.8, .8)
        self.size=(400, 400)
        self.auto_dismiss = True

class YesNo(Popup):
    def __init__(self, title, message, yes_callback, no_callback, **kwargs):
        super(YesNo, self).__init__(**kwargs)
        __content = BoxLayout(orientation = 'vertical')
        __label = Label(text = message, size_hint=(1, 1), valign='middle', halign='center')
        __label.bind(
            width=lambda *x: __label.setter('text_size')(__label, (__label.width, None)),
            texture_size=lambda *x: __label.setter('height')(__label, __label.texture_size[1]))
        __content.add_widget(__label)
        __button1 = Button(text = 'Yes', size_hint_y = .2,
                            color = BUTTON_COLOR,
                            background_color = BUTTON_BACKGROUND,
                            background_normal = '')
        __content.add_widget(__button1)
        __button1.bind(on_press = yes_callback)
        __button2 = Button(text = 'No', size_hint_y = .2,
                            color = BUTTON_COLOR,
                            background_color = BUTTON_BACKGROUND,
                            background_normal = '')
        __content.add_widget(__button2)
        __button2.bind(on_press = no_callback)
        self.title = title
        self.content = __content
        self.size_hint = (.8, .8)
        self.size=(400, 400)
        self.auto_dismiss = True
