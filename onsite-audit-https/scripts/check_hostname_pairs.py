"""Collect homepage/observed www pairs, redirects and bounded static content evidence.

Standard-library helper. Produces observations, not agent-reviewed findings.json.
"""
import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from http.client import HTTPException
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NetworkInterrupted(RuntimeError):
    """Abort the entire audit; the user must start a fresh skill run."""

    def __init__(self, url, cause):
        self.url, self.cause = url, cause
        super().__init__(f"Network request failed at {url}: {cause}. Check the network and rerun the entire skill in a new run directory.")


def parts(url):
    p = urlsplit(url)
    if p.scheme not in {"http", "https"} or not p.hostname or p.username or p.password:
        raise ValueError("Use absolute HTTP(S) URLs without credentials")
    _ = p.port  # Validate port.
    return p


def bare(host):
    return host[4:] if host.startswith("www.") else host


def build_pairs(start_url, pages, page_limit=None):
    p = parts(start_url)
    base = bare(p.hostname.lower())
    if ":" in base or re.fullmatch(r"[\d.]+", base):
        raise ValueError("www pairing requires a DNS hostname")
    port = f":{p.port}" if p.port is not None else ""
    home = [urlunsplit(("https", host + port, "/", "", "")) for host in [base, "www." + base]]
    pairs = [{"urls": home, "source": "homepage_generated"}]
    groups = {}
    for row in pages:
        if not isinstance(row, dict) or not isinstance(row.get("url"), str):
            raise ValueError("Normalized pages require url and content_type fields")
        if "html" not in str(row.get("content_type", "")).lower():
            continue
        q = parts(row["url"])
        host = q.hostname.lower()
        if bare(host) != base or q.port != p.port:
            continue
        key = (q.path or "/", q.query)
        groups.setdefault(key, {False: set(), True: set()})[host.startswith("www.")].add(
            urlunsplit((q.scheme, q.netloc.lower(), q.path or "/", q.query, "")))
    observed = []
    for key in sorted(groups):
        group = groups[key]
        for x in sorted(group[False]):
            for y in sorted(group[True]):
                if {x, y} != set(home):
                    observed.append({"urls": [x, y], "source": "main_crawl_observed"})
    if page_limit is not None:
        if not isinstance(page_limit, int) or isinstance(page_limit, bool) or page_limit < 1:
            raise ValueError("hostname_page_limit must be null or a positive observed-pair limit")
        selected, omitted = observed[:page_limit], len(observed[page_limit:])
    else:
        selected, omitted = observed, 0
    return pairs + selected, omitted


class TextEvidence(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    SKIP = {"head", "script", "style", "nav", "header", "footer", "aside", "noscript", "template"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.visible, self.main, self.title, self.h1 = [], [], [], [], []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in self.stack:
            self.stack = self.stack[:len(self.stack) - 1 - self.stack[::-1].index(tag)]

    def handle_data(self, data):
        if "title" in self.stack:
            self.title.append(data)
        if "h1" in self.stack and not set(self.stack) & {"script", "style", "template"}:
            self.h1.append(data)
        if not set(self.stack) & self.SKIP:
            self.visible.append(data)
            if "main" in self.stack:
                self.main.append(data)

    def evidence(self):
        clean = lambda xs: re.sub(r"\s+", " ", " ".join(xs)).strip()
        text = clean(self.main or self.visible)
        return {"title": clean(self.title), "h1": clean(self.h1), "main_text": text,
                "extraction": "main" if self.main else "visible_without_common_chrome",
                "text_sha256": hashlib.sha256(text.encode()).hexdigest()}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Checker:
    def __init__(self, allowed_hosts, usage, max_requests=200, max_hops=5, timeout=15,
                 delay=1, opener=None, save_usage=None, stop_errors=2):
        self.allowed = {h.lower() for h in allowed_hosts}
        self.usage, self.limit, self.max_hops = usage, max_requests, max_hops
        self.timeout, self.delay = timeout, delay
        self.opener = opener or build_opener(NoRedirect())
        self.save_usage = save_usage or (lambda: None)
        self.cache, self.last_request = {}, None
        self.paused, self.errors, self.stop_errors = False, 0, stop_errors
        if not isinstance(usage.get("live_requests", 0), int) or usage.get("live_requests", 0) < 0:
            raise ValueError("Invalid cumulative live_requests")
        for value in [max_requests, max_hops, stop_errors]:
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError("Request/hop/error limits must be nonnegative integers")
        if stop_errors < 1 or timeout <= 0 or delay < 0:
            raise ValueError("Require positive error limit/timeout and nonnegative delay")

    def response(self, url):
        if url in self.cache:
            return self.cache[url]
        if self.paused:
            return {"error": "deferred_after_errors"}
        if self.usage.get("live_requests", 0) >= self.limit:
            return {"error": "budget"}
        if self.last_request is not None:
            time.sleep(max(0, self.delay - (time.monotonic() - self.last_request)))
        self.usage["live_requests"] = self.usage.get("live_requests", 0) + 1
        self.save_usage()
        self.last_request = time.monotonic()
        try:
            req = Request(url, headers={"User-Agent": "OnsiteHostnameAudit/1.0"})
            try:
                reply = self.opener.open(req, timeout=self.timeout)
            except HTTPError as exc:
                reply = exc
            with reply:
                raw = reply.read(1048577)
                mime = reply.headers.get("Content-Type", "")
                result = {"status": reply.code, "location": reply.headers.get("Location"),
                          "retry_after": reply.headers.get("Retry-After"), "content_type": mime,
                          "body_truncated": len(raw) > 1048576}
                if "html" in mime.lower():
                    parser = TextEvidence()
                    parser.feed(raw[:1048576].decode(reply.headers.get_content_charset() or "utf-8", errors="replace"))
                    result["content"] = parser.evidence()
        except (URLError, OSError, HTTPException) as exc:
            raise NetworkInterrupted(url, exc) from exc
        except (ValueError, LookupError) as exc:
            result = {"error": "content_decode", "error_detail": str(exc)}
        self.errors = self.errors + 1 if result.get("error") else 0
        if result.get("status") == 429 or self.errors >= self.stop_errors:
            self.paused = True
        self.cache[url] = result
        return result

    def check(self, start):
        current, chain, visited = start, [], set()
        for hop in range(self.max_hops + 1):
            try:
                p = parts(current)
            except ValueError:
                return {"start_url": start, "chain": chain, "error": "invalid_target"}
            if p.hostname.lower() not in self.allowed:
                return {"start_url": start, "chain": chain, "error": "out_of_scope", "target": current}
            if current in visited:
                return {"start_url": start, "chain": chain, "error": "loop"}
            visited.add(current)
            response = self.response(current)
            chain.append({"url": current, **response})
            if response.get("error"):
                return {"start_url": start, "chain": chain, "error": response["error"]}
            status = response["status"]
            if status in {301, 302, 303, 307, 308}:
                if not response.get("location"):
                    return {"start_url": start, "chain": chain, "error": "missing_location"}
                current = urljoin(current, response["location"])
                q = urlsplit(current)
                current = urlunsplit((q.scheme, q.netloc, q.path, q.query, ""))
                continue
            return {"start_url": start, "chain": chain, "final_url": current, "final_status": status,
                    "content": response.get("content"), "body_truncated": response.get("body_truncated"),
                    "error": "rate_limited" if status == 429 else None}
        return {"start_url": start, "chain": chain, "error": "hop_limit"}


def compare(left, right):
    if left.get("error") == "loop" or right.get("error") == "loop":
        return {"observation": "redirect_loop", "reason": "Repeated URL in a verified redirect chain", "requires_agent_validation": True}
    if left.get("error") or right.get("error") or left.get("final_status") != 200 or right.get("final_status") != 200:
        return {"observation": "human_check", "reason": "Incomplete/unusable response evidence; inspect status and error source"}
    a, b = left.get("content") or {}, right.get("content") or {}
    if left.get("body_truncated") or right.get("body_truncated") or min(len(a.get("main_text", "")), len(b.get("main_text", ""))) < 80:
        return {"observation": "human_check", "reason": "Insufficient static content; obtain page-purpose/rendered evidence"}
    identical = a["main_text"] == b["main_text"]
    converged = left["final_url"] == right["final_url"]
    return {"observation": "converged" if converged else "identical_without_convergence" if identical else "different_content_without_convergence",
            "static_text_identical": identical, "final_urls_equal": converged,
            "requires_agent_validation": True}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--pages", required=True, type=Path, help="Normalized JSON list: url, content_type")
    ap.add_argument("--run-dir", required=True, type=Path)
    args = ap.parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8-sig"))
    if not cfg.get("checks", {}).get("hostname_consistency", True):
        raise ValueError("hostname_consistency is disabled")
    if cfg.get("checks", {}).get("hostname_executor", "python") != "python":
        raise ValueError("Selected executor is not python; honor the override or migrate the run config explicitly")
    pages = json.loads(args.pages.read_text(encoding="utf-8-sig"))
    pairs, omitted = build_pairs(cfg["site"]["start_url"], pages, cfg.get("checks", {}).get("hostname_page_limit"))
    args.run_dir.mkdir(parents=True, exist_ok=True)
    output = args.run_dir / "hostname-observations.json"
    if output.exists():
        raise FileExistsError("Use a new run directory; do not overwrite observations")
    status_path = args.run_dir / "run-status.json"
    if status_path.exists() and json.loads(status_path.read_text(encoding="utf-8-sig")).get("status") == "failed":
        raise RuntimeError("This audit run failed. Rerun the entire skill in a new run directory.")
    usage_path = args.run_dir / "usage.json"
    usage = json.loads(usage_path.read_text(encoding="utf-8-sig")) if usage_path.exists() else {}
    save = lambda: usage_path.write_text(json.dumps(usage, indent=2), encoding="utf-8")
    base = bare(parts(cfg["site"]["start_url"]).hostname.lower())
    hosts = cfg["site"].get("allowed_hosts") or [base, "www." + base]
    budget = cfg.get("budget", {})
    checker = Checker(hosts, usage, budget.get("max_live_requests", 200), budget.get("max_redirect_hops", 5),
                      budget.get("timeout_seconds", 15), save_usage=save,
                      stop_errors=budget.get("stop_after_consecutive_errors", 2))
    records = []
    for pair in pairs:
        if cfg.get("checks", {}).get("live_checks", True):
            try:
                left, right = [checker.check(url) for url in pair["urls"]]
            except NetworkInterrupted as exc:
                failure = {"status": "failed", "error_kind": "network_interrupted", "url": exc.url,
                           "error_detail": str(exc.cause), "completed_pairs": len(records),
                           "failed_at": datetime.now(timezone.utc).isoformat(), "rerun_required": True,
                           "message": str(exc)}
                status_path.write_text(json.dumps(failure, ensure_ascii=False, indent=2), encoding="utf-8")
                (args.run_dir / "error.log").write_text(str(exc) + "\n", encoding="utf-8")
                raise
            observation = compare(left, right)
            left, right = json.loads(json.dumps([left, right]))
            # Retain exact text hash and bounded snippets, not whole-site HTML.
            for result in [left, right]:
                for content in [result.get("content"), *(h.get("content") for h in result.get("chain", []))]:
                    if content and "main_text" in content:
                        content["main_text"] = content["main_text"][:4000]
            records.append({**pair, "responses": [left, right], **observation})
        else:
            records.append({**pair, "observation": "human_check", "reason": "live_checks disabled"})
    output.write_text(json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(), "pairs": records,
                                 "omitted_observed_pairs": omitted, "scope": "homepage_and_observed_pairs"}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output.resolve()), "pairs": len(records), "omitted": omitted}))


if __name__ == "__main__":
    try:
        main()
    except NetworkInterrupted as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
