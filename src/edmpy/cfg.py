from typing import List
from tinydb import where
import logging
import os

from edmpy.lib.blockdata import blockdata

__BUTTONS__ = 13
__DEFAULT_FIELDS__ = ['X', 'Y', 'Z', 'SLOPED', 'VANGLE', 'HANGLE', 'STATIONX', 'STATIONY', 'STATIONZ', 'LOCALX', 'LOCALY', 'LOCALZ', 'DATE', 'PRISM', 'ID']
__DEFAULT_FIELDS_NUMERIC__ = ['X', 'Y', 'Z', 'SLOPED', 'STATIONX', 'STATIONY', 'STATIONZ', 'LOCALX', 'LOCALY', 'LOCALZ', 'PRISM']


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
        return self.load()

    def validate_datafield(self, data_to_insert, data_table):
        # This just validates one field (e.g. when an existing record is edit)
        if data_to_insert and data_table and len(data_to_insert) == 1:
            for field, value in data_to_insert.items():
                f = self.get(field)
                if f.required and str(value).strip() == "":
                    error_message = f'\nThe field {field} is set to unique or required.  Enter a value to save this record.'
                    return error_message
                if f.inputtype == 'NUMERIC':
                    try:
                        float(value)
                    except ValueError:
                        error_message = f'\nThe field {field} requires a valid number.  Correct to save this record.'
                        return error_message
                if f.unique:
                    result = data_table.search(where(field) == value)
                    if result:
                        error_message = f'\nThe field {field} is set to unique and the value {value} already exists for this field in this data table.'
                        return error_message
                if "\"" in str(value):
                    error_message = f'\nThe field {field} contains characters that are not recommended in a data file.  These include \" and \\.'
                    return error_message
        return True

    def validate_datarecord(self, data_to_insert, data_table):
        # This validates one record (e.g. one a record is about to be inserted)
        for field in self.fields():
            f = self.get(field)
            if f.required:
                if field in data_to_insert.keys():
                    if str(data_to_insert[field]).strip() == '':
                        error_message = f'\nThe field {field} is set to unique or required.  Enter a value to save this record.'
                        return error_message
                else:
                    error_message = f'\nThe field {field} is set to unique or required.  Enter a value to save this record.'
                    return error_message
            if f.inputtype == 'NUMERIC':
                if field in data_to_insert.keys():
                    try:
                        float(data_to_insert[field])
                    except ValueError:
                        error_message = f'\nThe field {field} requires a valid number.  Correct to save this record.'
                        return error_message
            if f.unique:
                if field in data_to_insert.keys():
                    result = data_table.search(where(field) == data_to_insert[field])
                    if result:
                        error_message = f'\nThe field {field} is set to unique and the value {data_to_insert[field]} already exists \
                                            for this field in this data table.'
                        return error_message
                else:
                    error_message = f'\nThe field {field} is set to unique and a value was not provided for this field.  Unique fields require a value.'
                    return error_message

        # TODO test to see if it is units, prisms or datums
        # TODO create a unit, prism or datum from the dictionary using *data_to_insert
        # TODO run the validator in whichever
        # TODO and return results
        return True

    def save_as_numeric_field(self, field_name):
        if field_name in ['HANGLE', 'VANGLE']:
            return False
        if field_name in __DEFAULT_FIELDS_NUMERIC__:
            return True
        return self.get_value(field_name, 'TYPE').upper() == 'NUMERIC'

    def edit_as_numeric_field(self, field_name):
        if field_name in __DEFAULT_FIELDS_NUMERIC__:
            return True
        return self.get_value(field_name, 'TYPE').upper() == 'NUMERIC'

    def get(self, field_name):
        if not field_name:
            return ''
        f = self.field(field_name)
        f.inputtype = self.get_value(field_name, 'TYPE').upper()
        f.prompt = self.get_value(field_name, 'PROMPT')
        f.length = self.get_value(field_name, 'LENGTH')
        menulist = self.get_value(field_name, 'MENU')
        f.menu = self.clean_menu((menulist).split(",")) if menulist else []
        link_fields = self.get_value(field_name, 'LINKED')
        if link_fields:
            f.link_fields = link_fields.upper().split(",")
        f.carry = self.get_value(field_name, 'CARRY').upper() == 'TRUE'
        f.required = self.get_value(field_name, 'REQUIRED').upper() == 'TRUE'
        f.increment = self.get_value(field_name, 'INCREMENT').upper() == 'TRUE'
        f.unique = self.get_value(field_name, 'UNIQUE').upper() == 'TRUE'
        if f.unique:
            f.required = True
        return f

    def clean_menu(self, menulist):
        # Remove leading and trailing spaces
        menulist = [item.strip() for item in menulist]
        # and remove empty items.
        menulist = list(filter(('').__ne__, menulist))
        return menulist

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
        return field_names

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
        self.update_value('UNIT', 'Type', 'Menu')
        self.update_value('UNIT', 'Length', 6)
        self.update_value('UNIT', 'REQUIRED', 'TRUE')
        self.update_value('UNIT', 'CARRY', 'TRUE')

        self.update_value('ID', 'Prompt', 'ID :')
        self.update_value('ID', 'Type', 'Text')
        self.update_value('ID', 'Length', 6)
        self.update_value('ID', 'REQUIRED', 'TRUE')
        self.update_value('ID', 'INCREMENT', 'TRUE')

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
                self.errors.append(f"The table name {table_name} has non-standard characters in it that cause a problem in JSON files.  "\
                                    "Do not use any of these '{bad_characters}' characters.  Change the name before collecting data.")
                self.has_errors = True

        unique_together = self.get_value('EDM', 'UNIQUE_TOGETHER')
        if unique_together:
            no_errors = True
            for field_name in unique_together.split(','):
                if field_name not in field_names:
                    self.errors.append(f"The field '{field_name}' is listed in UNIQUE_TOGETHER but does not appear as a field in the CFG file.")
                    self.has_errors = True
                    no_errors = False
                    break
            self.unique_together = unique_together.split(',') if no_errors else []
        else:
            if 'UNIT' in field_names and 'ID' in field_names and 'SUFFIX' in field_names:
                self.update_value('EDM', 'UNIQUE_TOGETHER', 'UNIT,ID,SUFFIX')
                self.unique_together = ['UNIT', 'ID', 'SUFFIX']
            if 'ID' in field_names and 'SUFFIX' in field_names:
                self.update_value('EDM', 'UNIQUE_TOGETHER', 'ID,SUFFIX')
                self.unique_together = ['ID', 'SUFFIX']

        for field_name in field_names:
            if any((c in set(bad_characters)) for c in field_name):
                self.errors.append(f"The field name '{field_name}' has non-standard characters in it that cause a problem in JSON files.  "
                                    f"Do not use any of these '{bad_characters}' characters.  Change the name before collecting data.")
                self.has_errors = True
            f = self.get(field_name)

            if not self.is_numeric(f.length):
                self.errors.append(f'The length specified for field {field_name} must be a valid number.  If you do not want to limit the length, '
                                     'delete the Length specification in the CFG.')
                self.has_errors = True

            if f.prompt == '':
                f.prompt = field_name

            f.inputtype = f.inputtype.upper()

            if f.inputtype == '':
                if field_name in ['X', 'Y', 'Z', 'SLOPED', 'VANGLE', 'HANGLE', 'STATIONX', 'STATIONY', 'STATIONZ', 'LOCALX', 'LOCALY', 'LOCALZ', 'PRISM']:
                    f.inputtype = 'NUMERIC'
                elif field_name in ['DATE']:
                    f.inputtype = 'DATETIME'
                else:
                    f.inputtype = 'TEXT'

            if f.inputtype not in ['TEXT', 'NOTE', 'NUMERIC', 'MENU', 'DATETIME', 'BOOLEAN', 'CAMERA', 'GPS', 'INSTRUMENT']:
                self.errors.append(f"The value '{f.inputtype}' for the field {field_name} is not a valid TYPE. "
                                    "Valid TYPES include Text, Note, Numeric, and Menu.")
                self.has_errors = True

            if field_name in ['UNIT', 'ID', 'SUFFIX', 'X', 'Y', 'Z']:
                self.update_value(field_name, 'REQUIRED', 'TRUE')

            if field_name == 'ID':
                self.update_value(field_name, 'INCREMENT', 'TRUE')

            if f.link_fields:
                self.link_fields.append(field_name)
                # uppercase the link fields
                for link_field_name in f.link_fields:
                    if link_field_name not in field_names:
                        self.errors.append(f"The field {field_name} is set to link to {link_field_name} but the field {link_field_name} "
                                            "does not exist in the CFG.")
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
            self.errors.append('Every CFG file should contain at least one field or a set of fields that together are unique.  '\
                                'Normally, this will be something like Unit, ID and Suffix together.  '\
                                'Set this value by either setting one field to UNIQUE=TRUE or by adding a UNIQUE_TOGETHER line in '\
                                'the EDM block of the CFG file (e.g. something like UNIQUE_TOGETHER=UNIT,ID,SUFFIX).')
            self.has_errors = True

        return (self.has_errors, self.errors)

    def is_numeric(self, value):
        if value:
            try:
                float(value)
                return True
            except ValueError:
                return False
        else:
            return True

    def save(self):
        self.write_blocks()

    def load(self, filename = ''):
        if filename:
            self.filename = filename
        self.path = os.path.split(self.filename)[0]

        self.blocks = []
        if os.path.isfile(self.filename):
            self.blocks = self.read_blocks()
            has_errors, errors = self.validate()
            if not has_errors:     # This is bad.  Errors returned are not dealt with when starting program
                self.save()
            else:
                return (has_errors, errors)
        else:
            self.filename = 'default.cfg'
            self.build_default()
        logger = logging.getLogger(__name__)
        logger.info('CFG ' + self.filename + ' opened.')
        return (False, [])

    def status(self):
        txt = '\nCFG file is %s\n' % self.filename
        return txt

    def write_csvs(self, filename, table):
        '''
        This routine could be shortened with Python libraries, however,
        It is written this way to ensure a proper CSV even if users
        change their CFG part way through data collection
        (meaning that the CFG and the JSON datafile do not perfectly match)
        '''
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
            return ''
        except OSError:
            return '\nCould not write data to %s.' % (filename)

    def get_unique_key(self, data_record, unique_together):
        unique_key = []
        for field in unique_together:
            unique_key.append("%s" % data_record[field] if field in data_record else '')
        return "-".join(unique_key)

    def get_objects(self, table):
        unique_together = self.unique_together
        if 'SUFFIX' in unique_together:
            unique_together.remove('SUFFIX')
        objects = {}
        for row in table:
            unique_key = self.get_unique_key(row, unique_together)
            # print(row)
            if unique_key in objects:
                objects[unique_key][int(row['SUFFIX'])] = row.doc_id
            else:
                objects[unique_key] = {int(row['SUFFIX']): row.doc_id}
        return objects

    def build_properties(self, row, cfg_fields):
        properties = ''
        comma = ' '
        for fieldname in cfg_fields:
            if fieldname in row.keys():
                if row[fieldname] != '':
                    properties += comma + f'"{fieldname}": '
                    if cfg_fields[fieldname] in ['NUMERIC', 'INSTRUMENT']:
                        properties += str(row[fieldname])
                    else:
                        properties += f'"{row[fieldname]}"'
                    comma = ', '
        return properties

    def get_object(self, table, doc_ids, cfg_fields_optional, cfg_fields_defaults):
        properties = ''
        points = []
        for doc_id in sorted(doc_ids):
            row = table.get(doc_id = doc_ids[doc_id])
            if not properties:
                properties = self.build_properties(row, cfg_fields_optional)
            properties += ', "Suffix_%s": {' % row['SUFFIX'] + self.build_properties(row, cfg_fields_defaults) + "}"
            points.append(self.get_XYZ(row))
        return (properties, points)

    def points_to_json(self, points):
        if len(points) == 1:
            geojson_points = '"geometry": { "type": "Point", "coordinates": [ '
            geojson_points += '%s, %s, %s' % points[0]
        else:
            geojson_points = '"geometry": { "type": "LineString", "coordinates": [ '
            geojson_points += ', '.join(['[%s, %s, %s]' % point for point in points])
        geojson_points += '] } }'
        return geojson_points

    def fields_with_types(self):
        cfg_fields_with_types = {}
        for field in self.fields():
            cfg_fields_with_types[field] = self.get(field).inputtype
        return cfg_fields_with_types

    def remove_default_fields(self, cfg_fields):
        cfg_fields_optional = {}
        for field in cfg_fields:
            if field not in __DEFAULT_FIELDS__ or field == 'ID':
                cfg_fields_optional[field] = cfg_fields[field]
        return cfg_fields_optional

    def keep_default_fields(self, cfg_fields):
        cfg_fields_default = {}
        for field in cfg_fields:
            if field in __DEFAULT_FIELDS__:
                cfg_fields_default[field] = cfg_fields[field]
        return cfg_fields_default

    def write_geojson(self, filename, table, status):
        try:
            cfg_fields = self.fields_with_types()
            cfg_fields_optional = self.remove_default_fields(cfg_fields)
            cfg_fields_default = self.keep_default_fields(cfg_fields)
            if "SUFFIX" in cfg_fields_optional:
                cfg_fields_optional.pop('SUFFIX')
            basename = os.path.basename(filename)
            basename = os.path.splitext(basename)[0]
            geojson_header = '{\n'
            geojson_header += '"type": "FeatureCollection",\n'
            geojson_header += '"name": "%s",\n' % basename
            geojson_header += '"features": [\n'
            squids = self.get_objects(table)
            output = []
            for counter, squid in enumerate(squids):
                status.content.bar.value = counter / len(squids)
                properties, points = self.get_object(table, squids[squid], cfg_fields_optional, cfg_fields_default)
                output.append('{ "type": "Feature", "properties": {' + properties + ' },\n' + self.points_to_json(points))
            with open(filename, 'w') as handle:
                handle.write(geojson_header + ',\n'.join(output) + '\n]\n}')
            status.status = ''
        except Exception as e:
            status.status = '\nCould not write data to %s. %s' % (filename, str(e))

    def get_XY(self, row):
        cfg_fields = self.fields()
        if 'X' in cfg_fields and 'Y' in cfg_fields:
            return (row['X'], row['Y'])
        elif 'LATITUDE' in cfg_fields and 'LONGITUDE' in cfg_fields:
            return (row['LONGITUDE'], row['LATITUDE'])
        elif self.gps_field(row):
            gps_data = self.gps_to_dict(self.gps_field(row))
            return (gps_data['Lon'], gps_data['Lat'])
        else:
            return (0, 0)

    def get_XYZ(self, row):
        cfg_fields = self.fields()
        if 'X' in cfg_fields and 'Y' in cfg_fields and 'Z' in cfg_fields:
            return (row['X'], row['Y'], row['Z'])
        elif 'LATITUDE' in cfg_fields and 'LONGITUDE' in cfg_fields and 'ELEVATION' in cfg_fields:
            return (row['LONGITUDE'], row['LATITUDE'], row['ELEVATION'])
        elif self.gps_field(row):
            gps_data = self.gps_to_dict(self.gps_field(row))
            return (gps_data['Lon'], gps_data['Lat'], 0)
        else:
            return (0, 0, 0)

    def gps_field(self, row):
        for fieldname in self.fields():
            field = self.get(fieldname)
            if field.inputtype in ['GPS']:
                return row[fieldname]
        return ''

    def gps_to_dict(self, delimited_data):
        dict_data = {}
        for item in delimited_data.split(','):
            dict_item = item.split('=')
            dict_data[dict_item[0].strip()] = dict_item[1].strip()
        return dict_data
