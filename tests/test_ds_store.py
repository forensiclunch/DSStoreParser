import os
import unittest
from ds_store_parser import ds_store_handler

TEST_STORE_001 = "../.testdata/.DS_Store"


class TestStoreParser(unittest.TestCase):
    def test_parser(self):
        with open(TEST_STORE_001, "rb") as fh:
            handler = ds_store_handler.DsStoreHandler(
                fh, TEST_STORE_001
            )

            records = []
            for record in handler:
                records.append(record)

            self.assertEqual(len(records), 53)

            record = records[33]
            entry_dict = record.as_dict()
            self.assertEqual(entry_dict['filename'], u"M1-Test-Shared_Folder_Desktop")
            self.assertEqual(entry_dict['type'], u"dutc")
            self.assertEqual(entry_dict['code'], u"moDD")
            self.assertEqual(entry_dict['value'].isoformat(" "), "2017-09-12 22:03:23")

if __name__ == '__main__':
    unittest.main()
