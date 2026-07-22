#!/usr/bin/env python3
"""
sangsang 레포 auto-indexer
새 아티클 HTML이 푸시되면 index.html headline-grid & archive 섹션을 자동 업데이트한다.
"""
import re, sys
from pathlib import Path
from html.parser import HTMLParser

REPO_DIR = Path(__file__).parent
ARTICLE_PATTERN = re.compile(r'^(\d{4}-\d{2}-\d{2})-(.+)\.html$')
EXCLUDE = ['주식보고서', '복지뉴스', 'update_index', '404', 'about',
           'contact', 'index', 'post', 'posts', 'privacy']

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

class MetaExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ''; self.desc = ''; self._in_title = False
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'title': self._in_title = True
        if tag == 'meta' and d.get('name') == 'description':
            self.desc = d.get('content', '')
    def handle_data(self, data):
        if self._in_title: self.title += data
    def handle_endtag(self, tag):
        if tag == 'title': self._in_title = False

def get_meta(filepath):
    try:
        txt = filepath.read_text(encoding='utf-8')
        p = MetaExtractor(); p.feed(txt)
        title = p.title.strip()
        desc  = p.desc.strip() or title[:100] + '…'
        # category-badge or card-tag
        cm = re.search(r'(?:category-badge|card-tag)["\'][^>]*>([^<]{2,40})<', txt)
        raw_cat = cm.group(1).strip() if cm else ''
        # strip emoji
        raw_cat = re.sub(r'[^\w·\s]', '', raw_cat).strip()
        cat_label, cat_key = '일반', 'blue'
        for kw, (lbl, key) in CAT_MAP.items():
            if kw in raw_cat or kw in title:
                cat_label, cat_key = lbl, key; break
        return title, desc, cat_label, cat_key
    except Exception as e:
        return None, None, '일반', 'blue'

def articles_sorted():
    result = []
    for f in REPO_DIR.glob('*.html'):
        m = ARTICLE_PATTERN.match(f.name)
        if not m: continue
        if any(ex in f.name for ex in EXCLUDE): continue
        result.append((m.group(1), f.name, f))
    return sorted(result, reverse=True)

def run():
    idx = REPO_DIR / 'index.html'
    if not idx.exists():
        print("index.html 없음"); return False
    content = idx.read_text(encoding='utf-8')
    original = content
    arts = articles_sorted()
    changed = False

    for date_str, fname, fpath in arts:
        if fname in content:
            print(f"  이미 등록됨: {fname}"); continue
        title, desc, cat_label, cat_key = get_meta(fpath)
        if not title:
            print(f"  제목 없음, 건너뜀: {fname}"); continue

        dp = date_str.split('-')
        display_date = f"{dp[0]}년 {dp[1].lstrip('0')}월 {dp[2].lstrip('0')}일"
        short_date   = f"{dp[1]}.{dp[2]}"
        print(f"  추가: {fname} ({cat_label})")

        # ── headline-card 삽입 (첫 번째 headline-card 앞) ──
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

        # ── archive-item 삽입 (같은날 주식보고서 뒤, 없으면 최상단) ──
        new_arc = (
            f'        <li><a class="archive-item" href="{fname}">\n'
            f'          <span class="archive-date">{short_date}</span>\n'
            f'          <span class="archive-title">{title}</span>\n'
            f'          <span class="archive-tag" data-cat="{cat_key}">{cat_label}</span>\n'
            f'        </a></li>\n'
        )
        stock_ref = f'href="{date_str}-주식보고서.html"'
        if stock_ref in content:
            sp = content.find(stock_ref)
            le = content.find('</li>', sp)
            if le != -1:
                content = content[:le+5] + '\n' + new_arc + content[le+5:]
        else:
            fa = content.find('class="archive-item"')
            if fa != -1:
                ls = content.rfind('<li>', 0, fa)
                if ls != -1:
                    content = content[:ls] + new_arc + content[ls:]
        changed = True

    if changed:
        idx.write_text(content, encoding='utf-8')
        print("✅ index.html 업데이트 완료")
    else:
        print("변경 사항 없음")
    return changed

if __name__ == '__main__':
    run()
