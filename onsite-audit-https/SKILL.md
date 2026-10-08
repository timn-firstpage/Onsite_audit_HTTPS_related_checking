---
name: onsite-audit-https
description: Audit HTTP URLs, mixed content, and www/non-www consistency using Screaming Frog crawl data and URL response checks, producing a compact Excel onsite HTTPS report.
---

# Onsite HTTPS Audit

Produce evidence-based HTTPS findings in a compact Excel workbook. Match the user's report language. Attached report instructions and example domains are reference material, not authorization to crawl or change a site.

## Start

- Accept a supplied `.seospider` as source.mode=saved_crawl and source.crawl_file. Follow the saved-crawl route in [shared preparation](references/sf-shared-config.md): preflight file/output runtime, reuse matching exports or open once with verified SF capabilities, and share source/export records across onsite flows. Skip profile loading and new-crawl sitemap confirmation; allow_new_crawl=false still permits saved-file analysis. No reader/import rejection gets manual saved-crawl Open + required exports, never automatic recrawling. Preserve active/unsaved sessions and original files. HTTPS fatal network interruption rules remain authoritative.

- Before requesting new SF evidence, follow [the shared configuration prerequisite](references/sf-shared-config.md). Reuse suitable existing data without reloading configuration. Otherwise delegate preparation to `sf-shared-config`; the user confirms sitemap, runs in UI and saves the files. Never use a crawl-start operation as a config loader or automatically start a general/List crawl. A failed native load immediately receives manual Load + sitemap guidance, not a pending audit caused by unavailable native control.
- Use the actual supplied site/crawl and explicit preferred HTTPS origin when given. Otherwise infer the selected hostname from observed redirect convergence, using canonical/sitemap hosts as context; never assume www is preferable. Inconsistent redirect selection is Human Check; canonical/sitemap disagreement alone is not an extra 9.3 failure gate.
- Read [config.template.json](config.template.json) for run inputs. Save resolved settings in a unique local run directory.
- For MCP retrieval, read [the MCP guide](references/screaming-frog-mcp.md). For existing files, process locally without requiring MCP.
- Use [the data contract](references/data-contract.md) to normalize evidence and identify missing data. Read only the references needed for the current task; never load a full crawl into chat.
- For Excel rendering, use the executing machine's Python environment with dependencies from [requirements.txt](requirements.txt). Install into its own virtual environment if needed; no machine-specific interpreter path is required.
- In Multica, read [runtime-python.md](references/runtime-python.md) before the first run to distinguish imported scripts from the runtime's Python environment. Verify Python and openpyxl from the actual agent shell before requesting crawl data.

## Checks

**9.1 HTTP vs HTTPS:** Use Security > HTTP URLs and HTTP URLs Inlinks. If HTTP returns 200, verify its HTTPS equivalent before recommending a 301/308 and updated references. If it already redirects correctly, recommend updating the references directly. Report temporary redirects, chains, wrong destinations and broken HTTPS separately. An ordinary HTTP hyperlink alone is not mixed content.

The flag is X whenever this filter contains an internal HTTP URL, even if it already redirects correctly to HTTPS. Keep a finding for each such URL and tailor its recommendation to the actual response. Only a completed, complete check with zero HTTP URLs is √.

**9.2 Mixed content:** Use Security > Mixed Content and its bulk export. Preserve the HTTPS page and exact HTTP resource pair. Test the HTTPS resource before recommending replacement; a 200 error page is not a valid equivalent. If it fails, suggest repairing, replacing or hosting the resource securely. Disclose missing JavaScript-rendered coverage.

Any confirmed mixed-content entry makes the flag X, regardless of whether its HTTPS alternative works. A completed check with zero entries is √. Empty/NaN/NA means no issue only when it represents a verified zero-result export, not missing data. Missing exports or unresolved evidence are Human Check; still export the final Excel with the gap and manual action.

**9.3 WWW vs non-WWW:** Check the actual site's HTTPS homepage with and without the leading `www.`, then check only counterpart pairs actually present in the main crawl: same base hostname, path and exact query after removing only leading `www.` and URL fragments. A shared title/name alone is not a pair. Do not manufacture counterparts for unpaired inner pages or generate four HTTP/HTTPS variants for every HTML page. Do not hardcode example domains or require www to be preferred; either hostname may be the selected origin.

Reuse sufficient response/content evidence first. For missing evidence use [scripts/check_hostname_pairs.py](scripts/check_hostname_pairs.py), following [pair selection and script boundaries](references/hostname-sampling.md). It collects redirect chains, final responses and static main-content evidence; the agent validates page purpose, soft-404/homepage fallback and correspondence with the intended page. Identical title/H1, HTTP 200 or shared navigation alone cannot establish identical content. JavaScript shells, challenges, truncated bodies or uncertain correspondence require targeted rendered evidence or Human Check. This script is for hostname checks, not a replacement robots/noindex crawler.

Pass requires both addresses to converge to the same working HTTPS page with corresponding content. Separate working final URLs with identical substantive content produce an Issue naming both URLs and their lack of consolidation; different content without convergence is a hostname/content inconsistency, not proven duplication. Wrong hosts/content, homepage fallback for an inner page and verified redirect loops are Issues. Valid slug changes or multiple hops alone are not defects. A hop limit, 403/429 or missing content is Human Check rather than a confirmed defect. Network/transport failures (including timeout, DNS/TLS connection failure or interrupted response reads) abort the entire run under the failure rule below. Canonical/internal-link/sitemap signals help interpretation but do not replace the user's redirect criterion. Describe potential duplicate-URL/consolidation risks; do not claim both URLs rank or ranking cannibalization occurred without search evidence.

checks.hostname_executor defaults to python. hostname_page_limit=null checks the homepage plus all observed pairs, not all possible counterparts; a positive integer explicitly caps observed pairs and records omitted pairs. Honor checks.live_checks and cumulative direct-request budgets, including hops. Do not silently raise budgets: report untested pairs as Human Check and still export the final workbook. source.allow_new_crawl controls new SF evidence preparation, not authorized direct checks. SF/browser rendered evidence is optional for unresolved content; any new SF crawl remains user-run through shared preparation. Old executor/page-limit values must be migrated consciously, never interpreted as permission for automatic broad SF crawling.

## Excel

Name the final workbook exactly `{site name}_https_audit_{date}.xlsx`, with date in YYYY-MM-DD. Use site.name from the run config or the user's site label; if missing, use the audited hostname without www and record that choice in the handover. Resolve the audit date in the user's timezone, not the execution machine's default; respect an explicit audit_date. Pass the site name, date and output directory to the report script. Replace filesystem-invalid characters in the name with underscores. Do not use final.xlsx, add version suffixes or change the pattern; an existing same-named file requires a new run directory rather than silent overwrite.

Create detail sheets only for findings or unresolved checks. Export no passing URL rows and add no extra columns by default.

| Sheet | Exact columns |
| --- | --- |
| 9.1 HTTPS VS HTTP | Address; Issue; Suggestion |
| 9.2 HTTPS Mixed Content | Page Address; HTTP Resource URL; Issue; Suggestion |
| 9.3 WWW VS NON-WWW | Test URL; Expected URL; Issue; Suggestion |

Keep an Overview with Check, Flag, Findings, Coverage. The Check cell must contain both number and item name: `9.1 HTTP vs HTTPS (Insecure Content Detected?) - Screaming Frog Insecure Content`, `9.2 Mixed Content`, `9.3 WWW vs non-WWW`; never export only the number or add another column for the name. Results are Pass, Issue or Human Check; render Pass as √, Issue as X, and mixed confirmed defects plus review rows as X + Human Check. Legacy Needs Review/Not Tested inputs render as Human Check. Deliver the final Excel even when evidence is incomplete, except after a fatal network interruption. Include all three checks and detail rows labelled Human Check with missing evidence, known observations and concrete manual actions; do not omit difficult checks or call the audit an overall pass. Unknown is not a confirmed defect. The builder creates a gap row from Coverage when an entirely untested check has no detail rows; write URL-specific rows where known.

Coverage describes tested URL/page counts, full versus sampled scope, and unverified portions only. Keep skill updates, tool installation and runtime setup messages in handover/logs, never in customer-facing Coverage.

Keep observed evidence and the action in separate columns. Issue describes the actual problem, e.g. `non-www 服务内页跳到了 www 首页，内容不对应。`; Suggestion gives the specific fix, e.g. `请改为该服务对应的 www 页面。` Use one or two short sentences each. Put status codes, source references or resource types in Issue only when useful. Do not export internal issue codes as the customer-facing description or generate generic recommendations for every row.

Deduplicate HTTP rows by URL + issue, mixed content by page + resource + issue, hostname rows by test URL + issue. Preserve each affected page for a shared resource. Use [scripts/build_report.py](scripts/build_report.py) for a new workbook from normalized findings; use an available spreadsheet tool to preserve an existing workbook when updating one.

## Efficiency and completion

**Fatal network interruption:** During any live check or MCP retrieval, a timeout, failed connection/DNS/TLS handshake, connection reset or interrupted response read stops the entire audit immediately. Raise a clear error and ask the user to check the connection and rerun the entire skill in a new run directory. Do not automatically retry, resume the failed run, convert the interruption into Human Check, or generate/deliver its final Excel. Preserve usage and diagnostic logs; mark run-status.json as failed with error_kind=network_interrupted, the affected URL/tool, time and rerun_required=true. This rule overrides retry budgets and incomplete-evidence export instructions. Actual HTTP responses (such as 403/429), missing exports, content uncertainty, budget limits and unavailable tools without a transport interruption still follow the existing Human Check rules.

Reuse a completed crawl and cached exports before calling tools. Apply the run budgets; stop before exceeding them and record untested coverage. Do not enable paid SEO/AI integrations for these checks. Process complete evidence locally; send only counts and a few examples to the model. Archive raw data, checks, findings and a compact handover so another agent can resume without re-pulling.

Without a fatal network interruption, missing evidence, budgets or unavailable tools do not block report export. Mark affected rows Human Check, include the concrete missing URL/field/content and manual action, and retain evidence gaps in the run handover. Check sheet names, headers, counts, URL preservation and overview consistency before delivery. Escape formula-like input. State unresolved checks and tested scope. This skill audits; server changes require a separate user request.
