# Auto Blog — 기능 명세서 (SKILLS.md)

## 스킬 1: AI 콘텐츠 생성 (Content Generation)

**파일:** `src/auto_blog/generator.py`

### 설명
Claude claude-opus-4-7 모델을 사용해 주제를 입력받아 완성된 블로그 글을 자동 생성합니다.

### 입력
| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `topic` | str | 블로그 글 주제 |
| `style` | str | 글쓰기 스타일 (`informative`, `tutorial`, `opinion`, `listicle`) |

### 출력
- YAML frontmatter + Markdown 형식의 `.md` 파일 (`content/` 디렉토리 저장)
- 파일명 형식: `YYYY-MM-DD-slug.md`

### Claude API 설정
- 모델: `claude-opus-4-7`
- Adaptive thinking 활성화
- 시스템 프롬프트 캐싱 (반복 호출 비용 절감)
- 스트리밍으로 실시간 출력

### 생성 콘텐츠 구조
```yaml
---
title: 글 제목
excerpt: 2-3문장 요약
tags: [태그1, 태그2, 태그3]
date: YYYY-MM-DD
---

# 본문 마크다운 (1000-2000단어)
```

---

## 스킬 2: 정적 사이트 빌드 (Site Building)

**파일:** `src/auto_blog/builder.py`

### 설명
`content/` 디렉토리의 Markdown 파일을 읽어 완성된 HTML 정적 사이트를 `output/`에 생성합니다.

### 처리 과정
1. `content/*.md` 파일 읽기
2. YAML frontmatter 파싱 (`python-frontmatter`)
3. Markdown → HTML 변환 (`markdown` 라이브러리)
4. Jinja2 템플릿에 데이터 주입
5. `output/` 디렉토리에 HTML 파일 저장

### 출력 구조
```
output/
├── index.html          # 메인 페이지 (글 목록)
└── posts/
    ├── post-slug-1.html
    └── post-slug-2.html
```

### 템플릿
| 파일 | 역할 |
|------|------|
| `base.html` | 공통 레이아웃, 헤더, 푸터 |
| `index.html` | 글 목록 메인 페이지 |
| `post.html` | 개별 글 페이지 |

---

## 스킬 3: GitHub Pages 배포 (Publishing)

**파일:** `src/auto_blog/publisher.py`

### 설명
빌드된 `output/` 디렉토리를 GitHub Pages에 자동 배포합니다.

### 동작 방식
- `ghp-import` 라이브러리 사용
- `output/` 내용을 `gh-pages` 브랜치에 강제 푸시
- 커밋 메시지: 자동 생성

### 사전 조건
- GitHub 저장소에 연결된 상태
- `gh-pages` 브랜치 또는 GitHub Pages 설정 완료
- `ghp-import` 설치: `pip install ghp-import`

### 배포 URL
`https://Jessica9740.github.io/<저장소명>`

---

## 스킬 4: CLI 인터페이스 (Command Line Interface)

**파일:** `src/auto_blog/cli.py`

### 명령어 목록

| 명령어 | 설명 | 주요 옵션 |
|--------|------|----------|
| `auto-blog generate` | 글 생성만 | `--topic`, `--style` |
| `auto-blog build` | 사이트 빌드만 | - |
| `auto-blog publish` | 배포만 | - |
| `auto-blog run` | 생성 + 빌드 + 배포 | `--topic`, `--style` |

### 글쓰기 스타일

| 스타일 | 설명 |
|--------|------|
| `informative` | 정보 제공형 (기본값) |
| `tutorial` | 단계별 튜토리얼 |
| `opinion` | 의견/분석형 |
| `listicle` | 목록형 (Top 10 등) |

---

## 스킬 5: 사이트 설정 (Configuration)

**파일:** `config/config.yaml`

### 설정 항목

```yaml
site:
  title: 사이트 제목
  description: 사이트 설명
  url: https://username.github.io/repo
  author: 작성자 이름
  language: ko

blog:
  posts_per_page: 10
  default_style: informative
```
