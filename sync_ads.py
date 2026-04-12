import os
import re
import glob

# The target content from index.html
NEW_AD_BLOCK = """  <!-- 우측 고정 사이드바 광고 -->
  <div class="fixed-side-ad">
    <!-- 쿠팡 파트너스 배너 -->
    <div style="width:300px;margin-bottom:20px;background:linear-gradient(135deg,#514FE4,#FF6B35);border-radius:12px;padding:20px;box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
      <h4 style="color:#fff;font-size:16px;font-weight:800;margin:0 0 10px;">🛒 오늘의 쇼핑 추천!</h4>
      <p style="color:rgba(255,255,255,0.9);font-size:13px;margin:0 0 15px;line-height:1.4;">쿠팡 로켓배송으로 빠르고 편리하게 쇼핑하세요!</p>
      <a href="https://link.coupang.com/a/eiMhxP" target="_blank" rel="noopener noreferrer" style="display:block;text-align:center;background:#ffc107;color:#000;padding:10px;border-radius:6px;font-weight:700;text-decoration:none;font-size:13px;">쿠팡에서 확인하기 →</a>
      <p style="font-size:10px;color:rgba(255,255,255,0.6);margin-top:10px;text-align:center;">이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받습니다.</p>
    </div>

    <ins class="kakao_ad_area" style="display:none;"
      data-ad-unit = "DAN-KMCr4AoIjIDsi9XA"
      data-ad-width = "320"
      data-ad-height = "480"></ins>

    <ins class="kakao_ad_area" style="display:none;"
      data-ad-unit = "DAN-EVlth33UH8CTDu2u"
      data-ad-width = "320"
      data-ad-height = "100"></ins>
    <script type="text/javascript" src="//t1.daumcdn.net/kas/static/ba.min.js" async></script>
  </div>"""

def update_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Remove existing fixed-side-ad blocks and comments
    # Matches <div class="fixed-side-ad">...</div> and any leading/trailing comments or script tags related to it
    # This is tricky because the content varies.
    # Let's try to find the div and its closing tag.
    
    # Remove any existing fixed-side-ad div and its content
    content = re.sub(r'<!-- 우측 고정 사이드바 광고 -->\s*<div class="fixed-side-ad">.*?</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<div class="fixed-side-ad">.*?</div>', '', content, flags=re.DOTALL)
    
    # Sometimes there might be leftover comments or script tags if they were outside the div in some versions
    # But usually they are inside.
    
    # 2. Find insertion point
    # We want to insert after <canvas id="season-canvas"></canvas> if it exists, otherwise after <body>
    
    if '<canvas id="season-canvas"></canvas>' in content:
        placeholder = '<canvas id="season-canvas"></canvas>'
        content = content.replace(placeholder, placeholder + "\n\n" + NEW_AD_BLOCK)
    else:
        # Match <body> with any attributes and optional newline/whitespace
        match = re.search(r'(<body[^>]*>)', content, re.IGNORECASE)
        if match:
            body_tag = match.group(1)
            content = content.replace(body_tag, body_tag + "\n\n" + NEW_AD_BLOCK)
        else:
            print(f"Warning: No <body> tag found in {file_path}")
            return

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {file_path}")

# Target files: 2026-*.html and post-*.html (excluding index.html itself if it matches, but the prompt says match index.html's layout)
files = glob.glob('2026-*.html') + glob.glob('post-*.html')
for f in files:
    if os.path.basename(f) != 'index.html':
        update_file(f)
