from edmpy.edm import EDM

import unittest


class TestEDM(unittest.TestCase):
    def setUp(self):
        self.edm = EDM()

    def test_reset_screens(self):
        # Add some screens
        self.edm.add_screens()
        initial_screen_count = len(self.edm.screens)

        # Reset the screens
        self.edm.reset_screens()

        # Check if screens are deleted and added again
        self.assertEqual(len(self.edm.screens), initial_screen_count)


if __name__ == '__main__':
    unittest.main()
