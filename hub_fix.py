#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hub_fix.py — 분야별 허브 페이지 생성 + 기사 내부링크 주입

무엇을 하나 (2026-09-12 신설)
---------------------------
9/07 색인정리 뒤 살아남은 글들이 서로 연결돼 있지 않았다.
realestate 는 홈페이지에서 기사로 가는 링크가 **0개**였고,
sangsang 은 홈페이지가 noindex 처리된 288개까지 전부 링크하고 있었다.
글이 고립되면 크롤러가 타고 들어갈 길이 없고, 주제 묶음도 생기지 않는다.

그래서 이 스크립트가 두 가지를 한다.

  1) hubs.json 의 분류대로 `<slug>/index.html` 허브 페이지를 만든다
  2) 각 기사에 breadcrumb(위) 와 "같은 분야 다른 글"(아래) 을 주입한다

설계 원칙 (publish 계열 스크립트와 동일)
---------------------------------------
- 멱등: 마커 사이만 갈아끼우므로 몇 번을 돌려도 결과가 같다
- 주입 위치는 `<article>` 여는 태그 직후 / `</article>` 직전 — 두 저장소 공통
- 본문은 건드리지 않는다

사용법:  python3 hub_fix.py
"""
import json, os, re, html, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG  = os.path.join(ROOT, "hubs.json")

BC_B, BC_E = "<!-- HUB:BREADCRUMB:BEGIN -->", "<!-- HUB:BREADCRUMB:END -->"
RL_B, RL_E = "<!-- HUB:RELATED:BEGIN -->",   "<!-- HUB:RELATED:END -->"


def esc(s):
    return html.escape(s or "", quote=True)


def strip_tags(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def get_title(src):
    m = re.search(r"<title[^>]*>(.*?)</title>", src, re.S | re.I)
    t = strip_tags(m.group(1)) if m else ""
    return re.split(r"\s*[|｜]\s*", t)[0].strip() or "(제목 없음)"


def get_desc(src):
    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
                  src, re.S | re.I)
    if m and m.group(1).strip():
        return strip_tags(m.group(1))[:150]
    body = re.sub(r"(?is)<head.*?</head>", " ", src)
    for para in re.findall(r"(?is)<p[^>]*>(.*?)</p>", body):
        t = strip_tags(para)
        if len(t) >= 40:
            return t[:150]
    return ""


# ── 허브 페이지 ────────────────────────────────────────────────────────────
HUB_CSS = """
    :root{--hub-line:#e3e8ee;--hub-dim:#5b6672;--hub-ink:#12202e;--hub-accent:#1a5f8a}
    .hub-wrap{max-width:820px;margin:0 auto;padding:28px 18px 56px;
      font-family:'Noto Sans KR',-apple-system,BlinkMacSystemFont,'Malgun Gothic',sans-serif;
      color:var(--hub-ink);line-height:1.7}
    .hub-crumb{font-size:13px;color:var(--hub-dim);margin-bottom:18px}
    .hub-crumb a{color:var(--hub-dim);text-decoration:none}
    .hub-crumb a:hover{text-decoration:underline}
    .hub-wrap h1{font-family:'Noto Serif KR',serif;font-size:29px;line-height:1.35;
      margin:0 0 12px;letter-spacing:-.01em}
    .hub-lede{font-size:15px;color:var(--hub-dim);margin:0 0 8px}
    .hub-count{font-size:13px;color:var(--hub-dim);border-top:1px solid var(--hub-line);
      padding-top:14px;margin-top:22px}
    .hub-list{list-style:none;padding:0;margin:10px 0 0}
    .hub-list li{border-bottom:1px solid var(--hub-line);padding:17px 0}
    .hub-list a{text-decoration:none;color:inherit;display:block}
    .hub-list a:hover .hub-t{color:var(--hub-accent);text-decoration:underline}
    .hub-t{font-size:17px;font-weight:700;line-height:1.45;margin:0 0 5px;
      font-family:'Noto Serif KR',serif}
    .hub-d{font-size:14px;color:var(--hub-dim);margin:0}
    .hub-other{margin-top:40px;border-top:1px solid var(--hub-line);padding-top:20px}
    .hub-other h2{font-size:15px;margin:0 0 12px;font-weight:700}
    .hub-chips{display:flex;flex-wrap:wrap;gap:8px}
    .hub-chips a{font-size:13.5px;text-decoration:none;color:var(--hub-ink);
      border:1px solid var(--hub-line);border-radius:999px;padding:7px 14px;background:#fff}
    .hub-chips a:hover{border-color:var(--hub-accent);color:var(--hub-accent)}
    @media(max-width:520px){.hub-wrap{padding:20px 15px 44px}.hub-wrap h1{font-size:24px}}
"""

HUB_TPL = """<!doctype html>
<html lang="ko">
<head>
  <!-- HUB:PAGE — 분야 탐색 페이지. ads_fix.py 는 이 표시가 있는 파일에 광고를 넣지 않는다 -->
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="{desc}" />
  <title>{name} — {site_name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@500;700&family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet">
  <style>{css}</style>
</head>
<body>
<div class="hub-wrap">
  <nav class="hub-crumb"><a href="/">{site_name}</a> &rsaquo; <span>{name}</span></nav>
  <h1>{name}</h1>
  <p class="hub-lede">{desc}</p>
  <p class="hub-count">글 {n}편</p>
  <ul class="hub-list">
{items}  </ul>
  <div class="hub-other">
    <h2>다른 분야</h2>
    <div class="hub-chips">
{chips}    </div>
  </div>
</div>
</body>
</html>
"""


def build_hub(cfg, hub, pages):
    items = ""
    for stem in hub["files"]:
        p = pages.get(stem)
        if not p:
            continue
        items += ('    <li><a href="/%s">\n      <p class="hub-t">%s</p>\n'
                  '      <p class="hub-d">%s</p>\n    </a></li>\n'
                  % (stem, esc(p["title"]), esc(p["desc"])))
    chips = "".join('      <a href="/%s/">%s</a>\n' % (h["slug"], esc(h["name"]))
                    for h in cfg["hubs"] if h["slug"] != hub["slug"])
    chips += '      <a href="/">홈</a>\n'
    n = sum(1 for s in hub["files"] if s in pages)
    return HUB_TPL.format(name=esc(hub["name"]), desc=esc(hub["desc"]),
                          site_name=esc(cfg["site_name"]), css=HUB_CSS,
                          n=n, items=items, chips=chips)


# ── 기사 주입 ─────────────────────────────────────────────────────────────
INJ_CSS = """<style>
.hub-bc{font-size:13px;color:#5b6672;margin:0 0 18px;font-family:'Noto Sans KR',sans-serif}
.hub-bc a{color:#5b6672;text-decoration:none}.hub-bc a:hover{text-decoration:underline}
.hub-rel{margin:38px 0 6px;padding:20px 22px;border:1px solid #e3e8ee;border-radius:10px;
  background:#fafbfc;font-family:'Noto Sans KR',sans-serif}
.hub-rel h2{font-size:15px;margin:0 0 14px;font-weight:700;color:#12202e;
  font-family:'Noto Sans KR',sans-serif;border:0;padding:0}
.hub-rel ul{list-style:none;padding:0;margin:0}
.hub-rel li{padding:7px 0;font-size:14.5px;line-height:1.55}
.hub-rel li a{color:#12202e;text-decoration:none}
.hub-rel li a:hover{color:#1a5f8a;text-decoration:underline}
.hub-rel .hub-more{margin:14px 0 0;font-size:13.5px}
.hub-rel .hub-more a{color:#1a5f8a;text-decoration:none;font-weight:700}
</style>"""


def breadcrumb(cfg, hub):
    """눈에 보이는 경로 + BreadcrumbList 구조화 데이터.

    구조화 데이터가 없으면 구글은 검색결과에 날것의 URL 경로를 그대로 보여준다.
    welfare 의 `/archive/2026-09-06-1-복지뉴스` 처럼 제목과 어긋나는 주소는
    그것만으로 클릭을 깎는다. BreadcrumbList 를 주면 그 자리에
    `사이트명 › 분야` 가 대신 표시된다. URL 을 바꾸지 않고 고칠 수 있는 부분이다.
    """
    site = cfg["site"].rstrip("/")
    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1,
             "name": cfg["site_name"], "item": site + "/"},
            {"@type": "ListItem", "position": 2,
             "name": hub["name"], "item": "%s/%s/" % (site, hub["slug"])},
        ],
    }, ensure_ascii=False, separators=(", ", ": "))
    return ('%s\n<nav class="hub-bc"><a href="/">%s</a> &rsaquo; '
            '<a href="/%s/">%s</a></nav>\n'
            '<script type="application/ld+json">%s</script>\n%s'
            % (BC_B, esc(cfg["site_name"]), hub["slug"], esc(hub["name"]), ld, BC_E))


def related(cfg, hub, pages, me):
    sibs = [s for s in hub["files"] if s != me and s in pages]
    li = "".join('    <li><a href="/%s">%s</a></li>\n' % (s, esc(pages[s]["title"]))
                 for s in sibs)
    if not li:
        li = '    <li>이 분야의 다른 글을 준비하고 있습니다.</li>\n'
    return ('%s\n%s\n<aside class="hub-rel">\n  <h2>같은 분야 다른 글 — %s</h2>\n'
            '  <ul>\n%s  </ul>\n  <p class="hub-more">'
            '<a href="/%s/">%s 전체 보기 →</a></p>\n</aside>\n%s'
            % (RL_B, INJ_CSS, esc(hub["name"]), li, hub["slug"],
               esc(hub["name"]), RL_E))


def inject(src, block, begin, end, where):
    """마커가 있으면 교체, 없으면 지정 위치에 삽입."""
    if begin in src and end in src:
        return re.sub(re.escape(begin) + r".*?" + re.escape(end), lambda _: block,
                      src, count=1, flags=re.S)
    if where == "after_article_open":
        m = re.search(r"<article\b[^>]*>", src, re.I)
        if m:
            return src[:m.end()] + "\n" + block + src[m.end():]
        # 대체 앵커 — <article> 없는 옛 템플릿 (hero 배너 바로 위)
        m = re.search(r'<div\s+class="hero"', src, re.I) or re.search(r"<body\b[^>]*>", src, re.I)
        if not m:
            return None
        at = m.end() if m.group(0).lower().startswith("<body") else m.start()
        return src[:at] + "\n" + block + "\n" + src[at:]
    i = src.rfind("</article>")
    if i < 0:
        # 대체 앵커 — footer 직전, 없으면 </body> 직전
        i = src.rfind("<footer")
        if i < 0:
            i = src.rfind("</body>")
        if i < 0:
            return None
    return src[:i] + block + "\n" + src[i:]



# ── 홈페이지 분야별 색인 블록 ──────────────────────────────────────────────
HM_B, HM_E = "<!-- HUB:HOME:BEGIN -->", "<!-- HUB:HOME:END -->"

HOME_CSS = """<style>
.hub-home{max-width:1100px;margin:34px auto;padding:26px 22px;border:1px solid #e3e8ee;
  border-radius:12px;background:#fff;font-family:'Noto Sans KR',-apple-system,sans-serif}
.hub-home>h2{font-family:'Noto Serif KR',serif;font-size:21px;margin:0 0 4px;color:#12202e;
  border:0;padding:0}
.hub-home>p.hub-home-lede{font-size:14px;color:#5b6672;margin:0 0 22px}
.hub-home-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:22px}
.hub-home-col h3{font-size:15.5px;margin:0 0 4px;font-family:'Noto Sans KR',sans-serif}
.hub-home-col h3 a{color:#12202e;text-decoration:none}
.hub-home-col h3 a:hover{color:#1a5f8a;text-decoration:underline}
.hub-home-col .hub-home-n{font-size:12.5px;color:#8a949f;margin:0 0 9px}
.hub-home-col ul{list-style:none;padding:0;margin:0;border-top:1px solid #eef2f6}
.hub-home-col li{padding:6px 0;font-size:14px;line-height:1.5;border-bottom:1px solid #f4f7fa}
.hub-home-col li a{color:#3a4653;text-decoration:none}
.hub-home-col li a:hover{color:#1a5f8a;text-decoration:underline}
@media(max-width:560px){.hub-home{padding:20px 16px;margin:24px 12px}}
</style>"""


def build_home(cfg, pages):
    cols = ""
    for hub in cfg["hubs"]:
        live = [s for s in hub["files"] if s in pages]
        li = "".join('        <li><a href="/%s">%s</a></li>\n' % (s, esc(pages[s]["title"]))
                     for s in live)
        cols += ('      <div class="hub-home-col">\n'
                 '        <h3><a href="/%s/">%s</a></h3>\n'
                 '        <p class="hub-home-n">%d편</p>\n        <ul>\n%s        </ul>\n'
                 '      </div>\n' % (hub["slug"], esc(hub["name"]), len(live), li))
    return ('%s\n%s\n<section class="hub-home">\n  <h2>분야별로 찾아보기</h2>\n'
            '  <p class="hub-home-lede">주제별로 정리한 %d개 분야, 전체 %d편입니다.</p>\n'
            '  <div class="hub-home-grid">\n%s  </div>\n</section>\n%s'
            % (HM_B, HOME_CSS, len(cfg["hubs"]), len(pages), cols, HM_E))


def inject_home(cfg, pages):
    p = os.path.join(ROOT, "index.html")
    if not os.path.exists(p):
        print("[WARN] index.html 없음 — 홈 블록 건너뜀"); return
    s0 = read(p)
    block = build_home(cfg, pages)
    if HM_B in s0 and HM_E in s0:
        s = re.sub(re.escape(HM_B) + r".*?" + re.escape(HM_E), lambda _: block,
                   s0, count=1, flags=re.S)
    else:
        anchor = cfg.get("home_anchor")
        at = -1
        if anchor:
            m = re.search(anchor, s0, re.I)
            at = m.start() if m else -1
        if at < 0:
            at = s0.rfind("</main>")
        if at < 0:
            at = s0.rfind("</body>")
        if at < 0:
            print("[WARN] 홈 삽입 위치 못 찾음"); return
        s = s0[:at] + "\n" + block + "\n" + s0[at:]
    if s != s0:
        write(p, s)
    print("[OK] index.html 분야별 색인 블록 주입")


def main():
    cfg = json.load(open(CFG, encoding="utf-8"))

    # 1) 기사 메타 수집
    pages, missing = {}, []
    for hub in cfg["hubs"]:
        for stem in hub["files"]:
            p = os.path.join(ROOT, stem + ".html")
            if not os.path.exists(p):
                missing.append(stem)
                continue
            s = read(p)
            pages[stem] = {"title": get_title(s), "desc": get_desc(s), "path": p}
    if missing:
        print("[ERR] hubs.json 에 적힌 파일이 없다: %s" % ", ".join(missing))
        sys.exit(1)

    # 2) 허브 페이지 생성
    for hub in cfg["hubs"]:
        write(os.path.join(ROOT, hub["slug"], "index.html"), build_hub(cfg, hub, pages))
    print("[OK] 허브 %d개 생성" % len(cfg["hubs"]))

    # 3) 기사 주입
    n = 0
    for hub in cfg["hubs"]:
        for stem in hub["files"]:
            p = pages[stem]["path"]
            s0 = read(p)
            s = inject(s0, breadcrumb(cfg, hub), BC_B, BC_E, "after_article_open")
            if s is None:
                print("[WARN] <article> 없음 — 건너뜀: %s" % stem); continue
            s = inject(s, related(cfg, hub, pages, stem), RL_B, RL_E, "before_article_close")
            if s is None:
                print("[WARN] </article> 없음 — 건너뜀: %s" % stem); continue
            if s != s0:
                write(p, s); n += 1
    print("[OK] 기사 %d편 내부링크 주입 (전체 %d편)" % (n, len(pages)))

    # 4) 홈페이지 블록
    inject_home(cfg, pages)


main()
