import re
import sys
from datetime import datetime
from pathlib import Path

import anthropic
import frontmatter

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
date: [오늘 날짜 YYYY-MM-DD 형식]
---

[마크다운 본문 - 1000~2000단어]

Rules:
- 제목은 흥미롭고 SEO 친화적으로 (콜론 포함 시 반드시 따옴표로 감쌀 것: title: "제목: 부제목")
- excerpt는 독자의 관심을 끌도록
- tags는 3~5개의 관련 키워드
- 본문은 ## 헤더, **굵게**, 목록 등 마크다운 사용
- 한국어로 작성
- 출력은 반드시 --- 로 시작하는 YAML frontmatter부터 시작"""


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

    # YAML frontmatter 파싱
    try:
        post = frontmatter.loads(raw_content)
    except Exception as e:
        print(f"⚠️  frontmatter 파싱 실패, 기본값 사용: {e}")
        post = frontmatter.Post(raw_content)
        post.metadata = {
            "title": topic,
            "excerpt": "",
            "tags": [],
            "date": datetime.now().strftime("%Y-%m-%d"),
        }

    title = post.metadata.get("title", topic)
    date = post.metadata.get("date", datetime.now().strftime("%Y-%m-%d"))

    # 파일명용 슬러그 생성
    slug = re.sub(r"[^a-z0-9가-힣]+", "-", title.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    filename = f"{date}-{slug}.md"

    content_dir = Path(__file__).parent.parent.parent / "content"
    content_dir.mkdir(exist_ok=True)
    output_path = content_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(raw_content)

    print(f"\n✅ 저장 완료: {output_path}")
    return output_path
