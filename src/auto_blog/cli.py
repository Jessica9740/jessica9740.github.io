import click

from .builder import build_site
from .generator import generate_post
from .publisher import publish


@click.group()
def cli():
    """Auto Blog — Claude AI로 블로그를 자동 생성하고 GitHub Pages에 배포합니다."""
    pass


@cli.command()
@click.option("--topic", "-t", required=True, help="블로그 글 주제")
@click.option(
    "--style",
    "-s",
    default="informative",
    type=click.Choice(["informative", "tutorial", "opinion", "listicle"]),
    help="글쓰기 스타일",
    show_default=True,
)
def generate(topic: str, style: str) -> None:
    """Claude AI로 새 블로그 글을 생성합니다."""
    generate_post(topic, style)


@cli.command()
def build() -> None:
    """Markdown 파일에서 정적 HTML 사이트를 빌드합니다."""
    print("\n🔨 사이트 빌드 중...")
    build_site()


@cli.command("publish")
def publish_cmd() -> None:
    """빌드된 사이트를 GitHub Pages에 배포합니다."""
    publish()


@cli.command()
@click.option("--topic", "-t", required=True, help="블로그 글 주제")
@click.option(
    "--style",
    "-s",
    default="informative",
    type=click.Choice(["informative", "tutorial", "opinion", "listicle"]),
    help="글쓰기 스타일",
    show_default=True,
)
def run(topic: str, style: str) -> None:
    """글 생성 → 사이트 빌드 → GitHub Pages 배포를 한 번에 실행합니다."""
    generate_post(topic, style)
    print("\n🔨 사이트 빌드 중...")
    build_site()
    publish()
