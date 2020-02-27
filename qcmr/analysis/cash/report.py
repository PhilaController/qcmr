from . import compare
from ...cash import *
from ...other import *
import calendar
import pandas as pd
import numpy as np


class CashReport(object):
    """
    An interface for analyzing cash flow forecasts from 
    the City of Philadelphia.

    Parameters
    ----------
    year : int
        the fiscal year being analyzed
    quarter : int
        the quarter being analyzed
    """

    def __init__(self, year, quarter):

        assert quarter in [1, 2, 3, 4]
        self.year = year
        self.quarter = quarter

    def fund_balance_revisions(self, xmin=-200, xmax=1100):
        """
        Estimate the relationship between the modified accrual fund balance
        and the Q4 cash balance.
        """
        from seaborn.algorithms import bootstrap
        from seaborn.utils import ci

        # load the data
        df = load_end_of_year_fund_balance_revisions()
        df["Q1 Actual"] /= 1e3

        def reg_func(_x, _y):
            return np.linalg.pinv(_x).dot(_y)

        # Setup the regression
        XX = df.dropna().copy()
        XX["const"] = 1
        X = XX[["const", "Q4 Cash Balance"]].values
        y = XX["Q1 Actual"].values

        # Bootstrap and error bands
        Xs = sorted(
            np.concatenate(
                [np.linspace(xmin, xmax, 121), df["Q4 Cash Balance"].values], axis=0
            )
        )

        grid = np.vstack([np.ones(len(Xs)), Xs]).T

        beta_boots = bootstrap(X, y, func=reg_func, n_boot=10000, random_seed=42).T
        yhat_boots = grid.dot(beta_boots).T
        err_bands = ci(yhat_boots, axis=0)

        out = df.copy()
        out = out[["Year", "Q4 Cash Balance", "Q1 Actual"]]
        interp = pd.DataFrame(
            {
                "Q4 Cash Balance": grid[:, 1],
                "Q1 Actual (Lower)": err_bands[0],
                "Q1 Actual (Upper)": err_bands[1],
            }
        )
        out = pd.merge(out, interp, on="Q4 Cash Balance", how="outer").sort_values(
            "Q4 Cash Balance"
        )
        return out.rename(columns={"Year": "Fiscal Year"})

    def compare_to_last_quarter(self):
        """
        Compare the spending, revenues, and fund balances for this quarter to last
        quarter (on a monthly basis).
        """
        return self._get_comparison("last-quarter")

    def compare_to_first_quarter(self):
        """
        Compare the spending, revenues, and fund balances for this quarter to 
        the first quarter of the fiscal year (on a monthly basis).
        """
        return self._get_comparison("first-quarter")

    def compare_to_last_year(self):
        """
        Compare the spending, revenues, and fund balances for this year to last
        year (on a monthly basis).
        """
        return self._get_comparison("year")

    def _get_comparison(self, kind):
        assert kind in ["last-quarter", "year", "first-quarter"]
        if kind == "year":
            comparison = compare.to_last_year
        elif kind == "last-quarter":
            comparison = compare.to_last_quarter
        elif kind == "first-quarter":
            comparison = compare.to_first_quarter

        funcs = [get_GF_spending, get_GF_revenues, get_fund_balances]
        labels = ["Spending", "Revenue", "Fund Balance"]
        out = []

        for label, func in zip(labels, funcs):

            # get the data for this type
            df = func()

            # perform the comparison
            compared = comparison(df, self.year, self.quarter)
            compared["Kind"] = label

            out.append(compared)

        # combine
        out = pd.concat(out, axis=0).reset_index(drop=True)

        # format the month
        out["Month"] = out["month"].apply(lambda x: calendar.month_abbr[x])

        # remove month and fiscal month and return
        return out.drop(["month", "fiscal_month"], axis=1)

    def annual_projection_accuracy(self, kind):
        """
        Calculate the historical accuracy of annual, year-end projections.

        For fund balances, this compares the projection for end-of-year balance
        from the current quarter vs the actual value.

        For revenues/expenses, it compares the projected annual totals from the current
        quarter to the actual value.

        Parameters
        ----------
        kind : ['Fund Balance', 'Revenue', 'Spending']
            the type of data to return
        """
        assert kind in ["Fund Balance", "Revenue", "Spending"]

        # get the fund balance data
        if kind == "Fund Balance":
            X = get_fund_balances()
        elif kind == "Revenue":
            X = get_GF_revenues()
        elif kind == "Spending":
            X = get_GF_spending()

        # loop over
        out = []
        columns = list(set(X.columns) - set(["month", "fiscal_year", "quarter"]))
        for col in columns:

            # actual
            sel = X["quarter"] == 4
            if kind == "Fund Balance":
                sel &= X["month"] == 6
                actual = X.loc[sel, ["fiscal_year", col]]
                actual = actual.set_index("fiscal_year").squeeze()
            else:
                actual = X.loc[sel].groupby("fiscal_year")[col].sum()

            # projected
            sel = X["quarter"] == self.quarter
            if kind == "Fund Balance":
                sel &= X["month"] == 6
                proj = X.loc[sel, ["fiscal_year", col]]
                proj = proj.set_index("fiscal_year").squeeze()
            else:
                proj = X.loc[sel].groupby("fiscal_year")[col].sum()

            # calculate difference
            diff = (actual - proj).to_frame(f"Actual - Q{self.quarter} Projection")
            diff["Name"] = col
            diff = diff.reset_index()
            out.append(diff)

        out = pd.concat(out, axis=0).reset_index(drop=True)
        out = out.rename(columns={"fiscal_year": "Fiscal Year"})
        return out.dropna()

    def actual_vs_projected_changes(self):
        """
        Compare the actual and projected changes for the General Fund
        cash revenue and spending categories.

        For each spending/revenue category, columns 'Actual Change' and
        'Projected Change' will be calculated.
        """

        def calculate_difference(df, quarter, label, columns):
            X = df.loc[(df["quarter"] == quarter)].groupby("fiscal_year")[columns].sum()
            Y = df.loc[(df["quarter"] == 4)].groupby("fiscal_year")[columns].sum()
            Y.index += 1
            diff = X - Y
            change = diff / Y

            diff = diff.reset_index().melt(
                id_vars="fiscal_year", var_name="Name", value_name=f"{label} Change"
            )
            change = change.reset_index().melt(
                id_vars="fiscal_year",
                var_name="Name",
                value_name=f"{label} Change (Percent)",
            )
            return pd.merge(change, diff, on=["fiscal_year", "Name"])

        labels = ["Revenue", "Spending"]

        toret = []
        for i, label in enumerate(labels):

            if label == "Revenue":
                df = get_GF_revenues()
            elif label == "Spending":
                df = get_GF_spending()
            columns = list(set(df.columns) - set(["month", "fiscal_year", "quarter"]))

            # projected
            projected = calculate_difference(df, self.quarter, "Projected", columns)

            # actual
            actual = calculate_difference(df, 4, "Actual", columns)

            # combine
            out = pd.merge(actual, projected, on=["fiscal_year", "Name"])
            out["Kind"] = label
            out = out.dropna(subset=["Projected Change"])
            out = out.rename(columns={"fiscal_year": "Fiscal Year"})
            toret.append(out)

        # return revenue + spendimg
        out = pd.concat(toret, axis=0).reset_index(drop=True)

        # hide FY15 by default for Q1
        if self.quarter == 1:
            fy15 = out["Fiscal Year"] == 2015
            valid = fy15 & (
                out["Name"].isin(["Total Disbursements", "Total Cash Receipts"])
            )
            out.loc[valid, ["Projected Change (Percent)", "Projected Change"]] = np.nan

        return out

    def historical_balance_by_quarter(self):
        """
        Return the historical fund balances at the end of the
        current quarter.
        """

        df = get_fund_balances()
        df = compare.end_of_quarter_balances(df, self.year, self.quarter)
        df = df.reset_index()

        # add No TRAN column
        f = get_GF_balance_sheet()

        months = [7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6]
        actual_months = months[: 3 * self.quarter]
        sel = f["month"].isin(actual_months)
        sel &= (f["fiscal_year"] < self.year) & (f["quarter"] == 4) | (
            (f["fiscal_year"] == self.year) & (f["quarter"] == self.quarter)
        )
        TRAN = f.loc[sel].groupby("fiscal_year")["TRAN"].sum().reset_index()

        df = pd.merge(df, TRAN, on=["fiscal_year"])
        df["General Fund (No TRAN)"] = df["General Fund"] - df["TRAN"]
        df["Consolidated Cash (No TRAN)"] = df["Consolidated Cash"] - df["TRAN"]

        df = df.rename(columns={"fiscal_year": "Fiscal Year"})
        df["Fiscal Year"] = df["Fiscal Year"].astype(str)

        df = df[
            [
                "Fiscal Year",
                "Grants Fund",
                "Total Capital Funds",
                "General Fund",
                "Consolidated Cash",
                "Consolidated Cash (No TRAN)",
                "General Fund (No TRAN)",
            ]
        ]
        return df

    def annual_general_fund_totals(self):
        """
        Return the annual totals for General Fund revenues and spending.
        """
        out = []
        dfs = [get_GF_revenues(), get_GF_spending()]
        labels = ["Revenue", "Spending"]
        for i, label in enumerate(labels):

            df = dfs[i]

            # select valid
            valid = (df["fiscal_year"] == self.year) & (df["quarter"] == self.quarter)
            valid |= (df["fiscal_year"] != self.year) & (df["quarter"] == 4)

            X = df.loc[valid].groupby("fiscal_year").sum()
            X = X.drop(labels=["month", "quarter"], axis=1)
            X = X.reset_index().melt(
                id_vars=["fiscal_year"], value_name="Total", var_name="Name"
            )
            X["Kind"] = label
            out.append(X)

        out = pd.concat(out, axis=0).reset_index(drop=True)
        return out.rename(columns={"fiscal_year": "Fiscal Year"})

    def compare_totals_by_quarter(self, quarters):
        """
        Calculate historical General Fund spending/revenue totals by quarter.

        Parameters
        ----------
        quarter : int, list
            list of quarters to sum over
        """

        if isinstance(quarters, int):
            quarters = [quarters]
        assert isinstance(quarters, list)
        assert all(quarter in [1, 2, 3, 4] for quarter in quarters)

        out = []
        dfs = [get_GF_revenues(), get_GF_spending()]
        labels = ["Revenue", "Spending"]
        for i, label in enumerate(labels):

            df = dfs[i]
            X = compare.sum_over_quarters(df, self.year, self.quarter, quarters)
            X = X.reset_index().melt(
                id_vars=["fiscal_year"], value_name="Total", var_name="Name"
            )
            X["Kind"] = label
            out.append(X)

        out = pd.concat(out, axis=0).reset_index(drop=True)
        return out.rename(columns={"fiscal_year": "Fiscal Year"})

