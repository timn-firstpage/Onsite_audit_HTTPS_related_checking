"""Generate client config fragments from a user-supplied local endpoint; no client settings are overwritten."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit


def generate(url, directory, server_name):
    import re
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Supply the actual HTTP MCP URL, without embedded credentials")
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", server_name):
        raise ValueError("Invalid server name")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    files = {
        "codex.mcp.local.toml": f'[mcp_servers.{server_name}]\nurl = {json.dumps(url)}\nenabled = true\n',
        "claude.mcp.local.json": json.dumps({"mcpServers": {server_name: {"type": "http", "url": url}}}, indent=2) + "\n",
        "cursor.mcp.local.json": json.dumps({"mcpServers": {server_name: {"url": url}}}, indent=2) + "\n",
    }
    for name in files:
        if (directory / name).exists():
            raise FileExistsError(f"Existing config preserved: {directory / name}")
    for name, contents in files.items():
        (directory / name).write_text(contents, encoding="utf-8")
    return {"directory": str(directory.resolve()), "files": list(files), "connection_verified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--server-name", default="screaming-frog")
    args = parser.parse_args()
    print(json.dumps(generate(args.url, args.output_dir, args.server_name)))
