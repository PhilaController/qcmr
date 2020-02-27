from .. import data_dir
import os
import PyPDF2
import pandas as pd
import unidecode
import pdftotext


def get_pages(filename, tags, how="all"):

    assert how in ["all", "any"]

    with open(filename, "rb") as f:
        pdf = pdftotext.PDF(f)

    def test_page(page, phrases):
        test = [phrase in page for phrase in phrases]
        if how == "all":
            return all(test)
        else:
            return any(test)

    out = {}
    for key in tags:
        out[key] = [i for i, page in enumerate(pdf) if test_page(page, tags[key])]

    return out


def get_FY_abbreviation(fiscalYear):
    """
    Return the last two digits of the input fiscal year 
    as a string.
    """
    return str(fiscalYear)[2:]


def get_raw_PDF_path(fiscalYear, quarter):
    """
    Return the path to the raw data file.
    """
    FY = get_FY_abbreviation(fiscalYear)
    return os.path.join(data_dir, "raw", f"FY{FY}_Q{quarter}.pdf")


def sanitize_strings(x):
    return unidecode.unidecode(x).replace("\n", "")


def convert_to_floats(df, usecols=None, errors="coerce"):
    """
    Convert string values in currency format to floats.
    """
    if usecols is None:
        usecols = df.columns

    for col in usecols:
        df[col] = pd.to_numeric(
            df[col].replace("[\$,)]", "", regex=True).replace("[(]", "-", regex=True),
            errors=errors,
        )
    return df


def remove_empty_columns(df):
    """
    Drop any empty columns from the dataframe
    """
    for col in df.columns:
        invalid = df[col].isin(["", "."]).all()
        if invalid:
            df = df.drop(labels=[col], axis=1)
    return df


def find_page(fiscalYear, quarter, tags, how="all"):
    """
    Find the page number. 
    """
    assert how in ["all", "any"]
    assert isinstance(tags, list)

    # load the filename
    filename = get_raw_PDF_path(fiscalYear, quarter)

    with open(filename, "rb") as ff:

        pdf_reader = PyPDF2.PdfFileReader(ff)
        page_num = 0
        stop_page = pdf_reader.getNumPages()

        matches = []
        while page_num < stop_page:
            page = pdf_reader.getPage(page_num)
            try:
                text = page.extractText()
                text = text.replace("\n", " ")
            except:
                pass

            test = [tag in text for tag in tags]
            if how == "all":
                test = all(test)
            else:
                test = any(test)

            if test:
                matches.append(page_num)
            page_num += 1

    return matches


def page_is_blank(fiscalYear, quarter, page_num):

    # load the filename
    filename = get_raw_PDF_path(fiscalYear, quarter)
    with open(filename, "rb") as ff:
        pdf_reader = PyPDF2.PdfFileReader(ff)
        try:
            page = pdf_reader.getPage(page_num)
            text = page.extractText()
        except:
            return True
        return text == ""


def get_fiscal_months():

    return [
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
    ]


def fill_missing_values(df):
    for index, row in df.iterrows():
        idx = row.isnull()
        if idx.sum():
            missing = row.index[idx]
            for col in missing:
                prompt = f"Input missing value for category='{row['category']}' and column = '{col}': "
                value = float(input(prompt))
                row[col] = value

    return df
