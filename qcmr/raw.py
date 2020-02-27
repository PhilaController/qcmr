from .parse import utils
from .parse.tables.table import Table
from . import data_dir
from .parse import *
import pandas as pd
import os
import re
import calendar
from glob import glob


def load_leave_usage():

    all_data = []
    files = glob(os.path.join(data_dir, "processed", "leave_usage", "FY*_Q*.csv"))

    for f in sorted(files):
        tag = os.path.basename(f)
        matches = re.search("FY(?P<year>[0-9]{2})_Q(?P<quarter>[1234])", tag)
        year = int("20" + matches.group("year"))
        quarter = int(matches.group("quarter"))

        df = pd.read_csv(f)
        df["fiscal_year"] = year
        df["quarter"] = quarter

        all_data.append(df)

    return pd.concat(all_data)


def load_cash_forecasts(kind):

    assert kind in ["gf_revenue", "gf_spending", "gf_balance_sheet", "fund_balances"]

    month_dict = dict((v, k) for k, v in enumerate(calendar.month_abbr))

    files = glob(os.path.join(data_dir, "processed", "FY*_Q*", "Cash Flow Forecast"))

    all_data = []
    for f in sorted(files):
        matches = re.search("FY(?P<year>[0-9]{2})_Q(?P<quarter>[1234])", f)
        year = int("20" + matches.group("year"))
        quarter = int(matches.group("quarter"))

        df = Table.read_file(f)[kind]
        df["fiscal_year"] = year
        df["quarter"] = quarter

        df = (
            df.set_index(["fiscal_year", "quarter", "category"])
            .rename_axis(["month"], axis=1)
            .stack()
            .unstack(["category"])
            .reset_index()
            .rename_axis([None], axis=1)
            .sort_values(["fiscal_year", "quarter"], ascending=True)
        )
        df["month"] = df["month"].apply(lambda x: month_dict[x.capitalize()])

        all_data.append(df)

    return pd.concat(all_data, sort=True).reset_index(drop=True)


def process_qcmr(fiscalYear, quarter, tables=["cash", "leave_usage"]):

    # make sure we have the raw data file
    raw_filename = utils.get_raw_PDF_path(fiscalYear, quarter)
    if not os.path.exists(raw_filename):
        raise ValueError(
            f"no QCMR found for fiscal year {fiscalYear} and quarter {quarter}"
        )

    # get the filename
    FY = utils.get_FY_abbreviation(fiscalYear)
    filename = f"FY{FY}_Q{quarter}.csv"

    # get the pages
    pages = utils.get_pages(
        raw_filename,
        {
            "leave_usage": ["TOTAL LEAVE USAGE ANALYSIS"],
            "cash": ["CASH FLOW PROJECTIONS"],
        },
    )

    # process and save cash results
    if "cash" in tables:
        print("  Processing cash report...")
        dfs = get_cash_flow_forecast(raw_filename, pages["cash"])
        tags = ["gf_revenue", "gf_spending", "gf_balance_sheet", "fund_balances"]
        for i, tag in enumerate(tags):
            path = os.path.join(data_dir, "processed", "cash", tag, filename)
            dfs[i].to_csv(path)

    # process and save leave usage results
    if "leave_usage" in tables:
        print("  Processing leave usage report...")
        df = get_leave_usage(raw_filename, pages["leave_usage"])
        path = os.path.join(data_dir, "processed", "leave_usage", filename)
        df.to_csv(path)

