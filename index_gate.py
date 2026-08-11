#!/usr/bin/env python3
"""
index_gate.py — 발행 전 색인 가능성 게이트 (플레이북 §5)

사용법:
    python3 index_gate.py <검사할 HTML 파일> [--repo <저장소 루트>] [--json]

종료 코드: 0 = 통과, 1 = 차단(FAIL), 2 = 사용법 오류
설계 원칙: 멱등 / 실패는 하드 실패 / 의도적 예외는 .publishignore(glob) 로 관리
"""
import sys, os, re, glob, json, fnmatch
from html.parser import HTMLParser

# ── 1. 제목이 검색어 형태인가 ──────────────────────────────
QUERY_FORMS = [
    "방법", "하는법", "잡는법", "차이", "뜻", "시기", "이유", "비용", "가격",
    "기준", "계산", "조건", "자격", "신청", "순서", "절차", "종류", "언제",
    "얼마", "어디", "정리", "비교", "체크리스트", "총정리", "가이드", "고르는",
    "확인", "준비물", "주의사항", "부작용", "효과", "후기", "추천",
]

# ── 2. 낚시형 표현 ────────────────────────────────────────
BAIT = [
    "진짜 이유", "99%", "99프로", "숨겨진", "완전 해부", "의 과학", "충격",
    "경악", "전말", "모르면", "날립니다", "못 받", "이것만", "안 하면",
    "대반전", "발칵", "초비상", "역대급", "소름", "미쳤", "레전드",
    "아무도 모르는", "절대 하지", "당신이 모르는", "폭로",
]

# ── 3. 날짜·시의성 ────────────────────────────────────────
DATED = ["브리핑", "시황", "오늘의", "속보", "실시간", "제N보"]
DATE_RE = re.compile(r"20\d{2}[-./년]\s?\d{1,2}[-./월]\s?\d{1,2}")

TITLE_MAX = 60          # 4. 제목 길이
BODY_MIN_WORDS = 400    # 5. 본문 분량
DUP_RATIO = 0.50        # 6. 제목 중복
SUBTOPIC_MAX = 8        # 7. 소주제 포화
BIG_TOPIC_RATIO = 0.55  # 사이트 큰 주제(정체성) 판정 기준

STOP = set("""그리고 하지만 그러나 또한 위해 대한 통해 대해 있는 없는 하는 되는 이번 지난
다음 우리 이제 정말 매우 가장 모든 어떤 무슨 그런 이런 저런 것을 것이 수가 등을 등이
전국 관련 최근 오늘 내일 어제 올해 작년""".split())


class Extract(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title, self._t, self._skip, self.text = "", False, 0, []
    def handle_starttag(self, tag, attrs):
        if tag == "title": self._t = True
        if tag in ("script", "style"): self._skip += 1
    def handle_endtag(self, tag):
        if tag == "title": self._t = False
        if tag in ("script", "style") and self._skip: self._skip -= 1
    def handle_data(self, d):
        if self._t: self.title += d
        elif not self._skip: self.text.append(d)


def parse(path):
    p = Extract()
    p.feed(open(path, encoding="utf-8", errors="replace").read())
    title = re.split(r"\s*[|｜]\s*", p.title.strip())[0].strip()
    body = " ".join(p.text)
    return title, len(body.split())


def words(title):
    t = re.sub(r"[^\w가-힣 ]", " ", title)
    return {w for w in t.split() if len(w) >= 2 and w not in STOP}


def ignored(path, repo):
    pats = []
    f = os.path.join(repo, ".publishignore")
    if os.path.exists(f):
        pats = [l.strip() for l in open(f, encoding="utf-8")
                if l.strip() and not l.startswith("#")]
    rel = os.path.relpath(path, repo)
    return any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(os.path.basename(path), p)
               for p in pats)


def existing_titles(repo, target):
    out = []
    for f in glob.glob(os.path.join(repo, "**", "*.html"), recursive=True):
        if os.path.abspath(f) == os.path.abspath(target): continue
        if "/.git/" in f or ignored(f, repo): continue
        try:
            t, _ = parse(f)
            if t: out.append(t)
        except Exception:
            pass
    return out


def check(path, repo):
    fails, warns = [], []
    title, wc = parse(path)
    if not title:
        return [("제목", "<title> 을 찾을 수 없음")], [], title

    # 1
    if not any(k in title for k in QUERY_FORMS):
        fails.append(("1 검색어 형태", f"제목에 검색 의도 표현이 없음 — {'/'.join(QUERY_FORMS[:8])} 등을 넣을 것"))
    # 2
    hit = [b for b in BAIT if b in title]
    if hit:
        fails.append(("2 낚시형 표현", f"{', '.join(hit)}"))
    # 3
    d = [k for k in DATED if k in title]
    if DATE_RE.search(title): d.append("날짜 문자열")
    if d:
        fails.append(("3 날짜·시의성", f"{', '.join(d)} — 그날이 지나면 검색 수요가 0"))
    # 4
    if len(title) > TITLE_MAX:
        fails.append(("4 제목 길이", f"{len(title)}자 (최대 {TITLE_MAX}자, 검색결과에서 잘림)"))
    # 5
    if wc < BODY_MIN_WORDS:
        fails.append(("5 본문 분량", f"{wc}단어 (최소 {BODY_MIN_WORDS}단어)"))

    others = existing_titles(repo, path)
    tw = words(title)

    # 큰 주제(정체성) 판정 — 전체 글의 55% 이상에 등장하는 단어는 중복으로 세지 않는다
    big = set()
    if others:
        from collections import Counter
        c = Counter()
        for o in others: c.update(words(o))
        big = {w for w, n in c.items() if n / len(others) >= BIG_TOPIC_RATIO}

    core = tw - big
    # 6
    if tw:
        for o in others:
            ow = words(o)
            if ow and len(tw & ow) / len(tw | ow) >= DUP_RATIO:
                fails.append(("6 제목 중복", f"기존 글과 {int(len(tw & ow)/len(tw | ow)*100)}% 겹침 — \"{o[:40]}\""))
                break
    # 7
    if core:
        from collections import Counter
        c = Counter()
        for o in others:
            for w in words(o) & core: c[w] += 1
        sat = [(w, n) for w, n in c.items() if n >= SUBTOPIC_MAX]
        if sat:
            s = ", ".join(f"{w} {n}편" for w, n in sorted(sat, key=lambda x: -x[1])[:3])
            fails.append(("7 소주제 포화", f"{s} — 자기 글끼리 경쟁 중"))

    if big:
        warns.append(f"큰 주제(정체성, 중복 제외): {', '.join(sorted(big)[:6])}")
    return fails, warns, title


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    path = sys.argv[1]
    repo = os.path.dirname(os.path.abspath(path))
    if "--repo" in sys.argv:
        repo = sys.argv[sys.argv.index("--repo") + 1]
    if not os.path.exists(path):
        print(f"[FAIL] 파일 없음: {path}"); sys.exit(1)

    fails, warns, title = check(path, repo)
    as_json = "--json" in sys.argv

    if as_json:
        print(json.dumps({"file": path, "title": title, "pass": not fails,
                          "fails": [{"item": a, "detail": b} for a, b in fails],
                          "warns": warns}, ensure_ascii=False, indent=2))
    else:
        print(f"제목: {title}")
        for w in warns: print(f"  · {w}")
        if fails:
            print(f"\n[FAIL] {len(fails)}건 — 발행 차단")
            for a, b in fails: print(f"  ✗ {a}: {b}")
            print("\n제목을 검색어 형태로 고치고 다시 검사하세요.")
        else:
            print("\n[PASS] 발행 가능")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
