import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # .github repo root
PROFILE_README = ROOT / "profile" / "README.md"
REPOS_DIR = ROOT / "repos"

START = "<!-- KOTE_STATS_START -->"
END = "<!-- KOTE_STATS_END -->"

CODE_EXTS = {".c", ".cc", ".cpp", ".h", ".hpp", ".py", ".java", ".js", ".ts", ".rs", ".kt", ".go"}
BOJ_RE = re.compile(r"^boj_(\d+)$", re.IGNORECASE)

def last_commit_date(repo_path: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_path), "log", "-1", "--format=%cs"],
            text=True
        ).strip()
        return out or "-"
    except Exception:
        return "-"

def collect_repo_stats(repo_path: Path):
    solutions = repo_path / "solution"
    if not solutions.exists():
        return {"files": 0, "unique_boj": 0, "last_commit": last_commit_date(repo_path)}

    files = []
    unique_ids = set()

    for p in solutions.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in CODE_EXTS:
            continue

        files.append(p)
        m = BOJ_RE.match(p.stem)
        if m:
            unique_ids.add(m.group(1))

    return {
        "files": len(files),
        "unique_boj": len(unique_ids),
        "last_commit": last_commit_date(repo_path),
    }

def build_table(rows):
    header = "| Repo | 풀이 파일 수 | BOJ 문제 수(중복제거) | 마지막 커밋일 |\n|---|---:|---:|---|\n"
    body = ""
    total_files = 0
    total_unique = 0

    for r in rows:
        total_files += r["files"]
        total_unique += r["unique_boj"]
        body += f'| {r["name"]} | {r["files"]} | {r["unique_boj"]} | {r["last_commit"]} |\n'

    footer = f"\n**합계**: 풀이 파일 {total_files}개 / BOJ 문제 {total_unique}개(중복 제거)\n"
    return header + body + footer

def replace_block(original: str, new_block: str) -> str:
    if START not in original or END not in original:
        raise RuntimeError(f"README에 마커가 없습니다: {START}, {END}")

    pre, rest = original.split(START, 1)
    _, post = rest.split(END, 1)
    return pre + START + "\n" + new_block.rstrip() + "\n" + END + post

def main():
    repo_paths = sorted([p for p in REPOS_DIR.iterdir() if p.is_dir()], key=lambda p: p.name.lower())

    rows = []
    for rp in repo_paths:
        s = collect_repo_stats(rp)
        rows.append({"name": rp.name, **s})

    table = build_table(rows)

    readme = PROFILE_README.read_text(encoding="utf-8")
    updated = replace_block(readme, table)
    PROFILE_README.write_text(updated, encoding="utf-8")

    print("Updated:", PROFILE_README)

if __name__ == "__main__":
    main()
