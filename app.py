import streamlit as st
import json
import networkx as nx
import plotly.graph_objects as go
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import os

st.set_page_config(layout="wide")
st.title("Step-based Causality Tree Viewer")

DATA_FILE = "semantic_tree.json"
if not os.path.exists(DATA_FILE):
    st.error(f"Missing '{DATA_FILE}'. Please add it to the app root directory.")
    st.stop()

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

G_full = nx.DiGraph()
node_attrs = {}
for node in data["nodes"]:
    node_id = node["id"]
    G_full.add_node(node_id)
    node_attrs[node_id] = {
        "label": node.get("label", node_id),
        "step": node.get("step", 1),
        "count": node.get("count", 1),
        "cluster": node.get("cluster", ""),
    }
nx.set_node_attributes(G_full, node_attrs)

for edge in data["edges"]:
    G_full.add_edge(edge["source"], edge["target"])

max_step = max(attr.get('step', 1) for attr in node_attrs.values())
min_step = min(attr.get('step', 1) for attr in node_attrs.values())
unique_clusters = sorted(set(attr["cluster"] for attr in node_attrs.values()))

color_map = {
    c: mcolors.to_hex(cm.tab20(i / max(1, len(unique_clusters) - 1)))
    for i, c in enumerate(unique_clusters)
}

def build_figure(up_to_step):
    G = G_full.copy()
    nodes_to_keep = [n for n in G.nodes if G.nodes[n]["step"] <= up_to_step]
    G = G.subgraph(nodes_to_keep).copy()

    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
    except Exception as e:
        st.warning(
            "Graphviz layout could not be computed. This may be because Graphviz or pygraphviz is not installed on the server. "
            "Falling back to spring_layout (visual result may differ)."
        )
        pos = nx.spring_layout(G, seed=42)

    edge_x, edge_y = [], []
    for src, tgt in G.edges():
        x0, y0 = pos[src]
        x1, y1 = pos[tgt]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    node_x, node_y, node_text, node_size, node_color = [], [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        attr = G.nodes[node]
        label = attr.get("label", node)
        step = attr.get("step", 1)
        count = attr.get("count", 1)
        cluster = attr.get("cluster", 0)
        node_text.append(f"<b>{label}</b><br>Step: {step}<br>Count: {count}<br>Cluster: {cluster}")
        node_size.append(8 + 2 * count)
        node_color.append(color_map.get(cluster, "#cccccc"))

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode='markers',
        hovertext=node_text, hoverinfo='text',
        marker=dict(size=node_size, color=node_color, line=dict(width=1, color='black'))
    )

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode='lines',
        line=dict(width=1, color='gray'), hoverinfo='none'
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=f"Step {up_to_step} Causality Tree",
            title_x=0.5,
            showlegend=False,
            hovermode='closest',
            dragmode='pan',
            margin=dict(t=60, l=20, r=20, b=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=800,
        )
    )
    return fig

step = st.slider("Select Step", min_value=min_step, max_value=max_step, value=min_step)
fig = build_figure(step)
st.plotly_chart(fig, use_container_width=True)
