# ORCA 说明文档

说明文档。左侧目录用 [英文文档](https://orca.dev/docs) 的英文栏目名，两种语言下都不改。顶栏右上角可以在「中文」和 English 之间切换当前章的正文。中文是已有译文，English 是官网对应页的正文。选择记在浏览器本地，默认中文。

## 本地打开

用浏览器直接打开仓库根目录的 `index.html` 即可。不需要安装依赖。

从仓库根目录也可以起一个本地静态服务：

```bash
python3 -m http.server 8765
```

然后访问 <http://127.0.0.1:8765/>。

## 重新生成页面

栏目、中文译文和 `content/en/` 里的英文正文由 `scripts/build_skeleton.py` 生成页面。英文片段可以用 `scripts/fetch_english.py` 从官网重新抓取。改完后运行：

```bash
python3 scripts/build_skeleton.py
```

生成脚本需要 Python 包 `mistune`。
