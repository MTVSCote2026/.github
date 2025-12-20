import re
import subprocess
from datetime import datetime, time, timedelta
from pathlib import Path

from zoneinfo import ZoneInfo

# 스크립트 위치: <repo>/.github/scripts/update_kote_stats.py
ROOT = Path(__file__).resolve().parents[2]  # <repo>
PROFILE_DIR = ROOT / "profile"
PROFILE_README = PROFILE_DIR / "README.md"
REPOS_DIR = ROOT / "repos"

START = "<!-- KOTE_STATS_START -->"
END = "<!-- KOTE_STATS_END -->"

# 폴더명 변경 반영: solutions
SOLUTIONS_DIRNAME = "solutions"

BOJ_STEM_RE = re.compile(r"^boj_(\d+)$", re.IGNORECASE)

def ensure_readme_exists():
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    if not PROFILE_README.exists():
        PROFILE_README.write_text(
            "## 코테 통계\n\n"
            f"{START}\n"
            "(여기는 자동 생성됩니다)\n"
            f"{END}\n",
            encoding="utf-8",
        )

def replace_block(original: str, new_block: str) -> str:
    # 마커가 없으면 자동으로 추가해서 실패 방지
    if START not in original or END not in original:
        original = original.rstrip() + "\n\n" + START + "\n" + END + "\n"

    pre, rest = original.split(START, 1)
    _, post = rest.split(END, 1)
    return pre + START + "\n" + new_block.rstrip() + "\n" + END + post

def kst_today_range():
    tz = ZoneInfo("Asia/Seoul")
    now = datetime.now(tz)
    today = now.date()
    start_dt = datetime.combine(today, time(0, 0, 0), tzinfo=tz)
    end_dt = start_dt + timedelta(days=1)
    return start_dt, end_dt

def run_git(repo_path: Path, args: list[str]) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo_path), *args],
        text=True,
        errors="replace",
    )

def total_unique_boj(repo_path: Path) -> int:
    sol = repo_path / SOLUTIONS_DIRNAME
    if not sol.exists():
        return 0

    ids = set()
    for p in sol.rglob("*"):
        if not p.is_file():
            continue
        m = BOJ_STEM_RE.match(p.stem)
        if m:
            ids.add(m.group(1))
    return len(ids)

def today_unique_boj_added(repo_path: Path) -> int:
    """
    오늘(한국시간) 커밋에서 '추가(A)'된 solutions/boj_번호 파일들의 문제 번호(unique) 개수
    """
    start_dt, end_dt = kst_today_range()
    since = start_dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    until = end_dt.strftime("%Y-%m-%dT%H:%M:%S%z")

    try:
        out = run_git(
            repo_path,
            ["log", "--since", since, "--until", until, "--name-status", "--pretty=format:"],
        )
    except Exception:
        return 0

    ids = set()
    prefix = f"{SOLUTIONS_DIRNAME}/"

    for line in out.splitlines():
        if not line:
            continue
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue

        status, path = parts[0].strip(), parts[1].strip()
        if status != "A":
            continue
        if not path.startswith(prefix):
            continue

        stem = Path(path).stem
        m = BOJ_STEM_RE.match(stem)
        if m:
            ids.add(m.group(1))

    return len(ids)

def build_table(rows: list[dict]) -> str:
    # 헤더는 항상 출력
    header = "| 이름 | 총 갯수 | 오늘 푼 갯수 |\n|---|---:|---:|\n"
    body = ""
    for r in rows:
        body += f"| {r['name']} | {r['total']} | {r['today']} |\n"
    return header + body  # rows가 비면 header만 남음

def main():
    ensure_readme_exists()
    REPOS_DIR.mkdir(parents=True, exist_ok=True)

    repo_dirs = sorted([p for p in REPOS_DIR.iterdir() if p.is_dir()], key=lambda p: p.name.lower())

    rows = []
    for rp in repo_dirs:
        # clone이 완전하지 않으면 스킵(실패 방지)
        if not (rp / ".git").exists():
            continue

        rows.append(
            {
                "name": rp.name,
                "total": total_unique_boj(rp),
                "today": today_unique_boj_added(rp),
            }
        )

    table = build_table(rows)

    readme = PROFILE_README.read_text(encoding="utf-8")
    updated = replace_block(readme, table)
    PROFILE_README.write_text(updated, encoding="utf-8")

if __name__ == "__main__":
    main()
