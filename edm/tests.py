from main import MainScreen
from main import totalstation
from main import point
from main import datum

import unittest

from os import path
from os import remove

class Test_TotalStation(unittest.TestCase):
    def setUp(self):
        self.ts = totalstation()

    def test_angles(self):
        self.assertEqual(self.ts.dot_product(self.ts.normalize_vector(point(0, 1, 0)), self.ts.normalize_vector(point(0, 1, 0))), 1.0)
        self.assertEqual(self.ts.dot_product(self.ts.normalize_vector(point(0, 1, 0)), self.ts.normalize_vector(point(1, 0, 0))), 0.0)
        self.assertEqual(self.ts.dot_product(self.ts.normalize_vector(point(0, 1, 0)), self.ts.normalize_vector(point(0, -1, 0))), -1.0)
        self.assertEqual(self.ts.dot_product(self.ts.normalize_vector(point(0, 1, 0)), self.ts.normalize_vector(point(-1, 0, 0))), 0.0)

        self.assertEqual(self.ts.angle_between_points(point(-1, 1, 0), point(-1, 2, 0)), 0.0)
        self.assertEqual(self.ts.angle_between_points(point(-1, 1, 0), point(1, 1, 0)), 90.0)
        self.assertEqual(self.ts.angle_between_points(point(-1, 1, 0), point(-1, -1, 0)), 180.0)
        self.assertEqual(self.ts.angle_between_points(point(-1, 1, 0), point(-2, 1, 0)), 270.0)

class Test_DataClasses(unittest.TestCase):
    def setUp(self):
        self.datum1 = datum()
        self.datum2 = datum()
        self.datum3 = datum('Test', 1000, 1000, 1000)

    def test_datums(self):
        self.assertEqual(self.datum1.is_none(), True)
        self.assertEqual(self.datum1, self.datum2)
        self.assertEqual(self.datum3.is_none(), False)

class Test_FileMenu(unittest.TestCase):
    def setUp(self):
        if path.exists('./Import_from_EDM-Mobile/examples/BachoKiro.json'):
            remove('./Import_from_EDM-Mobile/examples/BachoKiro.json')
        self.mainscreen = MainScreen(user_data_dir = '')
        self.mainscreen.load_cfg('./Import_from_EDM-Mobile/examples/', ['BachoKiro.CFG'])

    def test_imports(self):
        self.mainscreen.csv_data_type = 'Datums'
        self.assertEqual(self.mainscreen.load_csv('./Import_from_EDM-Mobile/examples/', ['bk_datums.txt']), '')
        self.assertEqual(len(self.mainscreen.data.db.table('datums')), 23)

        self.mainscreen.csv_data_type = 'Prisms'
        self.assertEqual(self.mainscreen.load_csv('./Import_from_EDM-Mobile/examples/', ['bk_prisms.txt']), '')
        self.assertEqual(len(self.mainscreen.data.db.table('prisms')), 6)

        self.mainscreen.csv_data_type = 'Units'
        self.assertEqual(self.mainscreen.load_csv('./Import_from_EDM-Mobile/examples/', ['bk_units.txt']), '')
        self.assertEqual(len(self.mainscreen.data.db.table('units')), 65)

        # Do it twice to make sure duplicates are not created
        self.assertEqual(self.mainscreen.load_csv('./Import_from_EDM-Mobile/examples/', ['bk_units.txt']), '')
        self.assertEqual(len(self.mainscreen.data.db.table('units')), 65)

    def tearDown(self) -> None:
        self.mainscreen.data.db.close()
        if path.exists('EDM.ini'):
            remove('EDM.ini')

if __name__ == '__main__':
    unittest.main()