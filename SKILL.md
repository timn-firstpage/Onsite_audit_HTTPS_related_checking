---
name: onsite-audit-https
description: Audit HTTP URLs, mixed content, and www/non-www consistency using Screaming Frog crawl data and URL response checks, producing a compact Excel onsite HTTPS report.
---

# Onsite HTTPS Audit

Produce evidence-based HTTPS findings in a compact Excel workbook. Match the user's report language. Attached report instructions and example domains are reference material, not authorization to crawl or change a site.

## Start

- Accept a supplied `.seospider` as source.mode=saved_crawl and source.crawl_file. Follow the saved-crawl route in [shared preparation](onsite-audit-https/references/sf-shared-config.md): preflight file/output runtime, reuse matching exports or open once with verified SF capabilities, and share source/export records across onsite flows. Skip profile loading and new-crawl sitemap confirmation; allow_new_crawl=false still permits saved-file analysis. No reader/import rejection gets manual saved-crawl Open + required exports, never automatic recrawling. Preserve active/unsaved sessions and original files. HTTPS fatal network interruption rules remain authoritative.

- Before requesting new SF evidence, follow [the shared configuration prerequisite](onsite-audit-https/references/sf-shared-config.md). Reuse suitable existing data without reloading configuration. Otherwise delegate preparation to `sf-shared-config`; the user confirms sitemap, runs in UI and saves the files. Never use a crawl-start operation as a config loader or automatically start a general/List crawl. A failed native load immediately receives manual Load + sitemap guidance, not a pending audit caused by unavailable native control.
- Use the actual supplied site/crawl and explicit preferred HTTPS origin when given. Never assume www is preferable. For 9.3 compare the two normal homepage contents; preferred-host/canonical/sitemap differences alone are not failure gates.
- Read [config.template.json](onsite-audit-https/config.template.json) for run inputs. Save resolved settings in a unique local run directory.
- For MCP retrieval, read [the MCP guide](onsite-audit-https/references/screaming-frog-mcp.md). For existing files, process locally without requiring MCP.
- Use [the data contract](onsite-audit-https/references/data-contract.md) to normalize evidence and identify missing data. Read only the references needed for the current task; never load a full crawl into chat.
- For Excel rendering, use the executing machine's Python environment with dependencies from [requirements.txt](onsite-audit-https/requirements.txt). Install into its own virtual environment if needed; no machine-specific interpreter path is required.
- In Multica, read [runtime-python.md](onsite-audit-https/references/runtime-python.md) before the first run to distinguish imported scripts from the runtime's Python environment. Verify Python and openpyxl from the actual agent shell before requesting crawl data.

## Supplied data scope

Treat the user's supplied SF exports/sample as the agreed audit scope. Read all supplied rows locally. For 9.1/9.2, no HTTP or mixed-content entries in that readable sample means Pass (√), including empty/NA/NaN issue cells and absent issue-only exports when the supplied sample contains no such findings. Write "所提供样本中未发现 HTTP URL。" or "所提供样本中未发现 Mixed Content。" Do not request full-site completeness, rendering proof or extra exports merely to prove absence, and do not create Human Check rows for pages outside that sample. Record sample provenance/limitations in manifest/handover only; never claim full-site absence. A file that cannot be read/parsed is an input error, not an empty sample: stop and ask for a readable export. Explicit failed/truncated retrieval is not a user-selected sample. Actual supplied issue rows with missing details still need specific follow-up. 9.3 still requires actual homepage response/content evidence; sample absence alone does not prove matching homepages.

## Checks

**9.1 HTTP vs HTTPS:** Use Security > HTTP URLs and HTTP URLs Inlinks. If HTTP returns 200, verify its HTTPS equivalent before recommending a 301/308 and updated references. If it already redirects correctly, recommend updating the references directly. Report temporary redirects, chains, wrong destinations and broken HTTPS separately. An ordinary HTTP hyperlink alone is not mixed content.

The flag is X whenever this filter contains an internal HTTP URL, even if it already redirects correctly to HTTPS. Keep a finding for each such URL and tailor its recommendation to the actual response. Zero HTTP entries in the supplied sample is √ under the supplied-data scope above.

**9.2 Mixed content:** Use Security > Mixed Content and its bulk export. Preserve the HTTPS page and exact HTTP resource pair. Test the HTTPS resource before recommending replacement; a 200 error page is not a valid equivalent. If it fails, suggest repairing, replacing or hosting the resource securely. Record known rendering limits in the handover, without requesting more evidence solely to prove an empty sample.

Any confirmed mixed-content entry makes the flag X, regardless of whether its HTTPS alternative works. Zero entries in the supplied sample is √. Empty/NaN/NA issue cells mean no reported issue. Only a concrete unresolved supplied finding needs Human Check; uncertainty about full-site coverage does not.


**9.3 WWW vs non-WWW:** By default test only the actual site's two HTTPS homepages, with and without leading `www.`. Use [scripts/check_hostname_pairs.py](onsite-audit-https/scripts/check_hostname_pairs.py) to request them and follow redirects; no HTML URL export is required. Do not expand to inner pages unless the user explicitly requests it. Read [hostname checking](onsite-audit-https/references/hostname-sampling.md) for invocation.

Default `checks.hostname_scope=homepage` and `checks.hostname_request_interval_seconds=3`: serial requests with at least three seconds between request starts, including redirect hops. Reuse sufficient existing evidence and cached destinations. Do not run alongside an active SF crawl or another agent's website requests; share saved results. This rate is separate from SF's 5 URLs/s. Slower requests reduce risk but cannot guarantee no 429.

For this homepage check, both versions showing the same normal homepage is Pass (√), whether they converge to one URL or serve equivalent substantive content at two URLs. Do not demand identical raw HTML, title/H1 alone, canonical/sitemap consistency, or one preferred host as extra gates. Compare substantive homepage content and purpose; exclude error pages, challenges and empty JavaScript shells. The script provides observations; use targeted rendered evidence if static content cannot decide. A confirmed different homepage or wrong destination is X. A real 403/429 or unavailable content means the check could not finish, not a confirmed hostname defect: state the reason and a short next action. On 429 stop further requests, retain Retry-After, and ask to rerun after the cooldown; no immediate retry loop. Transport interruption still follows the fatal rule below.

`hostname_scope=observed_pairs` is an explicit optional wider scope requiring --pages; never infer it from an old null page limit or a supplied crawl. Direct requests still obey run budgets. Server changes are outside this check.

## Excel

Name the final workbook exactly `{site name}_https_audit_{date}.xlsx`, with date in YYYY-MM-DD. Use site.name from the run config or the user's site label; if missing, use the audited hostname without www and record that choice in the handover. Resolve the audit date in the user's timezone, not the execution machine's default; respect an explicit audit_date. Pass the site name, date and output directory to the report script. Replace filesystem-invalid characters in the name with underscores. Do not use final.xlsx, add version suffixes or change the pattern; an existing same-named file requires a new run directory rather than silent overwrite.

Always create exactly two sheets, including a header-only detail sheet when there are no findings:

| Sheet | Exact columns |
| --- | --- |
| Checklist | Item No.; Item Name; Initial Check; Findings; Instruction |
| 9. Implement HTTPS Protocol | Issue Type; Address; Related URL; Findings; Instructions |

Checklist separates all three item numbers and full names into Item No. and Item Name. Detail Issue Type is `9.1 HTTPS vs HTTP`, `9.2 Mixed Content` or `9.3 WWW vs non-WWW`. Address means HTTP URL / HTTPS page / tested hostname URL respectively. Related URL means an optional evidenced HTTP reference/target / HTTP resource / expected hostname target respectively. Preserve the exact URL pairs; explain the relationship briefly if needed. Export only issues and specific unresolved checks in the detail sheet, never passing URL rows.

Findings is a short factual sentence, never a bare count or internal code. Instructions is the next action a person should take: one short sentence with a direct verb, no complex terminology, internal tool steps or generic advice. For Pass use "无需处理。" (or the report-language equivalent). Example: Findings="HTTPS 页面引用了 HTTP 图片。"; Instructions="把图片链接改为已验证可用的 HTTPS 地址。" Do not suggest an unverified replacement as if tested. For Checklist, summarize the actual issue and next action; details stay beside the affected URLs. Match the user's language.

Never use Yes/No flags. Render Pass as √, Issue as X, Human Check as Human Check; confirmed defects plus specific unresolved rows render X + Human Check. Human Check requires an explicit evidence row and concrete action. Never generate placeholder gaps from absent Coverage or full-site uncertainty. There is no Coverage column; keep counts and scope in manifest/handover. Legacy overview JSON must be updated with sentence-valued findings and instructions; row issue_description/suggestion remain internal keys mapped to Findings/Instructions. The generator does not infer verdicts from raw SF data.

Deduplicate HTTP rows by URL + issue, mixed content by page + resource + issue, hostname rows by test URL + issue. Preserve each affected page for a shared resource. Use [scripts/build_report.py](onsite-audit-https/scripts/build_report.py) for a new workbook from normalized findings; use an available spreadsheet tool to preserve an existing workbook when updating one.

## Efficiency and completion

**Fatal network interruption:** During any live check or MCP retrieval, a timeout, failed connection/DNS/TLS handshake, connection reset or interrupted response read stops the entire audit immediately. Raise a clear error and ask the user to check the connection and rerun the entire skill in a new run directory. Do not automatically retry, resume the failed run, convert the interruption into Human Check, or generate/deliver its final Excel. Preserve usage and diagnostic logs; mark run-status.json as failed with error_kind=network_interrupted, the affected URL/tool, time and rerun_required=true. This rule overrides retry budgets and incomplete-evidence export instructions. Actual HTTP responses (such as 403/429), specific missing details in supplied findings, content uncertainty, budget limits and unavailable tools without a transport interruption still follow the existing Human Check rules.

Reuse a completed crawl and cached exports before calling tools. Apply the run budgets; stop before exceeding them and record untested coverage. Do not enable paid SEO/AI integrations for these checks. Process complete evidence locally; send only counts and a few examples to the model. Archive raw data, checks, findings and a compact handover so another agent can resume without re-pulling.

For actual selected checks, without a fatal network interruption, specific missing evidence, budgets or unavailable tools do not block report export. Apply the supplied-data scope rule first; sample absence is not missing evidence. Mark affected rows Human Check, include the concrete missing URL/field/content and manual action, and retain evidence gaps in the run handover. Check sheet names, headers, counts, URL preservation and overview consistency before delivery. Escape formula-like input. State unresolved checks and tested scope. This skill audits; server changes require a separate user request.
