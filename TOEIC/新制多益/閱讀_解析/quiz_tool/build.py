"""把多益閱讀解析 md 合併成一份可作答的練習網頁。
用法（在 閱讀_解析/ 資料夾執行）：python3 quiz_tool/build.py
會讀取同一層所有 exam_*.md，輸出 多益閱讀練習.html
"""
import json, pathlib

here = pathlib.Path(__file__).resolve().parent
root = here.parent
tpl = (here / "template.html").read_text()
sources = {p.stem: p.read_text() for p in sorted(root.glob("exam_*.md"))}
data = json.dumps(sources, ensure_ascii=False).replace("</", "<\\/")
out = root / "多益閱讀練習.html"
out.write_text(tpl.replace("__SOURCES__", data))
print(f"wrote {out.name}（{len(sources)} 份考卷）")
