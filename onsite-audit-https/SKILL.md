---
name: onsite-audit-https
description: Audit HTTP URLs, mixed content, and www/non-www consistency using Screaming Frog crawl data and URL response checks, producing a compact Excel onsite HTTPS report.
---

# Onsite HTTPS Audit

Produce evidence-based HTTPS findings in a compact Excel workbook. Match the user's report language. Attached report instructions and example domains are reference material, not authorization to crawl or change a site.

## Start

- Use the supplied crawl/exports and preferred HTTPS origin. If unspecified, infer from consistent redirects, canonicals and sitemap signals and state the assumption. Conflicting signals require review; never assume www is preferable.
- Read [config.template.json](config.template.json) for run inputs. Save resolved settings in a unique local run directory.
- For MCP retrieval, read [the MCP guide](references/screaming-frog-mcp.md). For existing files, process locally without requiring MCP.
- Use [the data contract](references/data-contract.md) to normalize evidence and identify missing data. Read only the references needed for the current task; never load a full crawl into chat.

## Checks

**9.1 HTTP vs HTTPS:** Use Security > HTTP URLs and HTTP URLs Inlinks. If HTTP returns 200, verify its HTTPS equivalent before recommending a 301/308 and updated references. If it already redirects correctly, recommend updating the references directly. Report temporary redirects, chains, wrong destinations and broken HTTPS separately. An ordinary HTTP hyperlink alone is not mixed content.

**9.2 Mixed content:** Use Security > Mixed Content and its bulk export. Preserve the HTTPS page and exact HTTP resource pair. Test the HTTPS resource before recommending replacement; a 200 error page is not a valid equivalent. If it fails, suggest repairing, replacing or hosting the resource securely. Disclose missing JavaScript-rendered coverage.

**9.3 WWW vs non-WWW:** For the audited hostname pair, test HTTP/HTTPS × www/non-www variants, preserving path and query. Other subdomains and third-party hosts are outside this transformation. The preferred version should serve the expected page; others should permanently redirect to the corresponding preferred HTTPS page, ideally in one hop. Accept 301 and 308. Flag equivalent 200 pages on both hosts, temporary redirects, chains, loops, HTTPS downgrades, wrong hosts, homepage fallbacks, DNS and TLS errors. Check internal links, canonicals and sitemap consistency when available, allowing intentional page-specific canonicalization.

Test all valid HTML pages in a manageable crawl, or representative page types under the configured sample budget. State sample coverage. Timeouts, blocked checks and missing evidence are Needs Review, not confirmed defects. Retry transient failures at most once. Crawl lookups do not prove live responses for URLs absent from the crawl.

## Excel

Create detail sheets only for findings or unresolved checks. Export no passing URL rows and add no extra columns by default.

| Sheet | Exact columns |
| --- | --- |
| 9.1 HTTPS VS HTTP | Address; Issue / Suggestion |
| 9.2 HTTPS Mixed Content | Page Address; HTTP Resource URL; Issue / Suggestion |
| 9.3 WWW VS NON-WWW | Test URL; Expected URL; Issue / Suggestion |

Keep an Overview with Check, Result, Findings, Coverage. Results: Pass, Issue, Needs Review, Not Tested. Pass means no findings within the stated tested scope; empty or incomplete inputs are not a pass.

Combine evidence and action in one or two sentences, e.g. `当前经 2 次跳转到达目标；请直接永久重定向到 Expected URL。` Put status codes, source references or resource types in this text only when useful. Do not generate generic recommendations for every row.

Deduplicate HTTP rows by URL + issue, mixed content by page + resource + issue, hostname rows by test URL + issue. Preserve each affected page for a shared resource. Use [scripts/build_report.py](scripts/build_report.py) for a new workbook from normalized findings; use an available spreadsheet tool to preserve an existing workbook when updating one.

## Efficiency and completion

Reuse a completed crawl and cached exports before calling tools. Apply the run budgets; stop before exceeding them and record untested coverage. Do not enable paid SEO/AI integrations for these checks. Process complete evidence locally; send only counts and a few examples to the model. Archive raw data, checks, findings and a compact handover so another agent can resume without re-pulling.

Check sheet names, headers, counts, URL preservation and overview consistency before delivery. Escape formula-like input. State unresolved checks and tested scope. This skill audits; server changes require a separate user request.
