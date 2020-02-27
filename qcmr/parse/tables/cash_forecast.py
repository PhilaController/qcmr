from .. import utils
from .table import Table
import camelot
import pandas as pd
import warnings

__all__ = ["parse"]


def parse(title, pdf_path, pages):
    """
    Parse the Cash Flow Forecast table in the QCMR.

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
    pages = ",".join(map(str, [pages[0] + 1, pages[1] + 1]))  # cash report is two pages

    # read the PDF
    tables = camelot.read_pdf(pdf_path, pages=pages, flavor="stream", edge_tol=500)

    # sanitize
    for table in tables:
        table.df[0] = table.df[0].apply(utils.sanitize_strings)

    # do revenue, spending and balance sheet
    data = {}
    tags = ["gf_revenue", "gf_spending", "gf_balance_sheet"]
    formatters = [_format_revenue, _format_spending, _format_balance_sheet]
    for tag, formatter in zip(tags, formatters):
        data[tag] = utils.fill_missing_values(formatter(tables[0].df))

    # get fund balances
    data["fund_balances"] = utils.fill_missing_values(
        _format_fund_balances(tables[1].df)
    )

    return Table(title, **data)


def _update_categories(df, names, col_num=0):
    """
    Internal function to update spending/revenue categories

    Parameters
    ----------
    df : DataFrame
        the data to update
    names : dict
        the dictionary mapping to use to replace the categories
    col_num : int, optional
        the integer column number to update
    """
    df[col_num] = df[col_num].replace(names)

    # check for extra
    extra = set(df[col_num]) - set(names.values())
    if len(extra):
        warnings.warn(f"Ignoring the following categories: {extra}")
        df = df.loc[~df[col_num].isin(list(extra))]

    return df


def _format_revenue(df):
    """
    Internal function to format the revenue table.
    """
    # extract this part
    idx = df.index[df[0].isin(["REVENUES", "TOTAL CASH RECEIPTS"])]
    df = df.loc[idx[0] + 1 : idx[1]].copy()

    # rename rows
    df = _update_categories(df, categories["revenue"])

    # drop empty columns
    df = utils.remove_empty_columns(df)

    # slice and convert to floats
    out = utils.convert_to_floats(df.replace("", "0"), usecols=df.columns[1:])

    # rename the  columns
    cols = ["category"] + utils.get_fiscal_months()
    out = out[out.columns[: len(cols)]]
    out.columns = cols

    return out.reset_index(drop=True)


def _format_spending(df):
    """
    Internal function to format the spending table.
    """
    # extract this part
    idx = df.index[df[0].isin(["EXPENSES AND OBLIGATIONS", "TOTAL DISBURSEMENTS"])]
    df = df.loc[idx[0] + 1 : idx[1]].copy()

    # rename rows
    df = _update_categories(df, categories["spending"])

    # drop empty columns
    df = utils.remove_empty_columns(df)

    # format and parse
    out = utils.convert_to_floats(df.replace("", "0"), usecols=df.columns[1:])

    # the columns
    cols = ["category"] + utils.get_fiscal_months()
    out = out[out.columns[: len(cols)]]
    out.columns = cols

    return out.reset_index(drop=True)


def _format_balance_sheet(df):
    """
    Internal function to format the balance sheet table.
    """
    # extract this part
    idx = df.index[df[0].isin(["TOTAL DISBURSEMENTS"])]
    df = df.loc[idx[0] + 1 :].copy()

    # rename rows
    df = _update_categories(df, categories["balance_sheet"])

    # drop empty columns
    df = utils.remove_empty_columns(df)

    # remove extract columns
    df = df.drop(labels=df.columns[df.apply(lambda x: x == "").all()], axis=1)

    # format and parse
    out = utils.convert_to_floats(df.replace("", "0"), usecols=df.columns[1:])

    # the columns
    columns = ["category"] + utils.get_fiscal_months()
    assert len(columns) == len(out.columns), "wrong number of columns in balance sheet"
    out.columns = columns

    return out.reset_index(drop=True)


def _format_fund_balances(df):
    """
    Internal function to format the fund balances table.
    """
    # slice
    df = df.iloc[2:].copy()

    # drop empty columns
    df = utils.remove_empty_columns(df)

    # format and parse
    out = utils.convert_to_floats(df, usecols=df.columns[1:]).reset_index(drop=True)

    # remove columns/rows that are all NaNs
    data_cols = out.columns[1:]
    isnull = out[data_cols].isnull()
    out = out.drop(labels=data_cols[isnull.all(axis=0)], axis=1)
    out = out.drop(labels=out.index[isnull.all(axis=1)], axis=0)

    # rename rows
    out = _update_categories(out, categories["fund_balances"])

    # the columns
    columns = ["category"] + utils.get_fiscal_months()
    assert len(columns) == len(out.columns), "wrong number of columns in fund balances"
    out.columns = columns

    return out.reset_index(drop=True)


categories = {}
categories["revenue"] = {
    "Real Estate Tax": "real_estate_tax",
    "Total Wage, Earnings, Net Profits": "wage_earnings_net_profits",
    "Realty Transfer Tax": "realty_transfer_tax",
    "Sales Tax": "sales_tax",
    "Business Income & Receipts Tax": "birt",
    "Beverage Tax": "beverage_tax",
    "Other Taxes": "other_taxes",
    "Locally Generated Non-tax": "locally_generated_non_tax",
    "Locally Generated Non-Tax": "locally_generated_non_tax",
    "Total Other Governments": "total_other_govts",
    "Total PICA Other Governments": "total_pica_other_govts",
    "Interfund Transfers": "interfund_transfers",
    "Total Current Revenue": "total_current_revenue",
    "Collection of prior year(s) revenue": "prior_year_revenue",
    "Other fund balance adjustments": "adjustments",
    "TOTAL CASH RECEIPTS": "total_cash_receipts",
}

categories["spending"] = {
    "Payroll": "payroll",
    "Employee Benefits": "employee_benefits",
    "Pension": "pension",
    "Purchases of Services": "purchases_of_services",
    "Purchase of Services": "purchases_of_services",
    "Materials, Equipment": "materials_equipment",
    "Contributions, Indemnities": "contributions_indemnities",
    "Debt Service-Short Term": "debt_service_short",
    "Debt Service-Long Term": "debt_service_long",
    "Interfund Charges": "interfund_charges",
    "Advances & Misc. Pmts. / Labor Obligations": "advances_misc_payments",
    "Current Year Appropriation": "current_year_appropriation",
    "Prior Yr. Expenditures against Encumbrances": "prior_year_expenditures_against_encumbrances",
    "Prior Yr. Salaries & Vouchers Payable": "prior_year_salaries_vouchers_payable",
    "TOTAL DISBURSEMENTS": "total_disbursements",
}

categories["balance_sheet"] = {
    "Excess (Def) of Receipts over Disbursements": "receipts_minus_disbursements",
    "TRAN": "tran",
    "Opening Balance": "opening_balance",
    "CLOSING BALANCE": "closing_balance",
}

categories["fund_balances"] = {
    "General": "general_fund",
    "Grants Revenue": "grants_revenue",
    "Community Development": "community_development",
    "Vehicle Rental Tax": "vehicle_rental_tax",
    "Hospital Assessment Fund": "hospital_assessment_fund",
    "Housing Trust Fund": "housing_trust_fund",
    "Budget Stabilization Fund": "budget_stabilization_fund",
    "Other Funds": "other_funds",
    "TOTAL OPERATING FUNDS": "total_operating_funds",
    "Capital Improvement": "capital_improvement",
    "Industrial & Commercial Dev.": "industrial_commercial_dev",
    "TOTAL CAPITAL FUNDS": "total_capital_funds",
    "TOTAL FUND EQUITY": "total_fund_equity",
}
