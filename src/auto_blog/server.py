import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()

HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Auto Blog</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: #f0f2f5; color: #1a1a1a; min-height: 100vh; }
    .wrap { max-width: 680px; margin: 0 auto; padding: 60px 24px 80px; }
    h1 { font-size: 2rem; font-weight: 800; letter-spacing: -0.5px; margin-bottom: 6px; }
    .sub { color: #666; margin-bottom: 40px; font-size: 0.95rem; }
    .card { background: #fff; border-radius: 16px; padding: 36px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.07); }
    label { display: block; font-weight: 600; font-size: 0.85rem;
            text-transform: uppercase; letter-spacing: 0.5px; color: #555; margin-bottom: 8px; }
    input, select {
      width: 100%; padding: 12px 16px; border: 1.5px solid #e0e0e0;
      border-radius: 10px; font-size: 1rem; outline: none;
      transition: border-color 0.15s; margin-bottom: 24px; background: #fafafa;
    }
    input:focus, select:focus { border-color: #6366f1; background: #fff; }
    button {
      width: 100%; padding: 14px; background: #6366f1; color: #fff;
      border: none; border-radius: 10px; font-size: 1rem; font-weight: 700;
      cursor: pointer; transition: background 0.15s, transform 0.1s;
    }
    button:hover:not(:disabled) { background: #4f46e5; transform: translateY(-1px); }
    button:disabled { background: #a5b4fc; cursor: not-allowed; transform: none; }
    .terminal {
      margin-top: 28px; background: #0d1117; color: #c9d1d9;
      border-radius: 12px; padding: 24px; font-family: 'Menlo', 'Courier New', monospace;
      font-size: 0.82rem; line-height: 1.7; min-height: 120px; max-height: 420px;
      overflow-y: auto; white-space: pre-wrap; display: none;
    }
    .terminal.on { display: block; }
    .done-box {
      margin-top: 20px; padding: 16px 20px; background: #f0fdf4;
      border: 1.5px solid #86efac; border-radius: 10px;
      font-weight: 600; display: none; align-items: center; gap: 10px;
    }
    .done-box.on { display: flex; }
    .done-box .links { margin-left: auto; display: flex; gap: 12px; }
    .done-box a { color: #16a34a; text-decoration: none; font-size: 0.9rem; }
    .done-box a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>✍️ Auto Blog</h1>
    <p class="sub">주제를 입력하면 Claude AI가 블로그 글을 자동으로 작성하고 배포합니다.</p>
    <div class="card">
      <label for="topic">주제</label>
      <input id="topic" type="text" placeholder="예: Python 비동기 프로그래밍 완벽 가이드" />
      <label for="style">스타일</label>
      <select id="style">
        <option value="informative">정보 제공형</option>
        <option value="tutorial">튜토리얼</option>
        <option value="opinion">의견 / 분석형</option>
        <option value="listicle">목록형</option>
      </select>
      <button id="btn" onclick="run()">🚀 글 생성 및 배포</button>
    </div>
    <pre id="terminal" class="terminal"></pre>
    <div id="done" class="done-box">
      ✅ 배포 완료!
      <div class="links">
        <a id="post-link" href="/" target="_blank">새 글 바로가기 →</a>
        <a href="/" target="_blank">블로그 홈 →</a>
      </div>
    </div>
  </div>
  <script>
    function run() {
      const topic = document.getElementById('topic').value.trim();
      if (!topic) { alert('주제를 입력해 주세요.'); return; }
      const style   = document.getElementById('style').value;
      const btn     = document.getElementById('btn');
      const term    = document.getElementById('terminal');
      const done    = document.getElementById('done');

      btn.disabled = true;
      btn.textContent = '⏳ 생성 중...';
      term.textContent = '';
      term.classList.add('on');
      done.classList.remove('on');

      const es = new EventSource(`/admin/generate?topic=${encodeURIComponent(topic)}&style=${encodeURIComponent(style)}`);
      es.onmessage = ({ data }) => {
        if (data === '__DONE__') {
          es.close();
          btn.disabled = false;
          btn.textContent = '🚀 글 생성 및 배포';
          done.classList.add('on');
        } else if (data === '__ERROR__') {
          es.close();
          btn.disabled = false;
          btn.textContent = '🚀 글 생성 및 배포';
        } else if (data.startsWith('__POST_URL__:')) {
          const url = data.split('__POST_URL__:')[1];
          document.getElementById('post-link').href = url;
        } else {
          term.textContent += data + '\\n';
          term.scrollTop = term.scrollHeight;
        }
      };
      es.onerror = () => {
        es.close();
        btn.disabled = false;
        btn.textContent = '🚀 글 생성 및 배포';
      };
    }

    document.getElementById('topic').addEventListener('keydown', e => {
      if (e.key === 'Enter') run();
    });
  </script>
</body>
</html>"""


@app.get("/admin", response_class=HTMLResponse)
def index():
    return HTML


def _post_url_from_path(saved_path: str) -> str:
    """'✅ 저장 완료: /path/to/content/YYYY-MM-DD-slug.md' 에서 /posts/{slug}.html 반환."""
    stem = Path(saved_path.strip()).stem
    parts = stem.split("-")
    if len(parts) > 3 and parts[0].isdigit() and len(parts[0]) == 4:
        slug = "-".join(parts[3:])
    else:
        slug = stem
    return f"/posts/{slug}.html"


@app.get("/admin/generate")
def generate(topic: str, style: str = "informative"):
    def stream():
        process = subprocess.Popen(
            [sys.executable, "-m", "auto_blog", "run", "--topic", topic, "--style", style],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(BASE_DIR),
        )
        for line in iter(process.stdout.readline, ""):
            text = line.rstrip()
            if "저장 완료:" in text:
                saved_path = text.split("저장 완료:")[-1].strip()
                post_url = _post_url_from_path(saved_path)
                yield f"data: __POST_URL__:{post_url}\n\n"
            yield f"data: {text}\n\n"
        process.wait()
        yield "data: __DONE__\n\n" if process.returncode == 0 else "data: __ERROR__\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


app.mount("/", StaticFiles(directory=str(OUTPUT_DIR), html=True), name="blog")
