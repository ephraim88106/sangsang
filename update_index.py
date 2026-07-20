#!/usr/bin/env python3
"""
update_index.py — sangsang 레포 index.html 자동 업데이터
사용법: python3 update_index.py <html파일명> <카테고리> <제목> <요약>

예시:
  python3 update_index.py 2026-07-20-example.html "기술·AI" "제목" "요약"
  python3 update_index.py 2026-07-20-주식보고서.html "증시" "시장 브리핑 제목" "요약"

카테고리 옵션: 기술·AI / 취업·노동 / 의료·복지 / 부동산·주거 / 정치·사법
               경제·금융 / 교육·입시 / 환경·기후 / 증시 / 복지
"""

import sys
import re
import os
from datetime import datetime

INDEX_PATH = os.path.join(os.path.dirname(__file__), 'index.html')

CAT_TAG_MAP = {
    '기술·AI': ('기술', '기술·AI'),
    '취업·노동': ('노동', '취업·노동'),
    '의료·복지': ('복지', '의료·복지'),
    '부동산·주거': ('부동산', '부동산·주거'),
    '정치·사법': ('사회', '정치·사법'),
    '경제·금융': ('경제', '경제·금융'),
    '교육·입시': ('교육', '교육·입시'),
    '환경·기후': ('환경', '환경·기후'),
    '증시': ('증시', '증시'),
    '복지': ('복지', '복지'),
}

def extract_date_from_filename(filename):
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', filename)
    if m:
        return m.group(2) + '.' + m.group(3)  # MM.DD
    return '??'

def add_to_index(filename, category, title, summary):
    if not os.path.exists(INDEX_PATH):
        print(f"[ERROR] index.html 없음: {INDEX_PATH}")
        return False

    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    # 이미 등록됐으면 스킵
    if filename in html:
        print(f"[SKIP] 이미 등록됨: {filename}")
        return True

    date_str = extract_date_from_filename(filename)
    cat_data = CAT_TAG_MAP.get(category, ('일반', category))
    is_market = '주식보고서' in filename or category == '증시'

    # ── 아카이브에 추가 ──
    archive_item = f'''        <li><a class="archive-item" href="{filename}">
          <span class="archive-date">{date_str}</span>
          <span class="archive-title">{title}</span>
          <span class="archive-tag" data-cat="{cat_data[0]}">{cat_data[1]}</span>
        </a></li>
'''
    archive_marker = '      <ul class="archive-list">'
    if archive_marker in html:
        html = html.replace(
            archive_marker + '\n',
            archive_marker + '\n' + archive_item
        )
        print(f"[OK] 아카이브 추가: {filename}")
    else:
        print("[WARN] archive-list 마커 없음")

    # ── 증시면 market-list에도 추가 (oldest 제거해서 4개 유지) ──
    if is_market:
        market_item = f'''        <a href="{filename}" class="market-item">
          <span class="market-date">{date_str}</span>
          <div>
            <p class="market-title">{title}</p>
            <p class="market-sub">{summary}</p>
          </div>
          <span class="market-arrow">→</span>
        </a>

'''
        market_list_open = '      <div class="market-list">'
        if market_list_open in html:
            html = html.replace(
                market_list_open + '\n',
                market_list_open + '\n' + market_item
            )
            # 5번째 market-item 제거 (4개 유지)
            items = re.findall(r'<a href="[^"]*" class="market-item">.*?</a>', html, re.DOTALL)
            if len(items) > 4:
                html = html.replace(items[4], '', 1)
            print(f"[OK] 시장 섹션 추가: {filename}")

    # ── 이슈 아티클이면 헤드라인에도 추가 ──
    if not is_market and summary:
        headline_card = f'''        <a href="{filename}" class="headline-card">
          <span class="card-tag" data-cat="{cat_data[0]}">{cat_data[1]}</span>
          <h3 class="headline-title">{title}</h3>
          <p class="headline-summary">{summary}</p>
          <div class="headline-meta">
            <span>2026년 {date_str.replace('.', '월 ')}일</span>
            <span class="headline-link">→ 전문 읽기</span>
          </div>
        </a>

'''
        headline_marker = '      <div class="headline-grid">'
        if headline_marker in html:
            html = html.replace(
                headline_marker + '\n',
                headline_marker + '\n' + headline_card
            )
            print(f"[OK] 헤드라인 추가: {filename}")

    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(html)

    return True


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("사용법: python3 update_index.py <파일명> <카테고리> <제목> <요약>")
        sys.exit(1)
    filename = sys.argv[1]
    category = sys.argv[2]
    title    = sys.argv[3]
    summary  = sys.argv[4]
    ok = add_to_index(filename, category, title, summary)
    sys.exit(0 if ok else 1)
