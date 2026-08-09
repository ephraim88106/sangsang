#!/usr/bin/env python3
"""
전체 HTML SEO 일괄 패치
 - canonical 없는 파일: 전체 SEO 블록 주입
 - canonical 있지만 NewsArticle schema 없는 파일: schema만 추가
"""
import re
from pathlib import Path
from urllib.parse import quote

REPO     = Path(__file__).parent.resolve()
BASE_URL = "https://sangsang.ephseed.com"
OG_IMG   = "https://sangsang.ephseed.com/assets/og-default.png"
SITE     = "생생 정보통"
SKIP     = {'index.html','404.html','about.html','contact.html',
            'privacy.html','posts.html','post.html','seo_patch.py'}

def url_of(stem):
    return f"{BASE_URL}/{quote(stem, safe='-')}"

def get_title(html):
    m = re.search(r'<title>(.*?)</title>', html, re.DOTALL|re.I)
    if m:
        t = re.sub(r'<[^>]+>','',m.group(1)).strip()
        return re.sub(r'\s+',' ',t)[:200]
    return ""

def get_desc(html):
    # 1) meta description
    m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']{30,})', html)
    if m: return m.group(1).strip()[:300]
    m = re.search(r'content=["\']([^"\']{30,})["\'][^>]*name=["\']description["\']', html)
    if m: return m.group(1).strip()[:300]
    # 2) 첫 긴 p 태그
    for p in re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL):
        t = re.sub(r'<[^>]+>','',p).strip()
        t = re.sub(r'\s+',' ',t)
        if len(t) > 50: return t[:250]
    return ""

def get_date(stem):
    m = re.match(r'(\d{4}-\d{2}-\d{2})', stem)
    return m.group(1) if m else "2026-01-01"

def je(s):
    return s.replace('\\','\\\\').replace('"','\\"').replace('\n',' ').replace('\r','')

def seo_block(title, desc, url, date):
    return f"""<!-- SEO:AUTO BEGIN -->
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{SITE}">
<meta property="og:title" content="{title[:200]}">
<meta property="og:description" content="{desc[:200]}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="ko_KR">
<meta property="og:image" content="{OG_IMG}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="article:published_time" content="{date}T09:00:00+09:00">
<meta property="article:modified_time" content="{date}T09:00:00+09:00">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title[:200]}">
<meta name="twitter:description" content="{desc[:150]}">
<meta name="twitter:image" content="{OG_IMG}">
<script type="application/ld+json">{{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "{je(title[:110])}",
  "description": "{je(desc[:200])}",
  "url": "{url}",
  "datePublished": "{date}T09:00:00+09:00",
  "dateModified": "{date}T09:00:00+09:00",
  "inLanguage": "ko-KR",
  "publisher": {{"@type":"Organization","name":"{SITE}","url":"{BASE_URL}",
    "logo":{{"@type":"ImageObject","url":"{OG_IMG}","width":1200,"height":630}}}},
  "image": {{"@type":"ImageObject","url":"{OG_IMG}","width":1200,"height":630}}
}}</script>
<!-- SEO:AUTO END -->"""

def schema_block(title, desc, url, date):
    return f"""<!-- SCHEMA:AUTO BEGIN -->
<script type="application/ld+json">{{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "{je(title[:110])}",
  "description": "{je(desc[:200])}",
  "url": "{url}",
  "datePublished": "{date}T09:00:00+09:00",
  "dateModified": "{date}T09:00:00+09:00",
  "inLanguage": "ko-KR",
  "publisher": {{"@type":"Organization","name":"{SITE}","url":"{BASE_URL}",
    "logo":{{"@type":"ImageObject","url":"{OG_IMG}","width":1200,"height":630}}}},
  "image": {{"@type":"ImageObject","url":"{OG_IMG}","width":1200,"height":630}}
}}</script>
<!-- SCHEMA:AUTO END -->"""

full_cnt = schema_cnt = skip_cnt = 0

for fp in sorted(REPO.glob('*.html')):
    if fp.name in SKIP: continue
    try:
        html = fp.read_text('utf-8')
    except: continue

    stem  = fp.stem
    url   = url_of(stem)
    title = get_title(html) or stem.replace('-',' ')
    desc  = get_desc(html)  or title[:200]
    date  = get_date(stem)

    has_canonical = bool(re.search(r'rel=["\']canonical["\']', html))
    has_schema    = 'NewsArticle' in html

    if not has_canonical:
        block = seo_block(title, desc, url, date)
        fp.write_text(html.replace('</head>', block+'\n</head>', 1), 'utf-8')
        print(f"[FULL  ] {fp.name}")
        full_cnt += 1
    elif not has_schema:
        block = schema_block(title, desc, url, date)
        fp.write_text(html.replace('</head>', block+'\n</head>', 1), 'utf-8')
        print(f"[SCHEMA] {fp.name}")
        schema_cnt += 1
    else:
        skip_cnt += 1

print(f"\n결과: 전체SEO={full_cnt}개, schema추가={schema_cnt}개, 이미OK={skip_cnt}개")
