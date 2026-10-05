#!/usr/bin/env bash
# Prepare local Python dependencies without changing global Python packages.
set -euo pipefail
[[ "$(uname -s)" == "Darwin" ]] || { echo "Run this setup on the Mac execution machine." >&2; exit 1; }
task_script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
task_repo_dir="$(cd -- "$task_script_dir/.." && pwd -P)"
task_python="${AUDIT_BOOTSTRAP_PYTHON:-python3}"
if ! "$task_python" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
  if command -v brew >/dev/null 2>&1; then
    brew install python
    task_python="$(brew --prefix python)/bin/python3"
  else
    echo "Python 3.9+ was not found. Install Python 3 from https://www.python.org/downloads/macos/ and rerun this script." >&2
    echo "For a custom installation set AUDIT_BOOTSTRAP_PYTHON to its executable path." >&2
    exit 1
  fi
fi
task_venv_dir="${AUDIT_VENV_DIR:-$task_repo_dir/.venv}"
task_config_dir="${AUDIT_LOCAL_CONFIG_DIR:-$task_repo_dir/config}"
if [[ -e "$task_venv_dir" && ! -f "$task_venv_dir/pyvenv.cfg" ]]; then
  echo "Existing directory is not a Python venv; choose another AUDIT_VENV_DIR: $task_venv_dir" >&2
  exit 1
fi
if [[ ! -f "$task_venv_dir/pyvenv.cfg" ]]; then
  "$task_python" -m venv "$task_venv_dir"
fi
task_runtime_python="$task_venv_dir/bin/python"
"$task_runtime_python" -m pip install -r "$task_repo_dir/requirements.txt"
"$task_runtime_python" -c 'import sys, openpyxl; print("Python:", sys.executable); print("openpyxl:", openpyxl.__version__)'
cd -- "$task_repo_dir"
"$task_runtime_python" "$task_repo_dir/onsite-audit-https/scripts/test_report.py"
"$task_runtime_python" - "$task_config_dir" <<'PY'
import json, pathlib, sys
directory = pathlib.Path(sys.argv[1]).expanduser().resolve()
directory.mkdir(parents=True, exist_ok=True)
output = directory / 'python.local.json'
config = {'schema_version': 1, 'python_executable': sys.executable, 'environment_variable': 'AUDIT_PYTHON', 'dependencies_verified': ['openpyxl']}
if output.exists():
    existing = json.loads(output.read_text(encoding='utf-8'))
    if existing != config:
        raise SystemExit(f'Existing config preserved: {output}. Use another AUDIT_LOCAL_CONFIG_DIR or resolve the old config.')
else:
    output.write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
print('Local Python config:', output)
print('Set AUDIT_PYTHON in the Multica test agent environment to:', sys.executable)
PY
echo "Python setup complete. In the Multica agent shell, verify AUDIT_PYTHON before using MCP."
