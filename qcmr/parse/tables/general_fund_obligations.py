from .table import Table
from .. import utils
import camelot
import pandas as pd
import numpy as np

__all__ = ["parse"]


def parse(title, pdf_path, pages):
    """
    Parse the General Fund Departmental Obligations table in the QCMR.

    Notes
    -----
    This is Table O-2 in the QCMR.

    Parameters
    ----------
    title : str
        the name of the table we are reading
    pdf_path : str
        the path to the PDF to read
    pages : list of int
        the list of page numbers for the table in the report

    Returns
    -------
    Table : 
        the table object holding the parsed DataFrames
    """
    # get pages of cash forecast data
    assert len(pages) == 2
    pages = ",".join([str(page + 1) for page in pages])

    # read the PDF
    tables = camelot.read_pdf(pdf_path, pages=pages, flavor="stream")

    return Table(title, first=_format(tables[0].df), second=_format(tables[1].df))


def _format(df):

    cols = (
        df.iloc[2:5]
        .apply(lambda x: " ".join(x.fillna("").tolist()), axis=0)
        .str.strip()
    )

    X = df.iloc[5:]
    X = X.replace("", np.nan).T.dropna(how="all").T.dropna()

    # set the columns
    cols = cols.replace("", np.nan).dropna()
    assert len(cols) == len(X.columns)
    X.columns = cols

    return utils.convert_to_floats(X, usecols=X.columns[1:])
