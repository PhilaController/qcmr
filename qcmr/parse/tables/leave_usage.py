from .table import Table
import camelot
import pandas as pd
import unidecode

__all__ = ["parse"]


def parse(title, pdf_path, pages):
    """
    Parse the Leave Usage Analysis report in the QCMR.

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
    assert len(pages) >= 2
    pages = ",".join(map(str, [pages[1] + 1, pages[1] + 2]))

    # read the PDF
    tables = camelot.read_pdf(pdf_path, pages=pages, flavor="stream")

    return Table(title, quarter_only=_format(tables[0].df), ytd=_format(tables[1].df))


def _format(df):
    """
    Internal function to format the parsed data for the leave
    usage analysis report.
    """
    # extract this part
    idx = df.index[df[0].isin(["Department"])]
    df = df.loc[idx[0] + 1 :].copy()

    # remove empty rows
    data_cols = df.columns[1:]
    isnull = (df[data_cols] == "").all(axis=1)
    df = df.drop(labels=df.index[isnull], axis=0)

    # slice and convert to floats
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col].str.replace("%", ""), errors="coerce")

    # remove all NaN rows/columns
    df = df.set_index(df.columns[0])
    df = df.dropna(axis=0, how="all").dropna(axis=1)

    # trim to first four columns
    df = df.reset_index()
    df = df[df.columns[:4]]

    # rename columns and return
    df.columns = ["department", "sickness/injury", "vacation/other", "total"]

    # format departments
    df["department"] = (
        df["department"].apply(unidecode.unidecode).str.replace(" - ", ": ")
    )

    return df
