from kivy.properties import ObjectProperty
from kivy.clock import Clock

import serial
from serial.serialutil import SerialTimeoutException
import os
from geo import point, prism
from constants import APP_NAME
from math import sqrt
from math import pi
from math import cos
from math import sin
from math import acos
from angles import r2d, deci2sexa, Angle
import string
import random
import time

if os.name == 'nt':  # sys.platform == 'win32':
    from serial.tools.list_ports_windows import comports
elif os.name == 'posix':
    from serial.tools.list_ports_posix import comports
# ~ elif os.name == 'java':
else:
    raise ImportError("Sorry: no implementation for your platform ('{}') available".format(os.name))

NO_ERROR = 0            # No total station error (Leica)
TMC_CLEAR = 3           # Stop the current measure and clear the stored values
TOPCON_TERMINATION = "\r\n"


class totalstation(object):

    popup = ObjectProperty(None)
    popup_open = False
    # rotate_source = []
    # rotate_destination = []

    def __init__(self, make=None, model=None):
        self.make = make if make else 'Manual XYZ'
        self.model = model
        self.communication = ''
        self.comport = ''
        self.baudrate = ''
        self.parity = ''
        self.databits = 0
        self.stopbits = 0
        self.comport_settings = ''
        self.serialcom = serial.Serial()
        self.serial_bt_input = serial.Serial()
        self.input_string = ''
        self.output_string = ''
        self.port_open = False
        self.location = point(0, 0, 0)
        self.xyz = point()
        self.prism_constant = 0.0
        self.prism_offset = 0.0
        self.prism_prompt = True
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
        self.io = ''                    # Used in debug mode to show back and forth with the station
        self.received = ''              # Used in normal com to store the last line received
        self.response = ''              # Used to store just the values returned from the station (with extra info deleted)
        self.error_code = 0             # A place to put io error messages
        self.error_message = ''         # A place to put io error messages
        self.open()

    def setup(self, ini, data):
        if ini.get_value(APP_NAME, 'STATION'):
            self.make = ini.get_value(APP_NAME, 'STATION')
        if ini.get_value(APP_NAME, 'COMMUNICATIONS'):
            self.communication = ini.get_value(APP_NAME, 'COMMUNICATIONS')
        if ini.get_value(APP_NAME, 'COMPORT'):
            self.comport = ini.get_value(APP_NAME, 'COMPORT')
        if ini.get_value(APP_NAME, 'BAUDRATE'):
            self.baudrate = ini.get_value(APP_NAME, 'BAUDRATE')
        if ini.get_value(APP_NAME, 'PARITY'):
            self.parity = ini.get_value(APP_NAME, 'PARITY')
        if ini.get_value(APP_NAME, 'DATABITS'):
            self.databits = ini.get_value(APP_NAME, 'DATABITS')
        if ini.get_value(APP_NAME, 'STOPBITS'):
            self.stopbits = ini.get_value(APP_NAME, 'STOPBITS')

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

        if ini.get_value('SETUPS', 'STATIONX'):
            self.location.x = float(ini.get_value('SETUPS', 'STATIONX'))
            self.location.y = float(ini.get_value('SETUPS', 'STATIONY'))
            self.location.z = float(ini.get_value('SETUPS', 'STATIONZ'))

    def status(self):
        txt = '\nTotal Station:\n'
        txt += f'  Make is {self.make}\n'
        if self.make not in ['Microscribe']:
            txt += f'  Communication type is {self.communication}\n'
            txt += f'  COM Port is {self.comport}\n'
            txt += '  Com settings are %s, %s, %s, %s\n' % (self.baudrate, self.parity, self.databits, self.stopbits)
            txt += f'COM Port is {"open" if self.serialcom.is_open else "closed"}\n'
            txt += f'  Station was initialized with {self.last_setup_type}\n'
            txt += f'  Station X : {self.location.x}\n'
            txt += f'  Station Y : {self.location.y}\n'
            txt += f'  Station Z : {self.location.z}\n'
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
        return txt

    def set_error_message(self):
        if self.error_code is not None:
            if "Leica" in self.make:
                if self.error_code == 0:
                    self.error_message = ''
                    return
                if self.error_code == 1283:
                    self.error_message = 'Warning: measurement without full correction'
                    return
                if self.error_code == 1284:
                    self.error_message = 'Info: accuracy can not be guaranteed'
                    return
                if self.error_code == 1285:
                    self.error_message = 'Warning: only angle measurement valid'
                    return
                if self.error_code == 1288:
                    self.error_message = 'Warning: only angle measurement valid but without full correction'
                    return
                if self.error_code == 1289:
                    self.error_message = 'Info: only angle measurement valid but accuracy can not be guaranteed'
                    return
                if self.error_code == 1290:
                    self.error_message = 'Error: no angle measurement'
                    return
                if self.error_code == 1291:
                    self.error_message = 'Error: wrong setting of PPM or MM on EDM'
                    return
                if self.error_code == 1292:
                    self.error_message = 'Error: distance measurement no done (no aim, etc.)'
                    return
                if self.error_code == 1293:
                    self.error_message = 'Error: system is busy (no measurement done)'
                    return
                if self.error_code == 1294:
                    self.error_message = 'Error: no signal on EDM (only in signal mode)'
                    return
                if self.error_code == 1380:
                    self.error_message = 'Warning: inclination our of time range'
                    return
                if self.error_code == 1381:
                    self.error_message = 'Warning: measurement without plane inclination correction'
                    return
                if self.error_code == 1382:
                    self.error_message = 'Warning: measurement without sensor inclination correction'
                    return
                if self.error_code == 1383:
                    self.error_message = 'Info: inclination accuracy can not be guaranteed'
                    return

    def text_to_point(self, txt):
        if len(txt.split(',')) == 3:
            x, y, z = txt.split(',')
            try:
                return point(float(x), float(y), float(z))
            except Exception:
                return None
        else:
            return None

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

        return angle

    def format_widget_value(self, widget):
        value = ''
        if widget == 'PRISM':
            value = self.coordinate_pretty(self.prism.height)
        if widget == 'X':
            value = self.coordinate_pretty(self.xyz_global.x)
        if widget == 'Y':
            value = self.coordinate_pretty(self.xyz_global.y)
        if widget == 'Z':
            value = self.coordinate_pretty(self.xyz_global.z)
        if widget in ['STATIONX', 'DATUMX']:
            value = self.coordinate_pretty(self.location.x)
        if widget in ['STATIONY', 'DATUMY']:
            value = self.coordinate_pretty(self.location.y)
        if widget in ['STATIONZ', 'DATUMZ']:
            value = self.coordinate_pretty(self.location.z)
        if widget == 'LOCALX':
            value = self.coordinate_pretty(self.xyz.x)
        if widget == 'LOCALY':
            value = self.coordinate_pretty(self.xyz.y)
        if widget == 'LOCALZ':
            value = self.coordinate_pretty(self.xyz.z)
        if widget == 'SLOPED':
            value = self.coordinate_pretty(self.sloped)
        if widget == 'HANGLE':
            value = self.decimal_degrees_to_dddmmss(self.hangle) if self.hangle is not None else ''
        if widget == 'VANGLE':
            value = self.decimal_degrees_to_dddmmss(self.vangle) if self.vangle is not None else ''
        return value

    def parse_dddmmss_angle(self, hangle):
        hangle = str(hangle)
        if '.' not in hangle:
            angle = int(float(hangle))
            minutes = 0
            seconds = 0
        else:
            hangle = hangle + "0000"
            angle = int(hangle.split(".")[0])
            minutes = int(hangle.split(".")[1][0:2])
            seconds = int(hangle.split(".")[1][2:4])

        return [angle, minutes, seconds]

    def coordinate_pretty(self, coordinate):
        return round(coordinate, 3) if coordinate is not None else ''

    def point_pretty(self, point):
        return f'X: {self.coordinate_pretty(point.x)}\nY: {self.coordinate_pretty(point.y)}\nZ: {self.coordinate_pretty(point.z)}'

    def decimal_degrees_to_dddmmss(self, angle):
        if angle is not None:
            sexa = deci2sexa(angle)
            return f'{sexa[1]}.{sexa[2]:02d}{int(sexa[3]):02d}'
        else:
            return ''

    def gon_to_decimal_degrees(self, angle):
        if angle is not None:
            return str(float(angle) * 180 / 200)
        else:
            return ''

    def decimal_degrees_to_gon(self, angle):
        if angle is not None:
            return str(float(angle) * 200 / 180)
        else:
            return ''

    def dddmmss_to_gon(self, dddmmss_angle):
        angle, minutes, seconds = self.parse_dddmmss_angle(dddmmss_angle)
        return (angle + minutes / 60.0 + seconds / 3600.0) * 200 / 180

    def dddmmss_to_decimal_degrees(self, dddmmss_angle):
        angle, minutes, seconds = self.parse_dddmmss_angle(dddmmss_angle)
        return angle + minutes / 60.0 + seconds / 3600.0

    def decimal_degrees_to_sexa_pretty(self, angle):
        if angle is not None:
            sexa = deci2sexa(angle)
            return f'{sexa[1]}° {sexa[2]:02d}\" {int(sexa[3]):02d}\''
        else:
            return ''

    def vhd_to_sexa_pretty_compact(self):
        return (f"hangle : {self.decimal_degrees_to_sexa_pretty(self.hangle)}, "
                f"vangle : {self.decimal_degrees_to_sexa_pretty(self.vangle)}, "
                f"sloped : {self.coordinate_pretty(self.sloped)}")

    def add_points(self, p1, p2):
        return point(p1.x + p2.x, p1.y + p2.y, p1.z + p2.z)

    def subtract_points(self, p1, p2):
        return point(p1.x - p2.x, p1.y - p2.y, p1.z - p2.z) if not p1.is_none() and not p2.is_none() else point()

    def hash(self, hashlen=5):
        hash = ""
        for a in range(0, hashlen):
            hash += random.choice(string.ascii_uppercase)
        return hash

    def is_numeric(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def set_horizontal_angle(self, angle):
        if self.is_numeric(angle):
            if self.make == 'Topcon':
                self.set_horizontal_angle_topcon(angle)
                time.sleep(1.5)
            elif self.make == 'GeoMax':
                self.set_horizontal_angle_geomax(angle)
                time.sleep(1.5)
            elif self.make in ['WILD', 'Leica']:
                self.set_horizontal_angle_leica(angle)
                time.sleep(1.5)
            elif self.make in ['Leica GeoCom']:
                self.set_horizontal_angle_geocom(angle)
                time.sleep(1.5)
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
        self.clear_serial_buffers()

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
        return False

    def take_shot(self):

        error = False

        self.clear_xyz()
        self.clear_serial_buffers()

        if self.make == 'Topcon':
            self.launch_point_topcon()

        elif self.make in ['WILD', 'Leica']:
            self.launch_point_leica()

        elif self.make == "Leica GeoCom":
            error = self.launch_point_leica_geocom()

        elif self.make == "GeoMax":
            self.launch_point_geomax()

        elif self.make == "SOKKIA":
            self.launch_point_sokkia()

        elif self.make == 'Simulate':
            error = self.launch_point_simulate()

        else:
            pass

        return error

    def fetch_point(self):
        if self.make in ['WILD', 'Leica']:
            self.fetch_point_leica()
        elif self.make in ['Leica GeoCom']:
            self.fetch_point_leica_geocom()

    def vhd_from_xyz(self):
        self.hangle = self.angle_between_xy_pairs(self.location.x, self.location.y, self.xyz.x, self.xyz.y)
        level_distance = sqrt((self.xyz.x - self.location.x)**2 + (self.xyz.y - self.location.y)**2)
        self.sloped = self.distance(self.location, self.xyz)
        self.vangle = self.angle_between_xy_pairs(0, 0, level_distance, self.xyz.z)

    def make_global(self):
        if not self.xyz.is_none():
            if self.make == 'Microscribe':
                if len(self.rotate_local) == 3 and len(self.rotate_global) == 3:
                    self.xyz_global = self.rotate_point(self.xyz)
                else:
                    self.xyz_global = self.xyz
                self.round_xyz()
            else:
                if not self.location.is_none():
                    self.xyz_global = point(self.xyz.x + self.location.x,
                                            self.xyz.y + self.location.y,
                                            self.xyz.z + self.location.z,)
                else:
                    self.xyz_global = self.xyz

    def round_xyz(self):
        self.xyz_global = self.round_point(self.xyz_global)
        self.xyz = self.round_point(self.xyz)

    def round_point(self, p):
        return point(round(p.x, 3), round(p.y, 3), round(p.z, 3)) if not p.is_none() else p

    def clear_xyz(self):
        self.xyz = point()
        self.xyz_global = point()
        self.vangle = None
        self.hangle = None
        self.sloped = 0.0

    def comport_nos(self):
        ports = self.list_comports()
        return list([port[0]['port'] for port in ports])

    def list_comports(self):
        ports = []
        for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
            ports.append([{'port': port, 'desc': desc}])
        return ports

    def clear_io(self):
        self.io = ''

    def trim_io(self, length=1024):
        self.io = self.io[-length:]

    def add_to_io(self, data):
        self.io = self.io + data
        self.trim_io()

    def wait_for_received(self, seconds=1):
        time_one = time.time()
        while time.time() - time_one < seconds:
            if self.data_waiting():
                self.receive()
                return

    # def check_receive_buffer(self, dt):
    #     if self.data_waiting():
    #         self.receive()

    def data_waiting(self):
        if self.serialcom.is_open:
            if self.serialcom.in_waiting > 0:
                return True
        return False

    def send(self, data):
        if self.serialcom.is_open:
            try:
                self.serialcom.write(data)
                self.add_to_io('Sent -> ' + data.decode())
                return True
            except SerialTimeoutException:
                return False

    def receive(self):
        data = ''
        if self.serialcom.is_open:
            data = self.serialcom.read_until().decode() if self.serialcom.is_open else ''
            if data:
                self.add_to_io('Received <- ' + data)
        self.received = data
        return data

    def close(self):
        if self.serialcom.is_open:
            self.serialcom.close()
            self.clear_io()
        if self.serial_bt_input.is_open:
            self.serial_bt_input.close()

    def open(self):
        self.close()
        self.error_message = ''
        self.error_code = 0
        if self.make in ['Simulate', 'Manual XYZ', 'Manual VHD', 'Microscribe', '']:
            return self.error_message
        if any(item is None for item in [self.baudrate, self.comport, self.parity, self.databits, self.stopbits]):
            self.error_code = 1
            self.error_message = 'Missing baudrate, comport, parity, databits, or stopbits'
            return self.error_message
        if any(item == '' for item in [self.baudrate, self.comport, self.parity, self.databits, self.stopbits]):
            self.error_code = 1
            self.error_message = 'Missing baudrate, comport, parity, databits, or stopbits'
            return self.error_message
        if self.comport not in self.comport_nos():
            self.error_code = 1
            self.error_message = self.comport + ' is an invalid COM port number'
            return self.error_message

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
        self.serialcom.write_timeout = 5
        try:
            self.serialcom.open()
            self.clear_io()
            self.initialize()
        except OSError as err:
            self.error_code = 1
            self.error_message = str(err) + '\n\n'
        return self.error_message

    def settings_pretty(self):
        if self.baudrate and self.comport and self.parity and self.databits and self.stopbits:
            return f"{self.comport}:{self.baudrate},{self.parity},{self.databits},{self.stopbits}"
        else:
            return "Incomplete Settings"

    def clear_serial_buffers(self):
        if self.serialcom.is_open:
            self.serialcom.reset_input_buffer()
            self.serialcom.reset_output_buffer()
            self.clear_serial_buffers_internal_only()

    def clear_serial_buffers_internal_only(self):
        self.received = ""
        self.response = ""
        self.error_code = 0
        self.error_message = ""

    def distance(self, p1, p2):
        return sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2) if not p1.is_none() and not p2.is_none() else point()

    def dms_to_decdeg(self, angle):
        angle = str(angle)
        if '.' not in angle:
            angle += "."
        angle += "0000"
        degrees = int(angle.split(".")[0])
        minutes = int(angle.split(".")[1][0:2])
        seconds = int(angle.split(".")[1][2:4])
        return degrees + minutes / 60.0 + seconds / 3600.0

    def decdeg_to_radians(self, angle):
        return angle / 360.0 * (2.0 * pi)

    def radians_to_decdeg(self, angle):
        return angle / (2.0 * pi) * 360.0

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

    def mm_to_meters(self, p):
        if p:
            p.x = round(p.x / 1000, 3)
            p.y = round(p.y / 1000, 3)
            p.z = round(p.z / 1000, 3)
        return p

    # The following functions are needed by the rotation function at the end of this list.
    # Note too that all of the dependent routines are self written
    # rather than pulled from existing libraries (like numpy) to avoid dependencies.  Dependencies make porting to
    # Apple and Android more difficult.
    def dot_product(self, a, b):
        return a.x * b.x + a.y * b.y + a.z * b.z if not a.is_none() and not b.is_none() else point()

    def normalize_vector(self, a):
        if sqrt(self.dot_product(a, a)) == 0:
            return a
        else:
            return self.scale_vector(1 / sqrt(self.dot_product(a, a)), a)

    def vector_subtract(self, p2, p1):
        return point(p2.x - p1.x, p2.y - p1.y, p2.z - p1.z) if not p2.is_none() and not p1.is_none() else point()

    def surface_normal(self, a):
        u = self.vector_subtract(a[1], a[0])
        v = self.vector_subtract(a[2], a[0])
        return self.normalize_vector(self.cross_product(u, v))

    def vector_magnitude(self, a):
        return sqrt(self.dot_product(a, a))

    def cross_product(self, v1, v2):
        return point(v1.y * v2.z - v1.z * v2.y,
                        v1.z * v2.x - v1.x * v2.z,
                        v1.x * v2.y - v1.y * v2.x)

    def scale_vector(self, scalar, a):
        return point(scalar * a.x,
                        scalar * a.y,
                        scalar * a.z)

    def empty_matrix(self):
        return [[0.0 for x in range(3)] for y in range(3)]

    def identity_matrix(self):
        i = self.empty_matrix()
        for n in range(3):
            i[n][n] = 1.0
        return i

    def matrix_product(self, a, b):
        result = self.empty_matrix()
        for row in range(3):
            for col in range(3):
                for index in range(3):
                    result[row][col] = result[row][col] + a[row][index] * b[index][col]
        return result

    def scale_matrix(self, scalar, m):
        result = self.empty_matrix()
        for row in range(3):
            for col in range(3):
                result[row][col] = scalar * m[row][col]
        return result

    def matrix_add(self, m1, m2):
        result = self.empty_matrix()
        for row in range(3):
            for col in range(3):
                result[row][col] = m1[row][col] + m2[row][col]
        return result

    def translate_point(self, translation, p):
        return point(p.x + translation.x,
                        p.y + translation.y,
                        p.z + translation.z)

    def rotate_point_2d(self, local_vector, global_vector, p):
        # local coodinate system and global coordinate system vectors that will be made to align with each other.
        # p is a point to be rotated along with this vector alignment.
        # This is in essence a 2D rotation in the plane formed by the two vectors and around the perpendicular to this plane.
        # (Two vectors have the origin in common and thus make three points altogether and this is a plane)
        # (The surface normal is the rotation axis and the angle of rotation is the angle between the two vectors in this plane)

        i = self.identity_matrix()

        v = self.cross_product(local_vector, global_vector)
        # s = self.vector_magnitude(v)
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
        return point((p.x * r[0][0]) + (p.y * r[1][0]) + (p.z * r[2][0]),
                        (p.x * r[0][1]) + (p.y * r[1][1]) + (p.z * r[2][1]),
                        (p.x * r[0][2]) + (p.y * r[1][2]) + (p.z * r[2][2]))

    def rotate_point_2d_2(self, rotation_vector, local_vector, global_vector, p):
        # local coodinate system and global coordinate system vectors that will be made to align with each other.
        # p is a point to be rotated along with this vector alignment.
        # This is in essence a 2D rotation in the plane formed by the two vectors and around the perpendicular to this plane.
        # (Two vectors have the origin in common and thus make three points altogether and this is a plane)
        # (The surface normal is the rotation axis and the angle of rotation is the angle between the two vectors in this plane)

        i = self.identity_matrix()

        v = rotation_vector
        # s = self.vector_magnitude(v)
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
        return point((p.x * r[0][0]) + (p.y * r[1][0]) + (p.z * r[2][0]),
                        (p.x * r[0][1]) + (p.y * r[1][1]) + (p.z * r[2][1]),
                        (p.x * r[0][2]) + (p.y * r[1][2]) + (p.z * r[2][2]))

    # This routine takes two sets of datums (local and global) and converts a newly recorded point
    # from the local coordinate system (e.g. Microscribe) to the global coordinate system.
    # It does this by performing a rotation around first one leg and then another of the triangle formed by the datums.
    # It is written to be readable.  Much efficiency could be gained but as points are only rotated as recorded,
    # the routine does not need to be fast.  Note too that all of the dependent routines are self written
    # rather than pulled from existing libraries (like numpy) to avoid dependencies.  Dependencies make porting to
    # Apple and Android more difficult.

    def rotate_point(self, p=None):
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
            nv1 = self.normalize_vector(self.vector_subtract(self.rotate_global[1], self.rotate_global[0]))
            nv2 = self.normalize_vector(self.vector_subtract(self.rotate_global[2], self.rotate_global[0]))
            global_datums_normal = self.normalize_vector(self.cross_product(nv1, nv2))
            p_out2 = self.rotate_point_2d(global_datums_normal, local_datums_normal, p_out)

            # Finish the rotation for the local datums as well (not strictly needed for points 2 and 3)
            rotated_local[0] = self.rotate_point_2d(global_vector, local_vector, rotated_local[0])
            rotated_local[1] = self.rotate_point_2d(global_vector, local_vector, rotated_local[1])
            rotated_local[2] = self.rotate_point_2d(global_vector, local_vector, rotated_local[2])

            # Now align the starting points of each grid systems by shifting the first datum points onto each other
            result = self.translate_point(self.rotate_global[0], p_out2)

            return result

        else:
            return None

    def rotate_initialize(self, local_datums, global_datums):
        # local and global datums are two lists of three corresponding points in the two grid systems

        self.rotate_local = local_datums
        self.rotate_global = global_datums

    def cancel(self):
        if self.make == 'Topcon':
            self.topcon_stop_tracking()
        elif self.make == 'Leica GeoCom':
            self.stop_and_clear_geocom()

    def initialize(self):
        if self.make == 'Topcon':
            self.topcon_initialize()

    """
    Topcon specific functions for the total statin
    """
    def launch_point_topcon(self):
        self.send(self.topcon_format("Z34"))   # Slope angle mode
        self.wait_for_received(1)
        # delay(0.5)

        self.send(self.topcon_format("C"))     # Take the shot
        self.wait_for_received(1)
        # delay(0.5)
        self.event1 = Clock.schedule_interval(self.check_receive_buffer, .2)

    def check_receive_buffer(self, dt):
        # need code here to check for a completed shot
        # and then acknowledge back
        self.event1.cancel()

    def make_bcc_topcon(self, text_to_send):
        b = 0
        for character in text_to_send:
            q = ord(character)
            b1 = q & (~b)
            b2 = b & (~q)
            b = b1 | b2
        bcc = "000" + str(b).strip()
        return bcc[-3:]

    def set_horizontal_angle_topcon(self, angle):
        # angle should be in dddmmss with decimal point
        if "." not in angle:
            angle = angle + "."
        angle = "000" + angle + "0000"
        decimal_point = angle.index('.')
        angle = angle[decimal_point - 3: decimal_point] + angle[decimal_point + 1: decimal_point + 5]
        self.send(self.topcon_format("J+" + angle + "d"))
        self.wait_for_received(1)
        # delay(1)
        self.clear_serial_buffers()

    def topcon_stop_tracking(self):
        self.send(self.topcon_format("N"))
        self.wait_for_received(2)

    def topcon_horizontal_mode(self):
        # Should bump the display back to angle mode
        # Can be used after taking a shot
        self.send(self.topcon_format("Z10"))
        self.wait_for_received(1)

    def topcon_initialize(self):
        self.send(self.topcon_format("L"))
        self.wait_for_received(1)
        self.topcon_set_response()
        return self.topcon_valid_bcc()

    def topcon_acknowledge(self):
        ack = chr(6) + "006" + chr(3) + TOPCON_TERMINATION
        self.send(bytes(ack, 'utf-8'))

    def topcon_format(self, text_to_send):
        return bytes(text_to_send + self.make_bcc_topcon(text_to_send) + chr(3) + TOPCON_TERMINATION, 'utf-8')

    def fetch_point_topcon(self):
        if self.data_waiting():
            self.receive()
            self.topcon_acknowledge()
            self.topcon_set_response()
            if self.response:
                self.topcon_parse()
                self.vhd_to_xyz()

    def topcon_set_response(self):
        self.response = self.received

    def topcon_valid_bcc(self):
        if chr(3) not in self.response:
            return False

        delimiter = self.response.index(chr(3))
        bcc1 = self.response[delimiter - 3:delimiter]
        bcc2 = self.make_bcc_topcon(self.response[:delimiter - 3])
        if bcc1 != bcc2:
            self.error_code = 3
            self.error_message = 'Communications error.  BCC did not match.'
            return False

        return True

    def topcon_parse(self):
        if self.response:
            if self.response[0] not in ['?', 'R']:
                self.error_code = 4
                self.error_message = 'Data stream did not start with ? or R'
                return False

        if not self.topcon_valid_bcc():
            return

        self.sloped = float(self.response[1:10]) / 1000.0
        self.hangle = self.dddmmss_to_decimal_degrees(self.response[19:22] + '.' + self.response[22:26])
        self.vangle = self.dddmmss_to_decimal_degrees(self.response[11:14] + '.' + self.response[14:18])
        self.prism_offset = float(self.response[43:48])
        measurement_unit = self.response[10:11]
        if measurement_unit != 'm':
            self.error_code = 2
            self.error_message = 'Distance unit not in meters'
            return False
        angle_unit = self.response[26:27]
        if angle_unit != 'd':
            self.error_code = 1
            self.error_message = 'Angle not in degrees'
            return False
        return True

    """
    Sokkia specific functions
    """
    def launch_point_sokkia(self):
        self.send(chr(17).encode())

    def set_horizontal_angle_sokkia(self, angle):
        # need to send to station in format ddd.mmss
        set_angle_command = "/Dc " + angle + "\r\n"
        self.send(set_angle_command.encode())
        # delay(5)
        self.clear_serial_buffers()

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

    """
    Leica specific functions
    """
    def pad_dms_leica(self, angle):
        degrees = ('000' + angle.split('.')[0])[-3:]
        minutes_seconds = (angle.split('.')[1] + '0000')[0:4]
        return degrees + minutes_seconds

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
        return self.receive()

    def launch_point_leica(self):
        self.send(b"GET/M/WI21/WI22/WI31/WI51\r\n")

    def fetch_point_leica(self):
        self.pnt = self.receive()
        self.set_response_leica()
        if self.pnt:
            self.parce_leica()
            self.vhd_to_xyz()

    def set_response_leica(self):
        self.response = self.leica_trim_crlf(self.received) if self.received else ""

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
        return acknow1 + acknow2

    """
    GeoMax specific functions
    """
    def launch_point_geomax(self):
        self.send(b"meas/all\r\n")

    def pad_dms_geomax(self, angle):
        degrees = ('000' + angle.split('.')[0])[-3:]
        minutes_seconds = (angle.split('.')[1] + '0000')[0:4]
        return degrees + minutes_seconds

    def set_horizontal_angle_geomax(self, angle):
        # function expects angle as ddd.mmss input
        # but decimal seconds are possible
        # to do angel must be ddd.dddd
        if angle.count('.') == 0:
            angle = angle + '.0000'
        elif angle.count('.') == 2:
            dms = angle.split('.')
            ms = '0000' + str(round(float(dms[1] + '.' + dms[2])))
            ms = ms[-4:]
            angle = str(dms[0] + '.' + ms)
        set_angle_command = "SET/hz_angle/{:10.8f}\r\n".format(self.decdeg_to_radians(self.dms_to_decdeg(angle)))
        self.send(set_angle_command.encode())
        return self.receive()

    def fetch_point_geomax(self):
        if self.data_waiting():
            self.receive()
            self.set_response_geomax()
            if self.response:
                self.parce_geomax()
                self.vhd_to_xyz()

    def parce_geomax(self):
        if self.response:
            if self.response.count(',') == 3:
                return False
        self.sloped, self.hangle, self.vangle = self.response.split(',')
        self.hangle = float(self.gon_to_decimal_degrees(self.hangle))
        self.vangle = float(self.gon_to_decimal_degrees(self.vangle))
        self.sloped = float(self.sloped)
        self.prism_constant = None

    def initialize_geomax(self):
        self.send("SET/distance_unit/0" + "\r\n")  # meters
        acknow1 = self.receive()
        self.send("SET/angle_unit/1" + "\r\n")  # degrees ddd.ddddddd
        acknow2 = self.receive()
        return acknow1 + acknow2

    def geomax_trim_crlf(self, value):
        return value.replace('\r', '').replace('\n', '') if value else ""

    def set_response_geomax(self):
        self.response = self.geomax_trim_crlf(self.received) if self.received else ""
        # self.set_error_code()

    """
    Leica GeoCom specific functions
    """
    def initialize_geocom(self):
        pass

    def set_horizontal_angle_geocom(self, angle):
        # function expects angle as ddd.mmss as input
        # %R1Q,2113:HzOrientation[double]
        output = "%R1Q,2113:{:10.8f}\r\n".format(self.decdeg_to_radians(self.dms_to_decdeg(angle)))
        self.send(bytes(output, 'utf-8'))
        self.wait_for_received(1)
        self.set_response_leica_geocom()
        return self.error_code == NO_ERROR

    def launch_point_leica_geocom(self):
        self.clear_serial_buffers()
        self.send(b"%R1Q,2008:1,1\r\n")          # Use the defaults with 1 and 1
        self.wait_for_received(5)
        self.set_response_leica_geocom()
        if self.error_code == 0:
            self.clear_serial_buffers_internal_only()
            self.send(b"%R1Q,2108:10000,1\r\n")     # Fetch the measurements and return the angles + sloped
        return self.error_code == NO_ERROR

    def fetch_point_leica_geocom(self):
        if self.data_waiting():
            self.receive()
            self.set_response_leica_geocom()
            if self.response:
                if self.parse_leica_geocom():
                    self.vhd_to_xyz()

    def stop_and_clear_geocom(self):
        output = f"%R1Q,2008:{TMC_CLEAR},1\r\n"
        self.send(bytes(output, 'utf-8'))
        self.wait_for_received(5)
        self.set_response_leica_geocom()
        return self.error_code == NO_ERROR

    def parse_leica_geocom(self):
        if self.response:
            if self.response.count(',') != 3:
                return False
        _, self.hangle, self.vangle, self.sloped = self.response.split(',')
        self.hangle = self.radians_to_decdeg(float(self.hangle))
        self.vangle = self.radians_to_decdeg(float(self.vangle))
        self.sloped = float(self.sloped)
        self.prism_constant = None
        return True

    def leica_trim_crlf(self, value):
        return value.replace('\r', '').replace('\n', '') if value else ""

    def leica_return_value(self, value):
        if value:
            return value[value.find(':') + 1:] if ":" in value else ""
        else:
            return value

    def set_response_leica_geocom(self):
        self.response = self.leica_return_value(self.leica_trim_crlf(self.received)) if self.received else ""
        self.set_error_code()

    def set_error_code(self):
        if self.response:
            if "," not in self.response:
                self.error_code = int(self.response)
            else:
                self.error_code = int(self.response[:self.response.find(',')])
            self.set_error_message()

    def is_leica(self):
        return self.make in ['Leica', 'Leica GeoCom']

    def get_model_name(self):
        pass

    def find_prism(self, horizontal_search=pi / 4, vertical_search=pi / 4):
        output = f'%R1Q,9037:{horizontal_search},{vertical_search},0\r\n'
        self.send(bytes(output, 'utf-8'))
        self.set_response_leica_geocom(self.receive())
        return self.response.startswith('0,')

    def is_motorized(self):
        if self.make not in ['Leica', 'Leica GeoCom']:
            return False
        self.send(b'%R1Q,6021:\r\n')
        return self.leica_return_value(self.leica_trim_crlf(self.receive())) == '0'

    def start_motor(self):
        self.send(b'%R1Q,6001:1\r\n')
        return self.leica_return_value(self.leica_trim_crlf(self.receive())) == '0'

    def stop_motor(self):
        self.send(b'%R1Q,6002:1\r\n')
        return self.leica_return_value(self.leica_trim_crlf(self.receive())) == '0'

    def get_scan_tolerances(self):
        self.send(b'%R1Q,9008:\r\n')
        self.set_response_leica_geocom(self.receive())
        return self.response.startswith('0,')
