"""A fake model for testing the pipeline without an API key.

* Design extraction: returns the gold class diagram.
* Agents: return one FILE block with empty stubs for the classes they own.
The code is deliberately not a real implementation, so scores are ~0.
"""
import re


def fake_reply(system: str, user: str, gold_text: str) -> str:
    if "domain model as a Mermaid classDiagram" in user:
        return gold_text
    owned = re.search(r"Classes you own: (.*)", user).group(1).split(", ")
    duties = re.findall(r"^- (\S+\.\S+)$", user, flags=re.M)
    path = "stocktrends/indicators.py"
    m = re.search(r"`([\w/]+\.py)`:", user)
    if m:
        path = m.group(1) if "/" in m.group(1) else f"stocktrends/{m.group(1)}"
    lines = ["import pandas as pd", ""]
    for c in owned:
        lines.append(f"class {c}:")
        body = [d.split(".", 1)[1] for d in duties if d.startswith(c + ".") and not d.endswith("<state>")]
        if not body:
            lines.append("    pass")
        for meth in body:
            lines += [f"    # duty: {c}.{meth}", f"    def {meth}(self, *args, **kwargs):", "        return None"]
        lines.append("")
    return f"### FILE: {path}\n```python\n" + "\n".join(lines) + "\n```\n"
