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

9.3 的 source URL 保留原路径/query 用于生成测试地址，最终 URL 允许合法路径变化；不能用 final URL 字符串不相等直接判错。归档 content_match（true/false/unknown）及简短依据，例如对应产品标识、服务名称、title/H1/主体内容。证据不足时 unknown → Needs Review。non-www 最终跳到有效且内容对应的 www 页面就是 Pass；跳转状态码或次数本身不产生问题行。HTTPS 和其他 canonical/link 信号不作为此 hostname 检查的额外门槛。

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
    {"check":"9.2","result":"Not Tested","coverage":"未提供 mixed content export"},
    {"check":"9.3","result":"Not Tested","coverage":"尚未配置 preferred origin"}
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
不确定行用 issue 前缀 `review:`；在 issue_description 写明尚未验证的部分，suggestion 写具体核验动作。有确定问题且同时有未完成检测时总览可写 Issue，但 coverage 必须包含未完成范围。

此 JSON 是 agent 判断后的结果，不是把原始 SF CSV 直接改名；build_report.py 只验证并渲染，不自动执行 MCP/crawl/网络检查。

共享 skill 的 sf-handover.json 只记录配置/用户确认/文件交接，不是 findings.json，也不能直接传给报表生成器。各检查的证据完整性仍由本 skill 按实际文件验证。
