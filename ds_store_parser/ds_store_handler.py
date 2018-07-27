from . import store as ds_store
import datetime
import binascii
import collections


class DsStoreHandler(object):
    """Wrapper class for handling the DS Store artifact."""
    def __init__(self, file_io, location):
        self._file_io = file_io
        self.location = location
        self.ds_store = ds_store.DSStore.open(
            self._file_io, "rb"
        )

    def __iter__(self):
        """Iterate the entries within the store.

        Yields
            <DsStoreRecord>: The ds store entry record
        """
        for ds_store_entry in self.ds_store:
            yield DsStoreRecord(ds_store_entry)


class DsStoreRecord(object):
    """A wrapper class for the DSStoreEntry."""
    def __init__(self, ds_store_entry):
        self.ds_store_entry = ds_store_entry

    def as_dict(self):
        """Turn the internal DSStoreEntry into a OrderedDict.

        Returns
            <OrderedDict>: The ordered dictionary representing the internal DSStoreEntry.
        """
        record_dict = collections.OrderedDict([
            ("filename", self.ds_store_entry.filename),
            ("type", self.ds_store_entry.type),
            ("code", self.ds_store_entry.code),
            ("value", self.ds_store_entry.value),
        ])

        if hasattr(self.ds_store_entry.type, "__name__"):
            record_dict["type"] = self.ds_store_entry.type.__name__

        if record_dict["type"] == "blob":
            record_dict["value"] = binascii.hexlify(
                record_dict["value"]
            )
        elif record_dict["type"] == 'dutc':
            epoch_dt = datetime.datetime(1904, 1, 1)
            parsed_dt = epoch_dt + datetime.timedelta(
                seconds=int(self.ds_store_entry.value) / 65536
            )
            record_dict["value"] = parsed_dt

        return record_dict
