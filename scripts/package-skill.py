"""Package just the portable skill, with SKILL.md at archive root."""
import argparse
import re
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def package(source, output):
    source = source.resolve()
    if not (source / "SKILL.md").is_file():
        raise ValueError("Skill source must contain SKILL.md")
    repo = Path(__file__).resolve().parent.parent
    if source == repo / "onsite-audit-https":
        # Multica repository URL import requires an entry at repository root.
        # Keep the locally installed skill as the authoring source and rewrite
        # its relative links for the generated repository-level entry.
        content = (source / "SKILL.md").read_text(encoding="utf-8")
        content = re.sub(r'\]\(([^)]+)\)', lambda m: '](' + ('onsite-audit-https/' + m[1] if '://' not in m[1] and not m[1].startswith(('#', '/')) else m[1]) + ')', content)
        (repo / "SKILL.md").write_text(content, encoding="utf-8")
    output = output.resolve()
    if source == output or source in output.parents:
        raise ValueError("Archive output must be outside the skill directory")
    files = sorted(p for p in source.rglob("*") if p.is_file() and not any(part in {"__pycache__", ".git", ".venv"} for part in p.relative_to(source).parts) and p.suffix not in {".pyc", ".pyo"})
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(source).as_posix())
    with ZipFile(output) as archive:
        if "SKILL.md" not in archive.namelist() or archive.testzip() is not None:
            raise RuntimeError("Archive verification failed")
    print(f"Verified archive: {output} ({len(files)} files)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parent.parent / "onsite-audit-https")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package(args.source, args.output)
