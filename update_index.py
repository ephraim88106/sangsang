#!/usr/bin/env python3
"""
sangsang 레포 auto-indexer (v2.0)
✅ 헤드라인 카드 MAX_HEADLINE_CARDS(7)개 제한 — 증시 섹션과 균형
✅ 아카이브 날짜 내림차순 자동 재정렬
✅ 주식보고서 → 오늘의 증시 섹션 자동 업데이트
"""
import re
from pathlib import Path
from html.parser import HTMLParser

REPO_DIR = Path(__file__).parent
ARTICLE_PATTERN = re.compile(r'^(\d{4}-\d{2}-\d{2})-(.+)\.html$')
STOCK_PATTERN   = re.compile(r'^(\d{4}-\d{2}-\d{2})-주식보고서\.html$')

EXCLUDE_HEADLINE = ['주식보고서', '복지뉴스', 'update_index', '404', 'about',
                    'contact', 'index', 'post', 'posts', 'privacy']
EXCLUDE_ALL      = ['update_index', '404', 'about', 'contact', 'index',
                    'post', 'posts', 'privacy']

MAX_HEADLINE_CARDS = 7   # 증시 섹션 항목 수와 동일하게 고정
MAX_MARKET_ITEMS   = 7   # 오늘의 증시 최대 표시 수

CAT_MAP = {
    '정치': ('정치·사법', '정치'), '사법': ('정치·사법', '정치'),
    '경제': ('경제·금융', '경제'), '금융': ('경제·금융', '경제'),
    '부동산': ('부동산·주거', '부동산'), '주거': ('부동산·주거', '부동산'),
    '의료': ('의료·복지', '의료'), '복지': ('의료·복지', '복지'),
    '교육': ('교육·입시', '교육'), '입시': ('교육·입시', '교육'),
    '기술': ('기술·AI', '기술'), 'AI': ('기술·AI', '기술'),
    '환경': ('환경·기후', '환경'), '기후': ('환경·기후', '환경'),
    '취업': ('취업·노동', '노동'), '노동': ('취업·노동', '노동'),
}


# ─────────────────────── helpers ───────────────────────

class MetaExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ''; self.desc = ''; self._in_title = False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'title':
            self._in_title = True
        if tag == 'meta' and d.get('name') == 'description':
            self.desc = d.get('content', '')

    def handle_data(self, data):
        if self._in_title:
            self.title += data

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False


def get_meta(filepath):
    try:
        txt = filepath.read_text(encoding='utf-8')
        p = MetaExtractor()
        p.feed(txt)
        title = p.title.strip()
        desc  = p.desc.strip() or title[:120] + '…'
        cm = re.search(r'(?:category-badge|card-tag)["\'][^>]*>([^<]{2,40})<', txt)
        raw_cat = cm.group(1).strip() if cm else ''
        raw_cat = re.sub(r'[^\w·\s]', '', raw_cat).strip()
        cat_label, cat_key = '일반', 'blue'
        for kw, (lbl, key) in CAT_MAP.items():
            if kw in raw_cat or kw in title:
                cat_label, cat_key = lbl, key
                break
        return title, desc, cat_label, cat_key
    except Exception:
        return None, None, '일반', 'blue'


def issue_articles_sorted():
    """주식보고서·복지뉴스 제외한 이슈 아티클, 최신순"""
    result = []
    for f in REPO_DIR.glob('*.html'):
        m = ARTICLE_PATTERN.match(f.name)
        if not m:
            continue
        if any(ex in f.name for ex in EXCLUDE_HEADLINE):
            continue
        result.append((m.group(1), f.name, f))
    return sorted(result, reverse=True)


def stock_reports_sorted():
    """주식보고서만, 최신순"""
    result = []
    for f in REPO_DIR.glob('*-주식보고서.html'):
        m = STOCK_PATTERN.match(f.name)
        if not m:
            continue
        result.append((m.group(1), f.name, f))
    return sorted(result, reverse=True)


# ─────────────────────── 헤드라인 그리드 ───────────────────────

def trim_headline_grid(content, max_cards=MAX_HEADLINE_CARDS):
    """headline-grid 카드를 최신 max_cards개로 제한"""
    positions = []
    search_pos = 0
    while True:
        fc = content.find('class="headline-card"', search_pos)
        if fc == -1:
            break
        a_start = content.rfind('<a ', 0, fc)
        if a_start == -1:
            break
        a_end = content.find('</a>', fc)
        if a_end == -1:
            break
        a_end += 4
        positions.append((a_start, a_end))
        search_pos = a_end

    if len(positions) <= max_cards:
        return content

    remove_start = positions[max_cards][0]
    remove_end   = positions[-1][1]
    prefix = content[:remove_start].rstrip(' \t')
    suffix = content[remove_end:].lstrip('\n')
    content = prefix + '\n      ' + suffix
    print(f"  헤드라인 카드 {len(positions)} → {max_cards}개로 정리")
    return content


# ─────────────────────── 아카이브 재정렬 ───────────────────────

def resort_archive(content):
    """archive-list 전체를 날짜 내림차순으로 재정렬"""
    archive_marker = content.find('class="archive-list"')
    if archive_marker == -1:
        return content

    list_gt = content.find('>', archive_marker)
    if list_gt == -1:
        return content
    list_open = list_gt + 1

    list_close = content.find('</ul>', list_open)
    if list_close == -1:
        return content

    archive_inner = content[list_open:list_close]
    li_items = re.findall(r'<li>.*?</li>', archive_inner, re.DOTALL)
    if not li_items:
        return content

    date_re = re.compile(r'href="(\d{4}-\d{2}-\d{2})-([^"]+)"')

    def sort_key(li):
        m = date_re.search(li)
        if m:
            # 같은 날은 파일명 역순 (주식보고서가 이슈 아티클보다 아래)
            return (m.group(1), m.group(2))
        return ('', '')

    li_sorted = sorted(li_items, key=sort_key, reverse=True)

    indent = '        '
    new_inner = ('\n' + indent).join(li_sorted)
    new_content = (
        content[:list_open]
        + '\n' + indent + new_inner + '\n      '
        + content[list_close:]
    )
    return new_content


# ─────────────────────── 오늘의 증시 섹션 ───────────────────────

def find_matching_close_div(content, open_pos):
    """open_pos의 <div …> 에 대응하는 </div> 위치 반환 (depth counting)"""
    depth = 1
    pos = content.find('>', open_pos) + 1
    while pos < len(content) and depth > 0:
        next_open  = content.find('<div', pos)
        next_close = content.find('</div>', pos)
        if next_close == -1:
            return -1
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                return next_close
            pos = next_close + 6
    return -1


def update_market_section(content, max_items=MAX_MARKET_ITEMS):
    """
    오늘의 증시 섹션을 최신 주식보고서 파일 기준으로 재구성.
    - 최신 항목이 이미 있어도 max_items 초과 시 트리밍 실행
    - market-list div의 실제 닫힘 위치를 depth-count 방식으로 정확히 탐색
    """
    stocks = stock_reports_sorted()[:max_items]
    if not stocks:
        return content

    ml_pos = content.find('class="market-list"')
    if ml_pos == -1:
        return content

    # depth counting으로 market-list의 실제 닫히는 </div> 위치 찾기
    ml_close = find_matching_close_div(content, ml_pos)
    if ml_close == -1:
        return content

    market_block = content[ml_pos:ml_close + 6]
    current_count = market_block.count('class="market-item"')
    latest_fname  = stocks[0][1]
    first_href    = re.search(r'href="([^"]+)"', market_block)
    already_latest = first_href and first_href.group(1) == latest_fname

    # 최신 항목 이미 있고, 7개 이하면 변경 불필요
    if already_latest and current_count <= max_items:
        return content

    # 새 market-list 아이템 전체 재구성 (최신 N개)
    items_html = []
    for date_str, fname, fpath in stocks:
        title, desc, _, _ = get_meta(fpath)
        if not title:
            continue
        dp = date_str.split('-')
        short = f"{dp[1]}.{dp[2]}"
        desc_short = (desc or '')[:120]
        item = (
            f'\n        <a href="{fname}" class="market-item">\n'
            f'          <span class="market-date">{short}</span>\n'
            f'          <div>\n'
            f'            <p class="market-title">{title}</p>\n'
            f'            <p class="market-sub">{desc_short}</p>\n'
            f'          </div>\n'
            f'          <span class="market-arrow">→</span>\n'
            f'        </a>\n'
        )
        items_html.append(item)

    if not items_html:
        return content

    new_market = ''.join(items_html)
    ml_inner_start = content.find('>', ml_pos) + 1
    content = content[:ml_inner_start] + new_market + '      ' + content[ml_close:]
    print(f"  오늘의 증시 섹션 → {stocks[0][1]} 기준 {len(items_html)}개로 갱신")
    return content


# ─────────────────────── 메인 ───────────────────────

def run():
    idx = REPO_DIR / 'index.html'
    if not idx.exists():
        print("index.html 없음")
        return False

    content = idx.read_text(encoding='utf-8')
    original = content
    changed = False

    # ① 신규 이슈 아티클 헤드라인 + 아카이브 추가
    arts = issue_articles_sorted()
    for date_str, fname, fpath in arts:
        if fname in content:
            print(f"  이미 등록됨: {fname}")
            continue
        title, desc, cat_label, cat_key = get_meta(fpath)
        if not title:
            print(f"  제목 없음, 건너뜀: {fname}")
            continue

        dp = date_str.split('-')
        display_date = f"{dp[0]}년 {dp[1].lstrip('0')}월 {dp[2].lstrip('0')}일"
        short_date   = f"{dp[1]}.{dp[2]}"
        print(f"  추가: {fname} ({cat_label})")

        # headline-card — 그리드 맨 앞에 삽입
        new_card = (
            f'        <a href="{fname}" class="headline-card">\n'
            f'          <span class="card-tag" data-cat="{cat_key}">{cat_label}</span>\n'
            f'          <h3 class="headline-title">{title}</h3>\n'
            f'          <p class="headline-summary">{desc}</p>\n'
            f'          <div class="headline-meta">\n'
            f'            <span>{display_date}</span>\n'
            f'            <span class="headline-link">→ 전문 읽기</span>\n'
            f'          </div>\n'
            f'        </a>\n'
        )
        fc = content.find('class="headline-card"')
        if fc != -1:
            a_s = content.rfind('<a ', 0, fc)
            if a_s != -1:
                content = content[:a_s] + new_card + content[a_s:]

        # archive-item — 일단 맨 앞에 추가 (resort_archive가 정렬)
        new_arc = (
            f'        <li><a class="archive-item" href="{fname}">\n'
            f'          <span class="archive-date">{short_date}</span>\n'
            f'          <span class="archive-title">{title}</span>\n'
            f'          <span class="archive-tag" data-cat="{cat_key}">{cat_label}</span>\n'
            f'        </a></li>\n'
        )
        arc_pos = content.find('class="archive-list"')
        if arc_pos != -1:
            gt = content.find('>', arc_pos)
            first_li = content.find('<li>', gt + 1)
            if first_li != -1:
                content = content[:first_li] + new_arc + content[first_li:]
            else:
                content = content[:gt + 1] + '\n' + new_arc + content[gt + 1:]
        changed = True

    # ② 신규 주식보고서 아카이브 추가 (헤드라인 제외, archive만)
    stocks = stock_reports_sorted()
    for date_str, fname, fpath in stocks:
        if fname in content:
            print(f"  이미 등록됨(주식): {fname}")
            continue
        title, desc, _, _ = get_meta(fpath)
        if not title:
            continue
        dp = date_str.split('-')
        short_date = f"{dp[1]}.{dp[2]}"
        print(f"  주식보고서 아카이브 추가: {fname}")
        new_arc = (
            f'        <li><a class="archive-item" href="{fname}">\n'
            f'          <span class="archive-date">{short_date}</span>\n'
            f'          <span class="archive-title">{title}</span>\n'
            f'          <span class="archive-tag" data-cat="증시">증시</span>\n'
            f'        </a></li>\n'
        )
        arc_pos = content.find('class="archive-list"')
        if arc_pos != -1:
            gt = content.find('>', arc_pos)
            first_li = content.find('<li>', gt + 1)
            if first_li != -1:
                content = content[:first_li] + new_arc + content[first_li:]
        changed = True

    # ③ 아카이브 날짜 내림차순 재정렬 (항상)
    resorted = resort_archive(content)
    if resorted != content:
        content = resorted
        changed = True
        print("  아카이브 날짜 순 재정렬 완료")

    # ④ 헤드라인 카드 수 제한 (항상)
    trimmed = trim_headline_grid(content, MAX_HEADLINE_CARDS)
    if trimmed != content:
        content = trimmed
        changed = True

    # ⑤ 오늘의 증시 섹션 갱신 (항상)
    updated = update_market_section(content, MAX_MARKET_ITEMS)
    if updated != content:
        content = updated
        changed = True

    if changed:
        idx.write_text(content, encoding='utf-8')
        print("✅ index.html 업데이트 완료")
    else:
        print("변경 사항 없음")
    return changed


if __name__ == '__main__':
    run()
