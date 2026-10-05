"""Offline behavioral checks using synthetic evidence."""
import tempfile
import unittest
from pathlib import Path
from openpyxl import load_workbook
from build_report import build, normalize, report_filename


def fixture():
    return {"overview": [
        {"check": "9.1", "result": "Issue", "coverage": "Synthetic HTTP evidence"},
        {"check": "9.2", "result": "Not Tested", "coverage": "No mixed export"},
        {"check": "9.3", "result": "Needs Review", "coverage": "Synthetic timeout"}],
        "http": [{"address": "http://example.com/a/?x=1&y=2", "issue": "http-200", "suggestion": "=untrusted text"}],
        "mixed": [], "hostname": []}


class ReportTests(unittest.TestCase):
    def test_report_naming_and_date_validation(self):
        self.assertEqual(report_filename("Example", "2026-10-05"), "Example_https_audit_2026-10-05.xlsx")
        self.assertEqual(report_filename("品牌/香港", "2026-10-05"), "品牌_香港_https_audit_2026-10-05.xlsx")
        with self.assertRaises(ValueError):
            report_filename("Example", "2026-02-30")
        with self.assertRaises(ValueError):
            report_filename("", "2026-10-05")

    def test_preserves_urls_and_text_without_empty_sheets(self):
        data = fixture()
        data["http"].append(dict(data["http"][0]))
        # Keep test artifacts under the caller-selected workspace.
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            output = Path(directory) / "audit.xlsx"
            result = build(data, output)
            self.assertEqual(result["findings"]["http"], 1)
            wb = load_workbook(output)
            self.assertEqual(wb.sheetnames, ["Overview", "9.1 HTTPS VS HTTP"])
            self.assertEqual(wb.worksheets[1]["A2"].value, data["http"][0]["address"])
            self.assertEqual(wb.worksheets[1]["B2"].data_type, "s")
            self.assertEqual(wb["Overview"]["B4"].value, "Needs Review")
            self.assertEqual(wb["Overview"]["B2"].value, "X")
            wb.close()
            with self.assertRaises(FileExistsError):
                build(data, output)

    def test_rejects_false_pass_and_missing_resource(self):
        data = fixture()
        data["overview"][0]["result"] = "Pass"
        with self.assertRaises(ValueError):
            normalize(data)
        data = fixture()
        data["mixed"] = [{"page_address": "https://example.com", "issue": "mixed", "suggestion": "Fix resource"}]
        with self.assertRaises(ValueError):
            normalize(data)

    def test_retains_shared_resource_on_different_pages(self):
        data = fixture()
        data["overview"][1]["result"] = "Issue"
        data["mixed"] = [{"page_address": page, "resource_url": "http://example.com/logo.png", "issue": "mixed", "suggestion": "Update image reference"} for page in ["https://example.com/a", "https://example.com/b"]]
        _, rows = normalize(data)
        self.assertEqual(len(rows["mixed"]), 2)

    def test_tick_is_rendered_without_treating_unknown_as_pass(self):
        data = fixture()
        data["overview"][1] = {"check": "9.2", "result": "Pass", "coverage": "Completed mixed check: zero issues"}
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            output = Path(directory) / "audit.xlsx"
            build(data, output)
            wb = load_workbook(output)
            self.assertEqual(wb["Overview"]["B3"].value, "√")
            self.assertEqual(wb["Overview"]["B4"].value, "Needs Review")
            self.assertEqual(wb["Overview"]["B2"].value, "X")
            wb.close()


if __name__ == "__main__":
    unittest.main()
