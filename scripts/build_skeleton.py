#!/usr/bin/env python3
"""Generate the browsable ORCA Chinese docs skeleton (index.html).

Navigation follows the sidebar on https://orca.dev/docs. Page bodies are
placeholders; this script does not translate documentation.
"""

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = "这一章的译文尚未放入。"
ORIGIN = "https://orca.dev"

# ("section", title) | ("group", title) | ("page", title, source_path)
NAV = [
    ("section", "从这里开始"),
    ("page", "Orca 是什么", "/docs"),
    ("page", "安装", "/docs/install"),
    ("page", "第一次三个智能体一起干活", "/docs/first-session"),
    ("page", "从 Conductor 迁移", "/docs/migrate-from-conductor"),
    ("group", "工作区的组织方式"),
    ("page", "工作树", "/docs/model/worktrees"),
    ("page", "标签页、窗格与分栏", "/docs/model/tabs-panes-splits"),
    ("page", "智能体与会话", "/docs/model/agents-sessions"),
    ("page", "恢复会话", "/docs/model/session-restore"),
    ("page", "快速打开与跳转面板", "/docs/model/quick-open"),
    ("group", "使用智能体"),
    ("page", "支持的智能体", "/docs/agents/supported"),
    ("page", "在 Orca 里使用 Claude Code", "/docs/agents/claude-code"),
    ("page", "在 Orca ADE 里使用 GLM-5.2", "/docs/agents/glm-agent"),
    ("page", "在 Orca 里使用 Codex", "/docs/agents/codex"),
    ("page", "在 Orca 里使用 Cursor CLI", "/docs/agents/cursor-cli"),
    ("page", "快速切换 Codex 账号", "/docs/agents/codex-hot-swap"),
    ("page", "聊天界面（原生对话）", "/docs/agents/native-chat"),
    ("page", "智能体会话记录", "/docs/agents/session-history"),
    ("page", "智能体休眠", "/docs/agents/hibernation"),
    ("page", "用量与速率上限", "/docs/agents/usage-tracking"),
    ("page", "智能体钩子与记忆", "/docs/agents/hooks-memory"),
    ("group", "审阅并交付代码"),
    ("page", "查看代码改动", "/docs/review/diff-viewer"),
    ("page", "给 AI 改动加批注", "/docs/review/annotate-ai-diff"),
    ("page", "标明改动出处", "/docs/review/attribution"),
    ("page", "在 Orca 里提交并推送", "/docs/review/commit-push"),
    ("page", "托管的评审、议题与 Actions", "/docs/review/github"),
    ("page", "Linear 事项抽屉", "/docs/review/linear"),
    ("page", "Jira 事项抽屉", "/docs/review/jira"),
    ("group", "在 Orca 里编辑"),
    ("page", "Monaco 编辑器与自动保存", "/docs/editing/monaco"),
    ("page", "Markdown 富文本编辑", "/docs/editing/markdown"),
    ("page", "HTML、Mermaid、PDF 与图片查看", "/docs/editing/viewers"),
    ("page", "文件浏览器与外部拖放", "/docs/editing/file-explorer"),
    ("group", "浏览器与设计模式"),
    ("page", "每个工作树各自的浏览器", "/docs/browser/overview"),
    ("page", "设计模式", "/docs/browser/design-mode"),
    ("page", "供智能体使用的浏览器配置", "/docs/browser/profiles"),
    ("section", "机器人"),
    ("page", "机器人快速上手", "/docs/bots"),
    ("page", "机器人能做什么", "/docs/bots/use-cases"),
    ("page", "机器人的外部连接", "/docs/bots/connectors"),
    ("page", "导入机器人", "/docs/bots/import"),
    ("page", "机器人安全", "/docs/bots/security"),
    ("section", "终端"),
    ("page", "终端", "/docs/terminal"),
    ("section", "远程与 SSH"),
    ("page", "运行 Orca 的方式", "/docs/ways-to-run"),
    ("page", "SSH 工作树", "/docs/ssh"),
    ("page", "远程 Orca 服务器", "/docs/remote-servers"),
    ("section", "命令行与自动化"),
    ("group", "Orca 命令行与技能"),
    ("page", "Orca 命令行概览", "/docs/cli/overview"),
    ("page", "Orca 命令行参考", "/docs/cli/reference"),
    ("page", "编排", "/docs/cli/orchestration"),
    ("page", "定时任务", "/docs/cli/automations"),
    ("page", "让智能体操作电脑", "/docs/cli/computer-use"),
    ("page", "工作树检查点", "/docs/cli/worktree-checkpoints"),
    ("page", "Orca 技能注册与 MCP", "/docs/cli/skills"),
    ("section", "移动端"),
    ("page", "手机伴侣", "/docs/mobile"),
    ("page", "在 Android 上安装 Orca Mobile", "/docs/android-apk"),
    ("section", "通知与收件箱"),
    ("page", "通知与收件箱", "/docs/notifications"),
    ("page", "智能体动态", "/docs/activity"),
    ("group", "场景示例"),
    ("page", "让三个智能体同时做一件事", "/docs/recipes/parallel-agents"),
    ("page", "逐行审阅 AI 改动", "/docs/recipes/review-ai-diff"),
    ("page", "在 10 个工作树之间跳转", "/docs/recipes/jump-worktrees"),
    ("page", "用设计模式修界面问题", "/docs/recipes/design-mode-fix"),
    ("page", "通过 SSH 在远程机器上工作", "/docs/recipes/remote-worktrees"),
    ("section", "设置说明"),
    ("page", "设置说明", "/docs/settings"),
    ("section", "隐私与遥测"),
    ("page", "隐私与遥测", "/docs/telemetry"),
    ("section", "故障排查与常见问题"),
    ("page", "故障排查与常见问题", "/docs/troubleshooting"),
    ("page", "排查 GitHub 错误", "/docs/github-errors"),
]


def slug_for(source: str) -> str:
    if source == "/docs":
        return "what-is-orca"
    return source.removeprefix("/docs/").replace("/", "-")


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
            title, source = item[1], item[2]
            pages.append(
                {
                    "slug": slug_for(source),
                    "title": title,
                    "source": source,
                    "section": section,
                    "group": group,
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
            page = pages_by_source[item[2]]
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
    if index == 0:
        parts.append(
            '        <a class="prev" href="#home"><span>返回</span><strong>文档骨架首页</strong></a>'
        )
    else:
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
    return f"""    <article id="{page["slug"]}" class="doc" data-source="{escape(page["source"])}">
      <p class="kicker">{escape(kicker(page))}</p>
      <h1>{escape(page["title"])}</h1>
      <p class="placeholder">{escape(PLACEHOLDER)}</p>
      <p class="meta">英文原文：<a href="{escape(url)}">{escape(url.removeprefix("https://"))}</a></p>
{pager(pages, index)}
    </article>"""


HOME = """    <article id="home" class="doc">
      <p class="kicker">文档骨架</p>
      <h1>ORCA 说明文档</h1>
      <p class="lead">这是 ORCA 中文说明文档的骨架。左侧目录按照英文文档站的真实栏目排好，先把站点立起来。各章正文的译文还没有放入。</p>
      <h2>现在能看什么</h2>
      <ul>
        <li>目录与 <a href="https://orca.dev/docs">orca.dev/docs</a> 的侧栏一致，名称是临时的中文意译。</li>
        <li>点开任意一章，会看到统一的占位句。</li>
        <li>版式按长文来排：正文有最大宽度，标题分层，代码单独成块。</li>
      </ul>
      <h2>版式预览</h2>
      <p>下面用一段命令确认代码块和行内代码的样式。命令和标识符保持原文。</p>
      <h3>代码块</h3>
      <pre><code>git worktree list</code></pre>
      <p>行内命令写成 <code>orca</code>，与正文分开。</p>
      <h2>接下来</h2>
      <p>从目录进入 <a href="#what-is-orca">Orca 是什么</a>。译文写好后，会替换各章里的占位，目录仍与英文站对应。</p>
    </article>"""


CURRENT_CSS = """
    body:not(:has(.doc:target)) a.nav-link[href="#home"],
    body:has(#home:target) a.nav-link[href="#home"],
    {selectors} {{
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 650;
    }}
"""


def current_css(pages):
    selectors = ",\n    ".join(
        f'body:has(#{page["slug"]}:target) a.nav-link[href="#{page["slug"]}"]' for page in pages
    )
    return CURRENT_CSS.format(selectors=selectors).strip()


SCRIPT = """
    (function () {
      var toggle = document.getElementById("nav-toggle");
      var sidebar = document.getElementById("sidebar");

      function sync() {
        var id = (location.hash || "#home").slice(1);
        if (!document.getElementById(id)) id = "home";
        var links = sidebar.querySelectorAll("a[href^='#']");
        for (var i = 0; i < links.length; i++) {
          var on = links[i].getAttribute("href") === "#" + id;
          if (on) links[i].setAttribute("aria-current", "page");
          else links[i].removeAttribute("aria-current");
        }
        var heading = document.querySelector("#" + id + " h1");
        document.title = !heading || id === "home"
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
  <meta name="description" content="ORCA 中文说明文档骨架。栏目已按英文文档站排好，各章译文尚未放入。">
  <link rel="stylesheet" href="styles.css">
  <style>
    {current_css(pages)}
  </style>
</head>
<body>
  <a class="skip" href="#content">跳到正文</a>
  <header class="topbar">
    <a class="brand" href="#home">ORCA 说明文档</a>
    <p class="brand-note">中文骨架</p>
    <label class="menu-button" for="nav-toggle">目录</label>
  </header>
  <input class="nav-toggle" id="nav-toggle" type="checkbox">
  <div class="layout">
    <aside class="sidebar" id="sidebar">
      <nav aria-label="文档目录">
        <a class="nav-link" href="#home">文档骨架</a>
{nav_html(by_source)}
      </nav>
    </aside>
    <label class="backdrop" for="nav-toggle"></label>
    <main class="content" id="content">
{HOME}
{chapters}
    </main>
  </div>
  <script>
{SCRIPT}
  </script>
</body>
</html>
"""


def main():
    pages = collect_pages()
    html = render(pages)
    if PLACEHOLDER not in html:
        raise SystemExit("缺少占位句")
    home, _, rest = html.partition('<article id="what-is-orca"')
    if PLACEHOLDER in home:
        raise SystemExit("首页不应使用章节占位句")
    if html.count(PLACEHOLDER) != len(pages):
        raise SystemExit("占位句数量与章节数不一致")
    if "Orca is a desktop IDE" in html:
        raise SystemExit("骨架里混入了英文正文")
    out = ROOT / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(pages)} chapters)")


if __name__ == "__main__":
    main()
