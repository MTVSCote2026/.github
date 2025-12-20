from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # .github repo root
PROFILE_DIR = ROOT / "profile"
PROFILE_README = PROFILE_DIR / "README.md"
REPOS_DIR = ROOT / "repos"

START = "<!-- KOTE_STATS_START -->"
END = "<!-- KOTE_STATS_END -->"

def build_header_only_table() -> str:
    # 레포가 0개면 이 두 줄만 남습니다(표 렌더링은 되고, 데이터 행은 없음)
    return "| 이름 | 총 갯수 | 오늘 푼 갯수 |\n|---|---:|---:|\n"

def ensure_readme_exists():
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    if not PROFILE_README.exists():
        PROFILE_README.write_text(
            "## 코테 통계\n\n"
            f"{START}\n"
            "(여기는 자동 생성됩니다)\n"
            f"{END}\n",
            encoding="utf-8"
        )

def replace_block(original: str, new_block: str) -> str:
    # 마커가 없으면 맨 끝에 자동으로 추가해서 “절대 실패”하지 않게
    if START not in original or END not in original:
        original = original.rstrip() + "\n\n" + START + "\n" + END + "\n"

    pre, rest = original.split(START, 1)
    _, post = rest.split(END, 1)
    return pre + START + "\n" + new_block.rstrip() + "\n" + END + post

def main():
    ensure_readme_exists()
    REPOS_DIR.mkdir(parents=True, exist_ok=True)

    # 레포 디렉토리가 하나도 없으면 헤더만 출력
    repo_dirs = [p for p in REPOS_DIR.iterdir() if p.is_dir()]
    if len(repo_dirs) == 0:
        block = build_header_only_table()
    else:
        # 레포가 있으면(추후 확장 대비) 기본적으로는 헤더만 유지하도록 요구하셨으니,
        # 여기서도 일단은 "헤더만" 유지합니다.
        # (원하시면 다음 단계에서 rows 출력 로직을 다시 넣어드리면 됩니다.)
        block = build_header_only_table()

    readme = PROFILE_README.read_text(encoding="utf-8")
    updated = replace_block(readme, block)
    PROFILE_README.write_text(updated, encoding="utf-8")

if __name__ == "__main__":
    main()
