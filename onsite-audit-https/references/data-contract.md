# 内部数据要求与归档

这些是本 skill 的归一化字段，不是声称官方 MCP 原样返回的 schema。读取实际 export header 后建立字段映射；用户提供的 SF 样本就是本次范围：9.1/9.2 没有问题记录（含空／NA／NaN）即样本内通过；不要求证明全站完整。读取／解析失败应报错，不能当空样本。Excel 仍只有 SKILL.md 指定的列。

## 每次 pull 必须保留

保存到 manifest.json：crawl ID、目标域名、抓取时间、抓取状态、渲染模式、版本、工具名与参数、category/filter、源字段映射、文件相对路径、SHA-256、行数、完整性/截断标记、缺失字段、获取时间。版本等无法获取就记录 unknown。记录用户选择的样本范围；MCP 预览不能冒充完整导出，但用户明确提供的样本可作为本次完整审核范围。

| 数据集 | 必须有的证据 | 按需补充 |
| --- | --- | --- |
| HTTP URLs | 完整 URL、crawl 状态码或明确 unavailable | content type、重定向目标、最终地址 |
| HTTP 引用 | source URL、target HTTP URL、引用类型 | anchor、模板/DOM 位置 |
| Mixed Content | HTTPS page URL、HTTP resource URL、资源类型或 unavailable | source location |
| HTML 页面集 | page URL、状态码、HTML 类型、总行数/抽样范围 | canonical、indexability |
| 主域名一致性 | 内部链接的 source/target、canonical source/target、sitemap URL 与位置 | 缺哪份记录哪份，不声称全部检查 |
| Live check | test URL、时间、每一跳 URL/状态码/Location、final URL、最终状态码、错误类别 | MIME、TLS 结果、资源等价性判断 |

请求失败使用明确 error_kind：timeout / dns / tls / blocked / rate_limited / loop / budget / unavailable。429 记录来源（网站或 MCP）、状态码、Retry-After 和受影响范围；工具错误不伪造成网站响应。成功返回 200 也需判断是否对应页面/资源。保留路径和 query，不擅自删掉参数。跨域跳转记录后停止，除非该 host 在 scope 中。HTTP 状态为 crawl 证据时记录其时间，不冒充 live 检测。

9.3 默认只检查 HTTPS www/non-www 首页，记录 chain、final response、content_match 与主体依据。两个正常首页显示相同主体内容即 Pass，允许两者未统一 URL；不同内容或错误目标为 Issue。错误页、验证码和相同标题不能证明通过。实际取不到页面时为 Human Check，网络中断仍按整次失败规则处理。范围与请求间隔来自 config，默认 homepage／3 秒；不要因存在内页导出就扩大检查。

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
  9.1-9.3_{site name}_https_audit_{YYYY-MM-DD}.xlsx
  handover.md          current state, coverage, next action
  sf-handover.json     optional shared preparation record or reference
```

run_id 用安全的站点标识与时间/随机后缀生成，不覆盖旧 run。raw 保留完整证据；聊天仅返回行数和少量样本。缓存 key 包括 crawl ID、工具、filter/category、字段集合、版本；live key 包括 URL、请求方式及必要请求头配置，不缓存凭据。crawl 改变或显式 force_refresh 时失效。

## findings.json：报表生成器输入

```json
{
  "overview": [
    {"check":"9.1","result":"Issue","findings":"发现 HTTP 页面，返回 200。","instructions":"为该页面设置 HTTPS 跳转。"},
    {"check":"9.2","result":"Pass","findings":"所提供样本中未发现 Mixed Content。","instructions":"无需处理。"},
    {"check":"9.3","result":"Human Check","findings":"首页返回 403，无法确认跳转后的内容。","instructions":"用浏览器打开首页，确认跳转后的内容。"}
  ],
  "http": [
    {"address":"http://example.com/a/","issue":"http-200","issue_description":"HTTP 页面返回 200。","suggestion":"将此页面跳转到已验证的 HTTPS 地址。"}
  ],
  "mixed": [],
  "hostname": [
    {"test_url":"https://example.com/","expected_url":"https://www.example.com/","issue":"human-check:403","issue_description":"首页返回 403，内容未能确认。","suggestion":"用浏览器打开首页，确认跳转后的内容。"}
  ]
}
```

Checklist 必须提供文字 findings 与 instructions，不能写数字计数；旧 coverage 不再必需也不输出，旧输入需根据实际证据补写两句简短文字。范围／数量保留在 manifest/handover。

http 行键：address, issue, issue_description, suggestion；可选 related_url 保留有证据的引用页面或目标 URL。
mixed 行键：page_address, resource_url, issue, issue_description, suggestion。
hostname 行键：test_url, expected_url, issue, issue_description, suggestion。
issue 是内部分类/去重代码；issue_description 映射为 Findings，suggestion 映射为 Instructions。每项一句简单的话；Instructions 直接说明人要做的事，无问题写「无需处理」。生成器自动加 Issue Type，并将三类合并到 `9. Implement HTTPS Protocol`。

只有具体未解决的检查才用 issue 前缀 `human-check:`（兼容 `review:`）。有确认问题及此类行时 Checklist 写 Issue，显示 X + Human Check。仅有具体未解决行时写 Human Check。无具体行的 Human Check 输入会被拒绝，生成器不再自动添加占位行。9.1/9.2 样本内零记录写 Pass、空数组；不因没有全站覆盖证明而补查。已提供的问题行缺字段仍需说明，不能删行伪造零问题。文件无法读取／解析则报错；网络中断遵循整次失败重跑规则。

overview.check 在内部 JSON 中保留 9.1／9.2／9.3 编号；生成器将编号和固定名称分别写入 Item No. 与 Item Name；结果写入 Initial Check。

此 JSON 是 agent 判断后的结果，不是把原始 SF CSV 直接改名；build_report.py 只验证并渲染，不自动执行 MCP/crawl/网络检查。

共享 skill 的 sf-handover.json 只记录配置/用户确认/文件交接，不是 findings.json，也不能直接传给报表生成器。各检查的证据完整性仍由本 skill 按实际文件验证。
