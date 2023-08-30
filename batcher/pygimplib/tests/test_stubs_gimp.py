import unittest

from . import stubs_gimp


class TestPdbStub(unittest.TestCase):
  
  def setUp(self):
    self.pdb = stubs_gimp.PdbStub()
  
  def test_known_pdb_func(self):
    image = stubs_gimp.ImageStub()
    image.valid = False
    self.assertFalse(self.pdb.gimp_image_is_valid(image))
  
  def test_unknown_pdb_func(self):
    self.assertTrue(callable(self.pdb.plug_in_autocrop))
    self.assertEqual(self.pdb.plug_in_autocrop(), 'plug_in_autocrop')
    self.assertEqual(
      self.pdb.plug_in_autocrop('some random args', 1, 2, 3), 'plug_in_autocrop')
