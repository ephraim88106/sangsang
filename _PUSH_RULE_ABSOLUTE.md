# 🔴 절대 규칙 — 주식보고서 생성 시 필수 행동

**주인님(이남호, namho1123@gmail.com)께서 2026-04-21, 2026-04-24 두 차례 지시:**

## 단 하나의 행동 지침
주식보고서 HTML 파일(`YYYY-MM-DD-주식보고서.html`)을 만들었다면 **100% 예외 없이 GitHub에 푸시한다.**

## 레포
- URL: `https://github.com/ephraim88106/sangsang`
- Branch: `main`
- User: `ephraim88106`
- Email: `namho1123@gmail.com`

## 🔐 토큰 관리 — 절대 이 파일에 하드코딩 금지
GitHub secret scanning이 토큰 포함 파일의 푸시를 차단한다. 그래서 토큰은 반드시 별도 파일로 분리한다.

- **토큰 파일 경로(Windows):** `C:\Users\inseo\Desktop\주식보고서\.secrets\github_token`
- **Bash 경로:** `/sessions/<현재세션>/mnt/Desktop/주식보고서/.secrets/github_token`
- 이 파일은 `.gitignore`에 추가되어 **절대 커밋되지 않음**
- 토큰이 만료/유출되면 이 파일만 새 토큰으로 덮어쓰면 됨

## 커맨드 (복붙용 — 토큰은 파일에서 읽는다)
```bash
SESSION=$(ls /sessions/ | head -1)   # 현재 세션 자동 감지
TOKEN_FILE="/sessions/${SESSION}/mnt/Desktop/주식보고서/.secrets/github_token"
TOKEN=$(cat "$TOKEN_FILE" | tr -d '\n\r')

cd /tmp && rm -rf sangsang-repo
git clone "https://ephraim88106:${TOKEN}@github.com/ephraim88106/sangsang.git" sangsang-repo
cd sangsang-repo

DATE=$(date +%Y-%m-%d)
cp "/sessions/${SESSION}/mnt/Desktop/주식보고서/${DATE}-주식보고서.html" "./${DATE}-주식보고서.html"

git config user.email "namho1123@gm