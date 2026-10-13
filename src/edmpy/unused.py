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
        self.bar_width = SCROLLBAR_WIDTH

        self.scrollbox = GridLayout(cols=1, size_hint=(1, None), spacing=5)
        self.scrollbox.bind(minimum_height=self.scrollbox.setter('height'))

        instructions = Label(color=self.colors.text_color,
                             size_hint_y=None,
                             font_size=self.colors.text_font_size if self.colors.text_font_size else 12)

        if setup_type == "Horizontal Angle Only":
            instructions.text = '\nEnter the horizontal angle to uploaded to the station.  Angle should be in degrees, minutes, seconds format (ddd.mmss).'
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
            instructions.text = "\nSelect the datum under the station and a datum to record.  "\
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
                datum_name = f'Record {datum_name.name}' if datum_name.name is not None else f'Record datum {n + 1}'
                self.recorder.append(datum_recorder(datum_name, datum_no=n + 1, station=station,
                                                                colors=self.colors, setup_type=setup_type, datum1=self.datum1, datum2=self.datum2, datum3=self.datum3, data=self.data))
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

    def on_enter(self, *args):
        self.rebuild(None, self.setup)
        print('rebuild')

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
