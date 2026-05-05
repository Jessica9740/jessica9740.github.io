import re
import shutil
from collections import defaultdict
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
    parts = filename_stem.split("-")
    if len(parts) > 3 and parts[0].isdigit() and len(parts[0]) == 4:
        return "-".join(parts[3:])
    return filename_stem


def _cat_slug(category: str) -> str:
    s = re.sub(r"/", "-", category)
    s = re.sub(r"[^a-z0-9가-힣\-]+", "", s.lower())
    return s.strip("-") or "etc"


def build_site() -> None:
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
    (output_dir / "categories").mkdir()

    md_converter = markdown.Markdown(extensions=["fenced_code", "tables", "toc", "nl2br"])

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

        category = post_data_raw.metadata.get("category", "기타")
        cat_slug = _cat_slug(category)

        post_data = {
            "title": post_data_raw.metadata.get("title", slug),
            "excerpt": post_data_raw.metadata.get("excerpt", ""),
            "tags": tags,
            "date": str(post_data_raw.metadata.get("date", "")),
            "slug": slug,
            "content": html_content,
            "url": f"/posts/{slug}.html",
            "category": category,
            "category_url": f"/categories/{cat_slug}/",
        }
        posts.append(post_data)

        post_template = env.get_template("post.html")
        post_html = post_template.render(post=post_data, config=config)
        (output_dir / "posts" / f"{slug}.html").write_text(post_html, encoding="utf-8")
        print(f"  📄 {post_data['title'][:50]}")

    # 카테고리 그룹핑
    cat_map = defaultdict(list)
    for p in posts:
        cat_map[p["category"]].append(p)
    categories = sorted(cat_map.keys())

    ctx = {"config": config, "categories": categories}

    # 카테고리별 페이지 생성
    cat_template = env.get_template("category.html")
    for cat, cat_posts in cat_map.items():
        cdir = output_dir / "categories" / _cat_slug(cat)
        cdir.mkdir(parents=True, exist_ok=True)
        cat_html = cat_template.render(category=cat, posts=cat_posts, **ctx)
        (cdir / "index.html").write_text(cat_html, encoding="utf-8")

    # 인덱스
    index_html = env.get_template("index.html").render(posts=posts, cat_map=dict(cat_map), **ctx)
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")

    # 글 목록
    posts_index_html = env.get_template("posts_index.html").render(
        posts=posts, cat_map=dict(cat_map), **ctx
    )
    (output_dir / "posts" / "index.html").write_text(posts_index_html, encoding="utf-8")

    print(f"\n✅ 빌드 완료: {len(posts)}개 글, {len(categories)}개 카테고리 → {output_dir}")
