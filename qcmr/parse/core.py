from . import utils, tables
from .. import data_dir
import os
import pandas as pd


class QCMR(object):
    """
    Parse the Quarterly City Manager's Report from the City of Philadelphia.

    Parameters
    ----------
    year : int
        the fiscal year of the report
    quarter : int
        the fiscal quarter of the report
    """

    tables = ["leave_usage", "cash_forecast", "general_fund_obligations"]

    def __init__(self, year, quarter):

        self.year = year
        self.quarter = quarter

        # the path to the raw PDF
        self.pdf_path = utils.get_raw_PDF_path(year, quarter)
        if not os.path.exists(self.pdf_path):
            raise ValueError(
                f"No QCMR found for fiscal year {year} and quarter {quarter}"
            )

        # store the tag
        FY = utils.get_FY_abbreviation(self.year)
        self.tag = f"FY{FY}_Q{self.quarter}"

        # verify processed path
        path = os.path.join(data_dir, "processed", self.tag)
        if not os.path.exists(path):
            os.makedirs(path)

        # determine the start pages for each tables
        self._pages = utils.get_pages(
            self.pdf_path,
            {
                "leave_usage": ["TOTAL LEAVE USAGE ANALYSIS"],
                "cash_forecast": ["CASH FLOW PROJECTIONS"],
                "general_fund_obligations": ["DEPARTMENTAL OBLIGATIONS SUMMARY"],
            },
        )

    def __repr__(self):
        return "<QCMR: %s>" % self.tag

    def process(self, tables=None, fresh=False):

        if tables is None:
            tables = self.tables

        for table in tables:
            func = getattr(self, table, None)
            if func is None:
                raise ValueError(f"{table} is not a valid table to be processed")
            func(fresh=fresh)

    def leave_usage(self, fresh=False):
        """
        The total leave usage by department.
        """
        title = "Leave Usage Analysis"
        path = os.path.join(data_dir, "processed", self.tag, title)

        if fresh or not os.path.exists(path):
            table = tables.leave_usage.parse(
                title, self.pdf_path, self._pages["leave_usage"]
            )
            table.to_file(path)
        else:
            from .tables.table import Table

            table = Table.read_file(path)

        return table

    def cash_forecast(self, fresh=False):
        """
        The cash flow forecast
        """
        title = "Cash Flow Forecast"
        path = os.path.join(data_dir, "processed", self.tag, title)

        if fresh or not os.path.exists(path):
            table = tables.cash_forecast.parse(
                title, self.pdf_path, self._pages["cash_forecast"]
            )
            table.to_file(path)
        else:
            from .tables.table import Table

            table = Table.read_file(path)

        return table

    def general_fund_obligations(self, fresh=False):
        """
        General Fund obligations by department.
        """
        title = "General Fund Obligations"
        path = os.path.join(data_dir, "processed", self.tag, title)

        if fresh or not os.path.exists(path):
            table = tables.general_fund_obligations.parse(
                title, self.pdf_path, self._pages["general_fund_obligations"]
            )
            table.to_file(path)
        else:
            from .tables.table import Table

            table = Table.read_file(path)

        return table

