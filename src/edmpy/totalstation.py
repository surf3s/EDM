from kivy.properties import ObjectProperty
from kivy.clock import Clock

from geo import point, prism
from constants import APP_NAME

import os
import serial
from serial.serialutil import SerialTimeoutException
from serial.serialutil import SerialException
from math import sqrt
from math import pi
from math import cos
from math import sin
from math import acos
from math import atan2
from math import radians
from math import degrees
from math import inf
from angles import r2d, deci2sexa, Angle, d2r

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
WAIT_FOR_RECEIVED_TIMEOUT = 3       # Seconds
SERIAL_TIMEOUT = 2                  # seconds
SERIAL_WRITE_TIMEOUT = 2            # seconds
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
        self.prism_constant = 0.0       # Used to set the prism_constant for Nikon and Leica GeoCom stations (in mm)
        self.prism_offset = 0.0         # Used only for storing what Topcon returns.  Should be changed to prism_constant, but I won't touch it for now to avoid bugs.
        self.prism_prompt = True
        self.using_prism = True         # Flip between prism and reflectorless measurement for Nikon stations
        self.hangle = None              # Decimal degrees
        self.vangle = None              # Decimal degrees
        self.sloped = 0.0
        self.suffix = 0
        self.prism = prism()
        self.xyz_global = point()
        self.rotate_local = []          # Used in 3 point transformations
        self.rotate_global = []         # Used in 3 point transformations
        self.rotator = {}               # Used in multi-datum transformations
        self.rotator_datums = {}        # Used in multi-datum transformations
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
        if ini.get_value(APP_NAME, 'PRISM_CONSTANT'):
            try:
                self.prism_constant = float(ini.get_value(APP_NAME, 'PRISM_CONSTANT'))
            except (ValueError, TypeError):
                self.prism_constant = 0.0

        self.last_setup_type = ini.get_value('SETUPS', 'LASTSETUP_TYPE')

        if self.last_setup_type == 'Three datum 3D transform':
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
        else:
            self.rotate_local = []
            self.rotate_global = []

        if self.last_setup_type == 'Multi datum 3D transform':
            if ini.get_value('SETUPS', 'MULTIDATUM_TRANSFORM_ROTATOR'):
                values = [float(v) for v in ini.get_value('SETUPS', 'MULTIDATUM_TRANSFORM_ROTATOR').split(',')]
                if len(values) == 7:
                    self.rotator = {'tx': values[0], 'ty': values[1], 'tz': values[2], 'omega': values[3], 'phi': values[4], 'kappa': values[5], 's': values[6]}
                else:
                    self.rotator = {}
            if ini.get_value('SETUPS', 'MULTIDATUM_TRANSFORM_DATUMS'):
                datum_names = ini.get_value('SETUPS', 'MULTIDATUM_TRANSFORM_DATUMS').split(',')
                self.rotator_datums = {name: data.get_datum(name) for name in datum_names}
        else:
            self.rotator = {}
            self.rotator_datums = {}

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
            txt += f'  COM Port is {"open" if self.serialcom.is_open else "closed"}\n'
            txt += f'  Station was initialized with {self.last_setup_type}\n'
            txt += f'  Station X : {self.location.x}\n'
            txt += f'  Station Y : {self.location.y}\n'
            txt += f'  Station Z : {self.location.z}\n'
            if self.make == "Nikon" and self.serialcom.is_open:
                try:
                    txt += f'  The prism constant is set to {self.nikon_get_prism_constant()} mm\n'
                    txt += self.nikon_get_settings()
                except Exception as e:
                    txt += f'  Error occurred while fetching Nikon data: {e}\n'
            elif self.make == "Leica GeoCom" and self.serialcom.is_open:
                try:
                    self.get_targettype_geocom()
                    self.get_prismconstant_geocom()
                    txt += f'  The station is set to {"prism" if self.using_prism else "reflectorless"} mode\n'
                    txt += f'  The prism constant is set to {self.prism_constant} mm\n'
                    txt += self.get_settings_geocom()
                except Exception as e:
                    txt += f'  Error occurred while fetching Leica GeoCom data : {e}\n'
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

    def ResetConnection(self):
        self.close()
        self.open()
        if self.make in ['Simulate', 'Manual XYZ', 'Manual VHD', 'Microscribe']:
            return False
        if self.serialcom.is_open:
            self.clear_serial_buffers()
            self.clear_xyz()
            self.set_error_message()
            return True
        else:
            return False
    
    def set_error_message(self):
        if self.error_code is not None:
            if "Leica" in self.make:
                if self.error_code == 0:
                    self.error_message = ''
                    return
                if self.error_code == 1283:
                    self.error_message = 'Warning: measurement without full correction. Check leveling the station.'
                    return
                elif self.error_code == 1284:
                    self.error_message = 'Info: accuracy can not be guaranteed'
                    return
                elif self.error_code == 1285:
                    self.error_message = 'Warning: only angle measurement valid'
                    return
                elif self.error_code == 1288:
                    self.error_message = 'Warning: only angle measurement valid but without full correction'
                    return
                elif self.error_code == 1289:
                    self.error_message = 'Info: only angle measurement valid but accuracy can not be guaranteed'
                    return
                elif self.error_code == 1290:
                    self.error_message = 'Error: no angle measurement'
                    return
                elif self.error_code == 1291:
                    self.error_message = 'Error: wrong setting of PPM or MM on EDM'
                    return
                elif self.error_code == 1292:
                    self.error_message = 'Error: distance measurement not done (no aim, etc.)'
                    return
                elif self.error_code == 1293:
                    self.error_message = 'Error: system is busy (no measurement done)'
                    return
                elif self.error_code == 1294:
                    self.error_message = 'Error: no signal on EDM (only in signal mode)'
                    return
                elif self.error_code == 1380:
                    self.error_message = 'Warning: inclination out of time range'
                    return
                elif self.error_code == 1381:
                    self.error_message = 'Warning: measurement without plane inclination correction'
                    return
                elif self.error_code == 1382:
                    self.error_message = 'Warning: measurement without sensor inclination correction'
                    return
                elif self.error_code == 1383:
                    self.error_message = 'Info: inclination accuracy can not be guaranteed'
                    return
        self.error_message = ''

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
        """
        Upload a horizontal angle to the total station.
        hangle is expected to be in dddmmss format.
        """

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
                try:
                    self.set_horizontal_angle_geocom(angle)
                except Exception as e:
                    raise(f"{e}")
                time.sleep(1.5)
            elif self.make == 'Sokkia':
                self.set_horizontal_angle_sokkia(angle)
            elif self.make == 'Nikon':
                self.set_horizontal_angle_nikon(angle)
            elif self.make == 'Nikon (SET)':
                self.set_horizontal_angle_nikon_set(angle)
            elif self.make == 'Simulate':
                pass
            elif self.make in ['Manual XYZ', 'Manual VHD']:
                pass

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

    def anyone_home(self):
        if self.make == 'Topcon':
            result = self.anyone_home_topcon()
            return result
        elif self.make in ['WILD', 'Leica']:
            pass
        elif self.make == "Leica GeoCom":
            result = self.anyone_home_geocom()
            return result
        elif self.make == "GeoMax":
            pass
        elif self.make == "Sokkia":
            pass
        elif self.make == "Nikon":
            result = self.anyone_home_nikon()
            return result
        elif self.make == "Nikon (SET)":
            pass
        elif self.make == 'Simulate':
            return True
        else:
            return False
        
    def upload_station_coordinates(self):
        try:
            if self.make == 'Topcon':
                pass
            elif self.make in ['WILD', 'Leica']:
                pass
            elif self.make == "Leica GeoCom":
                self.upload_station_coordinates_geocom()
            elif self.make == "GeoMax":
                pass
            elif self.make == "Sokkia":
                pass
            elif self.make == "Nikon":
                pass
            elif self.make == "Nikon (SET)":
                pass
            elif self.make == 'Simulate':
                pass
            else:
                pass
        except Exception as e:
            raise Exception(f"Error uploading station coordinates: {e}")
        
    def prism_vs_reflectorless(self):
        try:
            if self.make == 'Nikon':
                return self.prism_vs_reflectorless_nikon()
            elif self.make == 'Leica GeoCom':
                return self.prism_vs_reflectorless_geocom()
            else:
                raise Exception(f"Prism vs reflectorless is not supported for {self.make} total stations.")
        except Exception as e:
            raise Exception(f"Error setting prism vs reflectorless: {e}")

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

        elif self.make == "Sokkia":
            self.launch_point_sokkia()

        elif self.make == "Nikon":
            self.launch_point_nikon()

        elif self.make == "Nikon (SET)":
            self.launch_point_nikon_set()

        elif self.make == 'Simulate':
            error = self.launch_point_simulate()

        else:
            pass

        return error

    def fetch_hangle(self):
        """
        Fetch the horizontal angle from the total station.
        """

        hangle = None
        try:
            if self.make == "Topcon":
                hangle = self.fetch_hangle_topcon()
            elif self.make in ['WILD', 'Leica']:
                hangle = self.fetch_hangle_leica()
            elif self.make == "Leica GeoCom":
                hangle = self.fetch_hangle_leica_geocom()
            elif self.make == "GeoMax":
                hangle = self.fetch_hangle_geomax()
            elif self.make == "Sokkia":
                hangle = self.fetch_hangle_sokkia()
            elif self.make == "Nikon":
                hangle = self.fetch_hangle_nikon()
            elif self.make == "Nikon (SET)":
                hangle = self.fetch_hangle_nikon_set()
            else:
                hangle = None
        except Exception as e:
            raise Exception(f"Error fetching horizontal angle: {e}")

        return hangle

    def fetch_point(self):
        if self.make in ['WILD', 'Leica']:
            self.fetch_point_leica()
        elif self.make in ['Leica GeoCom']:
            self.fetch_point_leica_geocom()
        elif self.make == 'Nikon':
            self.fetch_point_nikon()
        elif self.make == 'Nikon (SET)':
            self.fetch_point_nikon_set()
        elif self.make == 'Topcon':
            self.fetch_point_topcon()
        elif self.make == 'GeoMax':
            self.fetch_point_geomax()
        elif self.make == 'Sokkia':
            self.fetch_point_sokkia()

    def vhd_from_xyz(self):
        self.hangle = self.angle_between_xy_pairs(self.location.x, self.location.y, self.xyz.x, self.xyz.y)
        level_distance = sqrt((self.xyz.x - self.location.x)**2 + (self.xyz.y - self.location.y)**2)
        self.sloped = self.distance(self.location, self.xyz)
        self.vangle = self.angle_between_xy_pairs(0, 0, level_distance, self.xyz.z)

    def make_global(self):
        if not self.xyz.is_none():
            if self.make == 'Microscribe':
                """ If it is Microscribe, then a transformation is required """
                if len(self.rotate_local) == 3 and len(self.rotate_global) == 3:
                    self.xyz_global = self.rotate_point(self.xyz)
                elif self.rotator:
                    self.xyz_global = point(*self.helmert_3d_transform(self.xyz, self.rotator))
                else:
                    self.xyz_global = self.xyz
            elif len(self.rotate_local) == 3 and len(self.rotate_global) == 3:
                """ Transformations are still possible with a total station """
                self.xyz_global = self.rotate_point(self.xyz) 
            elif self.rotator:
                """ Transformations are still possible with a total station """
                self.xyz_global = point(*self.helmert_3d_transform(self.xyz, self.rotator))
            else:
                """ Otherwise add the local coordinates to the station coordinatges """
                if not self.location.is_none():
                    self.xyz_global = point(self.xyz.x + self.location.x,
                                            self.xyz.y + self.location.y,
                                            self.xyz.z + self.location.z,)
                else:
                    self.xyz_global = self.xyz
            self.round_xyz()

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
                return self.receive()

    def delay(self, seconds=1):
        # This is used to wait for the station to respond
        time.sleep(seconds) 

    def data_waiting(self):
        if self.serialcom.is_open:
            try:
                if self.serialcom.in_waiting > 0:
                    return True
            except SerialException:
                pass
        return False

    def send(self, data):
        if self.serialcom.is_open:
            try:
                self.serialcom.write(data)
                self.add_to_io('Sent -> ' + self.convert_non_printing_characters(data.decode()) + '\r\n')
                # print('SENT -> ' + data.decode())
                return True
            except SerialException:
                print(f"SerialException: Could not write to serial port {self.serialcom.port}. Is it open?")
                return False
            except SerialTimeoutException:
                print(f"SerialTimeout: Could not write to serial port {self.serialcom.port}. Is it open?")
                return False

    def receive(self):
        data = ''
        if self.serialcom.is_open:
            data = self.serialcom.read_until().decode() if self.serialcom.is_open else ''
            if data:
                self.add_to_io('Received <- ' + self.convert_non_printing_characters(data) + '\r\n')
        self.received = data
        return data

    def convert_non_printing_characters(self, data):
        # This is used to make the io more readable by converting non printing characters to their hex values in brackets
        result = ''
        for char in data:
            if char in string.printable and char not in string.whitespace:
                result += char
            else:
                result += f'[{ord(char):02x}]'
        return result

    def comport_settings_from_dictionary(self, settings):
        self.baudrate = settings.get('baudrate', '')
        self.comport = settings.get('comport', '')
        self.parity = settings.get('parity', '')
        self.databits = settings.get('bytesize', 0)
        self.stopbits = settings.get('stopbits', 0)

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
        self.serialcom.timeout = SERIAL_TIMEOUT
        self.serialcom.write_timeout = SERIAL_WRITE_TIMEOUT
        try:
            self.serialcom.open()
            self.clear_io()
            self.initialize()
        except ValueError as err:
            self.error_code = 1
            self.error_message = str(err) + '\n\n'
        except OSError as err:
            self.error_code = 1
            self.error_message = str(err) + '\n\n'
        return self.error_message

    def quick_com_open_test(self, comport):
        try:
            self.serialcom.port = comport
            self.serialcom.baudrate = int(self.baudrate) if self.baudrate else 2400
            if self.parity == 'Even':
                self.serialcom.parity = serial.PARITY_EVEN
            elif self.parity == 'Odd':
                self.serialcom.parity = serial.PARITY_ODD
            else:
                self.serialcom.parity = serial.PARITY_NONE
            self.serialcom.stopbits = int(self.stopbits) if self.stopbits else serial.STOPBITS_ONE
            self.serialcom.bytesize = int(self.databits) if self.databits else serial.EIGHTBITS
            self.serialcom.timeout = SERIAL_TIMEOUT
            self.serialcom.open()
            if self.serialcom.is_open:
                self.clear_serial_buffers()
                can_receive = self.anyone_home()
                self.serialcom.close()
                return True, can_receive
        except Exception as e:
            return False, False
        return False, False


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
            slope_distance = self.sloped
            if self.prism.offset is not None:
                slope_distance = self.sloped + self.prism.offset
            z = slope_distance * cos(self.decdeg_to_radians(self.vangle))
            actual_distance = sqrt(slope_distance**2 - z**2)
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

    """
        Code to do a two shot setup.  It is not from AI.
        The following code is ported from EDM-Mobile (and EDMWin).
        I can't remember exactly how this works, but it does work.
        And I remember the hot, weekend day at Carsac when Harold
        and I first figured out how to do this.
    """

    def solve_two_shot_setup(self, datum1, result1, datum2, result2):
        measured_distance = self.distance(result1.xyz, result2.xyz)
        actual_distance = self.distance(datum1.as_point(), datum2.as_point())
        error_distance = abs(measured_distance - actual_distance)

        # Workout what the measured angle would be from datum1 to datum2
        y = -1 * result1.xyz.y
        y = y + result2.xyz.y
        p = point(result2.xyz.x, y, 0)
        measured_angle = self.angle_between_points(point(0, 0, 0), p)

        # Calculate the actual angle between datum1 and datum2
        defined_angle = self.angle_between_points(datum1.as_point(), datum2.as_point())

        # get the difference between these two angles
        angle_difference = defined_angle - measured_angle

        # Based on this, compute the new datum.
        x = round(-1 * result1.xyz.y * sin(d2r(angle_difference)) + datum1.x, 3)
        y = round(-1 * result1.xyz.y * cos(d2r(angle_difference)) + datum1.y, 3)
        z1 = datum1.z - result1.xyz.z
        z2 = datum2.z - result2.xyz.z
        z = round((z1 + z2) / 2, 3)
        new_station = point(x, y, z)

        # Workout what angle needs to be uploaded to the station
        new_foresight = self.angle_between_points(new_station, datum2.as_point())

        return new_station, new_foresight, measured_distance, actual_distance, error_distance

    """
        What follows is code to do resectioning.  The base of this code comes from Geminin AI.
        It uses a closed form solution to the 2x2 SVD problem to avoid using NumPy or other third-party libraries.  
        It is a bit slower than using NumPy, but it is more portable and avoids the need for additional dependencies.
    """

    def svd_2x2(self, a, b, c, d):
        """
            Computes exact SVD for a 2x2 matrix H = [[a, b], [c, d]]
            Returns U, S, Vt as 2x2 lists.
        """
        # Angles for rotation matrices U and V
        theta_v = 0.5 * atan2(2 * (a * c + b * d), (a**2 + b**2 - c**2 - d**2))
        theta_u = 0.5 * atan2(2 * (a * b + c * d), (a**2 - b**2 + c**2 - d**2))

        cu, su = cos(theta_u), sin(theta_u)
        cv, sv = cos(theta_v), sin(theta_v)

        U = [[cu, -su], 
            [su,  cu]]
        
        Vt = [[cv,  sv], 
            [-sv, cv]]

        return U, Vt

    def compute_free_station(self, control_points, observations, sigma_dist=0.003, sigma_angle_sec=5.0):
        """
            Computes Free Stationing using Weighted SVD without NumPy or third-party libraries.
        """
        if len(control_points) < 2:
            raise ValueError("At least 2 active datums are required.")

        sigma_angle_rad = radians(sigma_angle_sec / 3600.0)
        
        P_local = []
        P_world = []
        weights = []
        ids = []

        # 1. Local polar to Cartesian & per-point weighting
        for (pt_id, world_point), (datum_name, observation) in zip(control_points.items(), observations.items()):
            # S = obs['dist']
            # hz = obs['hz']
            # zen = obs.get('zenith', pi / 2.0)

            # # Local polar to Cartesian
            # HD = S * sin(zen)
            # x_loc = HD * sin(hz)
            # y_loc = HD * cos(hz)
            # z_loc = S * cos(zen)

            # Spatial variance weight
            HD = (observation.x ** 2 + observation.y ** 2) ** 0.5
            variance_i = (sigma_dist ** 2) + ((HD * sigma_angle_rad) ** 2)
            w_i = 1.0 / variance_i

            P_local.append(tuple(observation))
            P_world.append(tuple(world_point))
            weights.append(w_i)
            ids.append(pt_id)

        N = len(ids)
        sum_w = sum(weights)
        w_norm = [w / sum_w for w in weights]

        # 2. Height offset (Z0)
        Z0 = sum(w_norm[i] * (P_world[i][2] - P_local[i][2]) for i in range(N))

        # 3. Weighted Centroids
        loc_cx = sum(w_norm[i] * P_local[i][0] for i in range(N))
        loc_cy = sum(w_norm[i] * P_local[i][1] for i in range(N))
        
        wrd_cx = sum(w_norm[i] * P_world[i][0] for i in range(N))
        wrd_cy = sum(w_norm[i] * P_world[i][1] for i in range(N))

        # 4. Construct Weighted Cross-Covariance Matrix H = [[a, b], [c, d]]
        a = b = c = d = 0.0
        for i in range(N):
            dx_loc = P_local[i][0] - loc_cx
            dy_loc = P_local[i][1] - loc_cy
            dx_wrd = P_world[i][0] - wrd_cx
            dy_wrd = P_world[i][1] - wrd_cy
            
            w = weights[i]
            a += w * dx_loc * dx_wrd
            b += w * dx_loc * dy_wrd
            c += w * dy_loc * dx_wrd
            d += w * dy_loc * dy_wrd

        # 5. Closed-Form 2x2 SVD
        U, Vt = self.svd_2x2(a, b, c, d)

        # Rotation matrix R_2d = Vt^T * U^T
        # Vt^T = [[Vt[0][0], Vt[1][0]], [Vt[0][1], Vt[1][1]]]
        # U^T  = [[U[0][0],  U[1][0]],  [U[0][1],  U[1][1]]]
        r00 = Vt[0][0] * U[0][0] + Vt[1][0] * U[0][1]
        r01 = Vt[0][0] * U[1][0] + Vt[1][0] * U[1][1]
        r10 = Vt[0][1] * U[0][0] + Vt[1][1] * U[0][1]
        r11 = Vt[0][1] * U[1][0] + Vt[1][1] * U[1][1]

        # Reflection check (determinant)
        det = r00 * r11 - r01 * r10
        if det < 0:
            r01 = -r01
            r11 = -r11

        # Orientation and station coordinates
        t0_rad = atan2(r01, r00) % (2 * pi)
        X0 = wrd_cx - (r00 * loc_cx + r01 * loc_cy)
        Y0 = wrd_cy - (r10 * loc_cx + r11 * loc_cy)

        station_coords = (round(X0, 3), round(Y0, 3), round(Z0, 3))

        # 6. Residual Metrics per Point
        datum_errors = {}
        total_sq_residuals = 0.0

        for i, pt_id in enumerate(ids):
            px_loc, py_loc, pz_loc = P_local[i]
            pred_X = r00 * px_loc + r01 * py_loc + X0
            pred_Y = r10 * px_loc + r11 * py_loc + Y0
            pred_Z = pz_loc + Z0

            e_wrd, n_wrd, h_wrd = P_world[i]
            diff_E = e_wrd - pred_X
            diff_N = n_wrd - pred_Y
            diff_H = h_wrd - pred_Z

            dist_error = sqrt(diff_E**2 + diff_N**2 + diff_H**2)
            sigma_i = sqrt(1.0 / weights[i])
            std_residual = dist_error / sigma_i
            
            total_sq_residuals += dist_error**2

            datum_errors[pt_id] = {
                "east_residual_m": round(diff_E, 4),
                "north_residual_m": round(diff_N, 4),
                "elev_residual_m": round(diff_H, 4),
                "total_error_m": round(dist_error, 4),
                "std_residual_score": round(std_residual, 2),
                "weight_percent": round(w_norm[i] * 100, 1)
            }

        dof = max(1, (2 * N) - 3)
        sigma_0 = sqrt(total_sq_residuals / dof)

        return {
            "station_coords": point(*station_coords),
            "orientation_deg": round(degrees(t0_rad), 4),
            "orientation_rad": round(t0_rad, 6),
            "global_std_error_m": round(sigma_0, 4),
            "datum_errors": datum_errors
        }

    def offset_hangle(self, angle_offset):
        """
        Offsets a horizontal angle by a given amount, ensuring the result is within [0, 360) degrees.
        Parameters:
        - angle_offset: The amount to offset the horizontal angle by (in decimal degrees).
        """
        try:
            hangle = self.fetch_hangle()
        except Exception as e:
            raise Exception(f"{e}")    

        try:
            hangle = (self.dddmmss_to_decimal_degrees(hangle) + angle_offset) % 360.0
            hangle = self.decimal_degrees_to_dddmmss(hangle)
        except Exception as e:
            raise Exception(f"Error adjusting horizontal angle of {hangle} by offset of {angle_offset}: {e}")
        
        try:
            self.set_horizontal_angle(hangle)
        except Exception as e:
            raise Exception(f"Error setting horizontal angle of {hangle}: {e}")

        return hangle
    
    """
        End resectioning code.
    """

    """
    What follows are functions for Helmert transformations and 3D rotations.  These are used for the Microscribe and other applications.
    This code was written by Gemini AI and adapted to EDM.
    """

    def compute_helmert_transformation(self, source_points, target_points, fix_scale_to_one=True):
        """
        Source_points are the locally measured points, and target_points are the known global coordinates.
        This function computes the 7 Helmert parameters and the residual errors.
        """
        rotator = self.calculate_helmert_parameters(source_points, target_points, fix_scale_to_one=fix_scale_to_one)
        errors = self.residual_errors(source_points, target_points, rotator)
        return rotator, errors
    
    def helmert_residuals(self, params, source_pts, target_pts):
        """
        Calculates the 3D distance errors between transformed source points
        and target points for a given set of 7 parameters, without using NumPy.
        """
        def matmul(a, b):
            return [[sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))]
                    for i in range(len(a))]

        def rotate_x(theta):
            return [[1, 0, 0],
                    [0, cos(theta), -sin(theta)],
                    [0, sin(theta), cos(theta)]]

        def rotate_y(theta):
            return [[cos(theta), 0, sin(theta)],
                    [0, 1, 0],
                    [-sin(theta), 0, cos(theta)]]

        def rotate_z(theta):
            return [[cos(theta), -sin(theta), 0],
                    [sin(theta), cos(theta), 0],
                    [0, 0, 1]]

        tx, ty, tz, omega, phi, kappa, s = params

        R_x = rotate_x(omega)
        R_y = rotate_y(phi)
        R_z = rotate_z(kappa)
        R = matmul(matmul(R_z, R_y), R_x)
        T = [tx, ty, tz]

        residuals = []
        for p_src, p_tgt in zip(source_pts, target_pts):
            p = [float(p_src[0]), float(p_src[1]), float(p_src[2])]
            p_transformed = [T[i] + s * sum(R[i][j] * p[j] for j in range(3)) for i in range(3)]
            residuals.extend([p_transformed[i] - float(p_tgt[i]) for i in range(3)])

        return residuals

    def calculate_helmert_parameters(self, source_points, target_points, fix_scale_to_one=True):
        """
        Derives the 7 Helmert parameters using Least-Squares optimization.
        Accepts any number of points (minimum 3).
        """
        # Initial guesses: [tx, ty, tz, omega, phi, kappa, scale]
        # Starting with 0 translations, 0 rotations, and 1.0 scale
        initial_guess = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
        
        # Levenberg-Marquardt optimization with a finite-difference Jacobian.
        # Keep scale out of the optimization entirely when it is fixed.
        active = list(range(6)) if fix_scale_to_one else list(range(7))
        params = initial_guess[:]
        residual = self.helmert_residuals(params, source_points, target_points)
        cost = sum(value * value for value in residual)
        damping = 1e-3

        for _ in range(200):
            jacobian = [[0.0] * len(active) for _ in residual]
            for column, index in enumerate(active):
                step = 1e-6 * max(1.0, abs(params[index]))
                perturbed = params[:]
                perturbed[index] += step
                shifted = self.helmert_residuals(perturbed, source_points, target_points)
                for row in range(len(residual)):
                    jacobian[row][column] = (shifted[row] - residual[row]) / step

            size = len(active)
            normal = [[sum(jacobian[k][i] * jacobian[k][j] for k in range(len(residual)))
                       for j in range(size)] for i in range(size)]
            gradient = [sum(jacobian[k][i] * residual[k] for k in range(len(residual)))
                        for i in range(size)]
            for i in range(size):
                normal[i][i] += damping * max(normal[i][i], 1.0)

            # Solve (J'J + damping I) delta = -J'r by Gaussian elimination.
            matrix = [normal[i][:] + [-gradient[i]] for i in range(size)]
            for col in range(size):
                pivot = max(range(col, size), key=lambda row: abs(matrix[row][col]))
                if abs(matrix[pivot][col]) < 1e-20:
                    break
                matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
                divisor = matrix[col][col]
                matrix[col] = [value / divisor for value in matrix[col]]
                for row in range(size):
                    if row != col:
                        factor = matrix[row][col]
                        matrix[row] = [matrix[row][j] - factor * matrix[col][j]
                                       for j in range(size + 1)]
            else:
                delta = [matrix[i][-1] for i in range(size)]
                candidate = params[:]
                for i, index in enumerate(active):
                    candidate[index] += delta[i]
                candidate_residual = self.helmert_residuals(candidate, source_points, target_points)
                candidate_cost = sum(value * value for value in candidate_residual)
                if candidate_cost < cost:
                    params, residual, cost = candidate, candidate_residual, candidate_cost
                    damping = max(damping / 3.0, 1e-12)
                    if max(abs(value) for value in delta) < 1e-10:
                        break
                else:
                    damping = min(damping * 10.0, 1e12)
    
        """ This is a bit ineffecient for readability """
        tx, ty, tz, omega, phi, kappa, s = params
        rotator = {
            'tx': tx,
            'ty': ty,
            'tz': tz,
            'omega': omega,
            'phi': phi,
            'kappa': kappa,
            'scale': s
        }
        return rotator

    def residual_errors(self, local_measured_pts, original_field_pts, rotator):
        """
        Used to compute errors per datum used in the Helmert transformation.  
        This is useful for debugging and understanding how well the transformation fits the data.
        """
        tx, ty, tz, omega, phi, kappa, scale = rotator.values()
        errors = {}
        for i, (src, tgt) in enumerate(zip(local_measured_pts, original_field_pts)):
            src = list(src)
            tgt = list(tgt)

            # Re-create rotation matrix to transform and verify
            R_x = [[1, 0, 0],
                   [0, cos(omega), -sin(omega)],
                   [0, sin(omega), cos(omega)]]
            R_y = [[cos(phi), 0, sin(phi)],
                   [0, 1, 0],
                   [-sin(phi), 0, cos(phi)]]
            R_z = [[cos(kappa), -sin(kappa), 0],
                   [sin(kappa), cos(kappa), 0],
                   [0, 0, 1]]

            def matmul(a, b):
                return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

            R = matmul(R_z, matmul(R_y, R_x))
            rotated = [sum(R[row][j] * src[j] for j in range(3)) for row in range(3)]
            transformed = [tx + scale * rotated[0], ty + scale * rotated[1], tz + scale * rotated[2]]
            error = [transformed[j] - tgt[j] for j in range(3)]
            dist_error_3d = sqrt(sum(value * value for value in error))
            # print(f"Point {i + 1} -> dX: {error[0]:.4f}, dY: {error[1]:.4f}, dZ: {error[2]:.4f} | Total 3D Error: {dist_error_3d:.4f}")
            error.append(dist_error_3d)
            errors[i] = error

        return errors

    def helmert_3d_transform(self, point, rotator):
        """
        Transforms a 3D point using the 7-parameter Helmert Transformation.
        
        Parameters:
        point (list/array): [X, Y, Z] local total station coordinates
        tx, ty, tz: Translations along X, Y, Z axes (in meters/mm)
        omega, phi, kappa: Rotations around X, Y, Z axes (in radians)
        s: Scale factor multiplier (use 1.0 to preserve physical lab distance)
        """
        tx, ty, tz, omega, phi, kappa, s = rotator.values()
        P_local = list(point)
        
        # 3D Rotation matrices for each axis
        R_x = [[1, 0, 0],
            [0, cos(omega), -sin(omega)],
            [0, sin(omega), cos(omega)]]
    
        R_y = [[cos(phi), 0, sin(phi)],
            [0, 1, 0],
            [-sin(phi), 0, cos(phi)]]
    
        R_z = [[cos(kappa), -sin(kappa), 0],
            [sin(kappa), cos(kappa), 0],
            [0, 0, 1]]
        
        # Combined Rotation Matrix (R = Rz * Ry * Rx)
        R_zy = [[sum(R_z[i][k] * R_y[k][j] for k in range(3))
                for j in range(3)] for i in range(3)]
        R = [[sum(R_zy[i][k] * R_x[k][j] for k in range(3))
            for j in range(3)] for i in range(3)]
        
        # Apply standard Helmert formula: Target = T + s * R * Local
        rotated = [sum(R[i][j] * P_local[j] for j in range(3))
               for i in range(3)]
        P_target = [round(translation + s * coordinate, 3)
                for translation, coordinate in zip((tx, ty, tz), rotated)]
        
        return P_target

    """
        end of Helmert transformation code.
    """

    """
        The following functions are needed by the rotation function at the end of this list.
        Note too that all of the dependent routines are self written
        rather than pulled from existing libraries (like numpy) to avoid dependencies.  Dependencies make porting to
        Apple and Android more difficult.
    """

    def dot_product(self, a, b):
        return a.x * b.x + a.y * b.y + a.z * b.z if not a.is_none() and not b.is_none() else point()

    def normalize_vector(self, a):
        if a.is_none():
            return a
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
            if any(self.rotate_local[n].is_none() for n in range(3)) or any(self.rotate_global[n].is_none() for n in range(3)):
                return p

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
            return p

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
        elif self.make == 'Leica GeoCom':
            try:
                self.initialize_geocom()
            except ValueError as ve:
                raise ValueError(f"Error initializing Leica GeoCom total station: {ve}")
            except Exception as e:
                raise Exception(f"Error initializing Leica GeoCom total station: {e}")
        elif self.make == 'Nikon':
            self.nikon_initialize()

    """
    Topcon specific functions for the total station
    """
    def anyone_home_topcon(self):
        self.send(self.topcon_format("L"))  # Request settings
        self.wait_for_received(3)
        self.topcon_set_response()
        return self.topcon_valid_bcc()
        
    def launch_point_topcon(self):
        self.send(self.topcon_format("Z34"))   # Slope angle mode
        self.wait_for_received(3)
        # delay(0.5)

        self.send(self.topcon_format("C"))     # Take the shot
        self.wait_for_received(3)
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
        self.wait_for_received(3)
        # delay(1)
        self.clear_serial_buffers()

    def topcon_stop_tracking(self):
        self.send(self.topcon_format("N"))
        self.wait_for_received(3)

    def topcon_horizontal_mode(self):
        # Should bump the display back to angle mode
        # Can be used after taking a shot
        self.send(self.topcon_format("Z10"))
        self.wait_for_received(3)

    def topcon_initialize(self):
        return self.anyone_home_topcon()

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

    def fetch_hangle_topcon(self):
        self.send(self.topcon_format("L"))
        self.wait_for_received(3)
        self.topcon_set_response()
        self.topcon_acknowledge()
        hangle = None
        if self.response:
            try:
                hangle = self.dddmmss_to_decimal_degrees(self.response[2:5] + '.' + self.response[5:9])
            except Exception as e:
                pass
        self.clear_serial_buffers()
        return hangle
    
    """
    Nikon specific functions.
        See Nikon (SET) for running a Nikon total station as if it is Sokkkia
    """
    def initialize_nikon(self):
        try:
            good_connection = self.anyone_home_nikon()
            if not good_connection:
                raise Exception("No response from Nikon total station.")
            self.nikon_get_prism_constant()
        except Exception as e:
            raise Exception(f"Error initializing Nikon total station: {e}")    

    def anyone_home_nikon(self):
        """ Ask for the settings and see if at least an ack comes back """
        get_settings_command = "CT\x02?CND\x03"
        get_settings_command += self.nikon_checksum(get_settings_command)
        get_settings_command = "\x01" + get_settings_command + "\x04\r\n"
        self.send(get_settings_command.encode())
        ack_or_nak = self.wait_for_received(2)
        self.clear_serial_buffers()
        if not ack_or_nak:
            return False
        else:
            return True

    def nikon_get_settings(self):
        get_settings_command = "CT\x02?CND\x03"
        get_settings_command += self.nikon_checksum(get_settings_command)
        get_settings_command = "\x01" + get_settings_command + "\x04\r\n"
        self.send(get_settings_command.encode())
        ack_or_nak = self.wait_for_received(2)
        ack_text = ack_or_nak.decode(errors="ignore") if isinstance(ack_or_nak, (bytes, bytearray)) else str(ack_or_nak)
        if not ack_or_nak or 'TC\x06' not in ack_text:
            self.clear_serial_buffers()
            return "  Error: No ACK received - " + ack_text + "\n" if ack_or_nak else "  Error: No ACK received\n"
        
        data = self.wait_for_received(5)
        self.clear_serial_buffers()
        result = "  Settings: No data returned\n"
        if data:

            data = data.strip().decode(errors="ignore") if isinstance(data, (bytes, bytearray)) else str(data).strip()
            data = data[4:] if len(data) >= 4 else ""
            data = data.split("\x03", 1)[0]
            
            try:
                if data[12] == "H":
                    angle_resolution = "High"
                elif data[12] == "L":
                    angle_resolution = "Low"
                elif data[12] == "C":
                    angle_resolution = "Normal"
                else:
                    angle_resolution = "Unknown"

                if data[14] == "M":
                    distance_unit = "Meters"
                elif data[14] == "F":
                    distance_unit = "Feet"
                elif data[14] == "N":
                    distance_unit = "International Feet"
                else:
                    distance_unit = "Unknown"

                if data[15] == "D":
                    angle_unit = "DMS"
                elif data[15] == "G":
                    angle_unit = "GON"
                elif data[15] == "M":
                    angle_unit = "MIL"
                else:
                    angle_unit = "Unknown"

                if data[16] == "V":
                    vertical_zero_position = "Zenith"
                elif data[16] == "H":
                    vertical_zero_position = "Horizon"
                elif data[16] == "C":
                    vertical_zero_position = "Compass"
                else:
                    vertical_zero_position = "Unknown"

                if data[17] == "X":
                    coordinates_order = "NEZ"
                elif data[17] == "Y":
                    coordinates_order = "ENZ"
                else:
                    coordinates_order = "Unknown"

                if data[22] == "S":
                    distance_resolution = "High"
                elif data[22] == "L":
                    distance_resolution = "Low"
                else:
                    distance_resolution = "Unknown"

                result = f"  Angle Resolution: {angle_resolution}\n  Distance Unit: {distance_unit}\n  Angle Unit: {angle_unit}\n  Vertical Zero Position: {vertical_zero_position}\n  Coordinates Order: {coordinates_order}\n  Distance Resolution: {distance_resolution}"

            except (IndexError):
                result = "  Settings Error: Invalid data format\n"

        return result

    def nikon_get_prism_constant(self):
        get__prism_constant_command = "CT\x02?PSM\x03"
        get__prism_constant_command += self.nikon_checksum(get__prism_constant_command)
        get__prism_constant_command = "\x01" + get__prism_constant_command + "\x04\r\n"
        self.send(get__prism_constant_command.encode())
        ack_or_nak = self.wait_for_received(2)
        ack_text = ack_or_nak.decode(errors="ignore") if isinstance(ack_or_nak, (bytes, bytearray)) else str(ack_or_nak)
        if not ack_or_nak or 'TC\x06' not in ack_text:
            self.clear_serial_buffers()
            return "  Error: No ACK received - " + ack_or_nak.decode() if ack_or_nak else "  Error: No ACK received"
        
        data = self.wait_for_received(5)
        self.clear_serial_buffers()
        try:
            payload = data.strip().decode(errors="ignore") if isinstance(data, (bytes, bytearray)) else str(data).strip()
            value_part = payload.split(":", 1)[1]

            number = ""
            started = False
            for ch in value_part:
                if ch in "+-" and not started and not number:
                    number += ch
                    continue
                if ch.isdigit():
                    number += ch
                    started = True
                    continue
                if started:
                    break

            constant = float(number)
            self.prism_constant = constant
            return constant
        except (IndexError, ValueError, AttributeError):
            return "No data - " + data.decode() if data is not None else "No data"

    def nikon_set_prism_constant(self, constant):
        ''' The constant should be in mm '''
        try:
            constant = int(float(constant))
        except (ValueError, TypeError):
            constant = 0

        constant_str = f"{abs(constant):03d}"

        if constant < 0:
            constant_str = "-" + constant_str
        else:
            constant_str = "0" + constant_str

        set_prism_constant_command = "CT\x02!PSM" + constant_str + "\x03"
        set_prism_constant_command += self.nikon_checksum(set_prism_constant_command)
        set_prism_constant_command = "\x01" + set_prism_constant_command + "\x04\r\n"
        self.send(set_prism_constant_command.encode())
        self.wait_for_received(2)
        self.clear_serial_buffers()

    def nikon_set_prism_mode(self):
        set_prism_mode_command = "CT\x02!TGTP\x03"
        set_prism_mode_command += self.nikon_checksum(set_prism_mode_command)
        set_prism_mode_command = "\x01" + set_prism_mode_command + "\x04\r\n"
        self.send(set_prism_mode_command.encode())
        self.wait_for_received(2)
        self.clear_serial_buffers()
        self.nikon_set_prism_constant(self.prism_constant if self.prism_constant is not None else 0.0)
        self.using_prism = True

    def nikon_set_reflector_mode(self):
        set_reflector_mode_command = "CT\x02!TGTN\x03"
        set_reflector_mode_command += self.nikon_checksum(set_reflector_mode_command)
        set_reflector_mode_command = "\x01" + set_reflector_mode_command + "\x04\r\n"
        self.send(set_reflector_mode_command.encode())
        self.wait_for_received(2)
        self.clear_serial_buffers()
        self.nikon_set_prism_constant(0.0)
        self.using_prism = False

    def prism_vs_reflectorless_nikon(self):
        if self.using_prism:
            self.nikon_set_reflector_mode()
            return "Using\nReflectorless\n0.0 mm\nconstant"
        else:
            self.nikon_set_prism_mode()
            return f"Using\nPrism\n{self.prism_constant if self.prism_constant is not None else 0.0} mm\nconstant"

    def nikon_point_averaging(self, shots=5):
        """
        This sets the Nikon to average a number of shots.
        Currently not used but was added because one person thought it might be needed.
        """
        set_averaging = "CT\x02!AVE" + str(shots).zfill(2) + "\x03"
        set_averaging += self.nikon_checksum(set_averaging)
        set_averaging = "\x01" + set_averaging + "\x04\r\n"
        self.send(set_averaging.encode())
        self.wait_for_received(2)
        self.clear_serial_buffers()

    def nikon_initialize(self):
        """
        This sets the instrument to output SD/HA/VA after each shot.
        """
        initialize_command = "CT\x02$DNX\x03"
        initialize_command += self.nikon_checksum(initialize_command)
        initialize_command = "\x01" + initialize_command + "\x04\r\n"
        self.send(initialize_command.encode())
        self.wait_for_received(2)
        self.clear_serial_buffers()

        self.nikon_set_prism_mode()
        
    def launch_point_nikon(self):
        record_point_command = "CT\x02$MSR\x03"
        record_point_command += self.nikon_checksum(record_point_command)
        record_point_command = "\x01" + record_point_command + "\x04\r\n"
        self.send(record_point_command.encode())
        self.wait_for_received(1)
        self.clear_serial_buffers()

    # see also https://groups.google.com/g/sci.engr.surveying/c/1tLM6JHtMgI?pli=1
    def nikon_checksum(self, buf):
        """
        Get Nikon checksum for buf. Second complement of the sum of ascii codes.
        Returns the last two characters as a string (uppercase).
        """
        total = 0
        for c in buf:
            total += ord(c)
        s = total & 0xFF  # lower one byte
        checksum = (s % 0x40) + 0x20
        return chr(checksum)

    def set_horizontal_angle_nikon(self, angle):
        # need to send to station in format dddmmss
        angle = self.format_angle_nikon_set(angle)
        angle = angle.replace('.', '')
        set_angle_command = "CT\x02!HAN" + angle + "\x03"
        set_angle_command += self.nikon_checksum(set_angle_command)
        set_angle_command = "\x01" + set_angle_command + "\x04\r\n"
        self.send(set_angle_command.encode())
        self.wait_for_received(2)
        self.clear_serial_buffers()

    def fetch_point_nikon(self):
        self.pnt = self.receive()
        self.set_response_nikon()
        if self.pnt:
            self.parse_nikon()
            self.vhd_to_xyz()

    def parse_nikon(self):
        self.sloped = None
        self.hangle = None
        self.vangle = None
        if self.pnt:
            vhd = self.pnt.strip().split(" ")
            for item in vhd:
                if item.startswith('SD'):
                    self.sloped = float(item[3:]) / 10000.0
                elif item.startswith('HA'):
                    self.hangle = Angle(f'{item[3:7]}d{item[7:9]}m{item[9:12]}').d
                elif item.startswith('VA'):
                    self.vangle = Angle(f'{item[3:7]}d{item[7:9]}m{item[9:12]}').d

    def set_response_nikon(self):
        self.response = self.received

    def fetch_hangle_nikon(self):
        get__hangle_command = "CT\x02?HAN\x03"
        get__hangle_command += self.nikon_checksum(get__hangle_command)
        get__hangle_command = "\x01" + get__hangle_command + "\x04\r\n"
        self.send(get__hangle_command.encode())
        ack_or_nak = self.wait_for_received(2)
        ack_text = ack_or_nak.decode(errors="ignore") if isinstance(ack_or_nak, (bytes, bytearray)) else str(ack_or_nak)
        if not ack_or_nak or 'TC\x06' not in ack_text:
            self.clear_serial_buffers()
            return "  Error: No ACK received - " + ack_or_nak.decode() if ack_or_nak else "  Error: No ACK received"
        
        data = self.wait_for_received(5)
        self.clear_serial_buffers()
        try:
            payload = data.strip().decode(errors="ignore") if isinstance(data, (bytes, bytearray)) else str(data).strip()
            item = payload.split(":", 1)[1].strip()

            if item.startswith('HA'):
                hangle = Angle(f'{item[3:7]}d{item[7:9]}m{item[9:12]}').d
                return hangle
            else:
                return "No HA data - " + item
        except (IndexError, ValueError, AttributeError):
            return "No data - " + data.decode() if data is not None else "No data"

    """
    Nikon SET protocols.  This means the Nikon acts like a Sokkia.
    """
    def sokkia_checksum(self, buf):
        """
        Get Sokkia checksum for buf. Second complement of the sum of ascii codes.
        Returns the last two hex digits as a string (uppercase).
        """
        total = 0
        for c in buf:
            total += ord(c)
        total = -total
        hex_str = f"{total:X}"
        # Return the last two characters (pad with zeros if needed)
        return hex_str[-2:].upper().zfill(2)

    def launch_point_nikon_set(self):
        launch = chr(17) + "\r\n"
        self.send(launch.encode())

    def set_horizontal_angle_nikon_set(self, angle):
        # need to send to station in format ddd.mmss
        angle = self.format_angle_nikon_set(angle)
        set_angle_command = f"/Dc {angle},"
        set_angle_command += self.sokkia_checksum(set_angle_command)
        set_angle_command += "\r\n"
        # self.clear_io()
        if self.send(set_angle_command.encode()):
            self.delay(1)
            self.clear_serial_buffers()
        else:
            print("Failed to send set angle command to Nikon SET total station.")

    def format_angle_nikon_set(self, angle):
        # Converts angle to ddd.mmss format
        if '.' not in angle:
            angle += '.'
        angle = '000' + angle + '0000'
        decimal_point = angle.index('.')
        angle = angle[decimal_point - 3: decimal_point] + "." + angle[decimal_point + 1: decimal_point + 5]
        return angle

    def fetch_point_nikon_set(self):
        self.pnt = self.receive()
        self.set_response_nikon_set()
        if self.pnt:
            self.parse_nikon_set()
            self.vhd_to_xyz()

    def parse_nikon_set(self):
        if self.pnt:
            self.sloped = None
            self.hangle = None
            self.vangle = None
            vhd = self.pnt.strip().split(" ")
            if len(vhd) >= 3:
                try:
                    self.sloped = float(vhd[0]) / 1000.0
                    if vhd[1][0] != 'E':
                        self.vangle = Angle(f'{vhd[1][:3]}d{vhd[1][3:5]}m{vhd[1][5:7]}').d
                    if vhd[2][0] != 'E':
                        self.hangle = Angle(f'{vhd[2][:3]}d{vhd[2][3:5]}m{vhd[2][5:7]}').d
                except ValueError:
                    pass

    def set_response_nikon_set(self):
        self.response = self.received

    def fetch_hangle_nikon_set(self):
        raise NotImplementedError("fetch_hangle_nikon_set is not implemented yet.")
    
    """
    Sokkia specific functions
    Note - I am not sure these work.  I need someone with a Sokkia total station to test them.
    """
    def launch_point_sokkia(self):
        self.send(chr(17).encode())

    def set_horizontal_angle_sokkia(self, angle):
        self.set_horizontal_angle_nikon_set(angle)

    def fetch_point_sokkia(self):
        self.pnt = self.receive()
        if self.pnt:
            self.parse_sokkia()
            self.vhd_to_xyz()

    def parse_sokkia(self):
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
                self.hangle = Angle(f'{vhd[2][:3]}d{vhd[2][3:5]}m{vhd[2][5:7]}').d
            else:
                self.hangle = None

    def initialize_sokkia(self):
        pass

    def fetch_hangle_sokkia(self):
        raise NotImplementedError("fetch_hangle_sokkia is not implemented yet.")
    
    """
    Leica specific functions
    """
    def make_dddmmss(self, angle):
        if angle.count('.') == 0:
            angle = angle + '.0000'
        elif angle.count('.') == 2:
            dms = angle.split('.')
            ms = '0000' + str(round(float(dms[1] + '.' + dms[2])))
            ms = ms[-4:]
            angle = str(dms[0] + '.' + ms)
        return angle

    def pad_dms_leica(self, angle):
        degrees = ('000' + angle.split('.')[0])[-3:]
        minutes_seconds = (angle.split('.')[1] + '0000')[0:4]
        return degrees + minutes_seconds

    def set_horizontal_angle_leica(self, angle):
        # function expects angle as ddd.mmss input
        # but decimal seconds are possible
        angle = self.make_dddmmss(angle)
        set_angle_command = "PUT/21...4+%s0 \r\n" % self.pad_dms_leica(angle)
        self.send(set_angle_command.encode())
        return self.receive()

    def launch_point_leica(self):
        self.send(b"GET/M/WI21/WI22/WI31/WI51\r\n")

    def fetch_point_leica(self):
        self.pnt = self.receive()
        self.set_response_leica()
        if self.pnt:
            self.parse_leica()
            self.vhd_to_xyz()

    def set_response_leica(self):
        self.response = self.leica_trim_crlf(self.received) if self.received else ""

    def parse_leica(self):
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

    def fetch_hangle_leica(self):
        raise NotImplementedError("fetch_hangle_leica is not implemented yet.")
    
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
                self.parse_geomax()
                self.vhd_to_xyz()

    def parse_geomax(self):
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

    def fetch_hangle_geomax(self):
        raise NotImplementedError("fetch_hangle_geomax is not implemented yet.")
    
    """
        Leica GeoCom specific functions
        Note that quite a few of these related to motorized total stations do not work because they require
        one to purchase an additional license from Leica.  I have not purchased this license and so cannot test these functions.
    """
    def initialize_geocom(self):
        try:
            good_connection = self.anyone_home_geocom()
            if not good_connection:
                raise ValueError("No response from Leica GeoCom total station.  Check connection issues and try again.")
            self.get_targettype_geocom()
            self.get_prismconstant_geocom()
        except Exception as e:
            raise ValueError(f"Error initializing Leica GeoCom total station: {e}")

    def get_settings_geocom(self):
        txt = "\n"
        try:
            results = self.get_atmosphere_geocom()
            txt += f"  Lambda: {results['lambda_constant']}\n"
            txt += f"  Pressure: {results['pressure']}\n"
            txt += f"  Dry Temperature: {results['dry_temperature']}\n"
            txt += f"  Wet Temperature: {results['wet_temperature']}\n"
        except Exception as e:
            pass

        try:
            results = self.get_atmosphere_correction_geocom()
            txt += f"  Atmosphere correction factor: {results}ppm\n"
        except Exception as e:
            pass

        try:
            results = self.get_station_coordinates_geocom()
            txt += f"  Station Coordinates: X:{results['x']}, Y:{results['y']}, Z:{results['z']}, Height:{results['height']} (Note: Only relevant for the XYZ displayed on the station.  EDM uses the station coordinates calculated during setup and listed above.)\n"
        except Exception as e:
            pass

        try:
            results = self.get_the_reflectorheight_geocom()
            txt += f"  Reflector height: {results} m (NOTE: Only relevant for the XYZ displayed on the station.  EDM uses the prism heights set in the program.)\n"
        except Exception as e:
            pass

        return txt
    
    def set_horizontal_angle_geocom(self, angle):
        # function expects angle as ddd.mmss as input
        # %R1Q,2113:HzOrientation[double]
        self.stop_and_clear_geocom()
        output = "%R1Q,2113:{:10.8f}\r\n".format(self.decdeg_to_radians(self.dms_to_decdeg(angle)))
        self.send(bytes(output, 'utf-8'))
        self.wait_for_received(1)
        self.set_response_leica_geocom()
        acceptable_error_codes = [0, 1285, 1289, 1288, 1292, 1291, 1293, 8, 12]
        try:
            if int(self.error_code) not in acceptable_error_codes:
                raise ValueError(f"Leica returned an error code of {self.error_code} of while setting horiztonal angle.  It could be that the station is not level enough for the auto-compensator can work.")
        except (TypeError):
            raise ValueError(f"Invalid error code: {self.error_code}")
        return True

    def launch_point_leica_geocom(self):
        self.clear_serial_buffers()
        self.send(b"%R1Q,2008:1,1\r\n")          # Use the defaults with 1 and 1
        self.wait_for_received(WAIT_FOR_RECEIVED_TIMEOUT)
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
        self.wait_for_received(WAIT_FOR_RECEIVED_TIMEOUT)
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
        else:
            self.error_code = -1

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

    def fetch_hangle_leica_geocom(self):
        """
        Fetch the horizontal angle using Leica GeoCOM TMC_GetAngle.
        Value is returned in DDD.MMSS format.
        """

        """Manual says that first I need to send a clear to DoMeasure"""
        self.stop_and_clear_geocom()

        self.send(b'%R1Q,2107:1\r\n')
        self.receive()
        self.set_response_leica_geocom()

        acceptable_error_codes = [0, 1285, 1289, 1288, 1292, 1291, 1293, 8, 12]
        values = self.response.split(',')
        if len(values) < 3:
            raise ValueError("Invalid response format: expected at least 3 values, got {}".format(len(values)))
        try:
            if int(values[0]) not in acceptable_error_codes:
                raise ValueError(f"Leica returned an error code of {values[0]}.  It could be that the station is not level enough for the auto-compensator can work.")
        except (TypeError):
            raise ValueError(f"Invalid error code: {values[0]}")
        try:
            hangle = self.decimal_degrees_to_dddmmss(self.radians_to_decdeg(float(values[1])))
        except (ValueError, TypeError):
            raise ValueError("Invalid horizontal angle value: {}".format(values[1]))

        return hangle

    def set_prism_mode_geocom(self):
        output = f"%R1Q,17021:0\r\n"
        self.send(bytes(output, 'utf-8'))
        self.wait_for_received(WAIT_FOR_RECEIVED_TIMEOUT)
        self.set_response_leica_geocom()
        return self.error_code == NO_ERROR
    
    def set_reflectorless_mode_geocom(self):
        output = f"%R1Q,17021:1\r\n"
        self.send(bytes(output, 'utf-8'))
        self.wait_for_received(5)
        self.set_response_leica_geocom()
        return self.error_code == NO_ERROR
    
    def prism_vs_reflectorless_geocom(self):
        try:
            self.get_targettype_geocom()
            if self.using_prism:
                self.set_reflectorless_mode_geocom()
                self.get_prismconstant_geocom()
                self.using_prism = False
                return f"Using\nReflectorless\n{self.prism_constant if self.prism_constant is not None else 0.0} mm\nconstant"
            else:
                self.set_prism_mode_geocom()
                self.get_prismconstant_geocom()
                self.using_prism = True
                return f"Using\nPrism\n{self.prism_constant if self.prism_constant is not None else 0.0} mm\nconstant"
        except ValueError as e:
            raise ValueError(f"{e}")

    def get_targettype_geocom(self):
        """Get the target type using Leica GeoCOM."""
        output = f"%R1Q,17022:\r\n"
        success = self.send(bytes(output, 'utf-8'))
        if not success:
            raise ValueError("Failed to send command to Leica GeoCOM for getting target type.")
        self.wait_for_received(WAIT_FOR_RECEIVED_TIMEOUT)
        self.set_response_leica_geocom()
        if self.response == "":
            raise ValueError("No response received from Leica while getting target type.")
        if self.error_code == NO_ERROR:
            values = self.response.split(',')
            try:
                if int(values[1]) == 0:
                    self.using_prism = True
                else:
                    self.using_prism = False
            except (ValueError, IndexError):
                raise ValueError(f"Invalid target type value: {values[1]}")
        else:
            raise ValueError(f"Leica returned an error code of {self.error_code} while getting target type.")
        
    def get_prismconstant_geocom(self):
        """Get the prism constant using Leica GeoCOM."""
        output = f"%R1Q,2023:\r\n"
        success = self.send(bytes(output, 'utf-8'))
        if not success:
            raise ValueError("Failed to send command to Leica GeoCOM for getting prism constant.")
        self.wait_for_received(WAIT_FOR_RECEIVED_TIMEOUT)
        self.set_response_leica_geocom()
        if self.response == "":
            raise ValueError("No response received from Leica while getting prism constant.")
        if self.error_code == NO_ERROR:
            values = self.response.split(',')
            try:
                self.prism_constant = round(float(values[1]) * 1000, 1)
            except (ValueError, IndexError):
                raise ValueError(f"Invalid prism constant value: {values[1]}")
        else:
            raise ValueError(f"Leica returned an error code of {self.error_code} while getting prism constant.")

    def get_atmosphere_geocom(self):
        """Get the atmosphere settings using Leica GeoCOM."""
        output = f"%R1Q,2029:\r\n"
        self.send(bytes(output, 'utf-8'))
        self.wait_for_received(WAIT_FOR_RECEIVED_TIMEOUT)
        self.set_response_leica_geocom()
        if self.error_code == NO_ERROR:
            values = self.response.split(',')
            try:
                atmosphere = {
                    "lambda_constant": float(values[1]),
                    "pressure": float(values[2]),
                    "dry_temperature": round(float(values[3]), 1),
                    "wet_temperature": round(float(values[4]), 1),
                }
                return atmosphere
            except (ValueError, IndexError):
                raise ValueError(f"Invalid atmosphere values: {self.response}")
        else:
            raise ValueError(f"Leica returned an error code of {self.error_code} while getting atmosphere settings.")

    def get_station_coordinates_geocom(self):
        """Get the station coordinates using Leica GeoCOM."""
        output = f"%R1Q,2009:\r\n"
        self.send(bytes(output, 'utf-8'))
        self.wait_for_received(WAIT_FOR_RECEIVED_TIMEOUT)
        self.set_response_leica_geocom()
        if self.error_code == NO_ERROR:
            values = self.response.split(',')
            try:
                coordinates = {
                    "x": float(values[1]),
                    "y": float(values[2]),
                    "z": float(values[3]),
                    "height": float(values[4]),
                }
                return coordinates
            except (ValueError, IndexError):
                raise ValueError(f"Invalid station coordinates values: {self.response}")
        else:
            raise ValueError(f"Leica returned an error code of {self.error_code} while getting station coordinates.")

    def get_atmosphere_correction_geocom(self):
        """Get the atmosphere correction factor using Leica GeoCOM."""
        output = f"%R1Q,2151:\r\n"
        self.send(bytes(output, 'utf-8'))
        self.wait_for_received(WAIT_FOR_RECEIVED_TIMEOUT)
        self.set_response_leica_geocom()
        if self.error_code == NO_ERROR:
            values = self.response.split(',')
            try:
                correction = round(float(values[1]), 3)
                return correction
            except (ValueError, IndexError):
                raise ValueError(f"Invalid atmosphere correction value: {self.response}")
        else:
            raise ValueError(f"Leica returned an error code of {self.error_code} while getting atmosphere correction.") 
        
    def get_the_reflectorheight_geocom(self):
        """Get the reflector height using Leica GeoCOM."""
        output = f"%R1Q,2011:\r\n"
        self.send(bytes(output, 'utf-8'))
        self.wait_for_received(WAIT_FOR_RECEIVED_TIMEOUT)
        self.set_response_leica_geocom()
        if self.error_code == NO_ERROR:
            values = self.response.split(',')
            try:
                reflector_height = round(float(values[1]), 3)
                return reflector_height
            except (ValueError, IndexError):
                raise ValueError(f"Invalid reflector height value: {self.response}")
        else:
            raise ValueError(f"Leica returned an error code of {self.error_code} while getting reflector height.")

    def upload_station_coordinates_geocom(self):
        if self.location.is_none():
            raise ValueError("Station coordinates are not set. Cannot upload to Leica GeoCOM.")
        output = f"%R1Q,2010:{self.location.x},{self.location.y},{self.location.z},0.000\r\n"
        self.send(bytes(output, 'utf-8'))
        self.wait_for_received(WAIT_FOR_RECEIVED_TIMEOUT)
        self.set_response_leica_geocom()
        if self.error_code == NO_ERROR:
            return True
        else:
            raise ValueError(f"Leica returned an error code of {self.error_code} while uploading station coordinates.")
    
    def anyone_home_geocom(self):
        """Check if anyone is home using Leica GeoCOM."""
        output = f"%R1Q,0:\r\n"
        self.send(bytes(output, 'utf-8'))
        self.wait_for_received(WAIT_FOR_RECEIVED_TIMEOUT)
        self.set_response_leica_geocom()
        if self.error_code == NO_ERROR:
            return True
        else:
            return False