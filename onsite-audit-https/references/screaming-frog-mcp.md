# 官方 Screaming Frog MCP 使用指南

核对日期：2026-10-05。仅使用 SEO Spider 内置 MCP，不安装第三方 bridge。官方配置事实与 API 以 [MCP 文档](https://www.screamingfrog.co.uk/seo-spider/user-guide/configuration/#mcp-server) 和本机 `MCP > Configure > View Tools` 为准。以下调用是官方工具的示例；本仓库尚未连接真实 crawl 做端到端验证。

## 连接准备

需要支持 MCP 的付费版 SEO Spider、database storage。推荐在本机 UI 启动 HTTP server，复制软件实际显示的 URL 到 local config；不要把示例端口当作保证。三个客户端分别注册同一 URL。每台电脑填写自己的地址、存储根目录和解释器路径。Node 能力仅在需要服务端脚本时开启；本地 Python 可完成数据加工。

共享同一 Spider 实例时串行处理 crawl：一次只让一个 agent 负责加载/导出，其他 agent 使用归档文件。并行 load 会切换当前 crawl，导致数据串站。不同电脑必须各自安装/启用 server；localhost 永远指当前机器，不代表原电脑。

## 调用顺序

1. 用 MCP client 的 tools/list 或客户端工具目录取得真实 schema，存为本地 tools schema 快照；不需要把整份工具清单塞进聊天。SF UI 也可以导出 Markdown API。记录版本，只查本流程使用的工具。
2. 已给 crawl ID 时直接加载；否则 `sf_list_crawls({"limit":3})`，确认站点与时间后 `sf_load_crawl({"crawl_id":"<selected-id>"})`。不要默认用最近那个 crawl。
3. `sf_crawl_progress({})` 确认状态。未完成的数据可做 interim report，不能判全站 Pass。没有合适证据时按 [共享配置前提](sf-shared-config.md) 准备；source.allow_new_crawl 只控制是否可请求全站补爬，用户在 UI 确认 sitemap 并手动启动。agent 不调用 crawl-start，也不以 sf_crawl 的 config_path 加载配置。已有合适导出不要求 MCP 或历史配置全部可见。
4. 查询 `sf_list_available_filters_for_seo_element`、`sf_list_available_bulk_exports`、`sf_list_available_reports`，按 live schema 传入参数。保存返回的 Security filter、所需 bulk category 和字段名称映射。名称、大小写、语言差异都以返回值为准，不试猜十几个 category。
5. 按下表导出所需资料；总是传 file_path，完整数据落文件。返回聊天仅路径、行数、缺字段、少量预览。确认目录属于 SF allowed base，路径使用其相对格式。
6. 本地归一化与检测，写 findings.json，再生成 Excel。某 URL 未在 loaded crawl 中，不要用 `sf_url_info` 的缺失结果当成实时 404；需要受预算约束的 live 请求或按共享流程准备的用户手动 List 补爬。原生配置加载失败立即给手动 Load + sitemap 指引，不重复尝试 native control。

## Pull 什么资料

| 用途 | 拉取资料 | 策略 |
| --- | --- | --- |
| 9.1 | Security HTTP URLs + HTTP URLs Inlinks | 先 issue 列表；有结果才导出引用详情 |
| 9.2 | Security Mixed Content + 对应 bulk export | bulk 中要有 page/resource 配对，不只 HTML 页面列表 |
| 9.3 | HTML 页面 URL/状态、canonical、相关内部链接与 sitemap URL | 先重用已有 export；只取所需字段，避免全站 HTML 内容 |
| 细节补查 | 单个 URL 的 info/links | 只补缺失证据，不逐 URL 重拉已导出的资料 |

9.3 hostname 验证以最终 host 和对应内容为准。优先复用页面 title/H1/实体标识，只在无法确定对应内容时获取少量主体片段。路径不同或多次跳转不产生问题行；没有内容证据不能只靠 URL/200 判 Pass。不要为这个检查额外全量拉取 canonical/links/sitemap 并把它们设为通过门槛。

返回证据必须满足 [data-contract.md](data-contract.md)。工具原始返回不一定有 completeness/hash/count；在本地加工后补入 manifest，不能要求 API 返回其不支持的字段。

### 导出示例

以下 `$...` 是从 live 目录/配置读出的变量，不是提交给 server 的字符串。根据实际 schema 构造 JSON，不能原样提交占位符。

```text
sf_export_seo_element_urls({
  "seo_element_name": "Security",
  "filter_name": $httpFilter,
  "file_path": $relativeOutputPath,
  "data_fields": $verifiedFieldNames
})

sf_generate_bulk_export({
  "category": $mixedContentCategory,
  "file_path": $relativeOutputPath,
  "data_fields": $verifiedFieldNames,
  "export_type": "CSV"
})

sf_url_info({"url": $oneUrl, "file_path": $relativeOutputPath})
```

先核对所需参数；官方文档中的 `page_content_type` 等参数在不同版本可能存在，live schema 若要求则填对应枚举。不为了满足示例而开启整站 page content 导出。列表工具获得 field/category 后只发现一次，复用到本 run。

有分页参数时：完整导出所有页到本地，每页独立文件；start_index、实际数量和完整性记入 manifest。max_preview_rows 只限制聊天预览，不能限制实际报告证据。预算导致提前停下必须记录未完成数量。

## 节省 token 与 API credits

- 每站点一个 run，复用同 crawl 的 raw exports；agent 交接读取 handover + manifest + counts。
- 仅 security 数据和相关 URL 元数据；不导出整站正文、截图、embedding。
- 批量导出后用本地脚本筛选/计数/去重；不要让模型逐行读取 thousands of URLs。
- 所有数值预算来自 config。达到 MCP/live request/poll budget 时存 checkpoint 和 Needs Review，不自动扩容。
- live 检查按唯一 URL 去重，同一 HTTP 图片在 50 页出现只请求一次；Excel 仍保留 50 个 page/resource pair。
- budget 默认 max_paid_api_calls=0；本任务不调用 Ahrefs、PSI、OpenAI/Anthropic prompts 等附加 integrations，不为读取既有结果修改其他任务的配置。本地 MCP 不等于免费 AI：客户端 token/订阅、SF licence 和第三方 API 成本分别计算。具体费用以实际产品账单为准。
- Poll 只在状态确有必要时调用，间隔由配置指定；到 max_poll_calls 后保存待继续状态，避免不断询问进度。

## 换电脑后要核对的 remarks

以下为需要相应能力时的连接/证据核对项，不是读取已有文件的全局门槛。配置准备归共享 skill；历史设置 unknown 只在影响当前检查证据时记录具体缺口。

- licence 有效、MCP 支持版本、database mode、资源 Store/Crawl 设置。
- HTTP URL 与 allowed base directory 是该机的真实值；不要从另一台复制绝对路径。
- live tool schema、filter/category/data_fields 是否与示例一致。
- JavaScript rendering 是否需要，当前 crawl 是否完整、存档是否仍可访问。
- 三个客户端各自 tools/list 成功。能打开 URL 不等于 MCP handshake 成功。
- 本仓库不提供未验证的 stdio 启动参数；需要 stdio 时使用官方扩展/本机导出的设置。
