import hashlib
import hmac
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlencode

import httpx
import frontmatter as fm
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE_DIR / "output"
CONTENT_DIR = BASE_DIR / "content"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LINKEDIN_CLIENT_ID     = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_REDIRECT_URI  = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8080/admin/linkedin/callback")
LINKEDIN_TOKEN_FILE    = BASE_DIR / ".linkedin_token.json"

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password")
SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
SESSION_COOKIE = "ab_session"


def _make_token() -> str:
    msg = f"{ADMIN_USERNAME}:{SECRET_KEY}"
    return hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).hexdigest()


def _is_authenticated(request: Request) -> bool:
    token = request.cookies.get(SESSION_COOKIE, "")
    return hmac.compare_digest(token, _make_token())


def _slugify(stem: str) -> str:
    parts = stem.split("-")
    if len(parts) > 3 and parts[0].isdigit() and len(parts[0]) == 4:
        return "-".join(parts[3:])
    return stem


def _find_content_file(slug: str) -> Path | None:
    for f in CONTENT_DIR.glob("*.md"):
        if _slugify(f.stem) == slug:
            return f
    return None


def _li_load() -> dict | None:
    if LINKEDIN_TOKEN_FILE.exists():
        with open(LINKEDIN_TOKEN_FILE) as f:
            return json.load(f)
    return None


def _li_save(data: dict):
    with open(LINKEDIN_TOKEN_FILE, "w") as f:
        json.dump(data, f)


def _post_url_from_path(saved_path: str) -> str:
    stem = Path(saved_path.strip()).stem
    return f"/posts/{_slugify(stem)}.html"


app = FastAPI()

# ── HTML ──────────────────────────────────────────────────────────────────────

LOGIN_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>로그인 · Auto Blog</title>
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
         background:#0f1117;color:#e2e8f0;min-height:100vh;
         display:flex;align-items:center;justify-content:center}}
    .card{{background:#1a1d27;border:1px solid #2a2d3a;border-radius:16px;
           padding:40px 36px;width:100%;max-width:380px}}
    h1{{font-size:1.5rem;font-weight:800;margin-bottom:6px}}
    .sub{{color:#8892a4;font-size:.9rem;margin-bottom:28px}}
    label{{display:block;font-size:.82rem;font-weight:600;color:#8892a4;
           text-transform:uppercase;letter-spacing:.5px;margin-bottom:7px}}
    input{{width:100%;padding:11px 14px;background:#0f1117;border:1.5px solid #2a2d3a;
           border-radius:8px;color:#e2e8f0;font-size:.95rem;outline:none;
           margin-bottom:18px;transition:border-color .15s}}
    input:focus{{border-color:#7c6aff}}
    button{{width:100%;padding:12px;background:#7c6aff;color:#fff;border:none;
            border-radius:8px;font-size:1rem;font-weight:700;cursor:pointer;
            transition:background .15s}}
    button:hover{{background:#6356d4}}
    .error{{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);
            color:#f87171;border-radius:8px;padding:10px 14px;
            font-size:.88rem;margin-bottom:18px}}
  </style>
</head>
<body>
  <div class="card">
    <h1>✍️ Auto Blog</h1><p class="sub">관리자 로그인</p>
    {error}
    <form method="post" action="/admin/login">
      <label>아이디</label>
      <input name="username" type="text" autocomplete="username" required />
      <label>패스워드</label>
      <input name="password" type="password" autocomplete="current-password" required />
      <button type="submit">로그인</button>
    </form>
  </div>
</body></html>"""

ADMIN_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" /><meta name="viewport" content="width=device-width,initial-scale=1.0" />
  <title>Admin · Auto Blog</title>
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
         background:#f0f2f5;color:#1a1a1a;min-height:100vh}
    .wrap{max-width:720px;margin:0 auto;padding:48px 24px 80px}
    .top{display:flex;align-items:center;justify-content:space-between;margin-bottom:32px}
    h1{font-size:1.8rem;font-weight:800;letter-spacing:-.5px}
    .logout{font-size:.85rem;color:#888;text-decoration:none;padding:6px 14px;
            border:1px solid #ddd;border-radius:8px}
    .logout:hover{background:#fff}
    .section-title{font-size:1rem;font-weight:700;color:#444;margin-bottom:14px;
                   padding-bottom:8px;border-bottom:1px solid #e0e0e0}
    .card{background:#fff;border-radius:16px;padding:28px;
          box-shadow:0 4px 24px rgba(0,0,0,.07);margin-bottom:24px}
    label{display:block;font-weight:600;font-size:.82rem;text-transform:uppercase;
          letter-spacing:.5px;color:#555;margin-bottom:7px}
    input,select{width:100%;padding:11px 14px;border:1.5px solid #e0e0e0;
                 border-radius:10px;font-size:.95rem;outline:none;
                 transition:border-color .15s;margin-bottom:20px;background:#fafafa}
    input:focus,select:focus{border-color:#6366f1;background:#fff}
    .btn{width:100%;padding:13px;background:#6366f1;color:#fff;border:none;
         border-radius:10px;font-size:.95rem;font-weight:700;cursor:pointer;
         transition:background .15s,transform .1s}
    .btn:hover:not(:disabled){background:#4f46e5;transform:translateY(-1px)}
    .btn:disabled{background:#a5b4fc;cursor:not-allowed;transform:none}
    .terminal{margin-top:20px;background:#0d1117;color:#c9d1d9;border-radius:12px;
              padding:20px;font-family:'Menlo','Courier New',monospace;font-size:.8rem;
              line-height:1.7;min-height:100px;max-height:380px;overflow-y:auto;
              white-space:pre-wrap;display:none}
    .terminal.on{display:block}
    .done-box{margin-top:16px;padding:14px 18px;background:#f0fdf4;
              border:1.5px solid #86efac;border-radius:10px;font-weight:600;
              display:none;align-items:center;gap:10px}
    .done-box.on{display:flex}
    .done-box .links{margin-left:auto;display:flex;gap:12px}
    .done-box a{color:#16a34a;text-decoration:none;font-size:.88rem}
    .done-box a:hover{text-decoration:underline}
    /* posts list */
    .posts-list{display:flex;flex-direction:column;gap:10px}
    .post-row{display:flex;align-items:center;gap:12px;background:#fafafa;
              border:1px solid #e8e8e8;border-radius:10px;padding:12px 16px}
    .post-row .info{flex:1;min-width:0}
    .post-row .ptitle{font-weight:600;font-size:.92rem;white-space:nowrap;
                      overflow:hidden;text-overflow:ellipsis}
    .post-row .pdate{font-size:.78rem;color:#888;margin-top:2px}
    .post-row .actions{display:flex;gap:8px;flex-shrink:0}
    .act-btn{padding:6px 14px;border:none;border-radius:7px;font-size:.8rem;
             font-weight:600;cursor:pointer;transition:opacity .15s}
    .act-btn:hover{opacity:.8}
    .btn-rewrite{background:#e0e7ff;color:#4338ca}
    .btn-delete{background:#fee2e2;color:#dc2626}
    .btn-linkedin{background:#dbeafe;color:#0a66c2}
    .empty{text-align:center;padding:2rem;color:#aaa;font-size:.9rem}
    .li-status{display:flex;align-items:center;gap:10px;font-size:.88rem;color:#555}
    .li-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
    .li-dot.on{background:#16a34a;box-shadow:0 0 5px #16a34a}
    .li-dot.off{background:#d1d5db}
  </style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <h1>✍️ Admin</h1>
    <div style="display:flex;align-items:center;gap:8px">
      <a href="/" target="_blank" style="font-size:.82rem;color:#555;text-decoration:none;padding:6px 12px;border:1px solid #ddd;border-radius:8px;background:#fff">🏠 홈</a>
      <a href="/posts/" target="_blank" style="font-size:.82rem;color:#555;text-decoration:none;padding:6px 12px;border:1px solid #ddd;border-radius:8px;background:#fff">📋 글 목록</a>
      <a class="logout" href="/admin/logout">로그아웃</a>
    </div>
  </div>

  <!-- 새 글 작성 -->
  <div class="card">
    <div class="section-title">새 글 작성</div>
    <label>주제</label>
    <input id="topic" type="text" placeholder="예: Python 비동기 프로그래밍 완벽 가이드" />
    <label>스타일</label>
    <select id="style">
      <option value="informative">정보 제공형</option>
      <option value="tutorial">튜토리얼</option>
      <option value="opinion">의견 / 분석형</option>
      <option value="listicle">목록형</option>
    </select>
    <button class="btn" id="gen-btn" onclick="runGenerate()">🚀 글 생성 및 배포</button>
  </div>

  <pre id="terminal" class="terminal"></pre>
  <div id="done" class="done-box">
    ✅ 완료!
    <div class="links">
      <a id="post-link" href="/" target="_blank">새 글 바로가기 →</a>
      <a href="/" target="_blank">블로그 홈 →</a>
    </div>
  </div>

  <!-- LinkedIn 연동 -->
  <div class="card">
    <div class="section-title">LinkedIn 연동</div>
    <div id="li-status" class="li-status">
      <span class="li-dot off" id="li-dot"></span>
      <span id="li-text">확인 중...</span>
      <a id="li-btn" href="/admin/linkedin/connect" style="margin-left:auto;padding:7px 16px;background:#0a66c2;color:#fff;border-radius:8px;font-size:.82rem;font-weight:600;text-decoration:none;">🔗 연결하기</a>
    </div>
  </div>

  <!-- 글 목록 관리 -->
  <div class="card" style="margin-top:24px">
    <div class="section-title" style="display:flex;align-items:center;justify-content:space-between">
      글 목록 관리
      <button class="btn" id="cat-btn" onclick="runCategorize()" style="width:auto;padding:8px 18px;font-size:.85rem;">🗂 카테고리 재설정</button>
    </div>
    <div id="posts-list" class="posts-list" style="margin-top:14px"><div class="empty">불러오는 중...</div></div>
  </div>
</div>

<script>
  // ── 스트리밍 공통 ──────────────────────────────────────────────
  function startStream(url, btnEl, btnLabel) {
    const term = document.getElementById('terminal');
    const done = document.getElementById('done');
    btnEl.disabled = true;
    btnEl.textContent = '⏳ 진행 중...';
    term.textContent = '';
    term.classList.add('on');
    done.classList.remove('on');

    const es = new EventSource(url);
    es.onmessage = ({ data }) => {
      if (data === '__DONE__') {
        es.close(); btnEl.disabled = false; btnEl.textContent = btnLabel;
        done.classList.add('on'); loadPosts();
      } else if (data === '__ERROR__') {
        es.close(); btnEl.disabled = false; btnEl.textContent = btnLabel;
      } else if (data.startsWith('__POST_URL__:')) {
        document.getElementById('post-link').href = data.split('__POST_URL__:')[1];
      } else {
        term.textContent += data + '\\n';
        term.scrollTop = term.scrollHeight;
      }
    };
    es.onerror = () => { es.close(); btnEl.disabled = false; btnEl.textContent = btnLabel; };
  }

  // ── 새 글 생성 ──────────────────────────────────────────────────
  function runGenerate() {
    const topic = document.getElementById('topic').value.trim();
    if (!topic) { alert('주제를 입력해 주세요.'); return; }
    const style = document.getElementById('style').value;
    const url = `/admin/generate?topic=${encodeURIComponent(topic)}&style=${encodeURIComponent(style)}`;
    startStream(url, document.getElementById('gen-btn'), '🚀 글 생성 및 배포');
  }
  document.getElementById('topic').addEventListener('keydown', e => { if(e.key==='Enter') runGenerate(); });

  // ── 글 목록 로드 ──────────────────────────────────────────────
  async function loadPosts() {
    const res = await fetch('/admin/api/posts');
    const posts = await res.json();
    const el = document.getElementById('posts-list');
    if (!posts.length) { el.innerHTML = '<div class="empty">아직 작성된 글이 없습니다.</div>'; return; }
    el.innerHTML = posts.map((p, i) => `
      <div class="post-row">
        <div class="info">
          <div class="ptitle">${String(i+1).padStart(2,'0')}. ${p.title}</div>
          <div class="pdate">${p.date || ''}</div>
        </div>
        <div class="actions">
          <button class="act-btn btn-linkedin" onclick="liPost('${p.slug}','${escHtml(p.title)}')">in 포스팅</button>
          <button class="act-btn btn-rewrite" onclick="rewritePost('${p.slug}','${escHtml(p.title)}')">🔄 다시 작성</button>
          <button class="act-btn btn-delete"  onclick="deletePost('${p.slug}','${escHtml(p.title)}')">🗑 삭제</button>
        </div>
      </div>`).join('');
  }

  function escHtml(s) { return s.replace(/'/g,"&#39;").replace(/"/g,"&quot;"); }

  // ── 삭제 ──────────────────────────────────────────────────────
  async function deletePost(slug, title) {
    if (!confirm(`"${title}" 글을 삭제할까요?`)) return;
    const res = await fetch(`/admin/api/posts/${encodeURIComponent(slug)}`, { method:'DELETE' });
    if (res.ok) { loadPosts(); } else { alert('삭제 실패'); }
  }

  // ── 다시 작성 ─────────────────────────────────────────────────
  function rewritePost(slug, title) {
    if (!confirm(`"${title}" 글을 다시 작성할까요?\\n기존 글이 삭제되고 새로 생성됩니다.`)) return;
    const url = `/admin/rewrite/${encodeURIComponent(slug)}`;
    const btn = { disabled: false, textContent: '' };  // dummy — reuse gen-btn
    const genBtn = document.getElementById('gen-btn');
    startStream(url, genBtn, '🚀 글 생성 및 배포');
  }

  // ── 카테고리 재설정 ────────────────────────────────────────────
  function runCategorize() {
    const btn = document.getElementById('cat-btn');
    startStream('/admin/api/categorize', btn, '🗂 카테고리 재설정');
  }

  // ── LinkedIn 상태 ──────────────────────────────────────────────
  async function checkLinkedIn() {
    const res = await fetch('/admin/api/linkedin/status');
    const data = await res.json();
    const dot = document.getElementById('li-dot');
    const text = document.getElementById('li-text');
    const btn = document.getElementById('li-btn');
    if (data.connected) {
      dot.className = 'li-dot on';
      text.textContent = `연결됨: ${data.name}`;
      btn.textContent = '🔄 재연결';
      btn.style.background = '#6b7280';
    } else {
      dot.className = 'li-dot off';
      text.textContent = '연결되지 않았습니다.';
      btn.textContent = '🔗 연결하기';
      btn.style.background = '#0a66c2';
    }
  }

  // ── LinkedIn 포스팅 ───────────────────────────────────────────
  async function liPost(slug, title) {
    if (!confirm(`"${title}" 글을 LinkedIn에 포스팅할까요?`)) return;
    const res = await fetch(`/admin/api/posts/${encodeURIComponent(slug)}/linkedin`, { method:'POST' });
    const data = await res.json();
    if (res.ok) alert('✅ LinkedIn에 포스팅됐습니다!');
    else alert(`❌ 실패: ${data.error}`);
  }

  checkLinkedIn();
  loadPosts();
</script>
</body></html>"""


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/admin/login", response_class=HTMLResponse)
def login_page():
    return LOGIN_HTML.format(error="")


@app.post("/admin/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        resp = RedirectResponse(url="/admin", status_code=303)
        resp.set_cookie(SESSION_COOKIE, _make_token(), httponly=True, samesite="lax")
        return resp
    html = LOGIN_HTML.format(error='<div class="error">아이디 또는 패스워드가 올바르지 않습니다.</div>')
    return HTMLResponse(html, status_code=401)


@app.get("/admin/logout")
def logout():
    resp = RedirectResponse(url="/admin/login", status_code=303)
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    return ADMIN_HTML


# ── Posts API ─────────────────────────────────────────────────────────────────

@app.get("/admin/api/posts")
def list_posts(request: Request):
    if not _is_authenticated(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    posts = []
    for f in sorted(CONTENT_DIR.glob("*.md"), reverse=True):
        if f.name == ".gitkeep":
            continue
        try:
            post = fm.load(f)
        except Exception:
            continue
        slug = _slugify(f.stem)
        posts.append({
            "slug": slug,
            "title": post.metadata.get("title", slug),
            "date": str(post.metadata.get("date", "")),
        })
    return JSONResponse(posts)


@app.patch("/admin/api/posts/{slug}/category")
async def update_category(slug: str, request: Request):
    if not _is_authenticated(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    body = await request.json()
    category = (body.get("category") or "").strip()
    if not category:
        return JSONResponse({"error": "category required"}, status_code=400)
    f = _find_content_file(slug)
    if not f:
        return JSONResponse({"error": "not found"}, status_code=404)
    post = fm.load(f)
    post.metadata["category"] = category
    with open(f, "w", encoding="utf-8") as out:
        out.write(fm.dumps(post))
    subprocess.run(
        [sys.executable, "-m", "auto_blog", "build"],
        cwd=str(BASE_DIR), capture_output=True,
    )
    return JSONResponse({"ok": True, "category": category})


@app.delete("/admin/api/posts/{slug}")
def delete_post(slug: str, request: Request):
    if not _is_authenticated(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    f = _find_content_file(slug)
    if not f:
        return JSONResponse({"error": "not found"}, status_code=404)
    f.unlink()
    subprocess.run(
        [sys.executable, "-m", "auto_blog", "build"],
        cwd=str(BASE_DIR), capture_output=True,
    )
    return JSONResponse({"ok": True})


# ── Generate & Rewrite ────────────────────────────────────────────────────────

def _sse_run(cmd: list[str]) -> StreamingResponse:
    def stream():
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=str(BASE_DIR),
        )
        for line in iter(process.stdout.readline, ""):
            text = line.rstrip()
            if "저장 완료:" in text:
                saved_path = text.split("저장 완료:")[-1].strip()
                yield f"data: __POST_URL__:{_post_url_from_path(saved_path)}\n\n"
            yield f"data: {text}\n\n"
        process.wait()
        yield "data: __DONE__\n\n" if process.returncode == 0 else "data: __ERROR__\n\n"
    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/admin/generate")
def generate(request: Request, topic: str, style: str = "informative"):
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    return _sse_run([sys.executable, "-m", "auto_blog", "run", "--topic", topic, "--style", style])


@app.get("/admin/api/linkedin/status")
def linkedin_status(request: Request):
    if not _is_authenticated(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    token = _li_load()
    if token and token.get("access_token"):
        return JSONResponse({"connected": True, "name": token.get("name", "")})
    return JSONResponse({"connected": False})


@app.get("/admin/linkedin/connect")
def linkedin_connect(request: Request):
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    if not LINKEDIN_CLIENT_ID:
        return HTMLResponse("<p style='font-family:sans-serif;padding:2rem'>⚠️ .env에 LINKEDIN_CLIENT_ID가 없습니다.</p>")
    params = urlencode({
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "scope": "openid profile w_member_social",
        "state": "li_auth",
    })
    return RedirectResponse(url=f"https://www.linkedin.com/oauth/v2/authorization?{params}")


@app.get("/admin/linkedin/callback")
async def linkedin_callback(request: Request, code: str = None, error: str = None):
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    if error or not code:
        return RedirectResponse(url="/admin?msg=linkedin_error")
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": LINKEDIN_REDIRECT_URI,
                "client_id": LINKEDIN_CLIENT_ID,
                "client_secret": LINKEDIN_CLIENT_SECRET,
            },
        )
        token_data = token_resp.json()
        info_resp = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        info = info_resp.json()
        token_data["sub"] = info.get("sub", "")
        token_data["name"] = info.get("name", "")
        _li_save(token_data)
    return RedirectResponse(url="/admin?msg=linkedin_ok")


@app.post("/admin/api/posts/{slug}/linkedin")
async def post_to_linkedin(slug: str, request: Request):
    if not _is_authenticated(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    token = _li_load()
    if not token or not token.get("access_token"):
        return JSONResponse({"error": "LinkedIn이 연결되지 않았습니다. Admin에서 먼저 연결해 주세요."}, status_code=400)
    f = _find_content_file(slug)
    if not f:
        return JSONResponse({"error": "포스트를 찾을 수 없습니다."}, status_code=404)
    post = fm.load(f)
    title   = post.metadata.get("title", slug)
    excerpt = post.metadata.get("excerpt", "")
    site_url = os.getenv("SITE_URL", "https://jessica9740.github.io")
    post_url = f"{site_url}/posts/{_slugify(f.stem)}.html"
    text = f"{title}\n\n{excerpt}\n\n🔗 {post_url}"
    payload = {
        "author": f"urn:li:person:{token['sub']}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "ARTICLE",
                "media": [{
                    "status": "READY",
                    "description": {"text": excerpt[:200]},
                    "originalUrl": post_url,
                    "title": {"text": title},
                }],
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.linkedin.com/v2/ugcPosts",
            json=payload,
            headers={
                "Authorization": f"Bearer {token['access_token']}",
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )
    if resp.status_code in (200, 201):
        return JSONResponse({"ok": True})
    return JSONResponse({"error": resp.text}, status_code=resp.status_code)


@app.get("/admin/api/categorize")
def categorize(request: Request):
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=303)

    def stream():
        import anthropic
        client = anthropic.Anthropic()

        targets = []
        for f in sorted(CONTENT_DIR.glob("*.md")):
            if f.name == ".gitkeep":
                continue
            try:
                post = fm.load(f)
                if not post.metadata.get("category"):
                    targets.append(f)
            except Exception:
                continue

        if not targets:
            yield "data: ✅ 모든 글에 카테고리가 이미 설정되어 있습니다.\n\n"
            yield "data: __DONE__\n\n"
            return

        yield f"data: 카테고리 미설정 글 {len(targets)}개 처리 중...\n\n"

        for f in targets:
            try:
                post = fm.load(f)
                title = post.metadata.get("title", f.stem)
                tags = post.metadata.get("tags", [])
                resp = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=20,
                    messages=[{
                        "role": "user",
                        "content": (
                            "블로그 포스트를 카테고리로 분류해주세요. "
                            "카테고리명만 한국어 2~6글자로 답하세요. 예: 개발, AI, Mac/IT, 건강, 라이프, 비즈니스, 기타\n"
                            f"제목: {title}\n태그: {tags}"
                        ),
                    }],
                )
                category = resp.content[0].text.strip().splitlines()[0]
                post.metadata["category"] = category
                with open(f, "w", encoding="utf-8") as out:
                    out.write(fm.dumps(post))
                yield f"data: ✅ {title[:35]} → {category}\n\n"
            except Exception as e:
                yield f"data: ⚠️  {f.name}: {e}\n\n"

        yield "data: \n\n"
        yield "data: 🔨 사이트 재빌드 중...\n\n"
        process = subprocess.Popen(
            [sys.executable, "-m", "auto_blog", "build"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=str(BASE_DIR),
        )
        for line in iter(process.stdout.readline, ""):
            yield f"data: {line.rstrip()}\n\n"
        process.wait()
        yield "data: __DONE__\n\n" if process.returncode == 0 else "data: __ERROR__\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/admin/rewrite/{slug}")
def rewrite(slug: str, request: Request):
    if not _is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    f = _find_content_file(slug)
    if not f:
        return JSONResponse({"error": "not found"}, status_code=404)
    try:
        post = fm.load(f)
        topic = post.metadata.get("title", slug)
    except Exception:
        topic = slug
    f.unlink()
    return _sse_run([sys.executable, "-m", "auto_blog", "run", "--topic", topic])


app.mount("/", StaticFiles(directory=str(OUTPUT_DIR), html=True), name="blog")
