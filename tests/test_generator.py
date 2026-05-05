"""generator 모듈 단위 테스트."""

from auto_blog.generator import STYLE_PROMPTS


def test_style_prompts_exist():
    expected = ["informative", "tutorial", "opinion", "listicle"]
    for style in expected:
        assert style in STYLE_PROMPTS, f"스타일 '{style}'이 STYLE_PROMPTS에 없습니다."


def test_style_prompts_not_empty():
    for style, prompt in STYLE_PROMPTS.items():
        assert prompt.strip(), f"스타일 '{style}'의 프롬프트가 비어 있습니다."
