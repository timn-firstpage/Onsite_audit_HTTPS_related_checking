# Onsite Audit HTTPS Related Checking

<p align="center"><img src="assets/onsite-audit-cover.png" alt="Onsite audit cover showing HTTPS security, website inspection, crawl connections, hostname redirects, and an audit report" width="640"></p>

可移植的 HTTPS 审核 skill，供本机 **Codex、Claude Code、Cursor** 使用。基于 Screaming Frog 官方内置 MCP 或现有导出资料，检查 HTTP URLs、Mixed Content、www/non-www，并交付精简 Excel。每台电脑自己填写本地路径与 MCP 地址；仓库不绑定作者电脑。

## 输出

**支持直接提供已爬好的 `.seospider` 文件**：使用 `source.mode=saved_crawl` 和 `source.crawl_file`，或直接提供文件让 agent 解析路径。复用匹配导出，必要时通过 SF 支持的功能打开一次，与其他 onsite audits 共用结果；不重载 global config、不自动重爬。没有 reader 时只要求用户打开已有 crawl 并导出指定结果。`.seospiderconfig` 是配置文件，不是 crawl。详见 [共用 saved-crawl 操作与报错说明](https://github.com/timn-firstpage/On-_site_SF_shared_config/blob/main/references/saved-crawl-entry.md)。HTTPS 原有“网络中断终止整次审计”规则保持不变。

Overview 的 **Check** 列必须包含编号和 item name：`9.1 HTTP vs HTTPS (Insecure Content Detected?) - Screaming Frog Insecure Content`、`9.2 Mixed Content`、`9.3 WWW vs non-WWW`，不能只显示编号；名称与编号放在同一列。

Overview 的列为 Check / Flag / Findings / Coverage：通过显示 **√**，发现问题显示 **X**；待确认或未检测显示 **Human Check**；已有问题同时有证据缺口显示 **X + Human Check**，不冒充通过。没有致命网络中断时，证据不足仍输出最终 Excel，在 Issue／Suggestion 写清缺口与人工核查动作。发现任何内部 HTTP URL 就 X（即使已转 HTTPS）；Mixed Content 检测完成后零条目 √，有条目 X。空/NaN/NA 若代表缺失资料，不能自动给 √。

文件名固定为 **`{site name}_https_audit_{date}.xlsx`**，日期格式 YYYY-MM-DD，例如 `Example_https_audit_2026-10-05.xlsx`。site name 从本次配置/用户提供的名称读取；缺失时使用不带 www 的站点 hostname。日期按用户时区解析或使用指定 audit_date，不由 Mac/Windows 系统日期擅自决定。同日重复运行使用不同 run 目录，不自动加后缀或覆盖旧报告。

| Sheet | Columns |
| --- | --- |
| 9.1 HTTPS VS HTTP | Address · Issue · Suggestion |
| 9.2 HTTPS Mixed Content | Page Address · HTTP Resource URL · Issue · Suggestion |
| 9.3 WWW VS NON-WWW | Test URL · Expected URL · Issue · Suggestion |

只输出确认问题或 Human Check 行，不建空明细 sheet。Overview 保留结果、数量和范围。www/non-www 默认用 Python 检查实际首页两个版本，以及主 crawl 中已经出现的内页配对；不预设 www 为首选，不为全部内页生成四版本。两个独立地址提供相同内容且没有统一重定向时，Issue 列出两个 URL 及证据，Suggestion 写选定首选地址后的合并动作。内容不同则说明域名／路由不一致，不冒称重复。没有致命网络中断时，证据不足照样交付最终文件并标 Human Check，不能声称两个 URL 已排名或排名被蚕食。HTTP／Mixed Content 仍独立基于主 crawl 检查。

## 9.1–9.3 逐项检查逻辑

本 skill 检查 HTTP URLs、Mixed Content 和 www/non-www；SF 配置、crawl 与运行环境可与 robots 检查共用。每项按实际证据独立判断，报告使用 **√ / X / Human Check**。

| Item | 怎么检查 | 结果判断 |
| --- | --- | --- |
| **9.1 HTTP vs HTTPS：是否发现内部 HTTP URL？** | 读取 **Security → HTTP URLs**，有结果时导出 **HTTP URLs Inlinks**，保留 HTTP 地址和引用页面。检查状态码、重定向链、最终 HTTPS 地址及对应内容；提出替换引用或修复跳转建议前，验证 HTTPS 目标是否可用。普通 HTTP 超链接不等于 Mixed Content。 | **√：**完整检测确认零内部 HTTP URL。**X：**发现任何内部 HTTP URL，即使已经正确跳到 HTTPS；正确跳转的地址建议更新引用，其他地址按实际响应说明问题与动作。**Human Check：**导出缺失／截断、范围不明确或所需证据不足；确认已有 HTTP 问题且同时有缺口时显示 **X + Human Check**。 |
| **9.2 Mixed Content：HTTPS 页面是否引用 HTTP 资源？** | 读取 **Security → Mixed Content** 及对应 bulk export，保留「HTTPS 页面 + HTTP 资源」配对和资源类型。验证资源的 HTTPS 版本是否可用且对应原资源；同一资源只验证一次，但保留所有受影响页面。需要时补充 JavaScript 渲染证据。 | **√：**完整检测确认零 Mixed Content 条目。**X：**存在已确认条目，即使该资源的 HTTPS 版本可用；按验证结果建议更新引用、修复或替换资源。**Human Check：**缺少 page/resource 配对、渲染覆盖或资源验证证据。空／NaN／NA 只有在确认完整导出为零结果时才可判 √，不能把缺资料当通过；已有问题与缺口并存显示 **X + Human Check**。 |
| **9.3 WWW vs non-WWW：是否统一到对应 HTTPS 页面？** | 当前默认用 Python 检查实际 HTTPS 首页的两个版本，以及主 crawl 中两侧都已出现的内页配对；配对须只相差 leading `www.`，path／query 相同。记录每一跳、最终地址和主体内容，核对页面用途，排除软 404、验证码及错误跳到首页。默认检查全部已观察 pairs，明确配置正整数才限制数量；不预设 www 为首选。 | **√：**已检查范围内，两侧统一到同一可用 HTTPS 页面，内容对应原页面且符合明确指定的首选 origin。**X：**跳错内容／host、内页跳到首页、确认循环，或两个有效地址未统一；相同内容写未合并问题，不同内容写域名／路由不一致。合法路径变化、多跳或临时跳转本身不单独判 X。**Human Check：**403／429、hop／预算上限、主体内容不足或动态内容无法确认；title／H1 相同或返回 200 不能独立证明通过。 |

**Coverage：**按页面和测试 URL 分别记录候选数量、实际完成数量、未检查数量及原因。9.3 当前范围是“首页 + 已观察 pairs”，未配对内页不在此范围内；首页通过不能代表全部内页通过。只查已观察 pairs 与“从全部 HTML 页面生成四版本，再跑 SF List Mode”是不同范围，后者目前尚未实现为默认流程。

**网络中断：**live 检查或 MCP 发生连接失败、超时、DNS/TLS 连接失败、断连或响应读取中断时，立即报错并停止整个审核，保存失败标记、错误日志与用量；要求用户检查连接后在新 run 目录重新运行整个 skill。不自动重试／续跑，不生成或交付本次最终 Excel。已收到的 HTTP 403／429 响应、普通证据缺口及预算上限仍按 Human Check 处理。

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

入口文件名是 **SKILL.md**（单数）。仓库根目录现在也提供入口供 Multica repository URL 导入；`onsite-audit-https/` 保留可独立安装的 skill 源文件。不要把整个仓库下载 ZIP 当成单个 skill 包。

URL 导入请用仓库地址：https://github.com/timn-firstpage/Onsite_audit_HTTPS_related_checking

仓库入口：[根目录 SKILL.md](SKILL.md)。它包含完整规则并引用子目录中的 supporting files，不是只有链接的空入口。运行 package-skill.py 时会从独立 skill 同步根目录入口并调整相对引用，避免两份规则分叉。

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

### SF 共享配置前提

新 crawl 的准备由独立 [sf-shared-config](https://github.com/timn-firstpage/On-_site_SF_shared_config) 负责，需单独安装；HTTPS 的安装脚本和 ZIP 不包含它。已有适用 crawl/导出时直接复用，先核对站点、时间、范围、完成状态和必需字段，不要求重新加载或证明全部历史设置。部分证据可用时只补缺口，不强制重爬全站。

没有适用数据时自动用 shared skill 的 main；可靠记录显示配置已加载且未变则跳过加载。你在 UI 确认网站与 sitemap，手动 Start 并监督，再保存/导出到实际 Downloads 并提供路径。native control 或独立加载失败立即提供手动 Load + sitemap 指引，不反复重试、不停留 pending，也不通过 sf_crawl(config_path) 偷启动。正在进行的 crawl 保留原样，返回下一步 checkpoint。HTTPS 与 robots 同一 SF 会话共享准备记录，不分别覆盖配置或重设 sitemap。

调用返回后仍检查实际数据；sf-handover.json 是交接记录，不是审核通过证明。429 区分网站与 MCP 来源，缺失数据不当作零问题。详见 [完整前提及交接边界](onsite-audit-https/references/sf-shared-config.md)。

需要你手动 Load 时，Agent 先将选定 `.seospiderconfig` 保存到 SF 电脑的实际 Downloads 并验证，再给该路径让你加载和检查 sitemap。同名不同内容不覆盖；无法访问该电脑／目录时先给下载或复制步骤并说明未完成保存。该配置文件不是稍后保存的 `.seospider` 爬取结果。

### 9.3：首页与已观察 pair

1. 从本次实际网站 URL 生成 HTTPS 首页的 www／non-www 地址，不写死任何域名。
2. 从主 crawl 的 HTML URL 找两侧实际存在的配对：只相差 leading www.，path／query 相同。相同标题不能独立证明配对或内容重复。
3. 优先复用足够的响应／内容证据，缺少时用包内 [check_hostname_pairs.py](onsite-audit-https/scripts/check_hostname_pairs.py) 逐跳 GET，记录最终地址和有限主体内容。Agent 核对目的与软 404，只有未解决的动态内容才补 SF／浏览器。
4. 统一到同一可用 HTTPS 对应页 → √；没有统一且主体内容相同 → X，写明两个 URL；内容不同、错误目标或确认循环 → X 并区分原因；429、预算停止、内容不足 → Human Check，照样导出 Excel；网络中断／超时／DNS/TLS 连接失败 → 立即报错并停止整个审核，要求重跑。

`hostname_executor` 新默认 python；`hostname_page_limit: null` 表示首页 + 全部已观察 pairs，正整数仅限制内页 pairs 并披露遗漏。旧 run 的 screaming_frog／20 不会自动改写，需要按此次任务迁移；不能继续理解为所有页面四版本。直接请求受共享 200 次默认预算限制，含 hops；不够时标 Human Check，不暗中加预算。`allow_hostname_list_crawl` 只控制是否可请求用户运行的 SF 补查，不控制 Python direct checks。[选择、命令与判断边界](onsite-audit-https/references/hostname-sampling.md)。

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
.venv/Scripts/python.exe onsite-audit-https/scripts/build_report.py --input <run-directory>/findings.json --output-dir <run-directory> --site-name "<site name>" --date <YYYY-MM-DD>
```

`<run-directory>` 是说明占位符，调用时换成本机路径。报告生成器拒绝覆盖已有文件，更新既有 workbook 时使用合适的 spreadsheet 编辑工具。此仓库是 skill + 配置/归档约定 + 本地报表工具，**不是独立一键 crawler**；MCP 调用和证据判断由当前 agent 执行。

Mac 的报表命令用 `.venv/bin/python` 替代 `.venv/Scripts/python.exe`；其他参数和输出格式一致。run root 请使用可写的 Mac 目录，不能沿用 Windows 盘符。

## Token / credits 设计

1. 默认复用 crawl，不自动启动新 crawl；同一批导出只拉一次。
2. 完整资料导出到文件；只把计数、缺失字段和少量实例送进上下文。
3. 预算在 config 中可调，默认 30 MCP calls、200 agent/Python 直接 live requests；直接请求的 redirect hops 和 retries 计入该预算。SF 授权的 list crawl 请求由 SF 的 crawl 配置控制，不拿 200 直接请求预算偷偷截断 SF 页面列表。MCP 调用超预算时保存 checkpoint 并标记未完成，不暗中增加用量。
4. 默认付费第三方 API calls 为 0；这三个检查不调用 Ahrefs、AI prompts 或 embedding，不为读取旧结果修改其他任务的配置。
5. 表格渲染、去重和复核在本机执行，不发起 LLM API 请求。真实客户端 token/订阅用量仍由客户端计费，不能承诺固定节省百分比。
6. 多个 agent 共用一个 Spider 时，串行加载/导出；其他 agent 读同一个 run 的归档文件，避免重复 crawl 和上下文。

这些预算是 skill 的执行约束，当前没有独立 MCP proxy 强制扣减；执行 agent 必须记录 usage.json 并在每次调用前检查预算。不能将配置数字当作服务端硬限额。

网络传输中断采用失败即停止：Python live 检查或 MCP 调用出现连接失败、超时、断连或响应读取中断时，不自动重试／续跑，不交付本次最终 Excel。保存 run-status.json（failed）、错误日志和用量，提示用户检查连接后在新 run 目录重新运行整个 skill。HTTP 403/429、资料缺失及预算上限仍沿用 Human Check；此中断规则优先于一般的缺证据导出和 retry 配置。

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
