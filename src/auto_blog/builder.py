import re
import shutil
from pathlib import Path

import frontmatter
import markdown
import yaml
from jinja2 import Environment, FileSystemLoader


def _load_config() -> dict:
    config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _slugify(filename_stem: str) -> str:
    """파일명에서 날짜 prefix를 제거하고 슬러그를 반환합니다."""
    parts = filename_stem.split("-")
    if len(parts) > 3 and parts[0].isdigit() and len(parts[0]) == 4:
        return "-".join(parts[3:])
    return filename_stem


def build_site() -> None:
    """content/ 의 Markdown 파일을 읽어 output/ 에 정적 HTML 사이트를 생성합니다."""
    base_dir = Path(__file__).parent.parent.parent
    content_dir = base_dir / "content"
    output_dir = base_dir / "output"
    templates_dir = Path(__file__).parent / "templates"

    config = _load_config()

    env = Environment(loader=FileSystemLoader(str(templates_dir)))

    output_dir.mkdir(exist_ok=True)
    for item in output_dir.iterdir():
        shutil.rmtree(item) if item.is_dir() else item.unlink()
    (output_dir / "posts").mkdir()

    md_converter = markdown.Markdown(
        extensions=["fenced_code", "tables", "toc", "nl2br"],
    )

    posts = []
    md_files = sorted(
        [f for f in content_dir.glob("*.md") if f.name != ".gitkeep"],
        reverse=True,
    )

    for md_file in md_files:
        try:
            post_data_raw = frontmatter.load(md_file)
        except Exception as e:
            print(f"  ⚠️  {md_file.name} frontmatter 파싱 실패, 건너뜀: {e}")
            continue
        md_converter.reset()
        html_content = md_converter.convert(post_data_raw.content)

        slug = _slugify(md_file.stem)
        tags = post_data_raw.metadata.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]

        post_data = {
            "title": post_data_raw.metadata.get("title", slug),
            "excerpt": post_data_raw.metadata.get("excerpt", ""),
            "tags": tags,
            "date": str(post_data_raw.metadata.get("date", "")),
            "slug": slug,
            "content": html_content,
            "url": f"/posts/{slug}.html",
        }
        posts.append(post_data)

        post_template = env.get_template("post.html")
        post_html = post_template.render(post=post_data, config=config)
        post_output = output_dir / "posts" / f"{slug}.html"
        post_output.write_text(post_html, encoding="utf-8")
        print(f"  📄 {post_data['title'][:50]}")

    index_template = env.get_template("index.html")
    index_html = index_template.render(posts=posts, config=config)
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")

    posts_index_template = env.get_template("posts_index.html")
    posts_index_html = posts_index_template.render(posts=posts, config=config)
    (output_dir / "posts" / "index.html").write_text(posts_index_html, encoding="utf-8")

    print(f"\n✅ 빌드 완료: {len(posts)}개 글 → {output_dir}")
