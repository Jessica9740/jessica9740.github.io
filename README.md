# Auto Blog

Claude AI로 블로그 글을 자동 생성하고 GitHub Pages에 배포하는 프로젝트.

## 빠른 시작

### 1. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일에 ANTHROPIC_API_KEY 입력
```

### 2. Docker로 실행 (권장)

```bash
# 서버 시작
docker compose up -d

# 서버 중지
docker compose down

# 서버 재시작
docker compose restart
```

| URL | 설명 |
|-----|------|
| http://localhost:8080/admin | 글 생성 관리자 UI |
| http://localhost:8080/ | 블로그 홈 |
| http://localhost:8080/posts/{slug}.html | 개별 포스트 |

> **처음 실행 시** Docker Desktop이 켜져 있어야 합니다.  
> Docker Desktop 실행: `open -a Docker`

### 3. 로컬에서 직접 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# 글 생성 + 빌드 + GitHub Pages 배포
auto-blog run --topic "주제"

# 개별 실행
auto-blog generate --topic "주제" --style tutorial
auto-blog build
auto-blog publish
```

**스타일 옵션:** `informative` (기본값) · `tutorial` · `opinion` · `listicle`

## 개발 환경 재구성

소스 코드 변경 후 Docker 이미지를 재빌드합니다.

```bash
docker compose up -d --build
```

## GitHub Pages 배포

1. [github.com/{username}/auto-blog/settings/pages](https://github.com/Jessica9740/auto-blog/settings/pages) 접속
2. **Source** → `Deploy from a branch`
3. **Branch** → `gh-pages` / `/ (root)` 선택 후 **Save**

배포 후 주소: https://Jessica9740.github.io/auto-blog
