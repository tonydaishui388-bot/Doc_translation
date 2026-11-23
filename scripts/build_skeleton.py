#!/usr/bin/env python3
"""Build the ORCA Chinese docs site from the translated Markdown.

Navigation keeps the English sidebar's order and grouping. Page labels come
from each translation's title. Agent stays "Agent"; worktree stays "工作树".
Translator notes (选页说明 / 术语候选) are not published.
"""

from html import escape
from pathlib import Path
import re

import mistune

ROOT = Path(__file__).resolve().parents[1]
ZH_DIR = Path("/cursor/stores/bc-7f62f27b-3e33-4cb9-a277-10330258c79e/docs/zh")
PLACEHOLDER = "这一章的译文尚未放入。"
ORIGIN = "https://orca.dev"
NOTE_KEYS = ("原文：", "英文标题：", "页面导语：", "选页说明", "入门样章")

# ("section", title) | ("group", title) | ("page", source_path)
# Page titles are filled from the translation H1. Order matches orca.dev/docs.
NAV = [
    ("section", "从这里开始"),
    ("page", "/docs"),
    ("page", "/docs/install"),
    ("page", "/docs/first-session"),
    ("page", "/docs/migrate-from-conductor"),
    ("group", "工作区的组织方式"),
    ("page", "/docs/model/worktrees"),
    ("page", "/docs/model/tabs-panes-splits"),
    ("page", "/docs/model/agents-sessions"),
    ("page", "/docs/model/session-restore"),
    ("page", "/docs/model/quick-open"),
    ("group", "使用 Agent"),
    ("page", "/docs/agents/supported"),
    ("page", "/docs/agents/claude-code"),
    ("page", "/docs/agents/glm-agent"),
    ("page", "/docs/agents/codex"),
    ("page", "/docs/agents/cursor-cli"),
    ("page", "/docs/agents/codex-hot-swap"),
    ("page", "/docs/agents/native-chat"),
    ("page", "/docs/agents/session-history"),
    ("page", "/docs/agents/hibernation"),
    ("page", "/docs/agents/usage-tracking"),
    ("page", "/docs/agents/hooks-memory"),
    ("group", "审阅并交付代码"),
    ("page", "/docs/review/diff-viewer"),
    ("page", "/docs/review/annotate-ai-diff"),
    ("page", "/docs/review/attribution"),
    ("page", "/docs/review/commit-push"),
    ("page", "/docs/review/github"),
    ("page", "/docs/review/linear"),
    ("page", "/docs/review/jira"),
    ("group", "在 Orca 里编辑"),
    ("page", "/docs/editing/monaco"),
    ("page", "/docs/editing/markdown"),
    ("page", "/docs/editing/viewers"),
    ("page", "/docs/editing/file-explorer"),
    ("group", "浏览器与设计模式"),
    ("page", "/docs/browser/overview"),
    ("page", "/docs/browser/design-mode"),
    ("page", "/docs/browser/profiles"),
    ("section", "Bots"),
    ("page", "/docs/bots"),
    ("page", "/docs/bots/use-cases"),
    ("page", "/docs/bots/connectors"),
    ("page", "/docs/bots/import"),
    ("page", "/docs/bots/security"),
    ("section", "终端"),
    ("page", "/docs/terminal"),
    ("section", "远程与 SSH"),
    ("page", "/docs/ways-to-run"),
    ("page", "/docs/ssh"),
    ("page", "/docs/remote-servers"),
    ("section", "命令行与自动化"),
    ("group", "Orca CLI 与技能"),
    ("page", "/docs/cli/overview"),
    ("page", "/docs/cli/reference"),
    ("page", "/docs/cli/orchestration"),
    ("page", "/docs/cli/automations"),
    ("page", "/docs/cli/computer-use"),
    ("page", "/docs/cli/worktree-checkpoints"),
    ("page", "/docs/cli/skills"),
    ("section", "移动端"),
    ("page", "/docs/mobile"),
    ("page", "/docs/android-apk"),
    ("section", "通知与收件箱"),
    ("page", "/docs/notifications"),
    ("page", "/docs/activity"),
    ("group", "场景示例"),
    ("page", "/docs/recipes/parallel-agents"),
    ("page", "/docs/recipes/review-ai-diff"),
    ("page", "/docs/recipes/jump-worktrees"),
    ("page", "/docs/recipes/design-mode-fix"),
    ("page", "/docs/recipes/remote-worktrees"),
    ("section", "设置参考"),
    ("page", "/docs/settings"),
    ("section", "隐私与遥测"),
    ("page", "/docs/telemetry"),
    ("section", "故障排除与常见问题"),
    ("page", "/docs/troubleshooting"),
    ("page", "/docs/github-errors"),
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
            source = item[1]
            loaded = load_translation(source)
            pages.append(
                {
                    "slug": slug_for(source),
                    "source": source,
                    "section": section,
                    "group": group,
                    "title": loaded["title"] if loaded else source,
                    "html": loaded["html"] if loaded else "",
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
                f'        <a class="{css}" href="#{page["slug"]}">{escape(page["title"])}</a>'
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
            f'<strong>{escape(prev["title"])}</strong></a>'
        )
    if index < len(pages) - 1:
        nxt = pages[index + 1]
        parts.append(
            f'        <a class="next" href="#{nxt["slug"]}"><span>下一章</span>'
            f'<strong>{escape(nxt["title"])}</strong></a>'
        )
    parts.append("      </nav>")
    return "\n".join(parts)


def chapter_html(pages, index):
    page = pages[index]
    url = ORIGIN + page["source"]
    if page["missing"]:
        body = f'      <p class="placeholder">{escape(PLACEHOLDER)}</p>'
    else:
        body = f'      <div class="doc-body">\n{page["html"]}\n      </div>'
    return f"""    <article id="{page["slug"]}" class="doc" data-source="{escape(page["source"])}">
      <p class="kicker">{escape(kicker(page))}</p>
      <h1>{escape(page["title"])}</h1>
{body}
      <p class="meta">英文原文：<a href="{escape(url)}">{escape(url.removeprefix("https://"))}</a></p>
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

      function sync() {
        var id = (location.hash || "#what-is-orca").slice(1);
        if (!document.getElementById(id)) id = "what-is-orca";
        var links = sidebar.querySelectorAll("a[href^='#']");
        for (var i = 0; i < links.length; i++) {
          var on = links[i].getAttribute("href") === "#" + id;
          if (on) links[i].setAttribute("aria-current", "page");
          else links[i].removeAttribute("aria-current");
        }
        var heading = document.querySelector("#" + id + " h1");
        document.title = !heading || id === "what-is-orca"
          ? "ORCA 说明文档"
          : heading.textContent + " · ORCA 说明文档";
        var current = sidebar.querySelector('[aria-current="page"]');
        if (!current) return;
        var linkTop = current.getBoundingClientRect().top - sidebar.getBoundingClientRect().top;
        sidebar.scrollTop += linkTop - sidebar.clientHeight / 2 + current.clientHeight / 2;
      }

      sidebar.addEventListener("click", function (event) {
        if (event.target.closest("a")) toggle.checked = false;
      });
      window.addEventListener("hashchange", sync);
      sync();
    })();
"""


def render(pages):
    by_source = {page["source"]: page for page in pages}
    chapters = "\n".join(chapter_html(pages, index) for index in range(len(pages)))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ORCA 说明文档</title>
  <meta name="description" content="ORCA 中文说明文档。栏目与英文文档站对应。">
  <link rel="stylesheet" href="styles.css">
  <style>
    {current_css(pages)}
  </style>
</head>
<body>
  <a class="skip" href="#content">跳到正文</a>
  <header class="topbar">
    <a class="brand" href="#what-is-orca">ORCA 说明文档</a>
    <p class="brand-note">中文</p>
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
    if "https://orca.dev/whats-new/posters/orca-split-screen.jpg" not in html:
        raise SystemExit("首页图片 URL 不在页面里")
    if "brew install --cask stablyai/orca/orca" not in html:
        raise SystemExit("安装页代码块不在页面里")


def main():
    if not ZH_DIR.is_dir():
        raise SystemExit(f"找不到译文目录 {ZH_DIR}")
    pages = collect_pages()
    html = render(pages)
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
