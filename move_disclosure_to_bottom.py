import glob

MARKER = "사이트 신뢰도 안내 (자동 삽입)"

TOPBAR = """<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;font-size:13px;margin-bottom:10px;font-family:'Noto Sans KR',sans-serif;">
    <a href="index.html" style="font-weight:800;color:#333;text-decoration:none;">← 생생 정보통 홈</a>
    <div style="display:flex;gap:14px;">
      <a href="about.html" style="color:#555;text-decoration:underline;">소개</a>
      <a href="contact.html" style="color:#555;text-decoration:underline;">문의</a>
    </div>
  </div>"""

STOCK_NOTICE = """<div style="background:#fff8e1;border:1px solid #ffb300;border-radius:10px;padding:12px 16px;font-size:12.5px;line-height:1.6;color:#7a4b00;font-family:'Noto Sans KR',sans-serif;">
    ⚠️ <strong>안내:</strong> 이 보고서의 지수 등락률·사건 서술 일부는 AI가 생성한 정보성 시나리오이며 실제 거래소 데이터가 아닙니다. 투자 판단이나 시황 확인의 근거로 사용하지 마시고 반드시 공식 발표를 확인하세요. 자세한 내용은 <a href="about.html" style="color:#7a4b00;">소개 페이지</a>를 참고하세요.
  </div>"""

ISSUE_NOTICE = """<div style="background:#eef6ff;border:1px solid #90caf9;border-radius:10px;padding:12px 16px;font-size:12.5px;line-height:1.6;color:#0d47a1;font-family:'Noto Sans KR',sans-serif;">
    ℹ️ 이 글은 공개된 정부·언론 자료를 바탕으로 AI 편집 보조를 받아 작성되었습니다. 인용된 통계의 원문은 본문 하단 '출처'에서 확인할 수 있으며, 제작 방식은 <a href="about.html" style="color:#0d47a1;">소개 페이지</a>에서 안내합니다.
  </div>"""


def old_block(is_stock):
    notice = STOCK_NOTICE if is_stock else ISSUE_NOTICE
    return f"""<!-- ⓘ {MARKER} -->
<div style="max-width:800px;margin:0 auto;padding:10px 16px 0;box-sizing:border-box;">
  {TOPBAR}
  {notice}
</div>
"""


def new_top_block():
    return f"""<!-- ⓘ {MARKER} - 상단 네비 -->
<div style="max-width:800px;margin:0 auto;padding:10px 16px 0;box-sizing:border-box;">
  {TOPBAR}
</div>
"""


def new_bottom_block(is_stock):
    notice = STOCK_NOTICE if is_stock else ISSUE_NOTICE
    return f"""<!-- ⓘ {MARKER} - 하단 배너 -->
<div style="max-width:800px;margin:24px auto 0;padding:0 16px;box-sizing:border-box;">
  {notice}
</div>
"""


def update_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if "상단 네비" in content or "하단 배너" in content:
        return "already-migrated"

    is_stock = "주식보고서" in path
    old = old_block(is_stock)

    if old not in content:
        return "old-block-not-found"

    content = content.replace(old, new_top_block(), 1)

    if "</body>" not in content:
        return "no-body-close"

    content = content.replace("</body>", new_bottom_block(is_stock) + "</body>", 1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return "ok"


def main():
    files = sorted(glob.glob("2026-*.html") + glob.glob("post-*.html"))
    results = {}
    problems = []
    for f in files:
        r = update_file(f)
        results[r] = results.get(r, 0) + 1
        if r not in ("ok", "already-migrated"):
            problems.append((f, r))
    print(f"Total files: {len(files)}")
    print(results)
    if problems:
        print("Problems:", problems)


if __name__ == "__main__":
    main()
