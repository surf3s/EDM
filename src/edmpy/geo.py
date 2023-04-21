class point:
    def __init__(self, x = None, y = None, z = None):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return f'X : {round(self.x, 3)}, Y : {round(self.y, 3)}, Z : {round(self.z, 3)}'

    def __repr__(self):
        return f'X : {round(self.x, 3)}, Y : {round(self.y, 3)}, Z : {round(self.z, 3)}'

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.x == other.x and self.y == other.y and self.x == other.z
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_none(self):
        return self.x is None and self.y is None and self.y is None

    def round(self):
        self.x = round(self.x, 3)
        self.y = round(self.y, 3)
        self.z = round(self.z, 3)
        return self


class datum:
    def __init__(self, name = None, x = None, y = None, z = None, notes = ''):
        self.name = name if name else None
        self.x = x
        self.y = y
        self.z = z
        self.notes = notes

    def as_point(self):
        return point(self.x, self.y, self.z)

    def __str__(self):
        return f'Datum: {self.name} of X : {round(self.x, 3)}, Y : {round(self.y, 3)}, Z : {round(self.z, 3)}'

    def __repr__(self):
        return f'Datum: {self.name} of X : {round(self.x, 3)}, Y : {round(self.y, 3)}, Z : {round(self.z, 3)}'

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.x == other.x and self.y == other.y and self.x == other.z and self.name == other.name and self.notes == other.notes
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_none(self):
        return self.name is None and self.x is None and self.y is None and self.z is None and self.notes == ''


class prism:
    def __init__(self, name = None, height = None, offset = None):
        self.name = name
        self.height = height
        self.offset = offset

    def __str__(self):
        return 'Prism {self.name} with hieght of {round(self.height, 3)} and offset of {round(self.offset, 3)}'

    def __repr__(self):
        return f'Prism {self.name} with hieght of {round(self.height, 3)} and offset of {round(self.offset, 3)}'

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name and self.height == other.height and self.offset == other.offset
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_none(self):
        return self.name is None and self.height is None and self.offset is None

    def valid(self):
        if self.name == '':
            return 'A name field is required.'
        if len(self.name) > 20:
            return 'A prism name should be 20 characters or less.'
        if self.height == '':
            return 'A prism height is required.'
        if float(self.height) > 10:
            return 'Prism height looks too large.  Prism heights are in meters.'
        if self.offset == '':
            self.offset == 0.0
        if float(self.offset) > .2:
            return 'Prism offset looks to be too large.  Prism offsets are expressed in meters.'
        return True


class unit:
    def __init__(self, name = None, minx = None, miny = None, maxx = None, maxy = None, centerx = None, centery = None, radius = None):
        self.name = name
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.radius = radius
        self.centerx = centerx
        self.centery = centery

    def __str__(self):
        if not self.radius:
            return f'Unit {self.name} with limits ({self.minx},{self.miny})-({self.maxx},{self.maxy})'
        else:
            return f'Unit {self.name} centered on ({self.centerx},{self.centery}) with a radius of {self.radius}'

    def __repr__(self):
        if not self.radius:
            return f'Unit {self.name} with limits ({self.minx},{self.miny})-({self.maxx},{self.maxy})'
        else:
            return f'Unit {self.name} centered on ({self.centerx},{self.centery}) with a radius of {self.radius}'

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name and self.minx == other.minx and self.miny == other.miny and self.maxx == other.maxx and self.maxy == other.maxy and\
                self.centerx == other.centerx and self.centery == other.centery and self.radius == other.radius
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_none(self):
        return self.name is None and self.minx is None and self.miny is None and self.maxx is None and self.maxy is None and\
            self.radius is None and self.centerx is None and self.centery is None

    def is_valid(self):
        if self.name == '' or self.name is None:
            return 'A name field is required.'
        if len(self.name) > 20:
            return 'A unit name should be 20 characters or less.'
        if self.minx is not None and self.maxx is not None:
            if self.minx >= self.maxx:
                return 'The unit X2 coordinate must be larger than the X1 coordinate.'
        if self.miny is not None and self.maxy is not None:
            if self.miny >= self.maxy:
                return 'The unit Y2 coordinate must be larger than the Y1 coordinate.'
        return True
