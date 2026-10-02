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
지원: SWEA, 프로그래머스 (백준허브가 올린 README 형식)

사용법: python scripts/update_readme.py <algorithm 레포 경로> <README 경로>
"""
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

# ── 설정 ──────────────────────────────────────────────
REPO_URL = "https://github.com/Hiri-kor/algorithm/tree/main"
RECENT_COUNT = 5  # 최근 몇 문제를 보여줄지
START = "<!-- SOLVED:START -->"
END = "<!-- SOLVED:END -->"

# 백준허브 README 첫 줄 예:
#   SWEA        "# [D1] 홀수만 더하기 - 2072"
#   프로그래머스  "# [level 0] 문자열 출력하기 - 181952"
# \s 는 일반 공백뿐 아니라 백준허브가 쓰는 특수 공백(U+2005)도 잡는다.
HEADER_RE = re.compile(r"^#\s*\[(.+?)\]\s*(.+?)\s*-\s*(\d+)\s*$")
DATE_RE = re.compile(r"### 제출 일자\s+(.+)")

# 사이트마다 날짜 형식이 다르다.
#   SWEA        "2026-10-01 21:50"
#   프로그래머스  "2026년 10월 02일 12:20:20"
DATE_FORMATS = ["%Y-%m-%d %H:%M", "%Y년 %m월 %d일 %H:%M:%S"]


def parse_date(text):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            pass
    return None


def short_level(level):
    """'level 0' → 'Lv.0', 'D1' → 'D1'"""
    m = re.fullmatch(r"level\s*(\d+)", level, re.I)
    return f"Lv.{m.group(1)}" if m else level


def parse_problem(readme_path, repo_root):
    """문제 폴더의 README.md 하나를 읽어 정보를 딕셔너리로 돌려준다.
    형식이 예상과 다르면 None을 돌려준다."""
    text = readme_path.read_text(encoding="utf-8")
    first_line = text.splitlines()[0].strip() if text else ""

    header = HEADER_RE.match(first_line)
    date_match = DATE_RE.search(text)
    if not header or not date_match:
        return None
    date = parse_date(date_match.group(1))
    if date is None:
        return None

    level, title, number = header.groups()
    folder = readme_path.parent.relative_to(repo_root)
    return {
        "site": folder.parts[0],          # 맨 위 폴더 이름: SWEA, 프로그래머스
        "level": short_level(level),
        "title": title,
        "number": number,
        "date": date,
        "url": f"{REPO_URL}/{quote(folder.as_posix())}",
    }


def collect_problems(repo_root):
    """<사이트>/<난이도>/<문제 폴더>/README.md 를 모두 찾아 파싱한다."""
    problems = []
    for readme in sorted(repo_root.glob("*/*/*/README.md")):
        if readme.parts and any(p.startswith(".") for p in readme.relative_to(repo_root).parts):
            continue  # .github 같은 숨김 폴더는 건너뜀
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

    # 사이트별 개수: {"SWEA": 3, "프로그래머스": 1}
    counts = {}
    for p in problems:
        counts[p["site"]] = counts.get(p["site"], 0) + 1
    by_site = " · ".join(f"{site} {counts[site]}" for site in sorted(counts))

    # 최근 순으로 정렬해서 앞에서 RECENT_COUNT개만
    recent = sorted(problems, key=lambda p: p["date"], reverse=True)[:RECENT_COUNT]

    lines = [
        f"**총 {len(problems)}문제** ({by_site})",
        "",
        "| 날짜 | 사이트 | 난이도 | 문제 |",
        "| --- | --- | --- | --- |",
    ]
    for p in recent:
        day = p["date"].strftime("%Y-%m-%d")
        lines.append(
            f"| {day} | {p['site']} | {p['level']} | [{p['number']}. {p['title']}]({p['url']}) |"
        )
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
