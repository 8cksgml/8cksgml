"""SWEA 풀이 레포(algorithm)를 읽어서 프로필 README의 표시 구역을 갱신한다.

사용법: python scripts/update_readme.py <algorithm 레포 경로> <README 경로>
"""
import re
import sys
from pathlib import Path
from urllib.parse import quote

# ── 설정 ──────────────────────────────────────────────
REPO_URL = "https://github.com/Hiri-kor/algorithm/tree/main"
RECENT_COUNT = 5  # 최근 몇 문제를 보여줄지
START = "<!-- SOLVED:START -->"
END = "<!-- SOLVED:END -->"

# 백준허브 README 첫 줄 예: "# [D1] 홀수만 더하기 - 2072"
# \s 는 일반 공백뿐 아니라 백준허브가 쓰는 특수 공백(U+2005)도 잡는다.
HEADER_RE = re.compile(r"^#\s*\[(D\d)\]\s*(.+?)\s*-\s*(\d+)\s*$")
DATE_RE = re.compile(r"### 제출 일자\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2})")


def parse_problem(readme_path, repo_root):
    """문제 폴더의 README.md 하나를 읽어 정보를 딕셔너리로 돌려준다.
    형식이 예상과 다르면 None을 돌려준다."""
    text = readme_path.read_text(encoding="utf-8")
    first_line = text.splitlines()[0].strip() if text else ""

    header = HEADER_RE.match(first_line)
    date = DATE_RE.search(text)
    if not header or not date:
        return None

    level, title, number = header.groups()
    folder = readme_path.parent.relative_to(repo_root).as_posix()
    return {
        "level": level,
        "title": title,
        "number": number,
        "date": date.group(1),
        "url": f"{REPO_URL}/{quote(folder)}",
    }


def collect_problems(repo_root):
    """SWEA/D*/<문제 폴더>/README.md 를 모두 찾아 파싱한다."""
    problems = []
    for readme in sorted(repo_root.glob("SWEA/D*/*/README.md")):
        info = parse_problem(readme, repo_root)
        if info is None:
            print(f"[건너뜀] 형식이 다름: {readme}")
            continue
        problems.append(info)
    return problems


def build_section(problems):
    """README에 넣을 마크다운 문자열을 만든다."""
    if not problems:
        return "아직 기록된 문제가 없습니다."

    # 난이도별 개수: {"D1": 3, "D2": 1}
    counts = {}
    for p in problems:
        counts[p["level"]] = counts.get(p["level"], 0) + 1
    by_level = " · ".join(f"{lv} {counts[lv]}" for lv in sorted(counts))

    # 최근 순으로 정렬해서 앞에서 RECENT_COUNT개만
    recent = sorted(problems, key=lambda p: p["date"], reverse=True)[:RECENT_COUNT]

    lines = [
        f"**SWEA 총 {len(problems)}문제** ({by_level})",
        "",
        "| 날짜 | 난이도 | 문제 |",
        "| --- | --- | --- |",
    ]
    for p in recent:
        day = p["date"].split(" ")[0]
        lines.append(f"| {day} | {p['level']} | [{p['number']}. {p['title']}]({p['url']}) |")
    return "\n".join(lines)


def replace_section(readme_text, new_content):
    """START와 END 주석 사이의 내용만 새 내용으로 바꾼다."""
    if START not in readme_text or END not in readme_text:
        raise SystemExit(f"README에 {START} / {END} 표시가 없습니다.")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    return pattern.sub(lambda _: f"{START}\n{new_content}\n{END}", readme_text)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("사용법: python update_readme.py <algorithm 레포 경로> <README 경로>")
    repo_root = Path(sys.argv[1])
    readme_path = Path(sys.argv[2])

    problems = collect_problems(repo_root)
    old = readme_path.read_text(encoding="utf-8")
    new = replace_section(old, build_section(problems))

    if new == old:
        print("변경 없음")
        return
    readme_path.write_text(new, encoding="utf-8")
    print(f"README 갱신: 총 {len(problems)}문제")


if __name__ == "__main__":
    main()
