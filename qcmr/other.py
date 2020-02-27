import os
from . import data_dir
import pandas as pd


def load_end_of_year_fund_balance_revisions():
    """
    Load the data for the end-of-year fund balance revisions.
    """

    path = os.path.join(
        data_dir, "processed", "other", "end_of_year_fund_balance_revisions.xlsx"
    )

    return pd.read_excel(path)
