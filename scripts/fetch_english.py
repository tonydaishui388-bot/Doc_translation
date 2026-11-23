#!/usr/bin/env python3
"""Save the live orca.dev/docs article bodies as English HTML fragments.

Each file is the official page's title and prose (headings, paragraphs,
lists, tables, code, figures). Sidebar chrome, the email form, and
mobile-only duplicates are left out. Doc links point at this site's
chapter hashes instead of orca.dev.
"""

from html import escape
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from build_skeleton import NAV, ORIGIN, slug_for

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "content" / "en"

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SKIP_TAGS = {"script", "style", "svg", "form", "button", "input", "noscript", "iframe", "canvas", "template"}
KEEP = {
    "h1", "h2", "h3", "h4", "p", "ul", "ol", "li", "pre", "code", "a", "img",
    "table", "thead", "tbody", "tr", "th", "td", "strong", "em", "blockquote",
    "aside", "figure", "figcaption", "br", "hr", "kbd", "sup", "sub", "details", "summary",
}
HEADING = {"h2", "h3", "h4"}


def pages():
    found = []
    for item in NAV:
        if item[0] == "page":
            found.append((item[1], item[2]))
    return found


def skip_class(value):
    tokens = set((value or "").split())
    if "md:hidden" in tokens or "sm:hidden" in tokens or "lg:hidden" in tokens or "sr-only" in tokens:
        return True
    if "hidden" in tokens and not tokens.intersection({"md:block", "md:flex", "md:grid", "lg:block"}):
        return True
    return False


class Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = {"tag": None, "attrs": {}, "children": []}
        self.stack = [self.root]
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.skip:
            self.skip += 1
            return
        if tag in SKIP_TAGS or skip_class(attrs.get("class", "")):
            self.skip = 1
            return
        node = {"tag": tag, "attrs": attrs, "children": []}
        self.stack[-1]["children"].append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        if self.skip:
            self.skip -= 1
            return
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index]["tag"] == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        if self.skip or not data:
            return
        self.stack[-1]["children"].append(data)


def find_first(node, tag):
    if not isinstance(node, dict):
        return None
    if node.get("tag") == tag:
        return node
    for child in node.get("children", []):
        found = find_first(child, tag)
        if found:
            return found
    return None


def text_of(node):
    if isinstance(node, str):
        return node
    return "".join(text_of(child) for child in node.get("children", []))


def collect_ids(node, found):
    if not isinstance(node, dict):
        return
    if node.get("tag") in HEADING and node["attrs"].get("id"):
        found.add(node["attrs"]["id"])
    for child in node.get("children", []):
        collect_ids(child, found)


def article_parts(tree):
    article = find_first(tree, "article")
    if not article:
        return "", []
    title = ""
    body = []
    for child in article["children"]:
        if not isinstance(child, dict):
            continue
        if child["tag"] == "header":
            for sub in child["children"]:
                if isinstance(sub, dict) and sub["tag"] == "h1":
                    title = text_of(sub).strip()
                elif isinstance(sub, dict):
                    body.append(sub)
        elif child["tag"] == "nav":
            continue
        else:
            body.append(child)
    return title, body


def fetch(path):
    request = urllib.request.Request(ORIGIN + path, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read().decode("utf-8", "replace")


def parse_page(html):
    builder = Builder()
    builder.feed(html)
    return article_parts(builder.root)


def rewrite_href(href, current_source, ids_by_source):
    if not href:
        return href
    if href.startswith("#"):
        source = current_source
        fragment = href[1:]
        bare = None
    else:
        bare = href
        for prefix in (ORIGIN, "https://www.orca.dev"):
            if bare.startswith(prefix):
                bare = bare[len(prefix):]
                break
        if not bare.startswith("/docs"):
            if bare.startswith("/"):
                return ORIGIN + bare
            return href
        path, _, frag = bare.partition("#")
        path = path.split("?", 1)[0].rstrip("/") or "/docs"
        if path not in ids_by_source:
            return ORIGIN + bare
        source = path
        fragment = frag or None
    if fragment and fragment in ids_by_source.get(source, ()):
        return f"#{slug_for(source)}-{fragment}"
    if source in ids_by_source:
        return f"#{slug_for(source)}"
    return href


def serialize(node, slug, source, ids_by_source):
    if isinstance(node, str):
        return escape(node)
    tag = node["tag"]
    inner = "".join(serialize(child, slug, source, ids_by_source) for child in node["children"])
    if tag == "pre":
        code = text_of(node).strip("\n")
        return f"<pre><code>{escape(code)}</code></pre>"
    if tag == "img":
        src = node["attrs"].get("src", "")
        if src.startswith("/"):
            src = ORIGIN + src
        alt = node["attrs"].get("alt", "")
        return (
            f'<img src="{escape(src, quote=True)}" alt="{escape(alt, quote=True)}"'
            f' loading="lazy" decoding="async">'
        )
    if tag == "a":
        href = rewrite_href(node["attrs"].get("href", ""), source, ids_by_source)
        if not href:
            return inner
        return f'<a href="{escape(href, quote=True)}">{inner}</a>'
    if tag in HEADING:
        raw = node["attrs"].get("id")
        ident = f' id="{escape(slug + "-" + raw, quote=True)}"' if raw else ""
        return f"<{tag}{ident}>{inner}</{tag}>"
    if tag in KEEP:
        return f"<{tag}>{inner}</{tag}>"
    return inner


def main():
    listing = pages()
    raw = {}
    errors = []

    def load(item):
        source, nav_title = item
        try:
            html = fetch(source)
        except Exception as error:
            return source, nav_title, None, str(error)
        return source, nav_title, html, None

    with ThreadPoolExecutor(10) as pool:
        futures = [pool.submit(load, item) for item in listing]
        for future in as_completed(futures):
            source, nav_title, html, error = future.result()
            if error:
                errors.append({"source": source, "error": error})
            else:
                raw[source] = (nav_title, html)

    parsed = {}
    ids_by_source = {}
    for source, (nav_title, html) in raw.items():
        title, body = parse_page(html)
        ids = set()
        for node in body:
            collect_ids(node, ids)
        parsed[source] = (nav_title, title, body)
        ids_by_source[source] = ids

    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for source, nav_title in listing:
        slug = slug_for(source)
        record = {"source": source, "slug": slug, "navTitle": nav_title}
        if source not in parsed:
            record["issue"] = "fetch failed"
            manifest.append(record)
            continue
        _, title, body = parsed[source]
        html = "\n".join(serialize(node, slug, source, ids_by_source) for node in body)
        html = re.sub(r"\n{3,}", "\n\n", html).strip()
        text = re.sub(r"<[^>]+>", "", html)
        text = re.sub(r"\s+", " ", text).strip()
        record["h1"] = title
        record["textLength"] = len(text)
        record["codes"] = html.count("<pre>")
        record["images"] = html.count("<img ")
        issues = []
        if title != nav_title:
            issues.append(f"h1 {title!r} != nav {nav_title!r}")
        if len(text) < 80:
            issues.append("body is very short")
        if not title:
            issues.append("missing h1")
        if issues:
            record["issue"] = "; ".join(issues)
        (OUT / f"{slug}.html").write_text(f"<h1>{escape(title)}</h1>\n{html}\n", encoding="utf-8")
        manifest.append(record)

    (OUT / "manifest.json").write_text(json.dumps({"errors": errors, "pages": manifest}, ensure_ascii=False, indent=2), encoding="utf-8")
    problems = [page for page in manifest if page.get("issue")]
    print(f"wrote {len(manifest)} pages, problems {len(problems)}, fetch errors {len(errors)}")
    for page in problems:
        print("ISSUE", page["source"], page.get("issue"))
    for error in errors:
        print("ERROR", error)


if __name__ == "__main__":
    main()
