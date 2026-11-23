#!/usr/bin/env python3
"""Build the bilingual ORCA docs site.

Sidebar labels stay the English names from https://orca.dev/docs. Each chapter
embeds the Chinese translation and the official English article. A header
control switches the chapter body and remembers the choice. Autoplay clips use
the official mp4 plus poster. Translator notes are not published.
"""

from html import escape, unescape
from pathlib import Path
import re

import mistune

ROOT = Path(__file__).resolve().parents[1]
ZH_DIR = Path("/cursor/stores/bc-7f62f27b-3e33-4cb9-a277-10330258c79e/docs/zh")
EN_DIR = ROOT / "content" / "en"
PLACEHOLDER = "这一章的译文尚未放入。"
ORIGIN = "https://orca.dev"
NOTE_KEYS = ("原文：", "英文标题：", "页面导语：", "选页说明", "入门样章")

# ("section", title) | ("group", title) | ("page", source_path, english_nav_title)
# Order and English labels match the live sidebar on https://orca.dev/docs.
NAV = [
    ("section", "Start Here"),
    ("page", "/docs", "What is Orca?"),
    ("page", "/docs/install", "Install"),
    ("page", "/docs/first-session", "Your first 3-agent session"),
    ("page", "/docs/migrate-from-conductor", "Migrate from Conductor"),
    ("group", "The Orca Model"),
    ("page", "/docs/model/worktrees", "Worktrees"),
    ("page", "/docs/model/tabs-panes-splits", "Tabs, panes & split layouts"),
    ("page", "/docs/model/agents-sessions", "Agents & sessions"),
    ("page", "/docs/model/session-restore", "Session restore"),
    ("page", "/docs/model/quick-open", "Quick Open & Jump Palette"),
    ("group", "Working with Agents"),
    ("page", "/docs/agents/supported", "Supported agents"),
    ("page", "/docs/agents/claude-code", "Claude Code in Orca"),
    ("page", "/docs/agents/glm-agent", "How to use GLM-5.2 in Orca ADE"),
    ("page", "/docs/agents/codex", "Codex in Orca"),
    ("page", "/docs/agents/cursor-cli", "Cursor CLI in Orca"),
    ("page", "/docs/agents/codex-hot-swap", "Hot-swap Codex accounts"),
    ("page", "/docs/agents/native-chat", "Chat UI (native chat)"),
    ("page", "/docs/agents/session-history", "Agent session history"),
    ("page", "/docs/agents/hibernation", "Agent hibernation"),
    ("page", "/docs/agents/usage-tracking", "Usage & rate-limit tracking"),
    ("page", "/docs/agents/hooks-memory", "Agent hooks & memory"),
    ("group", "Reviewing & Shipping Code"),
    ("page", "/docs/review/diff-viewer", "Diff viewer"),
    ("page", "/docs/review/annotate-ai-diff", "Annotate AI Diff"),
    ("page", "/docs/review/attribution", "Attribution"),
    ("page", "/docs/review/commit-push", "Commit & push from Orca"),
    ("page", "/docs/review/github", "Hosted reviews, issues & Actions"),
    ("page", "/docs/review/linear", "Linear items drawer"),
    ("page", "/docs/review/jira", "Jira items drawer"),
    ("group", "Editing in Orca"),
    ("page", "/docs/editing/monaco", "Monaco editor & autosave"),
    ("page", "/docs/editing/markdown", "Rich markdown editor"),
    ("page", "/docs/editing/viewers", "HTML, Mermaid, PDF & image viewers"),
    ("page", "/docs/editing/file-explorer", "File explorer & external drag-drop"),
    ("group", "Browser & Design Mode"),
    ("page", "/docs/browser/overview", "Per-worktree browser"),
    ("page", "/docs/browser/design-mode", "Design Mode"),
    ("page", "/docs/browser/profiles", "Browser-use profiles"),
    ("section", "Bots"),
    ("page", "/docs/bots", "Bots quickstart"),
    ("page", "/docs/bots/use-cases", "Bot use cases"),
    ("page", "/docs/bots/connectors", "Bot connectors"),
    ("page", "/docs/bots/import", "Import a bot"),
    ("page", "/docs/bots/security", "Bot security"),
    ("section", "Terminal"),
    ("page", "/docs/terminal", "Terminal"),
    ("section", "Remote & SSH"),
    ("page", "/docs/ways-to-run", "Ways to run Orca"),
    ("page", "/docs/ssh", "SSH worktrees"),
    ("page", "/docs/remote-servers", "Remote Orca Servers"),
    ("section", "CLI & Automation"),
    ("group", "Orca CLI & Skills"),
    ("page", "/docs/cli/overview", "Orca CLI overview"),
    ("page", "/docs/cli/reference", "Orca CLI reference"),
    ("page", "/docs/cli/orchestration", "Orchestration"),
    ("page", "/docs/cli/automations", "Scheduled automations"),
    ("page", "/docs/cli/computer-use", "Computer use"),
    ("page", "/docs/cli/worktree-checkpoints", "Worktree checkpoints"),
    ("page", "/docs/cli/skills", "Orca skills registry & MCP"),
    ("section", "Mobile"),
    ("page", "/docs/mobile", "Mobile companion"),
    ("page", "/docs/android-apk", "Install Orca Mobile on Android"),
    ("section", "Notifications & Inbox"),
    ("page", "/docs/notifications", "Notifications & Inbox"),
    ("page", "/docs/activity", "Agents feed"),
    ("group", "Recipes"),
    ("page", "/docs/recipes/parallel-agents", "Race three agents on the same task"),
    ("page", "/docs/recipes/review-ai-diff", "Review an AI diff line-by-line"),
    ("page", "/docs/recipes/jump-worktrees", "Jump between 10 worktrees"),
    ("page", "/docs/recipes/design-mode-fix", "Fix a UI bug with Design Mode"),
    ("page", "/docs/recipes/remote-worktrees", "Work on a remote machine over SSH"),
    ("section", "Settings Reference"),
    ("page", "/docs/settings", "Settings reference"),
    ("section", "Privacy & Telemetry"),
    ("page", "/docs/telemetry", "Privacy & Telemetry"),
    ("section", "Troubleshooting & FAQ"),
    ("page", "/docs/troubleshooting", "Troubleshooting & FAQ"),
    ("page", "/docs/github-errors", "Troubleshooting GitHub errors"),
]

# Official AutoplayClip turns a .gif src into /whats-new/videos/<name>.mp4
# and shows /whats-new/posters/<name>.jpg until the clip is in view.
CLIP_STEMS = [
    "orca-split-screen",
    "default-agent-opening",
    "tab-split",
    "agent-statuses",
    "session-that-survives-restart",
    "codex-account-switcher",
    "annotate-ai-diff",
    "orca-github",
    "orca-markdown-editor",
    "orca-design-mode",
    "browser-2-demo",
    "orca-browser-use",
    "ghostty-style-terminal",
    "keyboard-native",
    "ssh-demo",
    "orca-cli-demo",
    "orca-mobile",
]

MARKDOWN = mistune.create_markdown(plugins=["table"])


def slug_for(source: str) -> str:
    if source == "/docs":
        return "what-is-orca"
    return source.removeprefix("/docs/").replace("/", "-")


def zh_path(source: str) -> Path:
    if source == "/docs":
        name = "what-is-orca.md"
    else:
        name = source.removeprefix("/docs/").replace("/", "--") + ".md"
    return ZH_DIR / name


def strip_notes(text: str) -> str:
    while True:
        text = text.lstrip("\n")
        if not text.startswith(">"):
            return text
        lines = text.splitlines()
        index = 0
        while index < len(lines):
            line = lines[index]
            if line.startswith(">"):
                index += 1
                continue
            if line.strip() == "" and index + 1 < len(lines) and lines[index + 1].startswith(">"):
                index += 1
                continue
            break
        block = "\n".join(lines[:index])
        if any(key in block for key in NOTE_KEYS):
            text = "\n".join(lines[index:])
            continue
        return text


def cut_glossary(text: str) -> str:
    kept = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if not in_fence and line.strip() == "## 术语候选":
            break
        kept.append(line)
    return "\n".join(kept).strip()


def load_english(slug: str):
    path = EN_DIR / f"{slug}.html"
    if not path.is_file():
        raise SystemExit(f"缺少英文正文 {path}")
    text = path.read_text(encoding="utf-8").lstrip()
    match = re.match(r"<h1>(.*?)</h1>\s*", text, flags=re.S)
    if not match:
        raise SystemExit(f"{path} 缺少英文标题")
    return unescape(match.group(1)).strip(), text[match.end():].strip()


def load_translation(source: str):
    path = zh_path(source)
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise SystemExit(f"{path} 缺少一级标题")
    title = lines[0][2:].strip()
    body = cut_glossary(strip_notes("\n".join(lines[1:])))
    if not body:
        return {"title": title, "html": "", "body": "", "path": path}
    html = MARKDOWN(body)
    return {"title": title, "html": html, "body": body, "path": path}


def collect_pages():
    section = None
    group = None
    pages = []
    for item in NAV:
        kind = item[0]
        if kind == "section":
            section = item[1]
            group = None
        elif kind == "group":
            if section is None:
                raise SystemExit(f"分组「{item[1]}」不在任何栏目下")
            group = item[1]
        elif kind == "page":
            source, nav_title = item[1], item[2]
            loaded = load_translation(source)
            slug = slug_for(source)
            en_title, en_html = load_english(slug)
            if en_title != nav_title:
                raise SystemExit(f"{source} 英文标题 {en_title!r} 和目录 {nav_title!r} 不一致")
            pages.append(
                {
                    "slug": slug,
                    "source": source,
                    "section": section,
                    "group": group,
                    "nav_title": nav_title,
                    "title": loaded["title"] if loaded else nav_title,
                    "html": loaded["html"] if loaded else "",
                    "en_title": en_title,
                    "en_html": en_html,
                    "body": loaded["body"] if loaded else "",
                    "path": loaded["path"] if loaded else None,
                    "missing": loaded is None or not (loaded and loaded["html"]),
                }
            )
        else:
            raise SystemExit(f"未知条目: {item!r}")
    slugs = [page["slug"] for page in pages]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("页面锚点重复")
    if len(pages) != 63:
        raise SystemExit(f"期望 63 个章节，实际 {len(pages)}")
    return pages


def nav_html(pages_by_source):
    lines = []
    group_open = False
    for item in NAV:
        kind = item[0]
        if kind == "section":
            group_open = False
            lines.append(f'        <p class="nav-section">{escape(item[1])}</p>')
        elif kind == "group":
            group_open = True
            lines.append(f'        <p class="nav-group">{escape(item[1])}</p>')
        else:
            page = pages_by_source[item[1]]
            css = "nav-link sub" if group_open else "nav-link"
            lines.append(
                f'        <a class="{css}" href="#{page["slug"]}">{escape(page["nav_title"])}</a>'
            )
    return "\n".join(lines)


def kicker(page):
    if page["group"]:
        return f'{page["section"]} · {page["group"]}'
    return page["section"]


def pager(pages, index):
    parts = ['      <nav class="pager" aria-label="章节">']
    if index > 0:
        prev = pages[index - 1]
        parts.append(
            f'        <a class="prev" href="#{prev["slug"]}"><span>上一章</span>'
            f'<strong>{escape(prev["nav_title"])}</strong></a>'
        )
    if index < len(pages) - 1:
        nxt = pages[index + 1]
        parts.append(
            f'        <a class="next" href="#{nxt["slug"]}"><span>下一章</span>'
            f'<strong>{escape(nxt["nav_title"])}</strong></a>'
        )
    parts.append("      </nav>")
    return "\n".join(parts)


def chapter_html(pages, index):
    page = pages[index]
    url = ORIGIN + page["source"]
    if page["missing"]:
        zh_body = f'      <p class="placeholder lang-zh">{escape(PLACEHOLDER)}</p>'
    else:
        zh_body = f'      <div class="doc-body lang-zh">\n{page["html"]}\n      </div>'
    en_body = f'      <div class="doc-body lang-en">\n{page["en_html"]}\n      </div>'
    return f"""    <article id="{page["slug"]}" class="doc" data-source="{escape(page["source"])}">
      <p class="kicker">{escape(kicker(page))}</p>
      <h1 class="lang-zh">{escape(page["title"])}</h1>
      <h1 class="lang-en">{escape(page["en_title"])}</h1>
{zh_body}
{en_body}
      <p class="meta"><span class="lang-zh">英文原文：</span><span class="lang-en">English source: </span><a href="{escape(url)}">{escape(url.removeprefix("https://"))}</a></p>
{pager(pages, index)}
    </article>"""


CURRENT_CSS = """
    body:not(:has(.doc:target)) a.nav-link[href="#what-is-orca"],
    body:has(#what-is-orca:target) a.nav-link[href="#what-is-orca"],
    {selectors} {{
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 650;
    }}
"""


def current_css(pages):
    selectors = ",\n    ".join(
        f'body:has(#{page["slug"]}:target) a.nav-link[href="#{page["slug"]}"]'
        for page in pages
        if page["slug"] != "what-is-orca"
    )
    return CURRENT_CSS.format(selectors=selectors).strip()


SCRIPT = """
    (function () {
      var toggle = document.getElementById("nav-toggle");
      var sidebar = document.getElementById("sidebar");
      var langKey = "orca-docs-lang";

      function chapterArticle() {
        var id = (location.hash || "#what-is-orca").slice(1);
        var el = document.getElementById(id);
        var article = el
          ? (el.classList.contains("doc") ? el : el.closest(".doc"))
          : null;
        if (!article) article = document.getElementById("what-is-orca");
        var docs = document.querySelectorAll(".doc");
        for (var i = 0; i < docs.length; i++) docs[i].classList.remove("is-current");
        article.classList.add("is-current");
        return article;
      }

      function sync() {
        var article = chapterArticle();
        var id = article.id;
        var links = sidebar.querySelectorAll("a[href^='#']");
        for (var i = 0; i < links.length; i++) {
          var on = links[i].getAttribute("href") === "#" + id;
          if (on) links[i].setAttribute("aria-current", "page");
          else links[i].removeAttribute("aria-current");
        }
        var lang = document.documentElement.getAttribute("data-lang") === "en" ? "en" : "zh";
        var heading = article.querySelector("h1.lang-" + lang);
        document.title = !heading || id === "what-is-orca"
          ? "ORCA 说明文档"
          : heading.textContent + " · ORCA 说明文档";
        var current = sidebar.querySelector('[aria-current="page"]');
        if (current) {
          var linkTop = current.getBoundingClientRect().top - sidebar.getBoundingClientRect().top;
          sidebar.scrollTop += linkTop - sidebar.clientHeight / 2 + current.clientHeight / 2;
        }
        var hashId = (location.hash || "").slice(1);
        var target = hashId && document.getElementById(hashId);
        if (target && target !== article) target.scrollIntoView();
      }

      function applyLang(lang, persist) {
        if (lang !== "en") lang = "zh";
        document.documentElement.setAttribute("data-lang", lang);
        document.documentElement.lang = lang === "en" ? "en" : "zh-CN";
        var zh = document.getElementById("lang-zh");
        var en = document.getElementById("lang-en");
        if (zh) zh.setAttribute("aria-pressed", lang === "zh" ? "true" : "false");
        if (en) en.setAttribute("aria-pressed", lang === "en" ? "true" : "false");
        if (persist) {
          try { localStorage.setItem(langKey, lang); } catch (e) {}
        }
        sync();
      }

      document.getElementById("lang-zh").addEventListener("click", function () {
        applyLang("zh", true);
      });
      document.getElementById("lang-en").addEventListener("click", function () {
        applyLang("en", true);
      });

      sidebar.addEventListener("click", function (event) {
        if (event.target.closest("a")) toggle.checked = false;
      });
      window.addEventListener("hashchange", sync);
      applyLang(document.documentElement.getAttribute("data-lang"), false);

      var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
      var clips = document.querySelectorAll(".clip");
      function mount(clip) {
        if (reduce.matches || clip.querySelector("video")) return;
        var video = document.createElement("video");
        video.src = clip.getAttribute("data-video");
        video.poster = clip.querySelector("img").src;
        video.muted = true;
        video.loop = true;
        video.playsInline = true;
        video.autoplay = true;
        video.preload = "none";
        video.setAttribute("aria-hidden", "true");
        clip.appendChild(video);
        var pending = video.play();
        if (pending && pending.catch) pending.catch(function () {});
      }
      function unmount(clip) {
        var video = clip.querySelector("video");
        if (video) video.remove();
      }
      if (!("IntersectionObserver" in window)) {
        for (var c = 0; c < clips.length; c++) mount(clips[c]);
        return;
      }
      var observer = new IntersectionObserver(function (entries) {
        for (var i = 0; i < entries.length; i++) {
          if (entries[i].isIntersecting) mount(entries[i].target);
          else unmount(entries[i].target);
        }
      }, { rootMargin: "200px 0px", threshold: 0.01 });
      for (var n = 0; n < clips.length; n++) observer.observe(clips[n]);
      if (reduce.addEventListener) {
        reduce.addEventListener("change", function () {
          for (var i = 0; i < clips.length; i++) {
            if (reduce.matches) unmount(clips[i]);
          }
        });
      }
    })();
"""


def render(pages):
    by_source = {page["source"]: page for page in pages}
    chapters = "\n".join(chapter_html(pages, index) for index in range(len(pages)))
    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-lang="zh">
<head>
  <meta charset="utf-8">
  <script>
    (function () {{
      try {{
        if (localStorage.getItem("orca-docs-lang") === "en") {{
          document.documentElement.setAttribute("data-lang", "en");
          document.documentElement.lang = "en";
        }}
      }} catch (e) {{}}
    }})();
  </script>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ORCA 说明文档</title>
  <meta name="description" content="ORCA docs in Chinese and English. The sidebar matches orca.dev/docs.">
  <link rel="stylesheet" href="styles.css">
  <style>
    {current_css(pages)}
  </style>
</head>
<body>
  <a class="skip" href="#content">跳到正文</a>
  <header class="topbar">
    <a class="brand" href="#what-is-orca">ORCA 说明文档</a>
    <div class="lang-switch" role="group" aria-label="语言">
      <button type="button" id="lang-zh" aria-pressed="true">中文</button>
      <button type="button" id="lang-en" aria-pressed="false">English</button>
    </div>
    <label class="menu-button" for="nav-toggle">目录</label>
  </header>
  <input class="nav-toggle" id="nav-toggle" type="checkbox">
  <div class="layout">
    <aside class="sidebar" id="sidebar">
      <nav aria-label="文档目录">
{nav_html(by_source)}
      </nav>
    </aside>
    <label class="backdrop" for="nav-toggle"></label>
    <main class="content" id="content">
{chapters}
    </main>
  </div>
  <script>
{SCRIPT}
  </script>
</body>
</html>
"""


def upgrade_clips(html: str) -> str:
    """Swap poster stills for the official muted, looping mp4 when in view."""

    def repl(match):
        src, alt = match.group(1), match.group(2)
        stem = src.rsplit("/", 1)[-1]
        if stem.endswith(".jpg"):
            stem = stem[: -len(".jpg")]
        else:
            return match.group(0)
        if stem not in CLIP_STEMS:
            return match.group(0)
        video = f"{ORIGIN}/whats-new/videos/{stem}.mp4"
        return (
            f'<span class="clip" data-video="{escape(video)}">'
            f'<img src="{src}" alt="{alt}" loading="lazy" decoding="async">'
            f"</span>"
        )

    return re.sub(
        r'<img src="(https://orca.dev/whats-new/posters/[^"]+\.jpg)" alt="([^"]*)"[^>]*>',
        repl,
        html,
    )


def check(pages, html):
    nav = html.split("<nav", 1)[1].split("</nav>", 1)[0]
    if "智能体" in nav:
        raise SystemExit("导航里仍有「智能体」")
    if "术语候选" in html or "选页说明" in html or "入门样章" in html:
        raise SystemExit("译者备注混进了页面")
    if PLACEHOLDER in html:
        missing = [page["source"] for page in pages if page["missing"]]
        raise SystemExit("仍有占位页: " + ", ".join(missing))
    used = {page["path"].name for page in pages if page["path"]}
    on_disk = {path.name for path in ZH_DIR.glob("*.md")}
    if used != on_disk:
        raise SystemExit(f"译文文件没有一一对应: 多 {sorted(on_disk - used)} 缺 {sorted(used - on_disk)}")
    image_re = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
    for page in pages:
        for url in image_re.findall(page["body"]):
            if url not in html:
                raise SystemExit(f"{page['source']} 丢了图片 {url}")
        for fence in re.findall(r"```[^\n]*\n(.*?)```", page["body"], flags=re.S):
            probe = fence.strip().splitlines()[0].strip() if fence.strip() else ""
            if not probe:
                continue
            rendered = (
                probe.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
            )
            if rendered not in html:
                raise SystemExit(f"{page['source']} 丢了代码块开头: {probe}")
    if "What is Orca?" not in nav or "Start Here" not in nav:
        raise SystemExit("侧栏没有换成英文栏目")
    if "从这里开始" in nav or "Orca 是什么" in nav:
        raise SystemExit("侧栏仍有中文栏目名")
    if "https://orca.dev/whats-new/videos/orca-split-screen.mp4" not in html:
        raise SystemExit("首页动图没有换成官网 mp4")
    if "https://orca.dev/whats-new/posters/orca-split-screen.jpg" not in html:
        raise SystemExit("首页海报静帧不在页面里")
    if html.count('class="clip"') != 38:
        raise SystemExit(f"动图数量不对: {html.count('class=\"clip\"')}")
    if html.count("brew install --cask stablyai/orca/orca") < 2:
        raise SystemExit("安装页中英文代码块不齐")
    if 'id="lang-zh"' not in html or 'id="lang-en"' not in html:
        raise SystemExit("缺少语言开关")
    if "orca-docs-lang" not in html:
        raise SystemExit("没有记住语言的 localStorage 键")
    install = html.split('id="install"', 1)[1].split("</article>", 1)[0]
    if "安装" not in install or ">Install<" not in install:
        raise SystemExit("安装页没有中英两个标题")


def main():
    if not ZH_DIR.is_dir():
        raise SystemExit(f"找不到译文目录 {ZH_DIR}")
    pages = collect_pages()
    html = upgrade_clips(render(pages))
    check(pages, html)
    out = ROOT / "index.html"
    out.write_text(html, encoding="utf-8")
    missing = [page["source"] for page in pages if page["missing"]]
    print(f"wrote {out}")
    print(f"replaced {len(pages) - len(missing)}")
    print(f"placeholder {len(missing)}")
    if missing:
        print("still placeholder: " + ", ".join(missing))


if __name__ == "__main__":
    main()
