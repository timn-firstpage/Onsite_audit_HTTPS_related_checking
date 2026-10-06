# WWW / non-WWW：SF 批量验证与可选采样

## 数量与范围

默认 executor 为 screaming_frog，checks.hostname_page_limit 为 null：检查现有 crawl 中所有符合范围的不同 HTML 页面，不自动截取 20 条。只有显式设置正整数时才采样；例如 20 指 20 个不同页面，不是 20 个 HTTP 请求。采样时按页面类型挑选代表样本，包括首页与存在的分类、产品/服务、文章、语言版本页面。记录选择清单与原 crawl 是否完整。

没有固定 20 页上限，例如 crawl 有 100 个合适页面就生成最多 400 个测试起点。批量由 SF 抓取、完整导出后用脚本分析，聊天只接收异常摘要。脚本不能替未抓取的四版本生成实际响应证据。max_live_requests 限制 agent/Python 的直接网络请求，不作为 SF 已授权 list crawl 的页面数限制；MCP call 与 poll 预算仍需遵守，超限记录 checkpoint，不缩成 20 页冒充完成。

每个样本生成 HTTP/HTTPS × www/non-www 四个版本，保留源路径/query。20 个页面最多 80 个唯一起点，重定向目标可能增加实际请求数。四个版本一起构成一个页面的验证组。此 sample 只用于 9.3，不能替代 9.1/9.2 的全站 security crawl。

## 用 Screaming Frog 做

1. 保存原全站 crawl 及其 ID，避免丢失 security 证据。
2. 将四版本测试列表存档。复用合适的既有结果；不足时按 [共享配置前提](sf-shared-config.md) 准备独立的 **List Mode**，由用户上传列表。
3. 指引用户确认 **Always Follow Redirects** 并手动 Start、监督检测；保存 checkpoint，用户完成后继续，不持续轮询等待。
4. 导出 **All Redirects**，保留每个起点的 Final Address、最终状态和跳转链。
5. 获取最终页面对应内容的证据；复用现有 title/H1/主体内容标识，不足时只补少量必要片段。SF 的 final 200 本身不能证明内容对应。

checks.allow_hostname_list_crawl 控制是否可请求本项定向补爬，source.allow_new_crawl 控制是否可请求一般全站补爬；两者均不授权 agent 自动启动。为 false 时保留已有证据，说明缺口和下一步，不绕过配置改用自动爬虫。批量大小、速度与 crawl 范围按本机 SF/任务配置执行；不是无限发现新页面。大型列表可分批，但批次不能变成未声明的总量上限，Coverage 汇总各批次及未完成范围。若复用完整 list 结果，则不重新抓同批地址。此 List 检查无需重新要求全站 sitemap；不要覆盖用户主 crawl 的 sitemap 设置。

官方流程：[Screaming Frog redirects audit](https://www.screamingfrog.co.uk/seo-spider/tutorials/audit-redirects/)。

## 通过标准

四个版本收敛到同一个可用的选定 HTTPS 页面，non-www 跳到了选定主域名，且内容是该样本对应的内容 → 通过（用户的 flag √）。允许目标路径变化、多次跳转；不因为跳转状态码类型而单独判失败。

没有跳转、最终地址不同/错误 hostname、跳到错误内容或首页、循环、目标不可访问 → 失败（X + 具体原因）。两个域名各自返回 200、即使内容一样，也不是统一跳转到同一目标。

canonical、内部链接、sitemap 可以辅助判断，但不作为这个 item 的额外通过门槛。超时、截断或无法确定内容对应 → 待确认，不直接给 √。

## MCP 与报告

用户在 SF UI 上传列表并启动；即使 MCP 提供 start 工具，本手动运行流程也不调用它。完成后通过 MCP 按正确 ID 加载并导出，或读取用户保存的必需导出文件。`sf_crawl` 只传 start URL 不等于上传 80 个 URL；禁止虚构 list API。保存的二进制 crawl 需 SF 成功加载，不能单凭文件存在判可用。

Coverage 写实际样本页数、版本数和未完成范围，例如：`抽样 20 页，检测 80 个版本；19 页统一到对应 HTTPS 页面，1 页跳到首页。` 通过仅代表这些样本，不能标全站通过。资料全部落本地，聊天只展示计数与少量异常。参数/预算从 run config 读取。
