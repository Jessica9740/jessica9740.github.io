# Auto Blog — CLAUDE.md

## 프로젝트 개요

Claude API로 블로그 글을 자동 생성하고, 정적 HTML 사이트로 빌드해 GitHub Pages에 자동 배포하는 프로젝트.

## 아키텍처

```
auto-blog/
├── src/auto_blog/
│   ├── generator.py     # Claude API → Markdown 생성
│   ├── builder.py       # Markdown → 정적 HTML 빌드
│   ├── publisher.py     # GitHub Pages 배포
│   ├── cli.py           # CLI 진입점
│   └── templates/       # Jinja2 HTML 템플릿
├── content/             # 생성된 마크다운 파일
├── output/              # 빌드된 정적 사이트 (git-ignored)
├── config/config.yaml   # 사이트 설정
└── SKILLS.md            # 기능 명세서
```

## 개발 환경 설정

```bash
pip install -e ".[dev]"
cp .env.example .env
# .env에 ANTHROPIC_API_KEY 추가
```

## 주요 명령어

```bash
# 블로그 글 생성
auto-blog generate --topic "Python 비동기 프로그래밍" --style tutorial

# 정적 사이트 빌드
auto-blog build

# GitHub Pages 배포
auto-blog publish

# 생성 + 빌드 + 배포 한 번에
auto-blog run --topic "머신러닝 기초"
```

## 핵심 파일

| 파일 | 역할 |
|------|------|
| `src/auto_blog/generator.py` | Claude API 호출, Markdown 파일 생성 |
| `src/auto_blog/builder.py` | Markdown 파싱, HTML 사이트 빌드 |
| `src/auto_blog/publisher.py` | ghp-import로 gh-pages 브랜치 배포 |
| `config/config.yaml` | 사이트 제목, 설명, 작성자 등 설정 |
| `src/auto_blog/templates/` | base.html, index.html, post.html |

## Claude API 사용 규칙

- 모델: `claude-opus-4-7` (adaptive thinking 활성화)
- 시스템 프롬프트에 `cache_control` 적용 → 반복 호출 비용 절감
- 스트리밍 출력으로 실시간 진행 상황 표시
- 생성 형식: YAML frontmatter + Markdown 본문

## 새 기능 추가 방법

- CLI 명령어 추가: `src/auto_blog/cli.py`
- 글 스타일 추가: `generator.py`의 `STYLE_PROMPTS` 딕셔너리
- 템플릿 수정: `src/auto_blog/templates/`
- 사이트 설정: `config/config.yaml`

## 테스트

```bash
pytest tests/
```

## 의존성

- `anthropic` — Claude API SDK
- `jinja2` — HTML 템플릿 엔진
- `markdown` — Markdown → HTML 변환
- `python-frontmatter` — YAML frontmatter 파싱
- `click` — CLI 프레임워크
- `ghp-import` — GitHub Pages 배포
