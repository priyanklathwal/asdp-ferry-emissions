"""Inline the model output into the dashboard so docs/index.html is fully self-contained."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, "docs", "data.json")))
tpl = open(os.path.join(ROOT, "src", "template.html")).read()
html = tpl.replace("__DATA__", json.dumps(data, separators=(",", ":")))
out = os.path.join(ROOT, "docs", "index.html")
open(out, "w").write(html)
print(f"wrote {out}  ({len(html)/1024:.0f} KB)")
