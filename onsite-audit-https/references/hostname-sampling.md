# 9.3 首页检查

默认只生成实际域名的 HTTPS www／non-www 两个首页地址，不依赖 HTML URL 导出，不查内页。域名来自 config，不能写死。Python 使用标准库。

```bash
python scripts/check_hostname_pairs.py --config <run>/config.json --run-dir <run>
```

在独立 skill 根目录运行，使用当前机器的 Python。仓库根目录运行时脚本路径为 onsite-audit-https/scripts/check_hostname_pairs.py。

- `checks.hostname_scope`: 默认 `homepage`。
- `checks.hostname_request_interval_seconds`: 默认 3 秒，串行请求，包含每一跳。与 SF 的 5 URLs/s 独立。
- 不与 SF 爬取或其他 agent 的网站请求同时运行。已有足够证据就复用，同一目标只请求一次。
- 若用户明确要求内页，设置 `hostname_scope=observed_pairs` 并传 `--pages <pages.json>`。列表字段为 url/content_type；只选实际已出现的 www/non-www 配对。hostname_page_limit 仅用于该可选范围。

两个地址显示相同的正常首页即 √，允许统一跳转，也允许两个地址分别提供相同主体内容。不要因为后者未统一 URL 而判 X。页面主体不同或明确跳错目标为 X；共同错误页、验证码、只有 title/H1 相同或空 JS 页面不能证明通过。脚本收集链、状态码与主体内容并输出 hostname-observations.json，agent 作最终判断。静态文字存在合理差异时判断页面内容，不机械比较 HTML hash。

429 后停止新请求，保留 Retry-After。不立即重试；Instructions 写「等待限流解除后，重新运行 9.3。」仍取不到页面时标 Human Check，不能伪装 √ 或网站缺陷 X。预算／403／内容不足也说明具体原因。慢速不能保证服务器永不限流。

网络连接失败、超时、DNS/TLS 错误或中断读取时立即报错，写 failed run-status.json 和 error.log，要求用户在新 run 目录重跑整个 skill，不自动重试，不交付最终 Excel。所有直接请求及跳转计入预算。
