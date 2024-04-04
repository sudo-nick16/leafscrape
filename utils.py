def assert_str(value: str | None, default_value: str = ""):
    if value is None:
        return default_value
    return value

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
