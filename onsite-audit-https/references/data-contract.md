# 内部数据要求与归档

这些是本 skill 的归一化字段，不是声称官方 MCP 原样返回的 schema。读取实际 export header 后建立字段映射；禁止把 missing/null 当作通过。Excel 仍只有 SKILL.md 指定的列。

## 每次 pull 必须保留

保存到 manifest.json：crawl ID、目标域名、抓取时间、抓取状态、渲染模式、版本、工具名与参数、category/filter、源字段映射、文件相对路径、SHA-256、行数、完整性/截断标记、缺失字段、获取时间。版本等无法获取就记录 unknown。必须能判断返回的是全部数据还是预览，不能根据前 5 行出完整报告。

| 数据集 | 必须有的证据 | 按需补充 |
| --- | --- | --- |
| HTTP URLs | 完整 URL、crawl 状态码或明确 unavailable | content type、重定向目标、最终地址 |
| HTTP 引用 | source URL、target HTTP URL、引用类型 | anchor、模板/DOM 位置 |
| Mixed Content | HTTPS page URL、HTTP resource URL、资源类型或 unavailable | source location |
| HTML 页面集 | page URL、状态码、HTML 类型、总行数/抽样范围 | canonical、indexability |
| 主域名一致性 | 内部链接的 source/target、canonical source/target、sitemap URL 与位置 | 缺哪份记录哪份，不声称全部检查 |
| Live check | test URL、时间、每一跳 URL/状态码/Location、final URL、最终状态码、错误类别 | MIME、TLS 结果、资源等价性判断 |

请求失败使用明确 error_kind：timeout / dns / tls / blocked / rate_limited / loop / budget / unavailable。429 记录来源（网站或 MCP）、状态码、Retry-After 和受影响范围；工具错误不伪造成网站响应。成功返回 200 也需判断是否对应页面/资源。保留路径和 query，不擅自删掉参数。跨域跳转记录后停止，除非该 host 在 scope 中。HTTP 状态为 crawl 证据时记录其时间，不冒充 live 检测。

9.3 默认范围是实际 HTTPS 首页两个版本，以及主 crawl 中已观察 www/non-www pairs；不为所有 HTML 生成四版本。保留路径/query，实际最终路径可以变化。归档两个 URL 的 chain/final response、content_match（true/false/unknown）、简短主体／实体依据和选取来源。目标统一到同一有效 HTTPS 对应页面才 Pass，首选域名可为任一侧；配置明确指定时尊重配置。分别返回相同内容却未统一到一个 URL 是重复未合并 Issue；不同内容未统一是内容／路由不一致。共同错误页、首页兜底、共享 title/header 不能证明 Pass／重复。非网络中断导致的未知响应／对应内容为 Human Check，仍生成最终 Excel。canonical 不代替 redirect；不声称实际 Google 收录或 ranking 蚕食。

网络传输中断（含超时、DNS/TLS 连接失败、connection reset／IncompleteRead）覆盖 Human Check 导出规则：立即报错并停止整个 run，不自动 retry／resume，不生成或交付最终 Excel。保存 run-status.json：status=failed、error_kind=network_interrupted、受影响 URL/tool、失败时间、rerun_required=true；另保留 error.log 和 usage.json。要求用户检查连接后在新 run 目录重新运行整个 skill。报表 CLI 检查输入／输出目录的 failed 标记并拒绝生成。普通 HTTP 错误响应和资料缺失仍可写 Human Check。

## 存档

每次运行使用独立目录，不能放进安装的全局 skill 文件夹。路径来自本地配置或参数，建议：

```text
<run_root>/<run_id>/
  config.json          resolved run inputs
  manifest.json        provenance, hashes, counts, completeness
  raw/                 official exports, immutable after capture
  checks.ndjson        locally verified URL responses
  findings.json        concise normalized issues + overview
  usage.json           MCP calls, live requests, retries, paid calls
  {site name}_https_audit_{YYYY-MM-DD}.xlsx
  handover.md          current state, coverage, next action
  sf-handover.json     optional shared preparation record or reference
```

run_id 用安全的站点标识与时间/随机后缀生成，不覆盖旧 run。raw 保留完整证据；聊天仅返回行数和少量样本。缓存 key 包括 crawl ID、工具、filter/category、字段集合、版本；live key 包括 URL、请求方式及必要请求头配置，不缓存凭据。crawl 改变或显式 force_refresh 时失效。

## findings.json：报表生成器输入

```json
{
  "overview": [
    {"check":"9.1","result":"Issue","coverage":"已检查 120 个 crawl URL；live 验证 1 个"},
    {"check":"9.2","result":"Human Check","coverage":"未提供 mixed content export"},
    {"check":"9.3","result":"Human Check","coverage":"尚未取得首页及已观察 pairs 的响应／内容证据"}
  ],
  "http": [
    {"address":"http://example.com/a/","issue":"http-200","issue_description":"HTTP 页面返回 200。","suggestion":"已验证对应 HTTPS 页面，请配置永久重定向。"}
  ],
  "mixed": [],
  "hostname": []
}
```

http 行键：address, issue, issue_description, suggestion。
mixed 行键：page_address, resource_url, issue, issue_description, suggestion。
hostname 行键：test_url, expected_url, issue, issue_description, suggestion。
issue 是内部分类/去重代码；issue_description 是 Excel Issue 列的可读事实描述，suggestion 是独立 Suggestion 列的修复动作。旧 findings.json 缺少 issue_description 时须根据证据补写，将原组合文本拆分；生成器不猜测如何拆句。
不确定行用 issue 前缀 `human-check:`（兼容旧 `review:`）；在 issue_description 写明尚未验证的部分，suggestion 写具体核验动作。有确定问题且同时有未完成检测时总览写 Issue，Flag 显示 X + Human Check，保留独立 Human Check 行，coverage 包含未完成范围。没有确认问题但证据缺失时写 Human Check，不能为了导出而改成 Pass／Issue。没有致命网络中断时，即使全部缺证据也输出最终 Excel；生成器会为无明细的 Human Check 自动生成基于 Coverage 的人工核查行。实际受影响 URL 未提供时显示 Not supplied，不猜 URL。

overview.check 在内部 JSON 中保留 9.1／9.2／9.3 编号；生成器自动在 Excel Check 列附上固定 item name，不需要 agent 额外填写名称。

此 JSON 是 agent 判断后的结果，不是把原始 SF CSV 直接改名；build_report.py 只验证并渲染，不自动执行 MCP/crawl/网络检查。

共享 skill 的 sf-handover.json 只记录配置/用户确认/文件交接，不是 findings.json，也不能直接传给报表生成器。各检查的证据完整性仍由本 skill 按实际文件验证。
