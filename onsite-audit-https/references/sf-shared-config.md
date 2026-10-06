# Shared SF preparation prerequisite

The independent [sf-shared-config skill](https://github.com/timn-firstpage/On-_site_SF_shared_config/blob/main/SKILL.md) owns profile loading, manual fallback, sitemap confirmation and file handover. Its [README](https://github.com/timn-firstpage/On-_site_SF_shared_config) includes installation and bundled profiles. This HTTPS package does not bundle or automatically install that dependency.

## Route before requesting a crawl

| Available evidence | HTTPS action |
| --- | --- |
| Suitable crawl or exports | Verify site, date, scope, completion and required fields; reuse directly. No profile load or exhaustive historical settings check. |
| Partly suitable evidence | Keep valid evidence and request only the missing check-specific export/follow-up. A missing export does not by itself require a recrawl. |
| User crawl currently running | Preserve it. Return a checkpoint and the files needed after completion; do not load a profile, stop it or indefinitely poll. |
| No suitable evidence and a permitted follow-up | Invoke the installed shared skill. Default to main for a full crawl; targeted profile only for a specific follow-up. |
| Shared skill unavailable | Give its installation link or equivalent manual Load → sitemap → Start → save instructions. Do not claim invocation or successful loading. Existing usable files remain usable. |

Resolve profiles from the installed shared skill on the SF host, rather than from a sibling checkout or another computer's path. An explicit user config overrides the default; an invalid override requires correction, not silent fallback. Reliable evidence of an unchanged loaded profile lets the shared skill skip loading; file existence alone does not. Share preparation across HTTPS and robots in the same SF session. Never reload after the user adds this site's sitemap.

Config-load failure immediately switches to manual guidance, preserving the original error. Unsupported native control is not a reason to block data reuse. `sf_crawl(config_path=...)` starts a crawl and is not a standalone loader. The user confirms site/scope/sitemap, manually starts and supervises the crawl, then saves to their actual Downloads folder and supplies the path. Neither allow_new_crawl nor allow_hostname_list_crawl changes that division of responsibility.

For a hostname follow-up, supply the complete URL list, require List Mode and Always Follow Redirects, and retain the original security crawl. Do not require another whole-site sitemap crawl for a four-variant test. Main does not store whole-page HTML; title/H1/identifiers may suffice, otherwise request targeted content evidence. CSS/JS resource coverage must be established from actual exports, not inferred from the profile name.

## Validate the handover

Keep the shared skill's `sf-handover.json` path in the local run manifest/handover. It records provenance and preparation state; it is not a passing audit or proof of complete data. A saved `.seospider` needs a supported SF load and actual field/export inspection. CSV/NDJSON needs readable structure, required fields and complete row coverage. Do not treat binary signature, file size or a filename as successful crawl verification.

Validate 9.1 HTTP URLs/inlinks, 9.2 page/resource pairs and rendering coverage, and 9.3 four-variant final response/chain/content evidence independently. Record known limitations only for affected checks. Missing sitemap evidence alone does not invalidate unrelated security checks. Empty exports mean zero findings only when the export and its scope are verified complete.

Separate website HTTP 429 from MCP/tool 429; retain source, Retry-After and affected coverage. Missing rows and failed requests are not passing responses. Safe reads/direct URL checks follow the HTTPS retry/budget rules; config-load failures follow the shared skill's immediate manual fallback. Sustained crawl errors are handed to the user for UI decisions, without automatic restart. Preserve partial evidence and return a concrete next action.
