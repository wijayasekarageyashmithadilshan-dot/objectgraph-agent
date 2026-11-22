"""Parse Mermaid ``classDiagram`` blocks (as used in DevBench UML_class.md files).

The parser is deliberately tolerant: DevBench diagrams mix several Mermaid
dialects (members inside ``class X { ... }`` blocks, ``X : +member`` lines,
generic names such as ``Queue~T~``, cardinalities, and labels).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Arrow tokens, longest first so that e.g. "<|--" wins over "--".
ARROWS = ["<|--", "--|>", "<|..", "..|>", "*--", "--*", "o--", "--o",
          "<--", "-->", "<..", "..>", "--", ".."]
STRONG = {"<|--", "--|>", "<|..", "..|>", "*--", "--*", "o--", "--o"}

_NAME = r"[A-Za-z_][\w]*(?:~[^~\s]*(?:~[^~\s]*~)?[^~\s]*~)?"
_REL_RE = re.compile(
    r"^\s*(?P<a>" + _NAME + r")\s*(?:\"[^\"]*\"\s*)?"
    r"(?P<arrow>" + "|".join(re.escape(a) for a in ARROWS) + r")"
    r"\s*(?:\"[^\"]*\"\s*)?(?P<b>" + _NAME + r")\s*(?::\s*(?P<label>.*))?$"
)
_CLASS_RE = re.compile(r"^\s*class\s+(?P<name>" + _NAME + r")\s*(?P<brace>\{)?\s*(?P<rest>.*)$")
_MEMBER_LINE_RE = re.compile(r"^\s*(?P<name>" + _NAME + r")\s*:\s*(?P<member>.+)$")


def base_name(name: str) -> str:
    """``Queue~T~`` -> ``Queue``."""
    return name.split("~", 1)[0]


@dataclass
class UMLClass:
    name: str
    methods: list[str] = field(default_factory=list)      # raw member strings with "("
    attributes: list[str] = field(default_factory=list)   # raw member strings without "("
    stereotypes: list[str] = field(default_factory=list)

    def method_names(self) -> list[str]:
        """Unique method names in declaration order (overloads merged)."""
        seen, out = set(), []
        for m in self.methods:
            n = method_name(m)
            if n and n not in seen:
                seen.add(n)
                out.append(n)
        return out


@dataclass
class Relation:
    a: str
    b: str
    arrow: str
    label: str = ""

    @property
    def strong(self) -> bool:
        return self.arrow in STRONG


@dataclass
class ClassDiagram:
    classes: dict[str, UMLClass]
    relations: list[Relation]


def method_name(member: str) -> str:
    """Extract the bare method name from a member string such as
    ``+vector~VertexType~ bfs(VertexType)`` or ``+parse_args() ArgumentParser``."""
    head = member.split("(", 1)[0].strip()
    head = head.lstrip("+-#~ ").strip()
    if not head:
        return ""
    token = head.split()[-1]          # C++/Java style puts the return type first
    token = token.strip("*&")
    return token


def _extract_mermaid(text: str) -> str:
    """Return the body of the first fenced block containing ``classDiagram``
    (or the whole text if there are no fences)."""
    blocks = re.findall(r"```[^\n]*\n(.*?)```", text, flags=re.S)
    for b in blocks:
        if "classDiagram" in b:
            return b
    return text


def parse_class_diagram(text: str) -> ClassDiagram:
    body = _extract_mermaid(text)
    classes: dict[str, UMLClass] = {}
    relations: list[Relation] = []

    def get(name: str) -> UMLClass:
        key = base_name(name)
        if key not in classes:
            classes[key] = UMLClass(key)
        return classes[key]

    def add_member(cls: UMLClass, member: str) -> None:
        member = member.strip().rstrip(";").strip()
        if not member or member in {"...", "}"}:
            return
        if member.startswith("<<"):
            cls.stereotypes.append(member.strip("<> "))
            return
        if "(" in member:
            cls.methods.append(member)
        elif re.match(r"^[+\-#~]?\s*[\w\[\]<>~:*&, ]+$", member):
            cls.attributes.append(member)
        # anything else (free-text notes) is ignored

    current: UMLClass | None = None
    for raw in body.splitlines():
        line = raw.split("%%", 1)[0].rstrip()
        s = line.strip()
        if not s or s == "classDiagram":
            continue
        if current is not None:
            if s.startswith("}"):
                current = None
                continue
            add_member(current, s.rstrip("}"))
            if s.endswith("}"):
                current = None
            continue
        m = _CLASS_RE.match(s)
        if m:
            cls = get(m.group("name"))
            rest = m.group("rest") or ""
            if m.group("brace"):
                if rest.endswith("}"):
                    for part in rest[:-1].split(";"):
                        add_member(cls, part)
                else:
                    if rest:
                        add_member(cls, rest)
                    current = cls
            continue
        r = _REL_RE.match(s)
        if r:
            relations.append(Relation(base_name(r.group("a")), base_name(r.group("b")),
                                      r.group("arrow"), (r.group("label") or "").strip()))
            continue
        mm = _MEMBER_LINE_RE.match(s)
        if mm:
            member = mm.group("member").strip()
            # "X : note text" lines (e.g. lice's Global_functions note) are notes, not members
            if "(" in member or re.match(r"^[+\-#~]", member):
                add_member(get(mm.group("name")), member)
    return ClassDiagram(classes, relations)
