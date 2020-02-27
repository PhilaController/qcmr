import pandas as pd
import numpy as np


def this_year(df, year, quarter):
    sel = df["fiscal_year"] == year
    sel &= df["quarter"] == quarter
    return df.loc[sel]


def this_quarter(df, year, quarter):
    return this_year(df, year, quarter)


def last_quarter(df, year, quarter):
    if quarter == 1:
        year -= 1
        quarter = 4
    else:
        quarter = quarter - 1
    sel = df["fiscal_year"] == year
    sel &= df["quarter"] == quarter
    return df.loc[sel]


def last_year(df, year):
    sel = df["fiscal_year"] == year
    sel &= df["quarter"] == 4
    return df.loc[sel]


def to_first_quarter(df, year, quarter, columns=[]):
    """
    Compare the cash projections from this quarter to the first quarter
    of the year.

    Parameters
    ----------
    df : DataFrame
        the data frame holding all historical cash flow data
    year : int
        the fiscal year to compare
    quarter
    columns : list, optional
        only compare the values for these columns; if not provided, all columns
        will be compared
    """
    assert quarter != 1

    COLS = {}
    COLS["This Quarter"] = f"FY{str(year)[-2:]} Q{quarter}"
    COLS["First Quarter"] = f"FY{str(year)[-2:]} Q1"

    if not len(columns):
        columns = list(set(df.columns) - set(["month", "fiscal_year", "quarter"]))
    out = []
    for col in columns:

        dfs = []
        for tag in ["This Quarter", "First Quarter"]:
            if tag == "This Quarter":
                X = this_quarter(df, year, quarter)
            else:
                X = this_quarter(df, year, 1)
            X = X[["month", col]]
            X = X.set_index("month").rename(columns={col: COLS[tag]})
            dfs.append(X)

        this = pd.concat(dfs, axis=1)

        # order by fiscal month
        order = list(np.arange(6, 6 + 12, 1) % 12 + 1)

        this = this.loc[order].reset_index()
        this = this.reset_index().rename(columns={"index": "fiscal_month"})
        this["fiscal_month"] += 1
        this["Name"] = col

        out.append(this)
    return pd.concat(out, axis=0).reset_index(drop=True)


def to_last_quarter(df, year, quarter, columns=[]):
    """
    Compare the cash projections from this quarter to last quarter.

    Parameters
    ----------
    df : DataFrame
        the data frame holding all historical cash flow data
    year : int
        the fiscal year to compare
    quarter
    columns : list, optional
        only compare the values for these columns; if not provided, all columns
        will be compared
    """
    COLS = {}
    COLS["This Quarter"] = f"FY{str(year)[-2:]} Q{quarter}"
    if quarter == 1:
        COLS["Last Quarter"] = f"FY{str(year-1)[-2:]} Q4"
    else:
        COLS["Last Quarter"] = f"FY{str(year)[-2:]} Q{quarter-1}"

    if not len(columns):
        columns = list(set(df.columns) - set(["month", "fiscal_year", "quarter"]))
    out = []
    for col in columns:

        dfs = []
        for tag in ["This Quarter", "Last Quarter"]:
            if tag == "This Quarter":
                X = this_quarter(df, year, quarter)
            else:
                X = last_quarter(df, year, quarter)
            X = X[["month", col]]
            X = X.set_index("month").rename(columns={col: COLS[tag]})
            dfs.append(X)

        this = pd.concat(dfs, axis=1)

        # order by fiscal month
        order = list(np.arange(6, 6 + 12, 1) % 12 + 1)

        this = this.loc[order].reset_index()
        this = this.reset_index().rename(columns={"index": "fiscal_month"})
        this["fiscal_month"] += 1
        this["Name"] = col

        out.append(this)
    return pd.concat(out, axis=0).reset_index(drop=True)


def to_last_year(df, year, quarter, columns=[]):
    """
    Compare the cash projections from this year to last year's projections.

    Parameters
    ----------
    df : DataFrame
        the data frame holding all historical cash flow data
    year : int
        the fiscal year to compare
    quarter
    columns : list, optional
        only compare the values for these columns; if not provided, all columns
        will be compared
    """
    COLS = {}
    COLS["This Year"] = "FY" + str(year)[-2:]
    COLS["Last Year"] = "FY" + str(year - 1)[-2:]

    if not len(columns):
        columns = list(set(df.columns) - set(["month", "fiscal_year", "quarter"]))
    out = []
    for col in columns:

        dfs = []
        for tag in ["This Year", "Last Year"]:
            if tag == "This Year":
                X = this_year(df, year, quarter)
            else:
                X = last_year(df, year - 1)
            X = X[["month", col]]
            X = X.set_index("month").rename(columns={col: COLS[tag]})
            dfs.append(X)

        this = pd.concat(dfs, axis=1)

        # order by fiscal month
        order = list(np.arange(6, 6 + 12, 1) % 12 + 1)

        this = this.loc[order].reset_index()
        this = this.reset_index().rename(columns={"index": "fiscal_month"})
        this["fiscal_month"] += 1
        this["Name"] = col

        out.append(this)
    return pd.concat(out, axis=0).reset_index(drop=True)


def end_of_year_balances(df, fiscal_year, quarter):
    """
    Compare fund balances at the end of a fiscal quarter.

    Parameters
    ----------
    df : DataFrame
        data frame holding the fund balance data
    fiscal_year : int
        the current fiscal year
    quarter : int
        the quarter to get balances at end of
    """
    assert quarter in [1, 2, 3, 4]
    valid = (df["fiscal_year"] == fiscal_year) & (df["quarter"] == quarter)
    valid |= (df["fiscal_year"] != fiscal_year) & (df["quarter"] == 4)

    # select the right month
    valid &= df["month"] == 6

    return df.loc[valid].set_index("fiscal_year")


def end_of_quarter_balances(df, fiscal_year, quarter):
    """
    Compare fund balances at the end of a fiscal quarter.

    Parameters
    ----------
    df : DataFrame
        data frame holding the fund balance data
    fiscal_year : int
        the current fiscal year
    quarter : int
        the quarter to get balances at end of
    """
    assert quarter in [1, 2, 3, 4]
    valid = (df["fiscal_year"] == fiscal_year) & (df["quarter"] == quarter)
    valid |= (df["fiscal_year"] != fiscal_year) & (df["quarter"] == 4)

    # select the right month
    if quarter == 1:
        month = 9
    elif quarter == 2:
        month = 12
    elif quarter == 3:
        month = 3
    else:
        month = 6
    valid &= df["month"] == month

    return df.loc[valid].set_index("fiscal_year")


def sum_over_quarters(df, this_year, this_quarter, quarters):
    """
    Given the input spending/revenue data, sum over the specified
    quarters.

    For the past fiscal year, use actuals (from quarter 4), while
    the current fiscal year / quarter may contain projected values.
    """

    valid = (df["fiscal_year"] == this_year) & (df["quarter"] == this_quarter)
    valid |= (df["fiscal_year"] != this_year) & (df["quarter"] == 4)
    df = df.loc[valid]

    # select the right months for this quarter
    min_quarter = min(quarters)
    max_quarter = max(quarters)
    start_month = (7 + (min_quarter - 1) * 3) % 12
    end_month = (9 + (max_quarter - 1) * 3) % 12
    valid = (df["month"] >= start_month) & (df["month"] <= end_month)

    # do the selection
    df = df.loc[valid]

    # do the sum over the quarter
    cols = set(df.columns) - set(["fiscal_year", "quarter", "year", "month"])
    return df.groupby("fiscal_year")[list(cols)].sum()
