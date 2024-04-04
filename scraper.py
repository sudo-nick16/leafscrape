import os
import sys
import re
from playwright import sync_api
from dotenv import dotenv_values
from utils import *

env = dotenv_values(".env")

credentials = {
    "username": assert_str(env["USERNAME"]),
    "password": assert_str(env["PASSWORD"])
}

main_page_url = "https://www.aepenergy.com/"
login_page_url = "https://www.aepenergy.com/residential/rates-plans/login/"

def get_utility_data(months: int, outdir: str) -> list:
    utility_data: list[list[str]] = []
    utility_data.append(["from (MM/DD/YYYY)", "to (MM/DD/YYYY)", "statement", "statement_details"])

    with sync_api.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(login_page_url)

            user_input = page.get_by_role("textbox", name="username")
            user_input.fill(credentials["username"])

            pass_input = page.get_by_role("textbox", name="password")
            pass_input.fill(credentials["password"])

            login_btn = page.get_by_role("button", name="Login")
            login_btn.click()

            acc_page: sync_api.Page = page.wait_for_event("popup")

            view_stmt_btn = acc_page.get_by_role("link", name="View All Statements")
            view_stmt_btn.click()

            view_all_btn = acc_page.get_by_role("link", name="View All").first
            view_all_btn.click()

            acc_page.wait_for_url(re.compile("pagesize=0"))

            trows = acc_page.locator("#row > tbody > tr").all()

            for i, row in enumerate(trows):
                if i >= months:
                    break

                period_el = row.locator("td:nth-child(1)")

                stmt_el = row.locator("td:nth-child(2)")

                stmt_det_el = row.locator("td:nth-child(3)")

                with acc_page.expect_download() as download_info:
                    stmt_el.click()
                download = download_info.value

                stmt_name = gen_file_name(period_el.inner_text(), ext=get_ext(download.suggested_filename))
                stmt_path = f"{outdir}/{stmt_name}"
                download.save_as(stmt_path)

                with acc_page.expect_download() as download_info:
                    stmt_det_el.click()
                download = download_info.value

                stmtd_name = gen_file_name(period_el.inner_text(), "_details", get_ext(download.suggested_filename))
                stmtd_path = f"{outdir}/{stmtd_name}"
                download.save_as(stmtd_path)

                period = period_el.inner_text().split("-")
                if len(period) < 2:
                    print("Invalid Period -", period_el.inner_text())
                    continue

                from_date = period[0]
                to_date = period[1]

                utility_data.append([from_date, to_date, stmt_path, stmtd_path])

        except Exception as e:
            print("[ERROR]:",e)

        finally:
            browser.close()

    return utility_data

outpath = os.path.relpath("downloaded_statements")
nmonths = int(sys.argv[1]) if len(sys.argv) > 1 else 12

print(f"Getting utility data for the last {nmonths} months..")
data = get_utility_data(nmonths, outpath)

print("Generating CSV..")
gen_csv("utility_data.csv", data)

print("Done..")
