"""Build the IEEE Access Word manuscript from the official template.

  python scripts/make_paper_assets.py          # numbers from results/
  python scripts/make_ieee_docx.py --template Access-Template-2024.docx --out paper/ObjectGraph-Agent_IEEE-Access.docx

Keeps the template's styles, title block, headers/footers and two-column
layout, and replaces its instructional content with the paper. Every result
number comes from paper/generated/numbers.tex and results/*.json. Citations are
numbered in order of first appearance, as IEEE requires.

Inline mark-up in the text below:
  {i:..} italic  {b:..} bold  {sub:..} {sup:..}  {cite:key1,key2}
  {N:Macro} number from numbers.tex  {P:..} red [PENDING] slot  {T:..} blue [TO ADD] slot
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------- references
REFS = {
 "hong2024metagpt": 'S. Hong {i:et al.}, “MetaGPT: Meta programming for a multi-agent collaborative framework,” in {i:Proc. Int. Conf. Learn. Represent. (ICLR)}, 2024, doi: 10.48550/arXiv.2308.00352.',
 "qian2024chatdev": 'C. Qian {i:et al.}, “ChatDev: Communicative agents for software development,” in {i:Proc. 62nd Annu. Meeting Assoc. Comput. Linguistics (ACL)}, 2024, doi: 10.48550/arXiv.2307.07924.',
 "wu2023autogen": 'Q. Wu {i:et al.}, “AutoGen: Enabling next-gen LLM applications via multi-agent conversation,” 2023, {i:arXiv:2308.08155}, doi: 10.48550/arXiv.2308.08155.',
 "ke2025maszero": 'Z. Ke {i:et al.}, “MAS-Zero: Designing multi-agent systems with zero supervision,” presented at the {i:NeurIPS Workshop Scaling Environments for Agents}, 2025, doi: 10.48550/arXiv.2505.14996.',
 "hu2025adas": 'S. Hu, C. Lu, and J. Clune, “Automated design of agentic systems,” in {i:Proc. Int. Conf. Learn. Represent. (ICLR)}, 2025, doi: 10.48550/arXiv.2408.08435.',
 "zhang2025aflow": 'J. Zhang {i:et al.}, “AFlow: Automating agentic workflow generation,” in {i:Proc. Int. Conf. Learn. Represent. (ICLR)}, 2025, doi: 10.48550/arXiv.2410.10762.',
 "zhang2025maas": 'G. Zhang, L. Niu, J. Fang, K. Wang, L. Bai, and X. Wang, “Multi-agent architecture search via agentic supernet,” in {i:Proc. 42nd Int. Conf. Mach. Learn. (ICML)}, vol. 267, 2025, pp. 75834–75852, doi: 10.48550/arXiv.2502.04180.',
 "kim2025scaling": 'Y. Kim {i:et al.}, “Towards a science of scaling agent systems,” 2025, {i:arXiv:2512.08296}, doi: 10.48550/arXiv.2512.08296.',
 "li2026scalingbehavior": 'J. Li, Z. Gu, Y. Cai, and H. Feng, “Scaling behavior of single LLM-driven multi-agent systems,” 2026, {i:arXiv:2606.00655}, doi: 10.48550/arXiv.2606.00655.',
 "bertalanic2026ringelmann": 'B. Bertalanič and C. Fortuna, “The Ringelmann effect in multi-agent LLM systems: A scaling law for effective team size,” 2026, {i:arXiv:2606.02646}, doi: 10.48550/arXiv.2606.02646.',
 "zhang2026rethinking": 'J. Zhang {i:et al.}, “Rethinking the evaluation of efficiency methods for multi-agent systems,” in {i:Proc. Conf. Empirical Methods Natural Lang. Process. (EMNLP)}, 2026, doi: 10.48550/arXiv.2609.05933.',
 "jwalapuram2026illusion": 'P. Jwalapuram {i:et al.}, “The illusion of multi-agent advantage,” in {i:Proc. Adv. Neural Inf. Process. Syst. (NeurIPS)}, 2026, doi: 10.48550/arXiv.2606.13003.',
 "cemri2025why": 'M. Cemri {i:et al.}, “Why do multi-agent LLM systems fail?” in {i:Proc. Adv. Neural Inf. Process. Syst. (NeurIPS) Datasets Benchmarks Track}, 2025, doi: 10.48550/arXiv.2503.13657.',
 "parnas1972criteria": 'D. L. Parnas, “On the criteria to be used in decomposing systems into modules,” {i:Commun. ACM}, vol. 15, no. 12, pp. 1053–1058, Dec. 1972, doi: 10.1145/361598.361623.',
 "chidamber1994metrics": 'S. R. Chidamber and C. F. Kemerer, “A metrics suite for object oriented design,” {i:IEEE Trans. Softw. Eng.}, vol. 20, no. 6, pp. 476–493, Jun. 1994, doi: 10.1109/32.295895.',
 "conway1968committees": 'M. E. Conway, “How do committees invent?” {i:Datamation}, vol. 14, no. 4, pp. 28–31, Apr. 1968.',
 "cheng2026oopmas": 'Q. Cheng {i:et al.}, “OOPMAS: Object-oriented multi-agent systems for query-level workflow generation,” 2026, {i:arXiv:2610.07787}, doi: 10.48550/arXiv.2610.07787.',
 "wei2026modeldriven": 'R. Wei {i:et al.}, “Model-driven discipline for multi-agent LLMs: Requirement-to-verification generation of traceable system models,” 2026, {i:arXiv:2607.16708}, doi: 10.48550/arXiv.2607.16708.',
 "zhang2025gdesigner": 'G. Zhang {i:et al.}, “G-Designer: Architecting multi-agent communication topologies via graph neural networks,” in {i:Proc. 42nd Int. Conf. Mach. Learn. (ICML)}, vol. 267, 2025, pp. 76678–76692, doi: 10.48550/arXiv.2410.11782.',
 "zhang2025agentprune": 'G. Zhang {i:et al.}, “Cut the crap: An economical communication pipeline for LLM-based multi-agent systems,” in {i:Proc. Int. Conf. Learn. Represent. (ICLR)}, 2025, doi: 10.48550/arXiv.2410.02506.',
 "wang2025agentdropout": 'Z. Wang {i:et al.}, “AgentDropout: Dynamic agent elimination for token-efficient and high-performance LLM-based multi-agent collaboration,” in {i:Proc. 63rd Annu. Meeting Assoc. Comput. Linguistics (ACL)}, 2025, pp. 24013–24035, doi: 10.18653/v1/2025.acl-long.1170.',
 "li2026argdesigner": 'S. Li, Y. Liu, Q. Wen, C. Zhang, and S. Pan, “Assemble your crew: Automatic multi-agent communication topology design via autoregressive graph generation,” in {i:Proc. AAAI Conf. Artif. Intell.}, 2026, doi: 10.48550/arXiv.2507.18224.',
 "hu2025evomac": 'Y. Hu {i:et al.}, “Self-evolving multi-agent collaboration networks for software development,” in {i:Proc. Int. Conf. Learn. Represent. (ICLR)}, 2025, doi: 10.48550/arXiv.2410.16946.',
 "yang2026cocoder": 'X. Yang, L. Nie, E. Chandra, S. Gannutin, F. Lin, and S. Chaudhuri, “When parallelism pays off: Cohesion-aware task partitioning for multi-agent coding,” in {i:Proc. Adv. Neural Inf. Process. Syst. (NeurIPS)}, 2026, doi: 10.48550/arXiv.2606.00953.',
 "rosvall2008infomap": 'M. Rosvall and C. T. Bergstrom, “Maps of random walks on complex networks reveal community structure,” {i:Proc. Nat. Acad. Sci. USA}, vol. 105, no. 4, pp. 1118–1123, Jan. 2008, doi: 10.1073/pnas.0706851105.',
 "mancoridis1998bunch": 'S. Mancoridis, B. S. Mitchell, C. Rorres, Y.-F. Chen, and E. R. Gansner, “Using automatic clustering to produce high-level system organizations of source code,” in {i:Proc. 6th Int. Workshop Program Comprehension (IWPC)}, 1998, pp. 45–52, doi: 10.1109/WPC.1998.693283.',
 "mitchell2006bunch": 'B. S. Mitchell and S. Mancoridis, “On the automatic modularization of software systems using the Bunch tool,” {i:IEEE Trans. Softw. Eng.}, vol. 32, no. 3, pp. 193–208, Mar. 2006, doi: 10.1109/TSE.2006.31.',
 "wirfsbrock1989responsibility": 'R. Wirfs-Brock and B. Wilkerson, “Object-oriented design: A responsibility-driven approach,” in {i:Proc. Conf. Object-Oriented Program. Syst., Lang. Appl. (OOPSLA)}, 1989, pp. 71–75, doi: 10.1145/74877.74885.',
 "giannouris2025nomad": 'P. Giannouris and S. Ananiadou, “NOMAD: A multi-agent LLM system for UML class diagram generation from natural language requirements,” 2025, {i:arXiv:2511.22409}, doi: 10.48550/arXiv.2511.22409.',
 "li2024devbench": 'B. Li {i:et al.}, “Prompting large language models to tackle the full software development lifecycle: A case study,” 2024, {i:arXiv:2403.08604} (benchmark released as DevBench/DevEval), doi: 10.48550/arXiv.2403.08604.',
 "hubert1985ari": 'L. Hubert and P. Arabie, “Comparing partitions,” {i:J. Classification}, vol. 2, no. 1, pp. 193–218, 1985, doi: 10.1007/BF01908075.',
 "blondel2008louvain": 'V. D. Blondel, J.-L. Guillaume, R. Lambiotte, and E. Lefebvre, “Fast unfolding of communities in large networks,” {i:J. Stat. Mech.: Theory Exp.}, vol. 2008, no. 10, Oct. 2008, Art. no. P10008, doi: 10.1088/1742-5468/2008/10/P10008.',
 "holm1979simple": 'S. Holm, “A simple sequentially rejective multiple test procedure,” {i:Scand. J. Statist.}, vol. 6, no. 2, pp. 65–70, 1979.',
}

# --------------------------------------------------------------------------- inline markup -> runs
ORDER: list[str] = []
NUMS: dict[str, str] = {}


def cite(keys: str) -> str:
    nums = []
    for k in [x.strip() for x in keys.split(",")]:
        if k not in REFS:
            raise KeyError(f"unknown citation {k}")
        if k not in ORDER:
            ORDER.append(k)
        nums.append(ORDER.index(k) + 1)
    nums = sorted(set(nums))
    parts, i = [], 0
    while i < len(nums):          # IEEE: [1], [2] or [3]–[5]
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        parts.append(f"[{nums[i]}]–[{nums[j]}]" if j - i >= 2 else ", ".join(f"[{n}]" for n in nums[i:j + 1]))
        i = j + 1
    return ", ".join(parts)


TOKEN = re.compile(r"\{(i|b|sub|sup|cite|N|P|T|bi):([^{}]*)\}")


def runs(text: str, base: str = "") -> str:
    """Convert mark-up to <w:r> elements. base = extra rPr (e.g. small font)."""
    out, pos = [], 0

    def r(t: str, rpr: str = "") -> str:
        if not t:
            return ""
        t = escape(t)
        props = rpr + base
        return f'<w:r>{"<w:rPr>" + props + "</w:rPr>" if props else ""}<w:t xml:space="preserve">{t}</w:t></w:r>'

    for m in TOKEN.finditer(text):
        out.append(r(text[pos:m.start()]))
        tag, val = m.group(1), m.group(2)
        if tag == "i":
            out.append(r(val, "<w:i/>"))
        elif tag == "b":
            out.append(r(val, "<w:b/>"))
        elif tag == "bi":
            out.append(r(val, "<w:b/><w:i/>"))
        elif tag == "sub":
            out.append(r(val, '<w:vertAlign w:val="subscript"/>'))
        elif tag == "sup":
            out.append(r(val, '<w:vertAlign w:val="superscript"/>'))
        elif tag == "cite":
            out.append(r(cite(val)))
        elif tag == "N":
            out.append(r(NUMS[val]))
        elif tag == "P":
            out.append(r(f"[PENDING: {val}]", '<w:color w:val="C00000"/>'))
        elif tag == "T":
            out.append(r(f"[TO ADD: {val}]", '<w:color w:val="1F4E9A"/>'))
        pos = m.end()
    out.append(r(text[pos:]))
    return "".join(out)


def para(style: str, text: str, extra_ppr: str = "", base: str = "") -> str:
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{extra_ppr}</w:pPr>{runs(text, base)}</w:p>'


# --------------------------------------------------------------------------- document pieces
SECT_2COL_CONT = ('<w:sectPr>{refs}<w:type w:val="continuous"/><w:pgSz w:w="11520" w:h="15660" w:code="1"/>'
                  '<w:pgMar w:top="1280" w:right="740" w:bottom="1040" w:left="740" w:header="360" w:footer="640" w:gutter="0"/>'
                  '<w:cols w:num="2" w:space="400"/><w:docGrid w:linePitch="360"/></w:sectPr>')
SECT_1COL_CONT = SECT_2COL_CONT.replace('<w:cols w:num="2" w:space="400"/>', '<w:cols w:space="720"/>')


class Doc:
    def __init__(self):
        self.body: list[str] = []
        self.h2num: int | None = None
        self.next_num = 200
        self.new_nums: list[str] = []
        self.images: list[tuple[str, Path]] = []
        self.fig = 0
        self.tab = 0

    def h1(self, title: str, first: bool = False, numbered: bool = True):
        style = ("H1ListNoSpace" if first else "H1ListSpace") if numbered else "H1"
        self.body.append(para(style, title.upper()))
        self.h2num = None

    def h2(self, title: str):
        if self.h2num is None:
            self.h2num = self.next_num
            self.next_num += 1
            self.new_nums.append(f'<w:num w:numId="{self.h2num}"><w:abstractNumId w:val="1"/>'
                                 f'<w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride></w:num>')
        self.body.append(f'<w:p><w:pPr><w:pStyle w:val="H2Cont"/><w:numPr><w:ilvl w:val="0"/>'
                         f'<w:numId w:val="{self.h2num}"/></w:numPr></w:pPr>{runs(title.upper())}</w:p>')

    def p(self, text: str, first: bool = False):
        self.body.append(para("PARA" if first else "PARAIndent", text))

    def eq(self, text: str, number: int):
        # column width = (11520 - 2*740 - 400) / 2 = 4820 twips: centre tab mid-column, right tab at the edge
        self.body.append(f'<w:p><w:pPr><w:pStyle w:val="Equation"/><w:tabs><w:tab w:val="clear" w:pos="4584"/>'
                         f'<w:tab w:val="clear" w:pos="4840"/><w:tab w:val="center" w:pos="2410"/><w:tab w:val="right" w:pos="4800"/></w:tabs>'
                         f'<w:ind w:left="0" w:right="0" w:firstLine="0"/><w:jc w:val="left"/></w:pPr>'
                         f'<w:r><w:tab/></w:r>{runs(text)}'
                         f'<w:r><w:rPr><w:i w:val="0"/></w:rPr><w:tab/><w:t>({number})</w:t></w:r></w:p>')

    def figure(self, png: Path, caption: str, width_in: float = 3.45):
        from PIL import Image
        self.fig += 1
        rid = f"rIdFig{self.fig}"
        self.images.append((rid, png))
        w, h = Image.open(png).size
        cx = int(width_in * 914400)
        cy = int(cx * h / w)
        drawing = (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
                   f'<wp:docPr id="{900 + self.fig}" name="Figure {self.fig}"/><wp:cNvGraphicFramePr/>'
                   '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                   '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                   '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                   f'<pic:nvPicPr><pic:cNvPr id="{900 + self.fig}" name="fig{self.fig}.png"/><pic:cNvPicPr/></pic:nvPicPr>'
                   f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
                   f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
                   '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
                   '</wp:inline></w:drawing></w:r>')
        self.body.append(f'<w:p><w:pPr><w:pStyle w:val="FigureCaption"/><w:keepNext/><w:jc w:val="center"/></w:pPr>{drawing}</w:p>')
        self.body.append(para("FigCaption", caption))

    def table(self, title: str, header: list[str], rows: list[list[str]], widths: list[int], size: int = 14,
              notes: str | None = None):
        """widths in twips; size in half-points."""
        self.tab += 1
        roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"][self.tab - 1]
        self.body.append(para("TableTitle", f"TABLE {roman}", "<w:keepNext/>"))
        self.body.append(para("TableTitle", title, "<w:keepNext/>"))
        base = f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'

        def cell(t: str, w: int, bold: bool = False, top: bool = False, bottom: bool = False) -> str:
            borders = ""
            if top or bottom:
                borders = "<w:tcBorders>" + ('<w:top w:val="single" w:sz="6" w:space="0" w:color="000000"/>' if top else "") + \
                          ('<w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/>' if bottom else "") + "</w:tcBorders>"
            txt = f"{{b:{t}}}" if bold and t else t
            return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{borders}</w:tcPr>'
                    f'<w:p><w:pPr><w:spacing w:before="0" w:after="0"/><w:jc w:val="left"/></w:pPr>{runs(txt, base)}</w:p></w:tc>')

        grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
        trs = ["<w:tr><w:trPr><w:tblHeader/></w:trPr>" + "".join(cell(h, w, True, True, True) for h, w in zip(header, widths)) + "</w:tr>"]
        for k, row in enumerate(rows):
            last = k == len(rows) - 1
            trs.append("<w:tr>" + "".join(cell(c, w, bottom=last) for c, w in zip(row, widths)) + "</w:tr>")
        self.body.append(f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:jc w:val="center"/>'
                         f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="50" w:type="dxa"/><w:right w:w="50" w:type="dxa"/></w:tblCellMar>'
                         f'</w:tblPr><w:tblGrid>{grid}</w:tblGrid>{"".join(trs)}</w:tbl>')
        if notes:
            self.body.append(para("FootnoteText", notes, '<w:spacing w:before="40" w:after="160"/>'))
        else:
            self.body.append('<w:p><w:pPr><w:spacing w:before="0" w:after="120"/></w:pPr></w:p>')

    def section_break(self, cols: int, refs: str = ""):
        sp = SECT_2COL_CONT if cols == 2 else SECT_1COL_CONT
        self.body.append(f'<w:p><w:pPr><w:spacing w:before="0" w:after="0"/>{sp.format(refs=refs)}</w:pPr></w:p>')


# --------------------------------------------------------------------------- content
def build_content(d: Doc, S: dict, REFT: list) -> dict:
    AG = json.loads((ROOT / "paper/generated/agent.json").read_text())
    has_pilot = bool(AG.get("pilot_rows"))
    ref_tab = "Table V" if has_pilot else "Table IV"
    multi = [p for p in S["projects"] if p["duty"]["k_star"] > 1]
    single = sorted([p for p in S["projects"] if p["duty"]["k_star"] == 1], key=lambda p: p["project"].lower())
    single_list = ", ".join(f'{p["project"]} ({p["duty"]["n"]})' for p in single)

    d.h1("Introduction", first=True)
    d.p("Multi-agent systems built on large language models (LLMs) split one software task among several agents {cite:hong2024metagpt,qian2024chatdev,wu2023autogen}. Someone must decide how many agents to use and what each one owns. Current practice takes one of three routes: fix the roles by hand {cite:hong2024metagpt,qian2024chatdev}, let a model propose a team {cite:ke2025maszero}, or search for or learn a team from scored executions {cite:hu2025adas,zhang2025aflow,zhang2025maas}. None of these routes gives a rule that can be stated, tested and repeated before the work starts.", first=True)
    d.p("Recent findings make the question pressing. Multi-agent variants can perform worse than a single agent on tasks with sequential dependencies {cite:kim2025scaling}. The best number of agents depends on the task and on the strength of the underlying model {cite:li2026scalingbehavior}, and the effective size of a team grows much more slowly than its head count {cite:bertalanic2026ringelmann}. Many reported efficiency gains appear in settings where a single agent or a randomly pruned system already does well {cite:zhang2026rethinking}, and automatically generated multi-agent systems can trail a single agent at several times the cost {cite:jwalapuram2026illusion}. Unclear role specification is also a major cause of multi-agent failure {cite:cemri2025why}. Together, these results suggest that the first decision, whether and how to split, deserves its own method and its own controls.")
    d.p("Software engineering has long studied a closely related problem. A good decomposition keeps strongly related responsibilities together and keeps dependencies between parts few {cite:parnas1972criteria,chidamber1994metrics}, and Conway observed that a system’s structure mirrors the communication structure of the team that builds it {cite:conway1968committees}. We take this idea literally for LLM agents: if the parts of a design are cohesive and loosely coupled, agents that each own one part should need to communicate less.")
    d.p("We study {i:design-time team sizing}: choosing the number of agents and their responsibilities from a domain model, here a Unified Modeling Language (UML) class diagram, before any code is written. The contributions of this article are as follows:")
    for t in [
        "1) A formulation of team sizing as choosing a partition of a design-derived {i:duty graph}, in which a single agent is a legitimate answer (Section III).",
        "2) A deterministic criterion based on average-linkage clustering and modularization quality (MQ) with a per-agent cost, together with a closed-form expected cross-agent dependency for random teams of equal sizes and a locality assumption that links that dependency to messages (Section IV).",
        "3) A structural study on all {N:NProjects} DevBench projects in four programming languages, with random, one-agent-per-class, Louvain and Infomap controls and two sensitivity analyses (Section V).",
        "4) " + AG["contribution4"],
        "5) A fully deterministic artifact: one command regenerates every number in this article, and cached model responses allow the agent tables to be rebuilt without calling any model.",
    ]:
        d.p(t)

    d.h1("Related Work")
    d.h2("Hand-designed and model-designed teams")
    d.p("MetaGPT and ChatDev encode software-company roles by hand {cite:hong2024metagpt,qian2024chatdev}, and AutoGen provides conversation primitives without a sizing rule {cite:wu2023autogen}. MAS-Zero lets a meta-agent design and refine the system for each problem without a validation set {cite:ke2025maszero}. OOPMAS treats agents as objects and generates query-level workflows {cite:cheng2026oopmas}, and model-driven approaches derive traceable system models from requirements before agents act {cite:wei2026modeldriven}. These systems decide roles by convention or by model judgment; they do not derive the number of agents from a measurable property of the design or compare that choice with random teams.", first=True)
    d.h2("Searched, learned and pruned teams")
    d.p("Automated design of agentic systems (ADAS) and AFlow search over agent programs and workflows using scored executions {cite:hu2025adas,zhang2025aflow}, and multi-agent architecture search (MaAS) learns a query-dependent distribution over architectures {cite:zhang2025maas}. A second line learns communication topologies over a given pool of agents: G-Designer decodes a task-adaptive topology with a graph auto-encoder {cite:zhang2025gdesigner}, AgentPrune and AgentDropout remove redundant messages and agents {cite:zhang2025agentprune,wang2025agentdropout}, and ARG-Designer generates the collaboration graph autoregressively {cite:li2026argdesigner}. For software development, EvoMAC revises a team of coding agents using test feedback {cite:hu2025evomac}. All of these methods need scored tasks, training runs or test feedback, and most start from a given pool of agents. The criterion proposed here needs none of these and is applied once per design.", first=True)
    d.h2("How many agents?")
    d.p("Kim {i:et al.} {cite:kim2025scaling} model how agent-system performance depends on coordination structure, model capability and task properties, and find that multi-agent coordination can hurt on sequential tasks. Li {i:et al.} {cite:li2026scalingbehavior} show that the best number of agents depends on the task and the model, and Bertalanič and Fortuna {cite:bertalanic2026ringelmann} fit a scaling law for effective team size from small pilot runs on reasoning benchmarks. Zhang {i:et al.} {cite:zhang2026rethinking} recommend evaluating efficiency methods against random and single-agent baselines, and Jwalapuram {i:et al.} {cite:jwalapuram2026illusion} find that automatically generated multi-agent systems often underperform a single agent. These studies size teams from executions on reasoning or tool-use tasks; this article sizes them from the structure of a software design, before execution, and adopts their recommended controls.", first=True)
    d.h2("Closest work: cohesion-aware partitioning of code")
    d.p("Co-Coder formalizes multi-agent coding as graph partitioning: it builds a dependency graph of repository files by static analysis, isolates hub files, partitions the graph with Infomap community detection {cite:rosvall2008infomap}, and schedules agents along dependencies {cite:yang2026cocoder}. The present work differs in three ways. First, it starts from the {i:design}, before code exists, so the partition can guide generation rather than reorganize existing code. Second, it chooses the team size explicitly, including a single agent, rather than letting a community-detection method set it implicitly. Third, its duties come from the domain model, so each agent action can be traced to a design element. Infomap on the same duty graph is included as a control (condition G6), which separates the partitioning step from the input representation.", first=True)
    d.h2("Software modularization and design generation")
    d.p("MQ and the Bunch tool cluster existing source code into modules {cite:mancoridis1998bunch,mitchell2006bunch}, and responsibility-driven design assigns duties to objects {cite:wirfsbrock1989responsibility}. NOMAD generates UML class diagrams from natural-language requirements with a multi-agent pipeline {cite:giannouris2025nomad}, which makes a design-first workflow realistic.", first=True)

    d.h1("Problem Formulation")
    d.p("A {i:domain model} 𝓜 is a class diagram with classes, their methods and attributes, and typed relations (association, dependency, aggregation, composition, inheritance and realization).", first=True)
    d.p("{bi:Definition 1 (Duty graph):} The duty graph {i:G}(𝓜) = ({i:V}, {i:W}) has one node, or {i:duty}, per method of each class; a class without methods contributes one {i:state duty}. The symmetric weight {i:W}{sub:uv} ≥ 0 is the sum of four terms: {i:w}{sub:in} if {i:u} and {i:v} belong to the same class; {i:w}{sub:str} if their classes are linked by composition, aggregation, inheritance or realization; {i:w}{sub:weak} if their classes are linked by association or dependency; and {i:w}{sub:sig} if the signature of {i:u} names the class of {i:v}, or vice versa. Weights are scaled so that max {i:W} = 1.")
    d.p("A {i:team} is a partition π = {{i:C}{sub:1}, …, {i:C}{sub:k}} of {i:V}; agent {i:i} owns the duties in {i:C}{sub:i} and the code that implements them. Writing {i:W}({i:C}{sub:i}, {i:C}{sub:j}) for the total weight of edges between groups {i:C}{sub:i} and {i:C}{sub:j}, the {i:cut} of a team is the total dependency that crosses agent boundaries:")
    d.eq("cut(π) = Σ{sub:i<j} {i:W}({i:C}{sub:i}, {i:C}{sub:j}).", 1)
    d.p("{bi:Design-time team sizing:} given only 𝓜, with no code and no scored executions, choose {i:k} and π so that a team of {i:k} agents, each implementing its part, produces correct software at low cost. The choice {i:k} = 1 must be allowed, because splitting is not always beneficial {cite:kim2025scaling}.")

    d.h1("Method")
    d.h2("Criterion")
    d.p("For a team π with group sizes {i:N}{sub:i} = |{i:C}{sub:i}|, let μ{sub:i} be the total weight inside group {i:i} (counted in both orders) and ε{sub:ij} the total weight between groups {i:i} and {i:j}. Following Mancoridis {i:et al.} {cite:mancoridis1998bunch}, the intra-connectivity (cohesion) of group {i:i} is {i:A}{sub:i} = μ{sub:i}/{i:N}{sub:i}{sup:2}, the inter-connectivity (coupling) of groups {i:i} and {i:j} is {i:E}{sub:ij} = ε{sub:ij}/({i:N}{sub:i}{i:N}{sub:j}), and", first=True)
    d.eq("MQ(π) = mean{sub:i} {i:A}{sub:i} − mean{sub:i<j} {i:E}{sub:ij},", 2)
    d.p("where the first mean runs over the {i:k} groups and the second over the {i:k}({i:k}−1)/2 pairs of groups, with MQ(π) = {i:A}{sub:1} when {i:k} = 1. Average-linkage agglomerative clustering on the distance 1 − {i:W} yields a nested family π{sub:1}, …, π{sub:n} with exactly {i:k} groups at level {i:k}. The selected team size is")
    d.eq("{i:k}* = arg max{sub:k} [MQ(π{sub:k}) − λ({i:k}−1)/({i:n}−1)],", 3)
    d.p("with ties broken towards fewer agents. The penalty λ ≥ 0 charges for each additional agent; λ = 0 is the pre-registered default and is tuned only on development projects. In summary, the procedure (i) builds the duty graph, (ii) computes the average-linkage cut for every {i:k}, (iii) scores each cut with (3), and (iv) returns {i:k}* and π{sub:k*}, one agent per group. It is deterministic, and its cost is dominated by the clustering step, which is quadratic in the number of duties. Fig. 1 illustrates the procedure on one DevBench project.")
    d.h2("Cost of a random team of the same sizes")
    d.p("A fair control keeps the team sizes fixed and changes only {i:which} duties go together {cite:zhang2026rethinking}. Its expected cut has a closed form.", first=True)
    d.p("{bi:Proposition 1:} Let σ be a uniformly random assignment of the {i:n} duties to groups of fixed sizes {i:N}{sub:1}, …, {i:N}{sub:k}, and let {i:W}{sub:tot} be the total edge weight. Then")
    d.eq("E[cut(σ)] = {i:W}{sub:tot} (1 − {i:q}),", 4)
    d.p("where {i:q} = Σ{sub:i} {i:N}{sub:i}({i:N}{sub:i}−1) / ({i:n}({i:n}−1)) is the probability that two given duties fall in the same group.")
    d.p("{i:Proof:} For any pair {i:u} ≠ {i:v}, the probability that both fall in group {i:i} is ({i:N}{sub:i}/{i:n})·(({i:N}{sub:i}−1)/({i:n}−1)), so they are separated with probability 1 − Σ{sub:i} {i:N}{sub:i}({i:N}{sub:i}−1)/({i:n}({i:n}−1)). The result follows from linearity of expectation over edges. ∎")
    d.p("On all {N:NMulti} multi-agent projects, (4) matches the mean of {N:Draws} sampled random teams to within {N:CFErr}% (Appendix A), which also checks the sampler.")
    d.h2("From cut weight to communication")
    d.p("{bi:Assumption 1 (Locality):} Each unit of dependency weight that crosses agent boundaries causes, in expectation, between {i:a} and {i:b} inter-agent messages (0 < {i:a} ≤ {i:b}), and dependencies inside one agent cause none.", first=True)
    d.p("{bi:Proposition 2:} Under Assumption 1, the expected number of inter-agent messages {i:M}(π) satisfies {i:a}·cut(π) ≤ E[{i:M}(π)] ≤ {i:b}·cut(π). Hence, at equal {i:k}, the criterion’s team is expected to need fewer messages than a random team whenever {i:b}·cut(π{sub:k*}) < {i:a}·E[cut(σ)]. The proof follows from linearity of expectation. The assumption is strong and is not taken for granted: hypothesis H2 tests it directly by correlating cut weight with logged messages per agent pair.")
    d.figure(ROOT / "paper/figures_docx/fig_method.png",
             "The method on the DevBench project stocktrends. (a) Duty graph: each dot is a method (duty), and line width is dependency weight; colors show the three agents of the selected team, and red dashed lines are dependencies between agents. (b) MQ of the average-linkage team at every size; the best score selects k* = 3.")

    d.h1("Structural Study on DevBench")
    d.h2("Data and pre-set choices")
    d.p("DevBench {cite:li2024devbench}, also released as DevEval, provides {N:NProjects} software projects in Python, C++, Java and JavaScript, each with a product requirements document, a UML class diagram, an architecture design and executable tests. The study uses commit {N:DevBenchCommit}. All {N:NProjects} class diagrams parse, and the designs range from {N:DutyMin} to {N:DutyMax} duties. The weights are {i:w}{sub:in} = 1, {i:w}{sub:str} = 0.5, {i:w}{sub:weak} = 0.25 and {i:w}{sub:sig} = 0.5, with λ = 0 and {N:Draws} random teams per project (seed {N:Seed}). These values were fixed before any agent run, and no language model is called in this section. The analysis runs in Python {N:PythonVersion} with NumPy {N:NumpyVersion}.", first=True)
    d.h2("When to split")
    d.p(f"The criterion recommends a single agent for {{N:NSingle}} projects: {single_list} (duty counts in parentheses). For the remaining {{N:NMulti}} it recommends teams of {{N:KMin}} to {{N:KMax}} agents (Table I, which also compares each team with one agent per class, denoted GC): {{N:NMultiPython}} Python, {{N:NMultiCpp}} C++, {{N:NMultiJava}} Java and {{N:NMultiJS}} JavaScript projects. Whether the single-agent recommendations are {{i:correct}} is an empirical question that the agent study answers (H3).", first=True)

    # Table I spans both columns
    d.section_break(2)
    short = {"cpp": "C++", "java": "Java", "javascript": "JS", "python": "Py"}
    rows = []
    for p in sorted(multi, key=lambda p: (p["language"], p["project"])):
        x = p["duty"]
        rows.append([p["project"], short[p["language"]], str(x["n_classes"]), str(x["n"]), str(x["k_star"]),
                     "+".join(map(str, x["sizes"])), f'{100 * x["cut_reduction_vs_random"]:.0f}', f'{x["p_random"]:.4f}',
                     f'{x["criterion_mq_minus_gc_mq"]:+.2f}', f'{x["ari_vs_infomap"]:.2f}', f'{x["weight_grid"]["same_k"]}/81'])
    d.table("Projects for Which the Criterion Recommends a Team (k* > 1)",
            ["Project", "Lang.", "Classes", "Duties", "k*", "Group sizes", "Cut reduction (%)", "p", "ΔMQ vs. GC", "ARI vs. Infomap", "Stable k*"],
            rows, [1900, 560, 700, 640, 420, 1250, 1000, 760, 900, 900, 800], size=14,
            notes="Cut reduction: cross-agent dependency of the criterion’s team relative to the mean of 2,000 random teams with the same group sizes. p: one-sided permutation p-value. ΔMQ vs. GC: MQ of the criterion’s team minus MQ of one agent per class. ARI vs. Infomap: adjusted Rand index [{}] with the Infomap partition. Stable k*: weight settings (of 81) that give the same k*.".replace("[{}]", cite("hubert1985ari")))
    d.section_break(1)

    d.h2("Teams cut far less dependency than random teams")
    d.p("For all {N:NMulti} projects, the criterion’s team has {N:CutRedMin}–{N:CutRedMax}% less cross-agent dependency than random teams of equal sizes (median {N:CutRedMedian}%; all p ≤ {N:PMax}; Fig. 2). Any method that optimizes a cohesion score should achieve this, so it is treated as a sanity check rather than as evidence that the teams build better software. Performance is the subject of Section VI.", first=True)
    d.figure(ROOT / "paper/figures_docx/fig_cut.png",
             "Cross-agent dependency (cut) of the criterion’s team relative to the mean of 2,000 random teams with the same group sizes (random = 1). Lower is better.")
    d.h2("Teams group whole classes")
    d.p("In none of the {N:NProjects} projects does the criterion split a class across agents ({N:NSplitClass}/{N:NProjects}). The duty-level method therefore acts as a principled way of {i:grouping classes}. Its team scores higher MQ than one agent per class (condition GC) in {N:NBeatGC} of {N:NMulti} projects and coincides with it in {N:NEqGC}. A class-level graph without intra-class weights is too sparse: it recommends a team for only {N:NClassLevelMulti} projects.", first=True)
    d.h2("Relation to community detection")
    d.p("Infomap {cite:rosvall2008infomap} produces exactly the same team as the criterion in {N:NInfomapSame} of {N:NMulti} projects and a similar one (adjusted Rand index of at least 0.75) in {N:NInfomapClose}, and Louvain {cite:blondel2008louvain} chooses the same number of agents in {N:NLouvainSameK}. On design graphs, the {i:partition} is therefore largely determined by the design rather than by the clustering algorithm. What the criterion adds is an explicit, tunable choice of {i:k} that includes {i:k} = 1, which Infomap and Louvain do not offer. Condition G6 measures whether this matters for agents.", first=True)
    d.h2("Robustness")
    d.p("Changing λ ∈ {0, 0.05, 0.1, 0.2} changes {i:k}* in {N:NLambdaChange} projects. Scaling each of the four weights by 0.5, 1 or 1.5 (3{sup:4} = 81 settings) leaves {i:k}* unchanged in {N:WeightStableAll}% of settings on average ({N:WeightStableMulti}% for multi-agent projects, with a mean adjusted Rand index of {N:WeightARIMulti} against the default team). Fig. 3 shows representative MQ curves: most have one clear peak, and where a curve has a second peak (redis-cache), the weight grid shows lower stability.", first=True)
    d.figure(ROOT / "paper/figures_docx/fig_mq.png",
             "MQ of the average-linkage team at each size k for four representative projects; the dashed line marks the selected size k*.")

    d.h1("Agent Study (Pre-Registered)")
    d.h2("Hypotheses")
    d.p("All thresholds were fixed and recorded in a version-controlled pre-registration file before any agent run.", first=True)
    for t in [
        "{b:H1:} On projects with {i:k}* > 1, the criterion’s team (G7) passes more reference tests than a random team of equal sizes (G4) and than one agent per class (GC) at an equal token budget (paired Wilcoxon signed-rank test over tasks, Holm-corrected {cite:holm1979simple}, α = 0.05).",
        "{b:H2:} Across agent pairs, cross-agent dependency weight predicts the number of messages exchanged (Spearman ρ ≥ 0.3; this tests Assumption 1).",
        "{b:H3:} The split or no-split decision ({i:k}* = 1 versus {i:k}* > 1) agrees with the empirically better choice (best single agent versus best team) more often than chance.",
        "{b:H4:} Designs extracted by an LLM from the requirements document give a {i:k}* within one of the gold design’s in at least 70% of projects, and H1 still holds with extracted designs.",
    ]:
        d.p(t)
    d.h2("Protocol and conditions")
    d.p("Every condition uses the same model, decoding settings, prompt templates, orchestrator and token cap; only the division of work changes (Table II). Each agent receives the requirements document, the full domain model, the architecture design and the list of duties it owns, each with an identifier. Agents run in the dependency order of the classes they own, and an agent receives the code already written by the agents it depends on; each such hand-over is logged as one message together with its size in tokens. Agents mark every implemented duty with its identifier in a code comment, which gives a traceability score. A deterministic merge step assembles the files, and DevBench’s tests score the result in a sandbox from which the reference implementation has been removed.", first=True)
    d.table("Experimental Conditions",
            ["Condition", "Division of work"],
            [["G1", "Single agent, requirements only"], ["G2", "Single agent, requirements and design"],
             ["G3", "Team size and roles proposed by the LLM"], ["G4", "Random team, same group sizes as G7"],
             ["GC", "One agent per class"], ["G5", "Oracle size: best k on development projects"],
             ["G6", "Infomap partition of the same duty graph"], ["G7", "Criterion team (k*, π_k*)"]],
            [1000, 3800], size=15,
            notes="All conditions use the same model, prompts, orchestrator and token cap per run. The pilot runs G2, G4, GC, G6 and G7; the main study adds G1, G3 and G5. When k* = 1, G4 uses the group sizes of GC so that splitting can be compared with not splitting.")
    d.p("{bi:Settings:} The pilot uses " + AG["model_sentence"] + " at temperature 0, at most 8,000 output tokens per call, a cap of 200,000 tokens per run, three runs per condition with different run identifiers, and the gold design. The main study adds designs extracted from the requirements (H4) and a second model. Every prompt and response is stored with a content hash, so all agent tables can be rebuilt offline. " + AG["hardware"])
    d.p("{bi:Scorer validity:} Before scoring any agent, DevBench’s tests are run against DevBench’s own reference code in the sandbox and against empty code. Of the {N:NRefRan} Python projects that could be run, {N:NRefFull} pass every unit and acceptance test (" + ref_tab + "); a project is scored only if its reference code passes in full and empty code passes nothing. DevBench’s C++ and Java reference code does not build with current compilers (g++ 13, JDK 21), so these projects are scored inside DevBench’s own container image, where their scorer checks are run and reported with their results.")
    d.h2("Results")
    d.p(AG["verification"], first=True)
    d.p(AG["probe"].replace("(Table IV)", "(Table III)"))
    d.table("Single-Agent Model Probe Used to Choose the Pilot Model", ["Model", "Seq. diagram", "Project", "Tests", "Tokens"],
            AG["probe_rows"], [1500, 800, 1000, 700, 800], size=14,
            notes="Condition G2 only, run 0, gold design. The probe was run before any team comparison, with a decision rule fixed in advance.")
    if has_pilot:
        d.p(AG["pilot"].replace("Table V", "Table IV"))
        d.section_break(2)
        d.table("Pilot on DevBench’s Python Projects", ["Project", "Condition", "Agents", "Tests (mean ± SD)", "Runs", "Tokens (mean ± SD)", "Messages", "Note"],
                AG["pilot_rows"], [1200, 2000, 700, 1100, 900, 900, 900, 1600], size=14,
                notes="Mean ± standard deviation over three runs (run identifiers 0, 1, 2); Runs lists tests passed per run. Identical teams receive identical prompts and cached responses.")
        d.section_break(1)
        d.figure(ROOT / "paper/figures_docx/fig_pilot.png", "Pilot: tests passed (left) and tokens per run (right) for each condition.")
        if (ROOT / "paper/figures_docx/fig_teams.png").exists():
            d.figure(ROOT / "paper/figures_docx/fig_teams.png", caption="Run 0 on stocktrends. (a, b) Cohesion (diagonal) and coupling (off-diagonal) between agents, as in MQ, for the criterion team and a random team of the same sizes; the classes each agent owns are listed below. (c) Input and output tokens per agent in that run.")
    else:
        d.p(AG["pilot"])
    for t in AG["main_pending"]:
        d.p(t)

    d.h1("Discussion")
    d.h2("What the structural results do and do not show")
    d.p("They show that design graphs from a public benchmark have strong cohesive structure, that the criterion finds this structure deterministically and stably, and that it recommends a single agent for half of the projects. They do not show that the recommended teams build better software; only the agent study can show that.", first=True)
    if AG.get("discussion_pilot"):
        d.h2("What the pilot shows")
        d.p(AG["discussion_pilot"].replace("{bi:What the pilot shows:} ", ""), first=True)
    d.h2("Threats to validity")
    d.p("{i:Internal validity:} LLM outputs vary between calls, so every condition runs three times with identical prompts, and identical teams receive identical prompts and cached responses. {i:Construct validity:} correctness is measured with DevBench’s own tests and traceability with duty comments, which may undercount duties implemented without a comment. {i:External validity:} DevBench projects are small (at most {N:DutyMax} duties), cover four languages and use gold designs written together with the reference code; H4 repeats the main test with designs extracted from requirements, which a real team would have. {i:Conclusion validity:} DevBench yields only {N:NMulti} multi-agent tasks, below the roughly 36 that the power analysis requires for H1, so the main study will add tasks from benchmarks used in closely related work {cite:yang2026cocoder} and from requirement sets of the kind used by NOMAD {cite:giannouris2025nomad}. " + AG["threat_extra"], first=True)
    d.h2("Weights and contamination")
    d.p("Edge weights are set by hand. The 81-setting grid shows that {i:k}* is stable in most settings but not all, so both the default and the full grid are reported and nothing is tuned on test projects. DevBench is public and may appear in model training data; conditions are compared only with each other, which controls for memorization that affects all conditions equally.", first=True)

    d.h1("Conclusion and Future Work")
    d.p("Before choosing how to coordinate LLM agents, one must decide whether to split the work at all. This article formulated that decision as design-time team sizing, gave a deterministic criterion with a closed-form random baseline, and found on {N:NProjects} DevBench projects that it recommends a single agent for {N:NSingle} and compact teams of {N:KMin} to {N:KMax} agents for the rest, with far less cross-agent dependency than random teams of the same sizes. " + AG["conclusion"] + " Future work will test the criterion on larger, multi-language benchmarks and with designs that LLMs write from requirements, learn edge weights on development projects instead of setting them by hand, and extend the criterion to teams whose roles change during execution.", first=True)

    d.h1("Appendix A", numbered=False)
    d.h1("Reproducibility", numbered=False)
    d.p("Every number in Sections V and VI is generated by scripts/make_paper_assets.py from results/structural.json and results/reference_tests.json. The command bash reproduce.sh fetches DevBench at commit {N:DevBenchCommit}, runs the unit tests and regenerates all results, and two runs give byte-identical output. Agent runs store every prompt and response with its hash, so the agent tables can be rebuilt from the cache without calling any model. The pre-registration file and its version-control tag are part of the released code. Mermaid class diagrams are parsed with a tolerant parser; overloaded methods are merged into one duty, relations to classes that are only mentioned (library types) are ignored, and duplicate relation declarations count once.", first=True)
    rr = []
    for r in REFT:
        name = r["project"].split("/")[1]
        if "status" in r:
            rr.append([name, "skipped here", "5/13 on Colab (unit + acceptance)"])
            continue
        cells = []
        for k in ("unit_test", "acceptance_test"):
            t = r.get(k)
            cells.append("–" if t is None else f"{t['passed']}/{t['passed'] + t['failed'] + t['errors']}")
        rr.append([name, *cells])
    d.table("DevBench Reference Code Tested Against Its Own Tests (Python)", ["Project", "Unit tests", "Acceptance tests"],
            rr, [2300, 1200, 1300], size=15,
            notes="Fresh virtual environment per project; coverage flags removed. TextCNN needs a model download that this build environment blocks; on Google Colab its reference code passes 5 of 13 tests, so it is excluded from the pilot.")

    d.h1("Data and Code Availability", numbered=False)
    d.p("All code, the pre-registration file, prompts, cached model responses, generated tables and figures are available at https://github.com/wijayasekarageyashmithadilshan-dot/objectgraph-agent. Running bash reproduce.sh regenerates every structural result, and the agent tables can be rebuilt offline from the cached responses. DevBench is publicly available and is used at commit {N:DevBenchCommit}.", first=True)
    d.h1("Ethics Statement", numbered=False)
    d.p("This study did not involve human participants, animals or personal data. All generated code was executed only in isolated sandboxes.", first=True)
    d.h1("Conflict of Interest", numbered=False)
    d.p("The authors declare no competing interests.", first=True)
    d.h1("Acknowledgment", numbered=False)
    d.p("The authors thank Achala Aponso, Informatics Institute of Technology, for his feedback on drafts of this article. Claude (Anthropic) served as an AI assistant during this work in November 2026: it helped to write the experiment and analysis code, the pre-registration and figure scripts and early versions of the text, and it helped to search and check the literature. The authors designed the study, made every pre-registration and analysis decision, checked all code, results and references, revised the text, and are fully responsible for the article.", first=True)
    return {}


def build(template: Path, out: Path) -> None:
    global NUMS
    NUMS = {k: v.replace("{,}", ",") for k, v in re.findall(r"\\newcommand\{\\(\w+)\}\{(.*?)\\xspace\}",
                                                          (ROOT / "paper/generated/numbers.tex").read_text())}
    S = json.loads((ROOT / "results/structural.json").read_text())
    REFT = json.loads((ROOT / "results/reference_tests.json").read_text())
    ORDER.clear()

    tmp = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(template) as z:
        z.extractall(tmp)
    W = tmp / "word"
    xml = (W / "document.xml").read_text(encoding="utf-8")
    head = xml[: xml.index("<w:body>") + len("<w:body>")]
    tail_sect = re.search(r"<w:sectPr\b(?:(?!<w:sectPr\b).)*</w:sectPr>\s*</w:body>", xml, re.S).group(0)
    paras = re.findall(r"<w:p[ >].*?</w:p>", xml[xml.index("<w:body>"):], re.S)

    d = Doc()
    build_content(d, S, REFT)

    # ---- front matter (template paragraphs 0-11 rewritten)
    front = []
    front.append(paras[0])   # date of publication line (filled by IEEE)
    front.append(paras[1].replace("ACCESS.2024.Doi Number", "ACCESS.2026.Doi Number") if "Doi Number" in paras[1] else paras[1])
    front.append('<w:p><w:pPr><w:pStyle w:val="PaperTitle"/></w:pPr>' + runs(
        "When Should a Software Task Be Split Across Large Language Model Agents? Sizing Multi-Agent Teams from Domain Models") + "</w:p>")
    front.append('<w:p><w:pPr><w:pStyle w:val="AU"/><w:spacing w:after="0"/></w:pPr>' + runs(
        "Yashmitha Dilshan{sup:1} and Maninda Edirisooriya{sup:1}") + "</w:p>")
    front.append('<w:p><w:pPr><w:pStyle w:val="PI"/><w:ind w:firstLine="0"/></w:pPr>' + runs(
        "{sup:1}School of Computing, University of Westminster, 309 Regent Street, London W1B 2HW, U.K., in collaboration with the Informatics Institute of Technology, Colombo, Sri Lanka (e-mail: yashmitha.20211432@iit.ac.lk; maninda.e@iit.ac.lk)") + "</w:p>")
    front.append('<w:p><w:pPr><w:pStyle w:val="PI"/><w:spacing w:before="100" w:after="100"/><w:ind w:right="1598" w:firstLine="0"/></w:pPr>' + runs(
        "Corresponding author: Y. Dilshan (e-mail: yashmitha.20211432@iit.ac.lk; ORCID: 0009-0002-2591-6018).") + "</w:p>")
    front.append('<w:p><w:pPr><w:pStyle w:val="FootnoteText"/><w:spacing w:after="540"/><w:ind w:firstLine="0"/></w:pPr>' + runs(
        "This work did not receive any specific funding.") + "</w:p>")
    abstract = ("Multi-agent systems built on large language models (LLMs) are increasingly used to develop software, yet team size and the division of work are usually fixed by hand, proposed by a model, or found by costly search, and recent controlled studies show that adding agents can lower accuracy. This article asks a prior question: given the design of the software to be built, should the work be split at all, and if so, into how many agents? A Unified Modeling Language (UML) class diagram is converted into a weighted graph of duties, every candidate team is built with average-linkage clustering, and the team size that maximizes modularization quality minus a per-agent cost is selected. The decision is made before any code exists, is deterministic, and may recommend a single agent. The expected dependency of equal-size random teams is derived in closed form. On all {N:NProjects} projects of the four-language DevBench benchmark, the criterion recommends one agent for {N:NSingle} projects and teams of {N:KMin} to {N:KMax} agents for the other {N:NMulti}. For those teams, cross-agent dependency is {N:CutRedMin} to {N:CutRedMax} percent lower than in {N:Draws} random teams of equal sizes, and the recommended size is unchanged in {N:WeightStableAll} percent of 81 edge-weight settings. " + json.loads((ROOT / "paper/generated/agent.json").read_text())["abstract"] + " All code, prompts and cached responses are public.")
    front.append('<w:p><w:pPr><w:pStyle w:val="Abstract"/></w:pPr><w:r><w:rPr><w:rStyle w:val="H5CharChar"/></w:rPr><w:t>ABSTRACT</w:t></w:r><w:r><w:t xml:space="preserve"> </w:t></w:r>' + runs(abstract) + "</w:p>")
    front.append('<w:p><w:pPr><w:pStyle w:val="IT"/></w:pPr><w:r><w:rPr><w:rStyle w:val="H5CharChar"/></w:rPr><w:t>INDEX TERMS</w:t></w:r><w:r><w:t xml:space="preserve"> </w:t></w:r>' + runs(
        "Graph partitioning, large language models, multi-agent systems, software design, software modularization") + "</w:p>")
    # end of the single-column title section: logo header/first footer on page 1, running header/footer after
    title_sect = paras[11].replace('<w:headerReference w:type="default" r:id="rId9"/><w:footerReference w:type="default" r:id="rId10"/>',
        '<w:headerReference w:type="default" r:id="rId12"/><w:footerReference w:type="default" r:id="rId13"/>'
        '<w:headerReference w:type="first" r:id="rId9"/><w:footerReference w:type="first" r:id="rId10"/>')
    title_sect = title_sect.replace('<w:docGrid w:linePitch="360"/></w:sectPr>', '<w:titlePg/><w:docGrid w:linePitch="360"/></w:sectPr>')
    assert 'w:type="first"' in title_sect and "<w:titlePg/>" in title_sect
    front.append(title_sect)

    # ---- body: first section break carries the running header/footer
    body = d.body

    # references + biographies
    refs = [d_ for d_ in []]
    ref_xml = [para("H1", "REFERENCES")]
    for k in ORDER:
        ref_xml.append(para("References", REFS[k]))
    unused = [k for k in REFS if k not in ORDER]
    if unused:
        raise SystemExit(f"references never cited: {unused}")
    bios = [
        '<w:p><w:pPr><w:pStyle w:val="AUBios"/><w:spacing w:before="240"/></w:pPr>' +
        '<w:r><w:rPr><w:rStyle w:val="AUBiosbd"/></w:rPr><w:t>YASHMITHA DILSHAN</w:t></w:r>' + runs(
            " is currently pursuing the B.Sc. degree in computer science at the Informatics Institute of Technology, Colombo, Sri Lanka, in collaboration with the University of Westminster, London, U.K., with expected graduation in 2027. His research interests include large language model agents, multi-agent systems for software engineering, human–computer interaction, and the reproducible evaluation of machine learning.") + "</w:p>",
        '<w:p><w:pPr><w:pStyle w:val="AUBios"/><w:spacing w:before="240"/></w:pPr>' +
        '<w:r><w:rPr><w:rStyle w:val="AUBiosbd"/></w:rPr><w:t>MANINDA EDIRISOORIYA</w:t></w:r>' + runs(
            " received the B.Eng. (Hons.) degree in computer science and engineering from the University of Moratuwa, Sri Lanka. He is a Senior Lecturer (Grade II) in the School of Computing at the Informatics Institute of Technology, Colombo, Sri Lanka. His research interests include artificial intelligence, machine learning, and deep learning.") + "</w:p>",
    ]
    final_sect = re.sub(r"<w:(header|footer)Reference[^>]*/>", "", tail_sect.replace("</w:body>", ""))
    newxml = head + "".join(front) + "".join(body) + "".join(ref_xml) + "".join(bios) + final_sect + "</w:body></w:document>"
    (W / "document.xml").write_text(newxml, encoding="utf-8")

    # numbering: per-section H2 restarts
    num = (W / "numbering.xml").read_text(encoding="utf-8")
    last = num.rindex("</w:num>") + len("</w:num>")          # <w:num> must follow the last existing <w:num>
    num = num[:last] + "".join(d.new_nums) + num[last:]
    (W / "numbering.xml").write_text(num, encoding="utf-8")

    for f in W.glob("footer*.xml"):
        f.write_text(f.read_text(encoding="utf-8").replace("VOLUME XX, 2017", "VOLUME XX, 2026"), encoding="utf-8")
    # running header text and page-number field in the body footer
    hdr = (W / "header2.xml").read_text(encoding="utf-8")
    hdr = hdr.replace("<w:t>Author Name</w:t>", "<w:t>Y. Dilshan and M. Edirisooriya</w:t>")
    hdr = hdr.replace("<w:t>Preparation of Papers for IEEE Access (February 2017)</w:t>",
                      "<w:t>Sizing LLM Agent Teams</w:t>")
    (W / "header2.xml").write_text(hdr, encoding="utf-8")
    ftr = (W / "footer2.xml").read_text(encoding="utf-8")
    ftr = ftr.replace("<w:t>2</w:t>", '</w:r><w:fldSimple w:instr=" PAGE "><w:r><w:t>2</w:t></w:r></w:fldSimple><w:r>', 1)
    (W / "footer2.xml").write_text(ftr, encoding="utf-8")

    # images
    rels = (W / "_rels/document.xml.rels").read_text(encoding="utf-8")
    add = ""
    for rid, png in d.images:
        name = f"objgraph_{png.name}"
        shutil.copy(png, W / "media" / name)
        add += f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{name}"/>'
    (W / "_rels/document.xml.rels").write_text(rels.replace("</Relationships>", add + "</Relationships>"), encoding="utf-8")

    # core properties
    core = tmp / "docProps/core.xml"
    if core.exists():
        c = core.read_text(encoding="utf-8")
        c = re.sub(r"<dc:title>.*?</dc:title>", "<dc:title>When Should a Software Task Be Split Across LLM Agents?</dc:title>", c)
        c = re.sub(r"<dc:creator>.*?</dc:creator>", "<dc:creator>Yashmitha Dilshan</dc:creator>", c)
        core.write_text(c, encoding="utf-8")

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    subprocess.run(["zip", "-XrDyq", str(out.resolve()), "."], cwd=tmp, check=True)
    shutil.rmtree(tmp)
    print(f"wrote {out} with {len(ORDER)} references, {d.fig} figures, {d.tab} tables")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--out", default=str(ROOT / "paper/ObjectGraph-Agent_IEEE-Access.docx"))
    a = ap.parse_args()
    build(Path(a.template), Path(a.out))
