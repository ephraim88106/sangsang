#!/usr/bin/env python3
"""
sangsang index.html 완전 재구성 스크립트
- market-list: 주식보고서만, 날짜 내림차순 최신 10개
- archive-list: 전체 아티클, 날짜 내림차순, 일관된 들여쓰기
- headline-grid: 한국이슈(주식보고서 제외), 최신 10개 (기존 유지)
- ticker-bar: 기존 유지
"""
import re
from pathlib import Path
from html.parser import HTMLParser

REPO = Path('/tmp/sangsang_repo')
IDX  = REPO / 'index.html'

STOCK_SUFFIX = '-주식보고서.html'
DATE_PAT     = re.compile(r'^(\d{4}-\d{2}-\d{2})-(.+)\.html$')
SKIP_FILES   = {'index.html','404.html','about.html','contact.html','privacy.html'}

# ─── 메타 추출 ────────────────────────────────────────────────
class MetaEx(HTMLParser):
    def __init__(self):
        super().__init__(); self.title=''; self.desc=''; self._t=False
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='title': self._t=True
        if tag=='meta' and d.get('name')=='description': self.desc=d.get('content','')
    def handle_data(self,data):
        if self._t: self.title+=data
    def handle_endtag(self,tag):
        if tag=='title': self._t=False

def get_meta(fp):
    try:
        txt = fp.read_text('utf-8')
        p = MetaEx(); p.feed(txt)
        title = re.sub(r'\s+',' ', p.title).strip()
        desc  = re.sub(r'\s+',' ', p.desc).strip() or title[:120]+'…'
        # market-sub or header-subtitle from report
        sub_m = re.search(r'class="(?:market-sub|header-subtitle)"[^>]*>(.*?)</p>', txt, re.DOTALL)
        sub   = re.sub(r'<[^>]+>','', sub_m.group(1)).strip() if sub_m else desc[:120]
        # card-tag / category
        cm = re.search(r'(?:card-tag|category-badge|ns-emoji)["\'][^>]*>([^<]{2,40})<', txt)
        raw = re.sub(r'[^\w·\s가-힣]','', cm.group(1)).strip() if cm else ''
        return title, desc, sub, raw
    except:
        return None, None, None, '일반'

CAT_MAP = {
    '정치':('정치·사법','정치'),'사법':('정치·사법','정치'),
    '경제':('경제·금융','경제'),'금융':('경제·금융','경제'),
    '부동산':('부동산·주거','부동산'),
    '의료':('의료·복지','의료'),'복지':('의료·복지','복지'),
    '교육':('교육·입시','교육'),
    '기술':('기술·AI','기술'),
    '환경':('환경·기후','환경'),'기후':('환경·기후','환경'),
    '취업':('취업·노동','노동'),'노동':('취업·노동','노동'),
    '증시':('증시','증시'),
}
def cat(raw, title=''):
    for k,(l,v) in CAT_MAP.items():
        if k in raw or k in title: return l,v
    return '일반','blue'

# ─── 모든 아티클 스캔 ────────────────────────────────────────
def scan_all():
    stocks = []   # (date_str, fname)
    koreas = []   # (date_str, fname)
    for f in REPO.glob('*.html'):
        if f.name in SKIP_FILES: continue
        m = DATE_PAT.match(f.name)
        if not m: continue
        date_str = m.group(1)
        if f.name.endswith(STOCK_SUFFIX):
            stocks.append((date_str, f.name, f))
        else:
            koreas.append((date_str, f.name, f))
    stocks.sort(key=lambda x: x[0], reverse=True)
    koreas.sort(key=lambda x: x[0], reverse=True)
    return stocks, koreas

# ─── 날짜 포맷 헬퍼 ─────────────────────────────────────────
def short_date(d): return f"{d[5:7]}.{d[8:10]}"
def long_date(d):
    y,mo,day = d[:4],d[5:7].lstrip('0'),d[8:10].lstrip('0')
    return f"{y}년 {mo}월 {day}일"

# ─── market-list 재빌드 ──────────────────────────────────────
def build_market_list(stocks):
    items = []
    for date_str, fname, fp in stocks[:10]:
        title,_,sub,_ = get_meta(fp)
        if not title: title = fname
        sub = sub or ''
        if len(sub)>160: sub=sub[:157]+'...'
        items.append(
            f'        <a href="{fname}" class="market-item">\n'
            f'          <span class="market-date">{short_date(date_str)}</span>\n'
            f'          <div>\n'
            f'            <p class="market-title">{title}</p>\n'
            f'            <p class="market-sub">{sub}</p>\n'
            f'          </div>\n'
            f'          <span class="market-arrow">→</span>\n'
            f'        </a>\n'
        )
    return ''.join(items)

# ─── archive-list 재빌드 (전체 합쳐서 날짜순) ────────────────
def build_archive_list(stocks, koreas):
    all_arts = []
    for date_str, fname, fp in stocks:
        title,_,_,_ = get_meta(fp)
        if not title: title = fname
        all_arts.append((date_str, fname, title, '증시', '증시'))
    for date_str, fname, fp in koreas:
        title,_,_,raw = get_meta(fp)
        if not title: title = fname
        cl, cv = cat(raw, title)
        all_arts.append((date_str, fname, title, cl, cv))
    # 날짜 내림차순 정렬 (같은 날은 주식보고서 먼저)
    all_arts.sort(key=lambda x: (x[0], x[3]=='증시'), reverse=True)
    items = []
    for date_str, fname, title, cl, cv in all_arts:
        items.append(
            f'        <li><a class="archive-item" href="{fname}">\n'
            f'          <span class="archive-date">{short_date(date_str)}</span>\n'
            f'          <span class="archive-title">{title}</span>\n'
            f'          <span class="archive-tag" data-cat="{cv}">{cl}</span>\n'
            f'        </a></li>\n'
        )
    return ''.join(items)

# ─── headline-grid 재빌드 ────────────────────────────────────
def build_headline_grid(koreas):
    items = []
    for date_str, fname, fp in koreas[:10]:
        title,desc,_,raw = get_meta(fp)
        if not title: continue
        cl, cv = cat(raw, title)
        items.append(
            f'        <a href="{fname}" class="headline-card">\n'
            f'          <span class="card-tag" data-cat="{cv}">{cl}</span>\n'
            f'          <h3 class="headline-title">{title}</h3>\n'
            f'          <p class="headline-summary">{desc or ""}</p>\n'
            f'          <div class="headline-meta">\n'
            f'            <span>{long_date(date_str)}</span>\n'
            f'            <span class="headline-link">→ 전문 읽기</span>\n'
            f'          </div>\n'
            f'        </a>\n'
        )
    return ''.join(items)

# ─── 메인 ───────────────────────────────────────────────────
def main():
    html = IDX.read_text('utf-8')
    stocks, koreas = scan_all()
    print(f"주식보고서 {len(stocks)}개, 한국이슈 {len(koreas)}개")

    # 1) market-list 교체
    market_inner = build_market_list(stocks)
    latest_stock = stocks[0][1] if stocks else ''
    new_market = (
        f'      <div class="market-list">\n'
        f'{market_inner}\n'
        f'      </div>\n'
        f'      <div class="more-link-row" style="text-align:right;padding:14px 4px 0;'
        f'border-top:1px solid #e8eef3;margin-top:14px;">\n'
        f'        <a href="{latest_stock}" style="font-size:13px;font-weight:700;'
        f'color:#1a6b3c;text-decoration:none;letter-spacing:0.02em;">증시 전체 보기 →</a>\n'
        f'      </div>\n'
    )
    html = re.sub(
        r'<div class="market-list">.*?</div>\s*<div class="more-link-row"[^>]*>.*?</div>',
        new_market.strip(),
        html, count=1, flags=re.DOTALL
    )
    print(f"[OK] market-list 재구성 ({min(10,len(stocks))}개)")

    # 2) archive-list 교체
    archive_inner = build_archive_list(stocks, koreas)
    html = re.sub(
        r'<ul class="archive-list">.*?</ul>',
        f'<ul class="archive-list">\n{archive_inner}      </ul>',
        html, count=1, flags=re.DOTALL
    )
    print(f"[OK] archive-list 재구성 ({len(stocks)+len(koreas)}개)")

    # 3) headline-grid 교체
    headline_inner = build_headline_grid(koreas)
    html = re.sub(
        r'<div class="headline-grid">.*?</div>\s*<div class="more-link-row"',
        f'<div class="headline-grid">\n{headline_inner}      </div>\n      <div class="more-link-row"',
        html, count=1, flags=re.DOTALL
    )
    print(f"[OK] headline-grid 재구성 ({min(10,len(koreas))}개)")

    IDX.write_text(html, 'utf-8')
    print("✅ index.html 저장 완료")

main()
