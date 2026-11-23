# ORCA 说明文档

中文说明文档。左侧目录对应 [英文文档](https://orca.dev/docs) 的栏目，正文是已经译好的章节。

## 本地打开

用浏览器直接打开仓库根目录的 `index.html` 即可。不需要安装依赖。

从仓库根目录也可以起一个本地静态服务：

```bash
python3 -m http.server 8765
```

然后访问 <http://127.0.0.1:8765/>。

## 重新生成页面

栏目和译文读取写在 `scripts/build_skeleton.py`。改完后运行：

```bash
python3 scripts/build_skeleton.py
```

生成脚本需要 Python 包 `mistune`。
