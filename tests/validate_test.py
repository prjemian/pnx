
'''
test the punx validation process
'''

import h5py
import os
import sys
import unittest
from test.test_xmlrpc import ADDR

_path = os.path.join(os.path.dirname(__file__), '..', )
if _path not in sys.path:
    sys.path.insert(0, _path)
from tests import common

_path = os.path.join(_path, 'src')
if _path not in sys.path:
    sys.path.insert(0, _path)


class Validate_writer_1_3(common.ValidHdf5File):

    testfile = 'writer_1_3.hdf5'
    expected_output = common.read_filelines('validate_writer_1_3.txt')


class Validate_writer_2_1(common.ValidHdf5File):

    testfile = 'writer_2_1.hdf5'
    expected_output = common.read_filelines('validate_writer_2_1.txt')


class Validate_33id_spec_22_2D(common.ValidHdf5File):

    testfile = '33id_spec_22_2D.hdf5'
    expected_output = common.read_filelines('validate_33id_spec_22_2D.txt')


class Validate_compression(common.ValidHdf5File):

    testfile = 'compression.h5'
    expected_output = common.read_filelines('validate_compression.txt')
    NeXus = False
 
 
class Validate_NXdata_is_now_optional_51(unittest.TestCase):

    def setUp(self):
        self.testfile = common.getTestFileName()
        self.validator = None

    def tearDown(self):
        if self.validator is not None and isinstance(self.validator.h5, h5py.File):
            self.validator.h5.close()
            self.validator = None
        common.cleanup()

    def test_simple_NXdata(self):
        import punx.validate, punx.finding, punx.logs

        hdf5root = h5py.File(self.testfile, "w")

        entry = hdf5root.create_group("entry")
        entry.attrs['NX_class'] = 'NXentry'
        data = entry.create_group("data")
        data.attrs['NX_class'] = 'NXdata'
        data.attrs["signal"] = "data"
        data.create_dataset("data", data="a string of characters")

        hdf5root.close()
        
        punx.logs.ignore_logging()
        self.validator = punx.validate.Data_File_Validator(self.testfile)
        self.validator.validate()
        self.report = []
        
        report = self.validator.report_findings(punx.finding.VALID_STATUS_LIST)
        #print('\n' + report + '\n')
        msg = 'NeXus default plot: /entry/data/data'
        self.assertFalse(report.find('no default plot: not a NeXus file') >= 0, msg)
        
        report = self.validator.report_findings_summary().splitlines()[6]
        #print('\n' + report + '\n')
        msg = 'no ERRORs should be found'
        self.assertEqual(int(report.split()[1]), 0, msg)
        

    def test_simple_no_NXdata(self):
        import punx.validate, punx.finding, punx.logs

        hdf5root = h5py.File(self.testfile, "w")

        entry = hdf5root.create_group("entry")
        entry.attrs['NX_class'] = 'NXentry'

        hdf5root.close()
        
        punx.logs.ignore_logging()
        self.validator = punx.validate.Data_File_Validator(self.testfile)
        self.validator.validate()
        self.report = []
        
        report = self.validator.report_findings(punx.finding.VALID_STATUS_LIST)
        #print('\n' + report + '\n')
        msg = 'no NeXus default plot, no NXdata group, valid NeXus as of NIAC2016'
        self.assertFalse(report.find('no default plot: not a NeXus file') >= 0, msg)
        
        report = self.validator.report_findings_summary().splitlines()[6]
        #print('\n' + report + '\n')
        msg = 'no ERRORs should be found'
        self.assertEqual(int(report.split()[1]), 0, msg)


class Validate_example_mapping(common.ValidHdf5File):

    testfile = 'example_mapping.nxs'
    expected_output = common.read_filelines('validate_example_mapping.txt')
    NeXus = False


class Validate_example_mapping_issue_53(common.CustomHdf5File):
    
    def createContent(self, hdf5root):
        '''
        abbreviated representation of example_mapping.nxs file
        '''
        import numpy
        entry = hdf5root.create_group("entry")
        entry.attrs['NX_class'] = 'NXentry'
        data = entry.create_group("data")
        data.attrs['NX_class'] = 'NXdata'
        data.attrs["signal"] = "data"
        data.attrs["axes"] = [b"x", b"y"]
        data.attrs["x_indices"] = [0,]
        data.attrs["y_indices"] = [1,]
        ds = data.create_dataset("data", data=numpy.array([[1,2,3], [3,1,2]], dtype=int))
        ds.attrs["interpretation"] = "image"
        data.create_dataset("x", data=[1, 1.1, 1.3])
        data.create_dataset("y", data=[2.2, 2.5])
    
    def test_indices_attribute_value_as_string_in_HDF5_file(self):
        import punx.validate, punx.finding, punx.logs
        punx.logs.ignore_logging()
        validator = punx.validate.Data_File_Validator(self.testfile)
        validator.validate()
        self.assertGreaterEqual(len(validator.findings), 0)
        self.assertEqual(validator.findings[0].status, punx.finding.OK)
        # print(validator.report_findings(punx.finding.VALID_STATUS_LIST))
        self.assertEqual(validator.report_findings(punx.finding.ERROR), "None")
        validator.h5.close()
        
        # re-write the *_indices attributes as str in that HDF5 and re-validate
        hdf5root = h5py.File(self.testfile, "r+")
        hdf5root["/entry/data"].attrs["x_indices"] = [b"0",]
        hdf5root["/entry/data"].attrs["y_indices"] = [b"1",]
        hdf5root.close()
        validator = punx.validate.Data_File_Validator(self.testfile)
        validator.validate()
        self.assertGreaterEqual(len(validator.findings), 0)
        self.assertEqual(validator.findings[0].status, punx.finding.OK)
        # print(validator.report_findings(punx.finding.VALID_STATUS_LIST))
        self.assertEqual(validator.report_findings(punx.finding.ERROR), "None")
        validator.h5.close()


class Validate_issue_57(unittest.TestCase):
    
    def test_order_of_appearance__observation_1(self):
        import punx.validate, punx.finding, punx.logs
        import numpy

        # construct a test file and check it
        fname = common.getTestFileName()
        hdf5root = h5py.File(fname, 'w')
        entry = hdf5root.create_group("entry")
        entry.attrs['NX_class'] = 'NXentry'
        data = entry.create_group("data")
        data.attrs['NX_class'] = 'NXdata'
        data.attrs["signal"] = "data"
        ds = data.create_dataset("data", data=[[1,2,3], [3,1,2]])
        ds.attrs['target'] = ds.name
        entry['ds_link'] = ds
        # TODO: may need more items to match error reported in issue #57
        hdf5root.close()

        punx.logs.ignore_logging()
        validator = punx.validate.Data_File_Validator(fname)
        validator.validate()
        # print('\n'.join(sorted(validator.addresses)))
        self.assertEqual(len(validator.addresses), 9)

        addresses_to_check_in_this_order = '''
        /
        /entry
        /entry@NX_class
        /entry/ds_link
        /entry/ds_link@target
        /entry/data
        /entry/data/data
        /entry/data@NX_class
        /entry/data@signal
        '''.split()
        addresses = list(validator.addresses.keys())
        for order, addr in enumerate(addresses_to_check_in_this_order):
            msg = 'HDF5 address not found: ' + addr
            self.assertTrue(addr in validator.addresses, msg)
            msg = 'expect ' + addr
            msg += ' on row ' + str(order)
            msg += ', found on row ' + str(addresses.index(addr))
            self.assertEqual(addr, addresses[order], msg)
    
    def test_inconsistent_findings__observation_2(self):
        import punx.validate, punx.finding, punx.logs
        fname = common.punx_data_file_name('example_mapping.nxs')
        punx.logs.ignore_logging()
        validator = punx.validate.Data_File_Validator(fname)
        validator.validate()
        # print('\n'.join(sorted(validator.addresses)))
        # self.assertEqual(len(validator.addresses), 114)
        addresses_to_check = '''
        /entry1/instrument/fluo/transformations@NX_class
        /entry1/instrument/fluo/transformations
        /entry1/instrument/fluo/data@units
        /entry1/instrument/fluo/energy@units
        /entry1/instrument/fluo/transformations/detector_arm
        /entry1/instrument/fluo/transformations@NX_class
        /entry1/instrument/trans/transformations/monitor_arm
        /entry1/sample/t_stage_set@units
        /entry1/sample/x_stage_set@units
        /entry1/sample/y_stage_set@units
        /entry1/user/username
        /entry1/user@NX_class
        /entry1/instrument/fluo/transformations@target
        '''.split()
        for addr in sorted(addresses_to_check):
            msg = 'HDF5 address not found: ' + addr
            self.assertTrue(addr in validator.addresses, msg)

 
def suite(*args, **kw):
    test_suite = unittest.TestSuite()
    test_list = [
        Validate_writer_1_3, 
        Validate_writer_2_1, 
        Validate_33id_spec_22_2D, 
        Validate_compression, 
        Validate_NXdata_is_now_optional_51,
        Validate_example_mapping, # FIXME: fails both tests
        Validate_example_mapping_issue_53,
        Validate_issue_57,
        ]
    for test_case in test_list:
        test_suite.addTest(unittest.makeSuite(test_case))
    return test_suite


if __name__ == '__main__':
    test_suite=suite()
    runner=unittest.TextTestRunner()
    runner.run(test_suite)
