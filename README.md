# Onsite Audit HTTPS Related Checking

可移植的 HTTPS 审核 skill，供本机 **Codex、Claude Code、Cursor** 使用。基于 Screaming Frog 官方内置 MCP 或现有导出资料，检查 HTTP URLs、Mixed Content、www/non-www，并交付精简 Excel。每台电脑自己填写本地路径与 MCP 地址；仓库不绑定作者电脑。

## 输出

| Sheet | Columns |
| --- | --- |
| 9.1 HTTPS VS HTTP | Address · Issue / Suggestion |
| 9.2 HTTPS Mixed Content | Page Address · HTTP Resource URL · Issue / Suggestion |
| 9.3 WWW VS NON-WWW | Test URL · Expected URL · Issue / Suggestion |

只输出问题或待确认行，不建空明细 sheet。Overview 保留结果、数量和范围，区分 Pass / Issue / Needs Review / Not Tested。建议根据实际响应生成，不机械重复 “change to HTTPS”。www/non-www 的目标由 preferred_origin 决定，301 和 308 均可通过。

## 文件导航

- [SKILL.md](onsite-audit-https/SKILL.md)：短入口，按需加载参考资料。
- [config.template.json](onsite-audit-https/config.template.json)：每次 run 的设置与预算，不是 Spider 原生 crawl config。
- [MCP 使用指南](onsite-audit-https/references/screaming-frog-mcp.md)：调用顺序、资料选择、文件导出、节约用量、待确认项。
- [数据与归档要求](onsite-audit-https/references/data-contract.md)：必须包含的证据、完整性、run 文件结构。
- [客户端配置指南](config/SETUP.md)：跨 agent 安装与 MCP 注册。
- `scripts/install-skills.ps1`：Windows 全局共享链接，支持传入其他 skill 路径。
- `scripts/install-skills.sh`：macOS/Linux 共享链接，无需 PowerShell。
- `scripts/setup-mac.sh`：Mac Python 检查、venv、依赖安装、自检及本机配置。
- `scripts/make-mcp-config.py`：从本机实际 URL 生成三个客户端配置片段。
- `onsite-audit-https/scripts/build_report.py`：从已判断的 findings.json 生成并验证 Excel，不联网。

## 换电脑安装

先确认该机 SSH GitHub 访问。Windows：

```powershell
git clone git@github.com:timn-firstpage/Onsite_audit_HTTPS_related_checking.git
Set-Location Onsite_audit_HTTPS_related_checking
powershell -NoProfile -File scripts/install-skills.ps1
```

脚本自动发现当前用户目录、仓库位置，不写死用户名/盘符。使用 junction 让 repo 保持唯一源，Codex/Cursor 从用户级 `.agents/skills` 发现，Claude Code 从 `.claude/skills` 发现。已有同名非本仓库链接会停止，保留原文件。移动 repo 后需重新连接，不能删掉 repo 却保留链接。

创建 Python 环境时选择本机解释器；裸 `python` 不能运行就用该机实际绝对路径，禁止复制另一台电脑的路径：

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe onsite-audit-https/scripts/test_report.py
```

macOS/Linux 使用相同 skill 与配置模板，执行：

```bash
git clone git@github.com:timn-firstpage/Onsite_audit_HTTPS_related_checking.git
cd Onsite_audit_HTTPS_related_checking
bash scripts/install-skills.sh
bash scripts/setup-mac.sh
```

Mac 脚本使用 symlink，不使用 Windows junction。若已 clone，先在 repo 执行 `git pull`。Windows 的 SSH key 不会自动搬到 Mac；该机需自己的 GitHub SSH 授权。不要复制 Windows `.venv`、MCP 本地配置或绝对路径。Mac 端安装自己的 SF 并启用 MCP；Python 报表工具不依赖 CPU 架构专用 Windows 程序。

`setup-mac.sh` 检查 Python 3.9+，没有时使用已安装的 Homebrew 执行 `brew install python`；没有 Homebrew 时提供官方 Python 安装入口，安装后重跑。它不自动安装 Homebrew，不覆盖系统 Python，也不把 Python 包装到全局环境。成功后生成 ignored 的 `config/python.local.json`，并显示需要填入 Multica agent 环境变量 `AUDIT_PYTHON` 的本机路径。

自定义路径通过 `AUDIT_BOOTSTRAP_PYTHON`、`AUDIT_VENV_DIR`、`AUDIT_LOCAL_CONFIG_DIR` 提供；默认位置根据当前 repo 推导，不含机器用户名。Python config 与 SF MCP config 分开，脚本不会替你注册 MCP 或修改 Multica agent 设置。

## Multica 导入

入口文件名是 **SKILL.md**（单数），位于 `onsite-audit-https/` 子目录，repo 根目录没有入口文件。不要把整个仓库下载 ZIP 当成单个 skill 包。

URL 导入请用：https://github.com/timn-firstpage/Onsite_audit_HTTPS_related_checking/blob/main/onsite-audit-https/SKILL.md

如果 URL 导入提示找不到入口，改用 Skills → New skill → Import from local，上传 [dist/onsite-audit-https.zip](dist/onsite-audit-https.zip)。这个包的根目录直接包含 SKILL.md、references、scripts、配置模板和依赖说明。也可选择本地 clone 的 `onsite-audit-https` 文件夹，不能选它的上层 repo 文件夹。

打包更新（Mac）：

```bash
.venv/bin/python scripts/package-skill.py --output dist/onsite-audit-https.zip
```

ZIP 已检查入口和文件完整性，但尚未在你的 Multica 实例内实际导入。导入后确认 supporting files 均存在，并绑定测试 agent。ZIP 导入版本更新需要重新导入，不能自动从 GitHub refresh。官方导入说明：https://multica.ai/docs/skills

**Multica 可以执行包内 Python 脚本，但不会因为导入就拥有 Python 环境。** Agent 必须绑定已安装 Python/openpyxl 的实际执行 runtime；你的测试场景就是那台 Mac。Windows 的 Python 不会随 ZIP 搬过去。

Mac 的安装、自检和 agent 环境变量配置见 [Python runtime 指南](onsite-audit-https/references/runtime-python.md)。先从 Multica agent 的 shell 验证解释器和 openpyxl，再测试 SF MCP。仅在个人 Terminal 运行成功不足以证明 runtime 可用。

## MCP 配置

只使用官方内置 MCP。需要支持 MCP 的付费版 SEO Spider 和 database mode，在软件里启用 HTTP server。复制软件显示的**真实 URL**；不要默认沿用别的电脑端口。详细命令见 [SETUP.md](config/SETUP.md)。安装 skill 与配置 MCP 是两件事，安装成功不代表 MCP 已连接。

```powershell
.venv/Scripts/python.exe scripts/make-mcp-config.py --url "$env:SCREAMING_FROG_MCP_URL" --output-dir config/generated
```

先在本机设置 `SCREAMING_FROG_MCP_URL`。生成文件是 ignored 的 `.local.*` 片段，按 SETUP 合并到客户端；脚本不会覆盖全局配置。没有 URL 时不要运行/注册。无需安装第三方 MCP server。

Mac 在 SF 启动 HTTP server 后，用以下命令输入其真实 URL 并生成配置：

```bash
printf 'Paste the MCP URL shown by this Mac\047s Screaming Frog: '
read -r SCREAMING_FROG_MCP_URL
export SCREAMING_FROG_MCP_URL
.venv/bin/python scripts/make-mcp-config.py --url "$SCREAMING_FROG_MCP_URL" --output-dir config/generated
```

这不会修改客户端全局设置；继续按 SETUP 注册，SF 存档目录使用 Mac 端实际 allowed base。

## 运行

在 repo 内或用户指定的数据目录创建唯一 run；将模板复制到 run/config.json，填写：

- `site.start_url`、`site.preferred_origin`、`site.allowed_hosts`。
- 已完成的 `source.crawl_id` 或 `source.export_directory`。
- 本机 MCP URL 与 allowed base directory；用导出文件时可保持 null。
- run root、报告语言和需要的 budgets。

示例请求：

> 使用 onsite-audit-https，按这个 run/config.json 检查 HTTPS，复用已完成的 crawl，输出精简 Excel；先将完整资料存本地，聊天只返回计数和最多 5 条样本。

Codex 可显式 `$onsite-audit-https`；Claude Code 和 Cursor 可从 `/` 技能列表选择。找不到时新开会话/重新加载客户端并检查安装路径。当前已打开会话不保证热加载。

Agent 将实际工具返回映射为归一化数据、完成检查、写 findings.json，然后：

```powershell
.venv/Scripts/python.exe onsite-audit-https/scripts/build_report.py --input <run-directory>/findings.json --output <run-directory>/final.xlsx
```

`<run-directory>` 是说明占位符，调用时换成本机路径。报告生成器拒绝覆盖已有文件，更新既有 workbook 时使用合适的 spreadsheet 编辑工具。此仓库是 skill + 配置/归档约定 + 本地报表工具，**不是独立一键 crawler**；MCP 调用和证据判断由当前 agent 执行。

Mac 的报表命令用 `.venv/bin/python` 替代 `.venv/Scripts/python.exe`；其他参数和输出格式一致。run root 请使用可写的 Mac 目录，不能沿用 Windows 盘符。

## Token / credits 设计

1. 默认复用 crawl，不自动启动新 crawl；同一批导出只拉一次。
2. 完整资料导出到文件；只把计数、缺失字段和少量实例送进上下文。
3. 预算在 config 中可调，默认 30 MCP calls、200 live requests；URL 请求、redirect hops 和 retries 都计入预算。到限保存 checkpoint 并标记未完成，不暗中增加用量。
4. 默认付费第三方 API calls 为 0；这三个检查不需要 Ahrefs、AI prompts 或 embedding。关闭已有 crawl config 中的相关 integration 才能落实此限制。
5. 表格渲染、去重和复核在本机执行，不发起 LLM API 请求。真实客户端 token/订阅用量仍由客户端计费，不能承诺固定节省百分比。
6. 多个 agent 共用一个 Spider 时，串行加载/导出；其他 agent 读同一个 run 的归档文件，避免重复 crawl 和上下文。

这些预算是 skill 的执行约束，当前没有独立 MCP proxy 强制扣减；执行 agent 必须记录 usage.json 并在每次调用前检查预算。不能将配置数字当作服务端硬限额。

## 验证与当前限制

离线测试覆盖 URL/query 保留、去重、共享资源关联、缺资料拒绝、false Pass 拒绝、公式注入防护与禁止覆盖。技能 frontmatter 已用 skill-creator validator 验证。

目前实际报表测试在 Windows 完成；Mac 安装脚本经过 Bash 语法检查，真实 macOS 安装、客户端发现和 SF MCP 连通性仍需在测试机确认。

**待本机确认 / remarks：** MCP licence、版本、数据库模式、server URL、allowed base、live tools schema、filter/category/field 名称、实际 crawl ID、动态渲染覆盖。尚未完成真实 Screaming Frog MCP → crawl → Excel 端到端测试，不能把示例调用当成 live 验证结果。第一次测试先做 1 个 crawl、少量页面，并在本机保存 tools schema 和 manifest；成功后再扩大范围。

用户级技能只覆盖该用户的本地客户端及具有对应文件访问权的 agents。Cloud/远程/另一位用户不自动继承本机文件或 MCP，需在对应环境另行安装配置。Cursor 兼容发现多个目录，若 UI 显示重复同名技能，显式选择该源并按客户端设置处理；不再建第三份副本。

## 官方资料

- [Screaming Frog MCP 与 API](https://www.screamingfrog.co.uk/seo-spider/user-guide/configuration/#mcp-server)
- [Codex skills](https://developers.openai.com/codex/skills) / [MCP](https://developers.openai.com/codex/mcp)
- [Claude Code skills](https://code.claude.com/docs/en/skills) / [MCP](https://code.claude.com/docs/en/mcp)
- [Cursor skills](https://cursor.com/help/customization/skills) / [MCP](https://cursor.com/docs/mcp)
- [Google redirects](https://developers.google.com/search/docs/crawling-indexing/301-redirects)
