from __future__ import unicode_literals

import frappe
from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import (
    execute as get_ageing,
)
from erpnext.accounts.report.general_ledger.general_ledger import execute as get_soa
from frappe.utils import today
from frappe.utils.pdf import _, get_pdf
from frappe.www.printview import get_print_style


class CustomerStatement(object):
    def __init__(self):
        self.settings = frappe.get_doc("Erpnext Customer Statement Settings")

    def validate(self):
        self.validate_feature()

    def validate_feature(self):
        if not self.settings.enable_customer_statement:
            frappe.throw(_("Feature is Disabled"))

    def in_words(self, integer, in_million=True):
        """
        Returns string in words for the given integer.
        """
        from num2words import num2words

        locale = "ar"
        integer = int(integer)
        try:
            ret = num2words(integer, lang=locale)
        except NotImplementedError:
            ret = num2words(integer, lang="en")
        except OverflowError:
            ret = num2words(integer, lang="en")
        return ret.replace("-", " ")


@frappe.whitelist()
def get_report_pdf(
    customer, company, from_date, to_date, consolidated=True, download=True
):
    customer_statement = CustomerStatement()

    aging = ""
    base_template_path = "frappe/www/printview.html"

    template = frappe.get_doc("Print Format", customer_statement.settings.print_format)
    include_ageing = False
    ageing_based_on = "Due Date"

    customer = frappe.get_doc("Customer", customer)
    company_doc = frappe.get_doc("Company", company)

    if include_ageing:
        ageing_filters = frappe._dict(
            {
                "company": company,
                "report_date": to_date,
                "ageing_based_on": ageing_based_on,
                "range1": 30,
                "range2": 60,
                "range3": 90,
                "range4": 120,
                "customer": customer.name,
            }
        )
        col1, aging = get_ageing(ageing_filters)
        if aging:
            aging[0]["ageing_based_on"] = ageing_based_on

    filters = frappe._dict(
        {
            "from_date": from_date,
            "to_date": to_date,
            "company": company,
            "account": [],
            "party_type": "Customer",
            "party": [customer.name],
            "customer_details": customer,
            "group_by": "Group by Voucher (Consolidated)",
            "currency": company_doc.default_currency,
            "show_opening_entries": 1,
            "include_default_book_entries": 0,
            "show_cancelled_entries": 0,
            "finance_book": None,
            "cost_center": None,
            "project": None,
            "tax_id": customer.tax_id if customer.tax_id else None,
        }
    )

    col, res = get_soa(filters)
    for i in res:
        if i.get("voucher_type") == "Journal Entry":
            i.user_remark = frappe.db.get_value(
                "Journal Entry", i.voucher_no, "user_remark"
            )

    for x in [0, -2, -1]:
        res[x]["account"] = res[x]["account"].replace("'", "")

    if customer_statement.settings.remove_subtotal:
        del res[-2]

    balance = res[-1]["balance"]
    balance_in_words = customer_statement.in_words(balance)

    letterhead = frappe.get_doc("Letter Head", customer_statement.settings.letterhead)
    footer = letterhead and letterhead.get("footer", None)

    template_payload = frappe._dict(
        {
            "letter_head": letterhead and letterhead.get("content", None),
            "footer": footer,
            "customer": customer,
            "filters": filters,
            "balance": balance,
            "balance_in_words": balance_in_words,
            "data": res,
            "aging": "Due Date",
        }
    )

    html = frappe.render_template(template.html, template_payload)
    html = frappe.render_template(
        base_template_path, {"body": html, "css": get_print_style()}
    )

    report = get_pdf(html, {"orientation": "portrait"})
    if report and not download:
        return report
    else:
        frappe.local.response.filename = customer.name + "-" + today() + ".pdf"
        frappe.local.response.filecontent = report
        frappe.local.response.type = "download"
