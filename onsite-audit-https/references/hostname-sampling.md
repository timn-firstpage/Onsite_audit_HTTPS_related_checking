# WWW / non-WWW：首页与已观察配对

## 选择范围

从实际 site.start_url 提取 hostname，只增减最前面的 www.，生成 HTTPS 首页的两个地址。不写死域名、不预设 www 为首选。其他子域名、不同注册域名、相似名称／标题不自动归组。

内页只从主 crawl 的 HTML URL 找配对：去掉 leading www. 和 fragment 后，base hostname、port、path 与 exact query 相同，且两侧实际出现。保留已观察 URL 的协议；不为只有一侧的内页生成另一个版本，不全量生成 HTTP/HTTPS 四版本。相同 title/H1 仅作内容线索。不同路径的潜在重复页属于另一个重复内容检查，不能擅自扩大此项。

hostname_page_limit=null 表示首页 + 全部已观察 pairs。正整数限制已观察内页 pairs，首页保留；未选部分写 Coverage。不声称首页通过代表所有内页通过，也不把未出现的 www 地址视为不存在。显式 allowed_hosts 限制仍需遵守；若缺少对应 host 许可则记录 Human Check，不偷偷扩大 scope。

主 crawl URL inventory 缺失／截断时，可以先检查首页，但不能把“没有资料”当作“已观察到零内页 pairs”；在最终报告记录 inventory 缺口及 Human Check。如果用户明确指定 preferred_origin，核对跳转是否符合该选择；未指定时依据实际统一目标，不写死方向。

## Python 执行

先复用足够的已有响应、跳转链、内容资料；缺少当前证据时使用包内 check_hostname_pairs.py。Agent 将 SF 实际 Address/Content Type 字段映射为 normalized-pages.json：

```json
[
  {"url":"https://example.org/service/","content_type":"text/html"},
  {"url":"https://www.example.org/service/","content_type":"text/html"}
]
```

example.org 仅说明结构，实际输入全部来自本次网站。脚本不直接猜 SF CSV 的本地化字段，也不把非 HTML 资源当内页。

```text
python scripts/check_hostname_pairs.py --config <run>/config.json --pages <run>/normalized-pages.json --run-dir <run>
```

这里的 scripts 路径相对于安装的 HTTPS skill；解释器来自实际 AUDIT_PYTHON/venv。使用整合任务同一 run/usage.json，不新建预算绕过累计限制。输出 hostname-observations.json 是证据，不是可直接交给 build_report.py 的 findings.json。

逐跳 GET，不自动跟随不可见的 redirect；保存 URL、状态码、Location、最终地址、Retry-After、主体 hash/有限片段及 checked_at。显式 scope 限制跨 host；单跳请求、redirect 请求都计入 max_live_requests。重复 URL 响应在本次执行内缓存。默认每秒至多 1 个直接请求；无 paid API。正文读取最多 1 MiB，截断内容标 Human Check，不存整站 HTML。循环被记录；达到跳数上限不是已证明循环。

遵守 live_checks=false，不做网络请求但输出各 pair 的 human_check observation。429 后停止新的网络请求并保留 Retry-After；达到非网络内容错误／budget 限制时剩余 pair 写 Human Check，不自动扩容／立即重试。网络／连接失败、超时、DNS/TLS 错误或响应读取中断立即 raise error，停止整个审核；脚本写 run-status.json（failed）及 error.log，保留 usage，不自动重试／续跑、不生成 observations 或最终 Excel，要求用户检查连接后在新 run 目录重新运行整个 skill。403/429 等实际 HTTP 响应不属于这类中断。其他证据缺口允许有遗漏的最终 Excel；Coverage 写完成、未完成和选取范围。

## 内容与判断

脚本忽略脚本、样式及常见导航／页眉页脚，优先提取 main；保留 title/H1 作辅助。足够的静态正文完全相同是 identical 线索；不同文字不必然代表不同页面，agent 须排除时间、cookie、个性化等变化。少于 80 字符、JS 空壳、403/429、错误响应或无法确定目的时写 Human Check。静态文本阈值只是自动证据边界，不是 SEO 质量门槛。所存内容不能保证代表浏览器最终渲染。

| 观察 | Agent 决策 |
| --- | --- |
| 最终地址统一、页面可用且内容对应原页面 | Pass / √ |
| 两个有效地址独立返回相同主体内容，没有统一 redirect | Issue / X；列出两个 URL、实际响应和重复证据，建议选定首选地址后永久重定向 |
| 没有统一 redirect 且内容不同 | Issue / X：域名／内容不一致；不能称为重复内容 |
| 统一到错误内容、错误 host 或内页被兜底到首页 | Issue / X：目标不对应 |
| 证据不够、HTTP 错误响应、预算／hop 上限、动态内容不明确 | Human Check；最终 Excel 写原因及人工动作 |

自动 observation 不直接证明 Pass。Agent 对照主 crawl 的 intended page 内容／实体／title/H1，排除两侧都跳错首页、软 404、验证码／登录页和模板正文相同等情况。合法路径变化和多跳本身不报问题。canonical 可以说明合并信号，但不代替本项要求的统一跳转；不声称 Google 已收录／排名两次或发生 ranking 蚕食。

## 只补无法判断的内容

需要浏览器／SF 渲染时只列缺口 URL，不要求全部 pairs 再跑 SF。已有证据直接复用；新的 SF List 补查须允许 allow_hostname_list_crawl，并通过共享 skill 准备、由用户手动运行。此设置不控制 Python direct checks，也不授权 agent 自动启动 SF。保留主 security crawl，不重新加载通用配置覆盖用户 sitemap。

除致命网络中断外，最终 Excel 不等待人工补查：每个缺口写 Human Check 和核查动作。人补证据后在新 run 更新结果，不静默覆盖已交付文件。
