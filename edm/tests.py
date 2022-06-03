from main import totalstation
from main import point
from main import datum
from angles import r2d

import unittest

class TestTotalStation(unittest.TestCase):
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

class TestDataClasses(unittest.TestCase):
    def setUp(self):
        self.datum1 = datum()
        self.datum2 = datum()
        self.datum3 = datum('Test', 1000, 1000, 1000)

    def test_datums(self):
        self.assertEqual(self.datum1.is_none(), True)
        self.assertEqual(self.datum1, self.datum2)
        self.assertEqual(self.datum3.is_none(), False)



#ts = totalstation()
#cosangle = ts.dot_product(ts.normalize_vector(point(0, 1, 0)), ts.normalize_vector(point(0, -1, 0)))
#print(cosangle)

if __name__ == '__main__':
    unittest.main()