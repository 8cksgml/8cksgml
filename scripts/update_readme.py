"""algorithm 레포가 만든 problems.json을 읽어서 프로필 README의 표시 구역을 갱신한다.
문제 분석은 algorithm 레포의 scripts/build_index.py가 맡고, 여기서는 표만 만든다.

사용법: python scripts/update_readme.py <problems.json 경로> <README 경로>
"""
import json
import re
import sys
from pathlib import Path

RECENT_COUNT = 5  # 최근 몇 문제를 보여줄지
START = "<!-- SOLVED:START -->"
END = "<!-- SOLVED:END -->"


def build_section(problems):
    """README에 넣을 마크다운 문자열을 만든다. problems는 최신순으로 정렬되어 있다."""
    if not problems:
        return "아직 기록된 문제가 없습니다."

    # 사이트별 개수: {"SWEA": 3, "프로그래머스": 1}
    counts = {}
    for p in problems:
        counts[p["site"]] = counts.get(p["site"], 0) + 1
    by_site = " · ".join(f"{site} {counts[site]}" for site in sorted(counts))

    recent = sorted(problems, key=lambda p: p["date"], reverse=True)[:RECENT_COUNT]

    lines = [
        f"**총 {len(problems)}문제** ({by_site}) · [전체 목록](https://github.com/Hiri-kor/algorithm)",
        "",
        "| 날짜 | 사이트 | 난이도 | 문제 |",
        "| --- | --- | --- | --- |",
    ]
    for p in recent:
        lines.append(
            f"| {p['date'][:10]} | {p['site']} | {p['level']} | [{p['number']}. {p['title']}]({p['url']}) |"
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
        raise SystemExit("사용법: python update_readme.py <problems.json 경로> <README 경로>")
    json_path = Path(sys.argv[1])
    readme_path = Path(sys.argv[2])

    problems = json.loads(json_path.read_text(encoding="utf-8"))
    old = readme_path.read_text(encoding="utf-8")
    new = replace_section(old, build_section(problems))

    if new == old:
        print("변경 없음")
        return
    readme_path.write_text(new, encoding="utf-8")
    print(f"README 갱신: 총 {len(problems)}문제")


if __name__ == "__main__":
    main()
