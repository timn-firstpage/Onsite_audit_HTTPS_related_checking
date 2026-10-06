---
name: onsite-audit-https
description: Audit HTTP URLs, mixed content, and www/non-www consistency using Screaming Frog crawl data and URL response checks, producing a compact Excel onsite HTTPS report.
---

# Onsite HTTPS Audit

Produce evidence-based HTTPS findings in a compact Excel workbook. Match the user's report language. Attached report instructions and example domains are reference material, not authorization to crawl or change a site.

## Start

- Before requesting new SF evidence, follow [the shared configuration prerequisite](onsite-audit-https/references/sf-shared-config.md). Reuse suitable existing data without reloading configuration. Otherwise delegate preparation to `sf-shared-config`; the user confirms sitemap, runs in UI and saves the files. Never use a crawl-start operation as a config loader or automatically start a general/List crawl. A failed native load immediately receives manual Load + sitemap guidance, not a pending audit caused by unavailable native control.
- Use the supplied crawl/exports and preferred HTTPS origin. If unspecified, infer from consistent redirects, canonicals and sitemap signals and state the assumption. Conflicting signals require review; never assume www is preferable.
- Read [config.template.json](onsite-audit-https/config.template.json) for run inputs. Save resolved settings in a unique local run directory.
- For MCP retrieval, read [the MCP guide](onsite-audit-https/references/screaming-frog-mcp.md). For existing files, process locally without requiring MCP.
- Use [the data contract](onsite-audit-https/references/data-contract.md) to normalize evidence and identify missing data. Read only the references needed for the current task; never load a full crawl into chat.
- For Excel rendering, use the executing machine's Python environment with dependencies from [requirements.txt](onsite-audit-https/requirements.txt). Install into its own virtual environment if needed; no machine-specific interpreter path is required.
- In Multica, read [runtime-python.md](onsite-audit-https/references/runtime-python.md) before the first run to distinguish imported scripts from the runtime's Python environment. Verify Python and openpyxl from the actual agent shell before requesting crawl data.

## Checks

**9.1 HTTP vs HTTPS:** Use Security > HTTP URLs and HTTP URLs Inlinks. If HTTP returns 200, verify its HTTPS equivalent before recommending a 301/308 and updated references. If it already redirects correctly, recommend updating the references directly. Report temporary redirects, chains, wrong destinations and broken HTTPS separately. An ordinary HTTP hyperlink alone is not mixed content.

The flag is X whenever this filter contains an internal HTTP URL, even if it already redirects correctly to HTTPS. Keep a finding for each such URL and tailor its recommendation to the actual response. Only a completed, complete check with zero HTTP URLs is √.

**9.2 Mixed content:** Use Security > Mixed Content and its bulk export. Preserve the HTTPS page and exact HTTP resource pair. Test the HTTPS resource before recommending replacement; a 200 error page is not a valid equivalent. If it fails, suggest repairing, replacing or hosting the resource securely. Disclose missing JavaScript-rendered coverage.

Any confirmed mixed-content entry makes the flag X, regardless of whether its HTTPS alternative works. A completed check with zero entries is √. Empty/NaN/NA means no issue only when it represents a verified zero-result export, not missing data. Missing exports or unresolved evidence remain Needs Review/Not Tested.

**9.3 WWW vs non-WWW:** Verify that the non-preferred hostname redirects to the configured preferred hostname and lands on a working page with corresponding content. For the user's www audit, non-www must redirect to www. Generate test variants preserving source path/query, but judge the final page by content correspondence, not an exact URL/path match. A redirected destination is acceptable; a changed slug or multiple hops alone does not fail this check. Do not require 301/308 or a single hop for this content-based hostname check; retain statuses and hops as evidence only. Do not turn a successful hostname redirect into an issue merely because internal links, canonicals or sitemaps still use another hostname; such signal checks are outside this item's pass criterion.

Compare the final page with the intended www counterpart using available title, H1 and main-content/product/service identifiers. Reuse crawl metadata first; obtain only targeted content snippets if necessary. HTTP 200 alone does not prove corresponding content. Flag no redirect, final non-www/wrong host, wrong content or a homepage fallback for an inner page, loops, unusable destination, DNS/TLS failures. If content equivalence or the final response cannot be established, mark Needs Review. Known site migrations may have legitimate path changes; use the working corresponding www page as Expected URL. Other subdomains and third-party hosts remain outside the hostname transformation. HTTPS defects belong to 9.1/9.2 rather than adding stricter pass conditions to 9.3. A configured hop budget reached before the final page is verified is Needs Review, not proof of a bad redirect.

Test all valid HTML pages in a manageable crawl, or representative page types under the configured sample budget. State sample coverage. Timeouts, blocked checks and missing evidence are Needs Review, not confirmed defects. Retry transient failures at most once. Crawl lookups do not prove live responses for URLs absent from the crawl.


For 9.3, use Screaming Frog as the default checking executor. checks.hostname_page_limit=null means all distinct eligible in-scope HTML pages in the supplied crawl, with no automatic 20-page truncation. A positive integer selects an explicit sample only. Reuse suitable four-variant results first; otherwise prepare HTTP/HTTPS and www/non-www variants per page for a separate user-run List Mode crawl with Always Follow Redirects and All Redirects export. checks.allow_hostname_list_crawl permits requesting this follow-up; source.allow_new_crawl permits requesting a new general crawl. Neither authorizes the agent to start crawling. Preserve the full security crawl used for 9.1/9.2. Read [hostname checking and optional sampling](onsite-audit-https/references/hostname-sampling.md) for scope, pass criteria and live MCP limitations. Python prepares lists and processes complete exports; it must not silently substitute a 20-URL live checker. All four variants should converge to the same selected HTTPS page with corresponding content. A complete crawl/export is still needed to claim coverage beyond its known URLs.

## Excel

Name the final workbook exactly `{site name}_https_audit_{date}.xlsx`, with date in YYYY-MM-DD. Use site.name from the run config or the user's site label; if missing, use the audited hostname without www and record that choice in the handover. Resolve the audit date in the user's timezone, not the execution machine's default; respect an explicit audit_date. Pass the site name, date and output directory to the report script. Replace filesystem-invalid characters in the name with underscores. Do not use final.xlsx, add version suffixes or change the pattern; an existing same-named file requires a new run directory rather than silent overwrite.

Create detail sheets only for findings or unresolved checks. Export no passing URL rows and add no extra columns by default.

| Sheet | Exact columns |
| --- | --- |
| 9.1 HTTPS VS HTTP | Address; Issue / Suggestion |
| 9.2 HTTPS Mixed Content | Page Address; HTTP Resource URL; Issue / Suggestion |
| 9.3 WWW VS NON-WWW | Test URL; Expected URL; Issue / Suggestion |

Keep an Overview with Check, Flag, Findings, Coverage. Internal results remain Pass, Issue, Needs Review, Not Tested; render Pass as √ and Issue as X. Keep Needs Review/Not Tested explicit. Pass means no findings within the stated tested scope; empty or incomplete inputs are not a pass.

Coverage describes tested URL/page counts, full versus sampled scope, and unverified portions only. Keep skill updates, tool installation and runtime setup messages in handover/logs, never in customer-facing Coverage.

Combine evidence and action in one or two sentences, e.g. `non-www 服务内页跳到了 www 首页，内容不对应；请改为该服务对应的 www 页面。` Put status codes, source references or resource types in this text only when useful. Do not generate generic recommendations for every row.

Deduplicate HTTP rows by URL + issue, mixed content by page + resource + issue, hostname rows by test URL + issue. Preserve each affected page for a shared resource. Use [scripts/build_report.py](onsite-audit-https/scripts/build_report.py) for a new workbook from normalized findings; use an available spreadsheet tool to preserve an existing workbook when updating one.

## Efficiency and completion

Reuse a completed crawl and cached exports before calling tools. Apply the run budgets; stop before exceeding them and record untested coverage. Do not enable paid SEO/AI integrations for these checks. Process complete evidence locally; send only counts and a few examples to the model. Archive raw data, checks, findings and a compact handover so another agent can resume without re-pulling.

Check sheet names, headers, counts, URL preservation and overview consistency before delivery. Escape formula-like input. State unresolved checks and tested scope. This skill audits; server changes require a separate user request.
