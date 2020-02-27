from .raw import load_cash_forecasts

__all__ = [
    "get_GF_revenues",
    "get_GF_spending",
    "get_fund_balances",
    "get_GF_balance_sheet",
]


def get_GF_revenues():
    """
    Return the formatted General Fund cash revenues.
    """
    return _format_revenues(load_cash_forecasts("gf_revenue"))


def get_GF_spending():
    """
    Return formatted General Fund cash spending.
    """
    return _format_spending(load_cash_forecasts("gf_spending"))


def get_fund_balances():
    """
    Return historical fund balance cash levels.
    """
    return _format_fund_balances(load_cash_forecasts("fund_balances"))


def get_GF_balance_sheet():
    """
    Return historical General Fund balance sheet.
    """
    return _format_balance_sheet(load_cash_forecasts("gf_balance_sheet"))


def _format_spending(df):
    """
    Format column names for expenditure columns.
    """
    # combine columns
    df["debt_service"] = df["debt_service_long"] + df["debt_service_short"]
    df["prior_year"] = (
        df["prior_year_salaries_vouchers_payable"]
        + df["prior_year_expenditures_against_encumbrances"]
    )

    # rename
    d = {}
    d["payroll"] = "Payroll"
    d["employee_benefits"] = "Employee Benefits"
    d["pension"] = "Pension"
    d["purchases_of_services"] = "Contracts / Leases"
    d["materials_equipment"] = "Materials / Equipment"
    d["contributions_indemnities"] = "Contributions / Indemnities"
    d["advances_misc_payments"] = "Advances / Labor Obligations"
    d["debt_service"] = "Debt Service"
    d["total_disbursements"] = "Total Disbursements"
    d["prior_year"] = "Prior Year Payments"

    df = df[sorted(d) + ["month", "fiscal_year", "quarter"]]
    return df.rename(columns=d)


def _format_revenues(df):
    """
    Format column names for revenue columns.
    """
    taxes = [
        "real_estate_tax",
        "wage_earnings_net_profits",
        "realty_transfer_tax",
        "sales_tax",
        "birt",
        "beverage_tax",
        "other_taxes",
    ]
    df["total_tax_revenue"] = df[taxes].sum(axis=1)
    df["total_other_govts"] += df["total_pica_other_govts"]

    d = {}
    d["real_estate_tax"] = "Real Estate Tax"
    d["wage_earnings_net_profits"] = "Wage, Earnings, Net Profits"
    d["realty_transfer_tax"] = "Realty Transfer Tax"
    d["sales_tax"] = "Sales Tax"
    d["birt"] = "BIRT"
    d["beverage_tax"] = "Beverage Tax"
    d["total_tax_revenue"] = "Total Tax Revenue"
    d["total_other_govts"] = "Other Governments"
    d["total_cash_receipts"] = "Total Cash Receipts"
    d["locally_generated_non_tax"] = "Locally Generated Non-Tax"
    d["other_taxes"] = "Other Taxes"
    d["prior_year_revenue"] = "Prior Year Revenue"

    df = df[sorted(d) + ["month", "fiscal_year", "quarter"]]
    return df.rename(columns=d)


def _format_fund_balances(df):
    """
    Format column names for fund balance columns.
    """
    d = {}
    d["total_capital_funds"] = "Total Capital Funds"
    d["general_fund"] = "General Fund"
    d["grants_revenue"] = "Grants Fund"
    d["total_fund_equity"] = "Consolidated Cash"

    df = df[sorted(d) + ["month", "fiscal_year", "quarter"]]
    return df.rename(columns=d)


def _format_balance_sheet(df):
    """
    Format column names for balance sheet.
    """
    d = {}
    d["opening_balance"] = "Opening Balance"
    d["receipts_minus_disbursements"] = "Receipts - Disbursements"
    d["tran"] = "TRAN"

    df = df[sorted(d) + ["month", "fiscal_year", "quarter"]]
    return df.rename(columns=d)
