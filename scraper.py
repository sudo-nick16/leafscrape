import os
from playwright import sync_api
from dotenv import dotenv_values

env = dotenv_values(".env")

def get_env(key: str, default_value: str = ""):
    value = env[key]
    if value is None:
        return default_value
    return value

credentials = {
        "username": get_env("USERNAME"),
        "password": get_env("PASSWORD")
}

main_page_url = "https://www.aepenergy.com/"
login_page_url = "https://www.aepenergy.com/residential/rates-plans/login/"

def get_ext(name: str) -> str:
    parts = name.split(".")
    if len(parts) == 1:
        return ""
    return parts[-1]

def gen_file_name(period: str, suffix: str = "", ext: str = "pdf")->str:
    if len(period) == 0:
        return "unknown"
    period = period.replace("/", "_")
    period = period.replace(" ", "")
    period = period + suffix + "." + ext
    return period

def gen_csv(path: str, data: list[list[str]]):
    csv = ""
    for row in data:
        csv += ",".join(row) + "\n"

    with open(path, "w") as f:
        f.write(csv)


def get_utility_data(outdir: str) -> list:
    utility_data: list[list[str]] = []
    utility_data.append(["from (MM/DD/YYYY)", "to (MM/DD/YYYY)", "statement", "statement_details"])

    with sync_api.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
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

        trows = acc_page.locator("#row > tbody > tr").all()

        for row in trows:
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

        browser.close()

        return utility_data

path = os.path.relpath("downloaded_statements")
data = get_utility_data(path)
print(data)
gen_csv("utility_data.csv", data)
