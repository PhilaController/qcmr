import pandas as pd
import os
from glob import glob


class Table(object):
    """
    A class to represent a table from a PDF, holding one (or more)
    pandas DataFrame objects.

    Parameters
    ----------
    name : str
        the name of the table
    **data : key/value pairs
        the pandas DataFrame objects storing the data for each table
    """

    def __init__(self, name, **data):

        self.name = name
        self.keys = sorted(data)
        for k, v in data.items():
            setattr(self, k, v)

    def __getitem__(self, key):
        if key in self.keys:
            return getattr(self, key)
        else:
            raise KeyError(f"Valid keys are: {self.keys}")

    def __repr__(self):
        return "<Table:%s>" % self.name

    def __str__(self):
        return self.name

    def to_file(self, path):
        """
        Write out the table to a series of dataframes
        """
        if not os.path.exists(path):
            os.makedirs(path)

        # write
        for key in self.keys:
            self[key].to_csv(os.path.join(path, f"{key}.csv"), index=False)

    @classmethod
    def read_file(cls, path):
        """
        Read the Table object from a file.
        """
        # remove trailing slash
        path = path.rstrip("/")

        if not os.path.isdir(path):
            raise ValueError("Input path should be an existing folder")

        name = os.path.basename(path)
        data = {}
        for f in glob(os.path.join(path, "*.csv")):
            key = os.path.splitext(os.path.basename(f))[0]
            data[key] = pd.read_csv(f)

        return cls(name=name, **data)

