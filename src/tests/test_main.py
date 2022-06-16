from edmpy.edm import MainScreen
from edmpy.edm import totalstation
from edmpy.edm import point
from edmpy.edm import datum
from edmpy.edm import prism
from edmpy.edm import unit

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
        self.assertTrue(self.datum1.is_none())
        self.assertEqual(self.datum1, self.datum2)
        self.assertFalse(self.datum3.is_none())


class Test_FileMenu(unittest.TestCase):
    def setUp(self):
        if path.exists('Import_from_EDM-Mobile/examples/BachoKiro.json'):
            remove('Import_from_EDM-Mobile/examples/BachoKiro.json')
        if path.exists('Import_from_EDM-Mobile/examples/ranis_2021.json'):
            remove('Import_from_EDM-Mobile/examples/ranis_2021.json')
        self.mainscreen = MainScreen(user_data_dir = '')

    def test_imports(self):
        for data_set in ['BK', 'RANIS']:
            if data_set == 'BK':
                self.mainscreen.load_cfg('Import_from_EDM-Mobile/examples/', ['BachoKiro.CFG'])
                table_lengths = {'datums': 23, 'prisms': 6, 'units': 65, 'points': 32}
                prefix = 'bk'
            elif data_set == 'RANIS':
                self.mainscreen.load_cfg('Import_from_EDM-Mobile/examples/', ['ranis_2021.CFG'])
                table_lengths = {'datums': 26, 'prisms': 12, 'units': 7, 'points': 5}
                prefix = 'ranis'

            self.assertNotEqual(self.mainscreen.data.status(), '\nA data file has not been opened.\n')

            self.mainscreen.csv_data_type = 'Datums'
            self.assertEqual(self.mainscreen.load_csv('Import_from_EDM-Mobile/examples/', [f'{prefix}_datums.txt']), '')
            self.assertEqual(len(self.mainscreen.data.db.table('datums')), table_lengths['datums'])

            # Do it twice to make sure duplicates are not created
            self.assertEqual(self.mainscreen.load_csv('Import_from_EDM-Mobile/examples/', [f'{prefix}_datums.txt']), '')
            self.assertEqual(len(self.mainscreen.data.db.table('datums')), table_lengths['datums'])

            self.mainscreen.csv_data_type = 'Prisms'
            self.assertEqual(self.mainscreen.load_csv('Import_from_EDM-Mobile/examples/', [f'{prefix}_prisms.txt']), '')
            self.assertEqual(len(self.mainscreen.data.db.table('prisms')), table_lengths['prisms'])
            self.assertEqual(self.mainscreen.data.fields('prisms'), ['NAME', 'HEIGHT', 'OFFSET'])

            # Do it twice to make sure duplicates are not created
            self.assertEqual(len(self.mainscreen.data.db.table('prisms')), table_lengths['prisms'])
            self.assertEqual(self.mainscreen.data.fields('prisms'), ['NAME', 'HEIGHT', 'OFFSET'])

            self.mainscreen.csv_data_type = 'Units'
            self.assertEqual(self.mainscreen.load_csv('Import_from_EDM-Mobile/examples/', [f'{prefix}_units.txt']), '')
            self.assertEqual(len(self.mainscreen.data.db.table('units')), table_lengths['units'])

            # Do it twice to make sure duplicates are not created
            self.assertEqual(self.mainscreen.load_csv('Import_from_EDM-Mobile/examples/', [f'{prefix}_units.txt']), '')
            self.assertEqual(len(self.mainscreen.data.db.table('units')), table_lengths['units'])

            self.mainscreen.csv_data_type = 'Points'
            self.assertEqual(self.mainscreen.load_csv('Import_from_EDM-Mobile/examples/', [f'{prefix}_points.txt']), '')
            self.assertEqual(len(self.mainscreen.data.db.table('_default')), table_lengths['points'])

            # Do it twice to make sure duplicates are not created
            self.assertEqual(self.mainscreen.load_csv('Import_from_EDM-Mobile/examples/', [f'{prefix}_points.txt']), '')
            self.assertEqual(len(self.mainscreen.data.db.table('_default')), table_lengths['points'])

            datum_name = self.mainscreen.data.db.table('datums').all()[-1]['NAME']
            self.assertNotEqual(self.mainscreen.data.get_datum(datum_name), datum())
            self.assertTrue(self.mainscreen.data.delete_datum(datum_name))
            self.assertTrue(self.mainscreen.data.get_datum(datum_name).is_none())

            prism_name = self.mainscreen.data.db.table('prisms').all()[-1]['NAME']
            self.assertNotEqual(self.mainscreen.data.get_prism(prism_name), prism())
            self.assertTrue(self.mainscreen.data.delete_prism(prism_name))
            self.assertTrue(self.mainscreen.data.get_prism(prism_name).is_none())

            for unit_name in self.mainscreen.data.names('units'):
                unit_data = self.mainscreen.data.get_unit(unit_name)
                if unit_data.is_valid() is True:
                    break
            self.assertEqual(self.mainscreen.data.point_in_unit(point(-1000, -1000, 0)), None)
            self.assertEqual(self.mainscreen.data.point_in_unit(point(unit_data.minx, unit_data.miny, 0)), unit_data.name)

            self.assertNotEqual(self.mainscreen.data.get_unit(unit_name), unit())
            self.assertTrue(self.mainscreen.data.delete_unit(unit_name))
            self.assertTrue(self.mainscreen.data.get_unit(unit_name).is_none())

            self.assertNotEqual(self.mainscreen.data.unit_ids(), [])
            self.assertNotEqual(self.mainscreen.data.names('prisms'), [])
            self.assertNotEqual(self.mainscreen.data.names('units'), [])
            self.assertNotEqual(self.mainscreen.data.names('datums'), [])
            self.assertEqual(self.mainscreen.data.names('_default'), [])

            self.mainscreen.data.delete_all('prisms')
            self.assertEqual(len(self.mainscreen.data.db.table('prisms')), 0)

            self.mainscreen.data.delete_all()
            self.assertEqual(len(self.mainscreen.data.db.table('_default')), 0)

            self.mainscreen.data.db.close()

        # need a test of export of csvs
        # need to test the LF data
        # need to test the ranis data

    def tearDown(self) -> None:
        self.mainscreen.data.db.close()
        if path.exists('EDM.ini'):
            remove('EDM.ini')
        if path.exists('Import_from_EDM-Mobile/examples/BachoKiro.json'):
            remove('Import_from_EDM-Mobile/examples/BachoKiro.json')
        if path.exists('Import_from_EDM-Mobile/examples/ranis_2021.json'):
            remove('Import_from_EDM-Mobile/examples/ranis_2021.json')


if __name__ == '__main__':
    unittest.main()
