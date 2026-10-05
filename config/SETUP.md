# Global skill 与客户端配置

保持与现有 skill 类似的结构：Git repo 是源，global skill 目录是链接，run config 与 client config 分开。SSH 是 GitHub repo 的访问方式；它和 Screaming Frog 本地 HTTP MCP 无关。

## 共享 skill

Windows 从 repo 运行 `scripts/install-skills.ps1`。也可将其他现有 skill 加入共享目录：

```powershell
powershell -NoProfile -File scripts/install-skills.ps1 -SkillPaths "<existing-skill-directory>"
```

目录必须含有效 SKILL.md，文件夹名称符合 skill 命名规则。脚本不会扫描/迁移所有旧 skills，避免重复名字与意外修改；逐个传入选定目录。全局路径自动来自当前用户，不复制上台电脑的绝对路径。

macOS/Linux：`bash scripts/install-skills.sh`。其他 skill 可作为路径参数传入：`bash scripts/install-skills.sh "<existing-skill-directory>"`。脚本从自身位置找到 repo，从 HOME 找到当前用户，使用 symlink；重复运行保持已有正确链接，遇到其他同名文件则停止。不要搬运 Windows junction 或虚拟环境。

Codex 的当前官方用户级路径是 `~/.agents/skills`，有独立 skill 发现机制；不要沿用旧文档中“Codex 没有 skills 目录”的说法。Claude Code 使用 `~/.claude/skills`，Cursor 可发现这两个目录。官方来源见 README。

## Screaming Frog 配置事实

默认只做 native HTTP 连接，不使用第三方桥接。server URL 从本机 UI 复制，保存在本机配置；allowed base 来自本机 SF 设置。每个客户端注册一次，三个客户端使用同一地址；启动由 SF 管理。

全局配置不能是把整个文件覆盖：Codex 合并 TOML section，Cursor 合并单个 mcpServers entry；已有同名 server 先检查，不建重复配置。不要共享 OAuth 凭据、cookie 或 licence。

### Codex

```powershell
codex mcp add screaming-frog --url "$env:SCREAMING_FROG_MCP_URL"
codex mcp list
```

或把生成的 `codex.mcp.local.toml` section 合并到 `~/.codex/config.toml`，保留其他字段。连接后在新会话检查工具目录。需要缩减工具时先取得 live 工具名，再用 enabled_tools；本仓库不提交未确认的 allowlist。

Mac Bash/Zsh：

```bash
codex mcp add screaming-frog --url "$SCREAMING_FROG_MCP_URL"
codex mcp list
```

### Claude Code

```powershell
claude mcp add --transport http --scope user screaming-frog "$env:SCREAMING_FROG_MCP_URL"
claude mcp list
```

在会话中 `/mcp` 查看连接与实际工具。生成的 Claude JSON 是参考片段；优先用 CLI 写入 user scope，不将它直接覆盖到 ~/.claude.json。Claude Desktop 扩展与 Claude Code 配置是不同客户端。

Mac Bash/Zsh：

```bash
claude mcp add --transport http --scope user screaming-frog "$SCREAMING_FROG_MCP_URL"
claude mcp list
```

### Cursor

将生成的 `cursor.mcp.local.json` 中 `screaming-frog` entry 合并到 `~/.cursor/mcp.json` 的 `mcpServers`，保留其他 server。在 Customize/MCP 中检查启用和工具。没有文件时可用完整生成内容初始化。

### 验证顺序

1. SF server 已启动，UI 显示本机实际 URL。
2. 客户端 handshake、tools/list 成功；只证明连接，不代表已有正确 crawl。
3. 取最多 3 个 crawl，确认站点，再按 ID 加载。
4. 一次小型 security 导出到 allowed base；校验文件存在、headers 和 counts。
5. 保存 manifest、真实 tool schema，运行离线报表测试。
6. 在新机器再重复，不复用旧机器的绝对路径或默认端口假设。
