import subprocess
import sys
from pathlib import Path


def publish() -> None:
    """output/ 디렉토리를 GitHub Pages (gh-pages 브랜치)에 배포합니다."""
    base_dir = Path(__file__).parent.parent.parent
    output_dir = base_dir / "output"

    if not output_dir.exists() or not any(output_dir.iterdir()):
        print("❌ 빌드된 사이트가 없습니다. 먼저 'auto-blog build'를 실행하세요.")
        sys.exit(1)

    try:
        subprocess.run(["ghp-import", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ghp-import가 설치되어 있지 않습니다.")
        print("   설치 방법: pip install ghp-import")
        sys.exit(1)

    print("🚀 GitHub Pages에 배포 중...")
    result = subprocess.run(
        ["ghp-import", "-n", "-p", "-f", str(output_dir)],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ 배포 완료!")
    else:
        print(f"❌ 배포 실패:\n{result.stderr}")
        sys.exit(1)
