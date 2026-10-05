# WWW / non-WWW：约 20 页的 SF 验证

## 数量与范围

checks.hostname_page_limit 默认 20，指 **20 个不同页面**，不是 20 个 HTTP 请求。按页面类型挑选代表样本：包括首页，及存在的分类、产品/服务、文章、语言版本页面；不足 20 页则测全部。记录实际选择清单。

20 是可调默认值，不是 SF 或代码的固定上限；需要时可提高配置，例如 100 页生成最多 400 个测试起点，并按范围调整检测预算。批量抓取与完整导出后用脚本分析，聊天只接收异常摘要。脚本不能替未抓取的四版本生成实际响应证据。

每个样本生成 HTTP/HTTPS × www/non-www 四个版本，保留源路径/query。20 个页面最多 80 个唯一起点，重定向目标可能增加实际请求数。四个版本一起构成一个页面的验证组。此 sample 只用于 9.3，不能替代 9.1/9.2 的全站 security crawl。

## 用 Screaming Frog 做

1. 保存原全站 crawl 及其 ID，避免丢失 security 证据。
2. 将四版本测试列表存档，使用独立的 **List Mode** 上传。
3. 启用 **Always Follow Redirects**，等待检测完成。
4. 导出 **All Redirects**，保留每个起点的 Final Address、最终状态和跳转链。
5. 获取最终页面对应内容的证据；复用现有 title/H1/主体内容标识，不足时只补少量必要片段。SF 的 final 200 本身不能证明内容对应。

官方流程：[Screaming Frog redirects audit](https://www.screamingfrog.co.uk/seo-spider/tutorials/audit-redirects/)。

## 通过标准

四个版本收敛到同一个可用的选定 HTTPS 页面，non-www 跳到了选定主域名，且内容是该样本对应的内容 → 通过（用户的 flag √）。允许目标路径变化、多次跳转；不因为跳转状态码类型而单独判失败。

没有跳转、最终地址不同/错误 hostname、跳到错误内容或首页、循环、目标不可访问 → 失败（X + 具体原因）。两个域名各自返回 200、即使内容一样，也不是统一跳转到同一目标。

canonical、内部链接、sitemap 可以辅助判断，但不作为这个 item 的额外通过门槛。超时、截断或无法确定内容对应 → 待确认，不直接给 √。

## MCP 与报告

先查本机 live schema 是否提供 list upload/start；支持时使用其真实接口。不支持时用 SF UI 创建 List Mode crawl，再通过 MCP 按 ID 加载并导出。`sf_crawl` 只传 start URL 不等于上传 80 个 URL；禁止虚构 list API。

Coverage 写实际样本页数、版本数和未完成范围，例如：`抽样 20 页，检测 80 个版本；19 页统一到对应 HTTPS 页面，1 页跳到首页。` 通过仅代表这些样本，不能标全站通过。资料全部落本地，聊天只展示计数与少量异常。参数/预算从 run config 读取。
