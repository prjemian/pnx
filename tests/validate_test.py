
'''
test punx tests/validate module

ISSUES

* [ ] #93 special classpath for non-NeXus groups
* [*] #92 add attributes to classpath
* [ ] #91 test changes in NXDL rules
* [*] #89 while refactoring 72, fix logging
* [ ] #72 refactor to validate application definitions

'''

import os
import sys
import h5py
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import punx, punx.validate, punx.utils


class No_Exception(Exception): pass


class Test_Constructor_Exceptions(unittest.TestCase):

    def test_bad_file_set_reference(self):
        self.assertRaises(
            KeyError, 
            punx.validate.Data_File_Validator, 
            'bad file set reference')

    def test_bad_file_name_detected(self):
        v = punx.validate.Data_File_Validator()
        self.assertRaises(punx.FileNotFound, v.validate, 'bad file name')

    def test_not_HDF5_file_detected(self):
        v = punx.validate.Data_File_Validator()
        self.assertRaises(punx.HDF5_Open_Error, v.validate, __file__)


class Test_Constructor(unittest.TestCase):
    
    def avert_exception(self, fname):
        try:
            self.validator = punx.validate.Data_File_Validator()
            self.validator.validate(fname)
        except Exception as _exc:
            pass
        else:
            self.validator.close()
            self.validator = None
            raise No_Exception
 
    def setUp(self):
        # create the test file
        tfile = tempfile.NamedTemporaryFile(suffix='.hdf5', delete=False)
        tfile.close()
        self.hdffile = tfile.name
        self.validator = None
     
    def tearDown(self):
        if self.validator is not None:
            self.validator.close()
            self.validator = None
        os.remove(self.hdffile)
        self.hdffile = None

    def test_valid_hdf5_file_constructed(self):
        f = h5py.File(self.hdffile)
        f['item'] = 5
        f.close()

        self.assertRaises(No_Exception, self.avert_exception, self.hdffile)
        self.validator = punx.validate.Data_File_Validator()
        self.validator.validate(self.hdffile)
        self.assertTrue(
            punx.utils.isHdf5FileObject(self.validator.h5), 
            "is valid HDF5 file")
        self.validator.close()
        self.validator = None

    def test_valid_nexus_file_constructed(self):
        f = h5py.File(self.hdffile)
        g = f.create_group("entry")
        g.attrs["NX_class"] = "NXentry"
        f.close()

        self.assertRaises(No_Exception, self.avert_exception, self.hdffile)
        self.assertTrue(punx.utils.isNeXusFile(self.hdffile), "is valid NeXus file")


class Test_Changing_NXDL_Rules(unittest.TestCase):

    def test_specific_hdf5_addresses_can_be_found(self):
        # TODO: (#91) test something that is defined in 
        #       one NXDL file set but not another,
        #       such as: NXdata group not required after NIAC2016
        assertTrue(True)


class Test_Validate(unittest.TestCase):

    def setUp(self):
        # create the test file
        tfile = tempfile.NamedTemporaryFile(suffix='.hdf5', delete=False)
        tfile.close()
        self.hdffile = tfile.name
        self.validator = None
     
    def tearDown(self):
        if self.validator is not None:
            self.validator.close()
            self.validator = None
        os.remove(self.hdffile)
        self.hdffile = None

    def setup_simple_test_file(self):
        f = h5py.File(self.hdffile)
        f.attrs["default"] = "entry"
        eg = f.create_group("entry")
        eg.attrs["NX_class"] = "NXentry"
        eg.attrs["default"] = "data"
        dg = eg.create_group("data")
        dg.attrs["NX_class"] = "NXdata"
        dg.attrs["signal"] = "data"
        ds = dg.create_dataset("data", data=[1, 2, 3.14])
        eg["link_to_data"] = ds
        f.close()
        self.validator = punx.validate.Data_File_Validator()
        self.validator.validate(self.hdffile)

    def use_example_file(self, fname):
        path = os.path.join(os.path.dirname(punx.__file__), 'data', )
        example_file = os.path.abspath(os.path.join(path, fname))
        self.validator = punx.validate.Data_File_Validator()
        self.validator.validate(example_file)

    def test_specific_hdf5_addresses_can_be_found(self):
        self.setup_simple_test_file()
        self.assertEqual(len(self.validator.addresses), 10)

    def test_proper_classpath_determined(self):
        self.setup_simple_test_file()
        self.assertEqual(len(self.validator.classpaths), 10)

        obj = self.validator.addresses["/"]
        self.assertTrue(obj.classpath in self.validator.classpaths)
        self.assertEqual(obj.classpath, "")

        obj = self.validator.addresses["/entry/data/data"]
        self.assertTrue(obj.classpath in self.validator.classpaths)
        self.assertEqual(obj.classpath, "/NXentry/NXdata/data")
        
        self.assertTrue("@default" in self.validator.classpaths)
        self.assertTrue("/NXentry@default" in self.validator.classpaths)
        self.assertTrue("/NXentry/NXdata@signal" in self.validator.classpaths)

    def test_writer_1_3(self):
        self.use_example_file("writer_1_3.hdf5")
        self.assertTrue("/NXentry/NXdata@two_theta_indices" in self.validator.classpaths)
        self.assertTrue("/NXentry/NXdata@signal" in self.validator.classpaths)
        self.assertTrue("/NXentry/NXdata/counts" in self.validator.classpaths)
        self.assertTrue("/NXentry/NXdata/counts@units" in self.validator.classpaths)
        self.assertTrue("/NXentry/NXdata/two_theta@units" in self.validator.classpaths)


def suite(*args, **kw):
    test_suite = unittest.TestSuite()
    test_list = [
        Test_Constructor,
        Test_Constructor_Exceptions,
        Test_Validate,
        ]
    for test_case in test_list:
        test_suite.addTest(unittest.makeSuite(test_case))
    return test_suite


if __name__ == '__main__':
    runner=unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
