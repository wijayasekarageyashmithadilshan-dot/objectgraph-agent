"""Draw every step of the method and bundle the pictures into one HTML report.

Step 1 domain model -> Step 2 duty graph -> Step 3 cohesion/coupling and team
size -> Step 4 agent task allocation -> Step 5 agent run -> Step 6 test score.
"""
from __future__ import annotations

import base64
import html
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402
import numpy as np  # noqa: E402
from scipy.cluster.hierarchy import dendrogram  # noqa: E402

from .criterion import hierarchy  # noqa: E402

AGENT_COLORS = ["#1D9E75", "#7F77DD", "#D85A30", "#378ADD", "#BA7517", "#D4537E", "#639922", "#888780"]
plt.rcParams.update({"font.size": 8})


def _png(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def fig_domain_model(diagram) -> str:
    G = nx.DiGraph()
    declared = [c for c, k in diagram.classes.items() if k.methods or k.attributes or k.stereotypes]
    for c in declared:
        G.add_node(c, n=len(diagram.classes[c].method_names()))
    styles = {}
    for r in diagram.relations:
        if r.a in G and r.b in G and r.a != r.b:
            G.add_edge(r.a, r.b)
            styles[(r.a, r.b)] = "solid" if r.strong else "dashed"
    pos = nx.spring_layout(G, seed=1, k=1.6) if len(G) > 1 else {declared[0]: (0, 0)}
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    for (u, v), st in styles.items():
        nx.draw_networkx_edges(G, pos, edgelist=[(u, v)], style=st, ax=ax, arrows=True,
                               arrowstyle="-|>", arrowsize=10, edge_color="#5F5E5A", node_size=2600)
    for c in G.nodes:
        x, y = pos[c]
        ax.text(x, y, f"{c}\n{G.nodes[c]['n']} methods", ha="center", va="center", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.5", fc="#EEEDFE", ec="#534AB7", lw=0.8))
    ax.set_title("Step 1 - domain model (classes; solid = inherit/compose, dashed = uses)", fontsize=9)
    ax.axis("off")
    ax.margins(0.25)
    return _png(fig)


def duty_layout(graph) -> dict:
    G = nx.from_numpy_array(graph.W)
    return nx.spring_layout(G, weight="weight", seed=7, k=1.2 / max(1, np.sqrt(graph.n)))


def _short(d: str) -> str:
    c, m = d.split(".", 1)
    return m if m != "<state>" else f"{c}.state"


def fig_duty_graph(graph, pos) -> str:
    classes = sorted(set(graph.owner))
    cmap = {c: plt.cm.tab20(i % 20) for i, c in enumerate(classes)}
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    n = graph.n
    for i in range(n):
        for j in range(i + 1, n):
            if graph.W[i, j] > 0:
                ax.plot(*zip(pos[i], pos[j]), color="#B4B2A9", lw=0.4 + 2.2 * graph.W[i, j], zorder=1)
    for i in range(n):
        ax.scatter(*pos[i], s=140, color=cmap[graph.owner[i]], edgecolor="white", zorder=2)
        if n <= 40:
            ax.annotate(_short(graph.duties[i]), pos[i], fontsize=6, ha="center", va="bottom",
                        xytext=(0, 5), textcoords="offset points")
    for c in classes:
        ax.scatter([], [], color=cmap[c], label=c)
    ax.legend(fontsize=6.5, frameon=False, loc="center left", bbox_to_anchor=(1, 0.5), title="class")
    ax.set_title(f"Step 2 - duty graph: {n} duties, line width = dependency weight", fontsize=9)
    ax.axis("off")
    return _png(fig)


def fig_cohesion(graph, curve: dict, k_star: int) -> str:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.2), gridspec_kw={"width_ratios": [1.4, 1]})
    if graph.n > 1:
        Z = hierarchy(graph.W)
        dendrogram(Z, labels=[_short(d) for d in graph.duties], ax=a1, leaf_font_size=6, leaf_rotation=90,
                   color_threshold=Z[-k_star, 2] if k_star > 1 else 0, above_threshold_color="#888780")
        if k_star > 1:
            a1.axhline((Z[-k_star, 2] + Z[-k_star + 1, 2]) / 2, color="#D85A30", ls="--", lw=1)
    a1.set_title(f"Step 3a - merge tree (cut gives {k_star} agent(s))", fontsize=9)
    a1.set_ylabel("distance = 1 - weight")
    ks = sorted(int(k) for k in curve)
    a2.plot(ks, [curve[k] if k in curve else curve[str(k)] for k in ks], color="#3B6D11", marker="o", ms=3)
    a2.axvline(k_star, color="#D85A30", ls="--", lw=1)
    a2.set_xlabel("number of agents k")
    a2.set_ylabel("MQ = cohesion - coupling")
    a2.set_title(f"Step 3b - score every team size: k* = {k_star}", fontsize=9)
    fig.tight_layout()
    return _png(fig)


def fig_team(graph, labels, pos, team) -> str:
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    n = graph.n
    for i in range(n):
        for j in range(i + 1, n):
            if graph.W[i, j] > 0:
                cut = labels[i] != labels[j]
                ax.plot(*zip(pos[i], pos[j]), color="#E24B4A" if cut else "#D3D1C7",
                        ls="--" if cut else "-", lw=0.4 + 2 * graph.W[i, j], zorder=1)
    groups = sorted(set(labels.tolist()), key=lambda g: int(np.flatnonzero(labels == g)[0]))
    for gi, g in enumerate(groups):
        idx = np.flatnonzero(labels == g)
        ax.scatter([pos[i][0] for i in idx], [pos[i][1] for i in idx], s=150,
                   color=AGENT_COLORS[gi % len(AGENT_COLORS)], edgecolor="white", zorder=2,
                   label=f"{team.agents[gi].agent_id}: {', '.join(team.agents[gi].classes)}")
    ax.legend(fontsize=6.5, frameon=False, loc="center left", bbox_to_anchor=(1, 0.5))
    ax.set_title(f"Step 4 - team of {team.k}: red dashed = dependencies between agents (cut = {team.cut})",
                 fontsize=9)
    ax.axis("off")
    return _png(fig)


def fig_cc_matrix(graph, labels, team) -> str:
    groups = sorted(set(labels.tolist()), key=lambda g: int(np.flatnonzero(labels == g)[0]))
    k = len(groups)
    M = np.zeros((k, k))
    for a, ga in enumerate(groups):
        ia = labels == ga
        for b, gb in enumerate(groups):
            ib = labels == gb
            if a == b:
                M[a, b] = graph.W[np.ix_(ia, ia)].sum() / (ia.sum() ** 2)
            else:
                M[a, b] = graph.W[np.ix_(ia, ib)].sum() / (ia.sum() * ib.sum())
    fig, ax = plt.subplots(figsize=(1.2 + 0.7 * k, 1.0 + 0.6 * k))
    im = ax.imshow(M, cmap="Greens", vmin=0, vmax=max(M.max(), 1e-9))
    names = [a.agent_id for a in team.agents]
    ax.set_xticks(range(k), names, rotation=45, fontsize=7)
    ax.set_yticks(range(k), names, fontsize=7)
    for a in range(k):
        for b in range(k):
            ax.text(b, a, f"{M[a, b]:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if M[a, b] > 0.6 * M.max() else "black")
    ax.set_title("Step 3c - diagonal = cohesion,\noff-diagonal = coupling", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046)
    return _png(fig)


def fig_run(team, run: dict) -> str:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 2.8), gridspec_kw={"width_ratios": [1.5, 1]})
    order = team.order
    xs = {a: i for i, a in enumerate(order)}
    for a in order:
        gi = [x.agent_id for x in team.agents].index(a)
        a1.scatter(xs[a], 0, s=900, color=AGENT_COLORS[gi % len(AGENT_COLORS)], zorder=2)
        a1.text(xs[a], 0, a.replace("agent_", "A"), ha="center", va="center", color="white", fontsize=8)
    for m in run.get("messages", []):
        x0, x1 = xs[m["from"]], xs[m["to"]]
        a1.annotate("", xy=(x1, 0.08), xytext=(x0, 0.08),
                    arrowprops=dict(arrowstyle="-|>", color="#5F5E5A", connectionstyle="arc3,rad=-0.4"))
        a1.text((x0 + x1) / 2, 0.32 + 0.05 * abs(x1 - x0), f"{m['tokens']} tok", ha="center", fontsize=6.5)
    a1.set_xlim(-0.6, len(order) - 0.4)
    a1.set_ylim(-0.4, 0.8)
    a1.axis("off")
    a1.set_title(f"Step 5a - run order and hand-overs ({len(run.get('messages', []))} messages)", fontsize=9)
    by_tag = run.get("usage", {}).get("by_tag", {})
    tags = [t for t in order if t in by_tag]
    a2.bar(tags, [by_tag[t]["input_tokens"] for t in tags], color="#B4B2A9", label="input")
    a2.bar(tags, [by_tag[t]["output_tokens"] for t in tags],
           bottom=[by_tag[t]["input_tokens"] for t in tags], color="#3B6D11", label="output")
    a2.set_title("Step 5b - tokens per agent", fontsize=9)
    a2.legend(fontsize=6.5, frameon=False)
    a2.tick_params(labelsize=7)
    fig.tight_layout()
    return _png(fig)


def team_table(team) -> str:
    rows = []
    for a in team.agents:
        rows.append("<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            a.agent_id, html.escape(", ".join(a.classes)), len(a.duties),
            html.escape(", ".join(a.depends_on) or "none"),
            html.escape(", ".join(f"{k}: {v}" for k, v in a.cut_to.items()) or "none")))
    return ("<table><tr><th>Agent</th><th>Classes owned</th><th>Duties</th><th>Depends on</th>"
            "<th>Cut weight to</th></tr>" + "".join(rows) + "</table>")


def duty_lists(team) -> str:
    out = []
    for a in team.agents:
        items = "".join(f"<code>{html.escape(d)}</code> " for d in a.duties)
        out.append(f"<p><b>{a.agent_id}</b>: {items}</p>")
    return "".join(out)


def build_html(title: str, sections: list[tuple[str, str, list[str], str]]) -> str:
    """sections: (heading, explanation, [png_b64...], extra_html)."""
    css = ("body{font-family:system-ui,sans-serif;max-width:980px;margin:24px auto;padding:0 16px;"
           "color:#2C2C2A;line-height:1.55}h1{font-size:22px;font-weight:500}h2{font-size:17px;"
           "font-weight:500;margin-top:32px;border-top:1px solid #D3D1C7;padding-top:16px}"
           "img{max-width:100%}table{border-collapse:collapse;font-size:13px;margin:8px 0}"
           "td,th{border:1px solid #D3D1C7;padding:4px 8px;text-align:left}code{font-size:12px;"
           "background:#F1EFE8;padding:1px 4px;border-radius:4px}.box{background:#F1EFE8;padding:10px 14px;"
           "border-radius:8px;font-size:14px}")
    body = [f"<h1>{html.escape(title)}</h1>"]
    for head, expl, imgs, extra in sections:
        body.append(f"<h2>{html.escape(head)}</h2><p>{expl}</p>")
        body += [f'<img src="data:image/png;base64,{b}">' for b in imgs]
        body.append(extra)
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title>" \
           f"<style>{css}</style></head><body>{''.join(body)}</body></html>"
