import re
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
import frontmatter
import httpx

STYLE_PROMPTS = {
    "informative": "정보 제공형으로. 사실과 근거를 바탕으로 독자가 새로운 것을 배울 수 있도록",
    "tutorial": "단계별 튜토리얼 형식으로. 코드 예시를 포함하고 따라할 수 있도록",
    "opinion": "의견/분석형으로. 주제에 대한 통찰력 있는 관점을 제시하도록",
    "listicle": "목록형으로. '5가지', '10가지' 형식으로 핵심 포인트를 정리하도록",
}

SYSTEM_PROMPT = """You are an expert blog writer who creates engaging, well-researched content in Korean.

Generate a complete blog post in this exact format:

---
title: [제목]
excerpt: [2-3문장 요약]
tags: [태그1, 태그2, 태그3]
date: [오늘 날짜 YYYY-MM-DD HH:MM 형식]
---

[마크다운 본문 - 1000~2000단어]

## 참고 자료

- [출처 제목](실제 URL)
- [출처 제목](실제 URL)
- [출처 제목](실제 URL)

Rules:
- 제목은 흥미롭고 SEO 친화적으로 (콜론 포함 시 반드시 따옴표로 감쌀 것: title: "제목: 부제목")
- excerpt는 독자의 관심을 끌도록
- tags는 3~5개의 관련 키워드
- 본문은 ## 헤더, **굵게**, 목록 등 마크다운 사용
- 한국어로 작성
- 출력은 반드시 --- 로 시작하는 YAML frontmatter부터 시작
- 참고 자료는 Wikipedia, 공식 문서(docs.python.org, developer.mozilla.org 등), GitHub, 공식 사이트 등 실제 존재하는 URL만 사용. 3~5개 포함."""


def _generate_image(title: str, tags: list, slug: str, content_dir: Path) -> Optional[str]:
    """Pollinations.ai로 블로그 헤더 이미지를 생성하고 저장합니다."""
    tag_str = ", ".join(tags[:3]) if tags else ""
    prompt = f"professional blog header image, {title}, {tag_str}, minimalist, modern, flat design, no text"
    encoded = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1200&height=630&nologo=true&model=flux&seed=42"
    )

    images_dir = content_dir / "images"
    images_dir.mkdir(exist_ok=True)
    img_path = images_dir / f"{slug}.jpg"

    print(f"\n🎨 이미지 생성 중...", flush=True)
    try:
        resp = httpx.get(url, timeout=60, follow_redirects=True)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
            img_path.write_bytes(resp.content)
            print(f"✅ 이미지 저장: {img_path.name}")
            return f"/images/{slug}.jpg"
        else:
            print(f"⚠️  이미지 생성 실패 (status {resp.status_code})")
    except Exception as e:
        print(f"⚠️  이미지 생성 실패: {e}")
    return None


def generate_post(topic: str, style: str = "informative") -> Path:
    """Claude API로 블로그 글을 생성하고 마크다운 파일로 저장합니다."""
    client = anthropic.Anthropic()
    style_instruction = STYLE_PROMPTS.get(style, STYLE_PROMPTS["informative"])

    print(f"\n✍️  주제: {topic} ({style})")
    print("─" * 50)

    content_parts = []

    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=4000,
        thinking={"type": "adaptive"},
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"다음 주제로 블로그 글을 작성해주세요: {topic}\n\n스타일: {style_instruction}",
            }
        ],
    ) as stream:
        for text in stream.text_stream:
            content_parts.append(text)
            print(text, end="", flush=True)

    print("\n" + "─" * 50)

    raw_content = "".join(content_parts)

    try:
        post = frontmatter.loads(raw_content)
    except Exception as e:
        print(f"⚠️  frontmatter 파싱 실패, 기본값 사용: {e}")
        post = frontmatter.Post(raw_content)
        post.metadata = {
            "title": topic,
            "excerpt": "",
            "tags": [],
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

    title = post.metadata.get("title", topic)
    tags = post.metadata.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]

    now = datetime.now()
    post.metadata["date"] = now.strftime("%Y-%m-%d %H:%M")

    slug = re.sub(r"[^a-z0-9가-힣]+", "-", title.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    filename = f"{now.strftime('%Y-%m-%d')}-{slug}.md"

    content_dir = Path(__file__).parent.parent.parent / "content"
    content_dir.mkdir(exist_ok=True)

    # 이미지 생성
    image_path = _generate_image(title, tags, slug, content_dir)
    if image_path:
        post.metadata["image"] = image_path

    output_path = content_dir / filename
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))

    print(f"\n✅ 저장 완료: {output_path}")
    return output_path
