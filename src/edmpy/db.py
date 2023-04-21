from tinydb import TinyDB, Query, where
import re
from typing import Dict
from math import sqrt
import logging

from geo import datum, unit, prism
from lib.dbs import dbs

class DB(dbs):
    MAX_FIELDS = 30
    db = None
    filename = None
    db_name = 'points'
    new_data = {}  # type: Dict[str, bool]

    def open(self, filename):
        try:
            if self.valid_format(filename):
                self.db = TinyDB(filename, sort_keys = True, indent = 4, separators = (',', ': '))
                self.filename = filename
                self.prisms = self.db.table('prisms')
                self.new_data['prisms'] = True
                self.units = self.db.table('units')
                self.new_data['units'] = True
                self.datums = self.db.table('datums')
                self.new_data['datums'] = True
                logger = logging.getLogger(__name__)
                logger.info('Database ' + filename + ' opened.')
                return True
            else:
                return False
        except FileNotFoundError:
            return False

    def get_unitid(self, unitid):
        unit, id = unitid.split('-')
        p = self.db.search((where('unit') == unit) & (where('id') == id)) if self.db else None
        return p if p else None

    def get_datum(self, name = None):
        p = self.get_by_name('datums', name)
        return datum(p['NAME'] if 'NAME' in p.keys() else None,
                        float(p['X']) if 'X' in p.keys() else None,
                        float(p['Y']) if 'Y' in p.keys() else None,
                        float(p['Z']) if 'Z' in p.keys() else None,
                        p['NOTES'] if 'NOTES' in p.keys() else '')

    def get_unit(self, name):
        p = self.get_by_name('units', name)
        return unit(name = p['NAME'] if 'NAME' in p.keys() else None,
                    minx = float(p['MINX']) if 'MINX' in p.keys() else None,
                    miny = float(p['MINY']) if 'MINY' in p.keys() else None,
                    maxx = float(p['MAXX']) if 'MAXX' in p.keys() else None,
                    maxy = float(p['MAXY']) if 'MAXY' in p.keys() else None,
                    centerx = float(p['CENTERX']) if 'CENTERX' in p.keys() else None,
                    centery = float(p['CENTERY']) if 'CENTERY' in p.keys() else None,
                    radius = float(p['RADIUS']) if 'RADIUS' in p.keys() else None)

    def get_prism(self, name):
        p = self.get_by_name('prisms', name)
        return prism(p['NAME'] if 'NAME' in p.keys() else None,
                        float(p['HEIGHT']) if 'HEIGHT' in p.keys() else None,
                        float(p['OFFSET']) if 'OFFSET' in p.keys() else None)

    def get_by_name(self, table = None, name = None):
        if table is not None and name is not None and self.db is not None:
            item = Query()
            p = self.db.table(table).search(item.NAME.matches('^' + name + '$', flags = re.IGNORECASE))
            if p != []:
                return p[0]
        return {}

    def delete_unit(self, name = None):
        return self.delete_by_name('units', name)

    def delete_prism(self, name = None):
        return self.delete_by_name('prisms', name)

    def delete_datum(self, name = None):
        return self.delete_by_name('datums', name)

    def delete_by_name(self, table = None, name = None):
        if name is not None and table is not None and self.db is not None:
            item = Query()
            self.db.table(table).remove(item.NAME.matches('^' + name + '$', flags = re.IGNORECASE))
            return True
        return False

    def unit_ids(self):
        return [row['UNIT'] + '-' + row['ID'] for row in self.db.table(self.table)] if self.db is not None else []

    def names(self, table_name):
        return [row['NAME'] for row in self.db.table(table_name) if 'NAME' in row] if self.db is not None and table_name is not None else []

    def distance(self, p1, a_unit):
        return sqrt((p1.x - a_unit.centerx)**2 + (p1.y - a_unit.centery)**2)

    def point_in_unit(self, xyz = None):
        if xyz.x is not None and xyz.y is not None:
            for unitname in self.names('units'):
                a_unit = self.get_unit(unitname)
                if a_unit.is_valid() is True:
                    if a_unit.minx is not None and a_unit.miny is not None and a_unit.maxx is not None and a_unit.maxy is not None:
                        if xyz.x <= a_unit.maxx and xyz.x >= a_unit.minx and xyz.y <= a_unit.maxy and xyz.y >= a_unit.miny:
                            return a_unit.name
                    elif a_unit.centerx is not None and a_unit.centery is not None and not a_unit.radius == 0.0:
                        if self.distance(xyz, a_unit) <= a_unit.radius:
                            return a_unit.name
        return None

    def get_link_fields(self, name = None, value = None):
        if name is not None and value is not None and self.db is not None:
            q = Query()
            r = self.db.table(name).search(q[name].matches('^' + value + '$', re.IGNORECASE))
            if r != []:
                return r[0]
        return None
