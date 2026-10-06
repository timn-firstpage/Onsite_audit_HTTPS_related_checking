"""Render normalized HTTPS findings. No network, MCP, or paid API calls."""
import argparse
import json
import re
from datetime import date
from pathlib import Path

SPECS = {
    "http": ("9.1", "9.1 HTTPS VS HTTP", ["Address", "Issue", "Suggestion"], ["address", "issue_description", "suggestion"]),
    "mixed": ("9.2", "9.2 HTTPS Mixed Content", ["Page Address", "HTTP Resource URL", "Issue", "Suggestion"], ["page_address", "resource_url", "issue_description", "suggestion"]),
    "hostname": ("9.3", "9.3 WWW VS NON-WWW", ["Test URL", "Expected URL", "Issue", "Suggestion"], ["test_url", "expected_url", "issue_description", "suggestion"]),
}


def report_filename(site_name, audit_date):
    if not isinstance(site_name, str) or not site_name.strip():
        raise ValueError("site name is required")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", audit_date):
        raise ValueError("audit date must use YYYY-MM-DD")
    date.fromisoformat(audit_date)
    # Preserve readable site names; replace only cross-platform unsafe characters.
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", site_name.strip()).strip(" .")
    if not name:
        raise ValueError("site name contains no usable filename characters")
    return f"{name}_https_audit_{audit_date}.xlsx"


def normalize(data):
    overview = data.get("overview", [])
    if len(overview) != 3 or {r.get("check") for r in overview} != {"9.1", "9.2", "9.3"}:
        raise ValueError("overview must contain one row each for 9.1, 9.2, 9.3")
    by_check = {r["check"]: r for r in overview}
    rows = {}
    for key, (check, _, _, fields) in SPECS.items():
        unique = {}
        for row in data.get(key, []):
            required = fields + ["issue"]
            if any(not isinstance(row.get(f), str) or not row[f].strip() for f in required):
                raise ValueError(f"{key}: missing/non-string {required}")
            identity = tuple(row[f] for f in fields[:-2]) + (row["issue"],)
            if identity in unique and unique[identity] != row:
                raise ValueError(f"{key}: conflicting duplicate {identity}")
            unique[identity] = row
        rows[key] = list(unique.values())
        summary = by_check[check]
        if summary.get("result") not in {"Pass", "Issue", "Needs Review", "Not Tested"}:
            raise ValueError(f"{check}: invalid result")
        if not isinstance(summary.get("coverage"), str) or not summary["coverage"].strip():
            raise ValueError(f"{check}: coverage is required")
        if rows[key] and summary["result"] in {"Pass", "Not Tested"}:
            raise ValueError(f"{check}: findings contradict result")
        if not rows[key] and summary["result"] == "Issue":
            raise ValueError(f"{check}: Issue requires evidence rows")
        if summary["result"] == "Issue" and all(r["issue"].startswith("review:") for r in rows[key]):
            raise ValueError(f"{check}: only review rows, use Needs Review")
    return overview, rows


def build(data, output):
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    overview, rows = normalize(data)
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}; select a new path")
    output.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Overview"
    ws.append(["Check", "Flag", "Findings", "Coverage"])
    for key, (check, *_rest) in SPECS.items():
        summary = next(r for r in overview if r["check"] == check)
        flag = {"Pass": "√", "Issue": "X"}.get(summary["result"], summary["result"])
        ws.append([check, flag, len(rows[key]), summary["coverage"]])
    for key, (_, title, headers, fields) in SPECS.items():
        if not rows[key]:
            continue
        sheet = wb.create_sheet(title)
        sheet.append(headers)
        for row in rows[key]:
            sheet.append([row[f] for f in fields])
    for sheet in wb:
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="2F75B5")
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                # Force text, including formula-looking untrusted input.
                if isinstance(cell.value, str):
                    cell.data_type = "s"
                    cell.number_format = "@"
                    if cell.value.startswith(("https://", "http://")):
                        cell.hyperlink = cell.value
                        cell.font = Font(color="0563C1", underline="single")
                cell.alignment = Alignment(vertical="top", wrap_text=True)
        for col in sheet.columns:
            label = col[0].value
            width = 65 if label in {"Issue", "Suggestion", "Coverage"} else 52
            if label in {"Check", "Flag", "Findings"}:
                width = 18
            sheet.column_dimensions[col[0].column_letter].width = width
    wb.save(output)
    verified = load_workbook(output)
    expected = ["Overview"] + [spec[1] for key, spec in SPECS.items() if rows[key]]
    if verified.sheetnames != expected:
        raise RuntimeError("Workbook sheet verification failed")
    for key, (_, title, headers, fields) in SPECS.items():
        if not rows[key]:
            continue
        sheet = verified[title]
        if [c.value for c in sheet[1]] != headers or sheet.max_row - 1 != len(rows[key]):
            raise RuntimeError(f"Workbook header/count verification failed: {title}")
        for i, source in enumerate(rows[key], 2):
            if [sheet.cell(i, j).value for j in range(1, len(fields) + 1)] != [source[f] for f in fields]:
                raise RuntimeError("Workbook value preservation failed")
    verified.close()
    return {"output": str(output.resolve()), "findings": {k: len(v) for k, v in rows.items()}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--site-name", required=True)
    parser.add_argument("--date", required=True, help="Audit date YYYY-MM-DD in the user's timezone")
    args = parser.parse_args()
    output = args.output_dir / report_filename(args.site_name, args.date)
    print(json.dumps(build(json.loads(args.input.read_text(encoding="utf-8-sig")), output), ensure_ascii=False))
