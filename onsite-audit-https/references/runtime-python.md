# Multica 的 Python 环境

导入 skill 会提供 Python 脚本、依赖清单与参考资料，**不会安装 Python、openpyxl 或虚拟环境，也不会连接作者 Windows 的 Python**。

脚本在哪台 runtime 执行，就使用哪台机器的解释器与文件权限。Multica 网页所在电脑不一定是执行机；先确认 agent 绑定的是测试 Mac 的在线 runtime。如果 runtime 是容器/远程机器，环境必须配置在那里，不能假设宿主机的 Python 可见。

## 首次执行自检

从当前 agent 的 shell 验证，而不是仅在人工 Terminal 验证：

```bash
python3 --version
python3 -c 'import sys; print(sys.executable)'
```

如已经提供 AUDIT_PYTHON，则用它验证：

```bash
"$AUDIT_PYTHON" -c 'import sys, openpyxl; print(sys.executable); print(openpyxl.__version__)'
```

找不到解释器或依赖时，先处理运行环境，不拉取新的 crawl。不要因此改用 Windows 路径，也不要调用付费 Python/LLM API。

## Mac repo 安装方式

在 clone 的仓库根目录执行：

有 repo 时可先运行 `bash scripts/setup-mac.sh` 自动检查解释器、准备 venv、安装依赖并生成本机 `config/python.local.json`。没有 Python 且有 Homebrew 时脚本安装 Python；没有 Homebrew 时先从 Python 官网安装，再重跑。生成的解释器路径需要填入 Multica agent 的 AUDIT_PYTHON 环境设置，不能把配置文件存在磁盘当成已经注册给 agent。

手动等价步骤：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -c 'import sys, openpyxl; print(sys.executable); print(openpyxl.__version__)'
.venv/bin/python onsite-audit-https/scripts/test_report.py
```

不依赖 shell activation，直接指定解释器更可靠。可在 Mac Terminal 输出本机实际路径：

```bash
printf '%s\n' "$(pwd)/.venv/bin/python"
```

将该机输出值填入测试 agent 的环境变量 AUDIT_PYTHON，或提供给 agent 作为本地配置。不要把该值提交到 GitHub。Terminal 的 export 不保证传给已经运行的 Multica runtime；在实际 agent shell 再自检，必要时通过 Multica agent 环境设置提供变量。

## 仅 ZIP 导入方式

脚本和 requirements.txt 都在导入的 skill 内。确认 Multica 为 agent 提供的实际 skill 路径，用其中的 requirements.txt 安装到执行机的独立 venv。路径从当前环境发现，不猜项目目录。即使没有 clone repo，也能从 skill 里的 scripts/build_report.py 生成报告；repo 根目录的安装/打包工具不是运行报告所必需的。

## 每次运行

- 通过 AUDIT_PYTHON 或已验证的解释器执行 scripts/build_report.py，输入输出路径由 run config 提供。
- 将运行机类型、解释器版本及依赖自检结果写入 handover/manifest。无需把环境的全部变量输出，避免泄漏凭据。
- 确认 run 目录可写、输出 final.xlsx 可以取回。导入 skill 的目录用于读取代码，run 数据存单独目录。
- Python 环境与 SF MCP 是两个独立检查。Python 成功不证明 MCP 成功，MCP 成功也不代表 openpyxl 已安装。
