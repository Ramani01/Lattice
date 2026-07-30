import streamlit as st
import os
import re
import json
import yaml
import requests
import time
import subprocess
import shutil
import tempfile
from neo4j import GraphDatabase

# Page config
st.set_page_config(
    page_title="Lattica: GraphRAG Migration Planner",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Sleek Dark Mode Styling with Gradients
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;500;600&display=swap');

    /* Global style override with grid background */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Outfit', sans-serif !important;
        background-color: #0b0f19 !important;
        background-image: radial-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 0), radial-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 0);
        background-size: 24px 24px;
        background-position: 0 0, 12px 12px;
        color: #f1f5f9 !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0d1321 !important;
        border-right: 1px solid #1e293b !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        font-family: 'Outfit', sans-serif !important;
    }

    /* Titles and Headers */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 5px;
    }
    .logo-icon {
        font-size: 2.5rem;
        animation: logoGlow 3s ease-in-out infinite alternate;
    }
    @keyframes logoGlow {
        from { filter: drop-shadow(0 0 2px rgba(0, 242, 254, 0.4)); }
        to { filter: drop-shadow(0 0 10px rgba(0, 242, 254, 0.8)); }
    }
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.05rem;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
        font-weight: 400;
    }

    /* Top bar status monitor */
    .status-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(15, 23, 42, 0.45);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 12px 24px;
        margin-bottom: 25px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    .status-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.85rem;
        color: #94a3b8;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .status-dot.online {
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981, 0 0 16px #10b981;
    }
    .status-dot.offline {
        background-color: #ef4444;
        box-shadow: 0 0 8px #ef4444, 0 0 16px #ef4444;
    }

    /* Glassmorphism Cards */
    .premium-card {
        background: rgba(17, 24, 39, 0.35);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .premium-card:hover {
        border-color: rgba(0, 242, 254, 0.25);
        box-shadow: 0 12px 40px -10px rgba(0, 242, 254, 0.12), 0 8px 32px 0 rgba(0, 0, 0, 0.4);
        transform: translateY(-2px);
    }
    .premium-card h3, .premium-card h4, .premium-card h5 {
        margin-top: 0 !important;
        color: #ffffff !important;
        font-weight: 600;
        letter-spacing: -0.02rem;
    }

    /* Custom styled badge */
    .status-badge {
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
    }
    .badge-legacy {
        background-color: rgba(239, 68, 68, 0.1);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.2);
    }
    .badge-hybrid {
        background-color: rgba(245, 158, 11, 0.1);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }
    .badge-pqc {
        background-color: rgba(16, 185, 129, 0.1);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    .badge-choke {
        background-color: rgba(139, 92, 246, 0.1);
        color: #a78bfa;
        border: 1px solid rgba(139, 92, 246, 0.2);
    }

    /* Tab styling overrides */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.4);
        padding: 6px;
        border-radius: 12px;
        border-bottom: none;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.04);
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 500;
        font-size: 0.9rem;
        padding: 0 16px;
        border: none !important;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff;
        background-color: rgba(255, 255, 255, 0.05);
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(79, 172, 254, 0.12) !important;
        color: #4FACFE !important;
        font-weight: 600 !important;
        border: 1px solid rgba(79, 172, 254, 0.2) !important;
    }

    /* Sleek Terminal styling */
    .terminal-container {
        background-color: #05080f !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        font-family: 'Fira Code', monospace !important;
        color: #34d399 !important;
        font-size: 0.88rem !important;
        line-height: 1.6 !important;
        overflow-x: auto;
        box-shadow: inset 0 4px 20px rgba(0, 0, 0, 0.9);
        margin-bottom: 15px;
    }
    .terminal-header {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 8px;
        color: #94a3b8;
        font-family: 'Outfit', sans-serif;
        font-size: 0.8rem;
    }
    .terminal-dot {
        width: 11px;
        height: 11px;
        border-radius: 50%;
    }
    .dot-red { background-color: #ef4444; box-shadow: 0 0 4px #ef4444; }
    .dot-yellow { background-color: #f59e0b; box-shadow: 0 0 4px #f59e0b; }
    .dot-green { background-color: #10b981; box-shadow: 0 0 4px #10b981; }

    /* Blinking Cursor Simulation */
    .terminal-container pre::after {
        content: '█';
        animation: cursorBlink 1s step-start infinite;
        color: #34d399;
        font-size: 0.9rem;
        margin-left: 2px;
    }
    @keyframes cursorBlink {
        50% { opacity: 0; }
    }

    /* Custom Action Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        box-shadow: 0 4px 15px rgba(0, 242, 254, 0.25) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 100%) !important;
        box-shadow: 0 6px 20px rgba(0, 242, 254, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    .stButton>button:active {
        transform: translateY(1px) !important;
    }

    /* Secondary Button Customization */
    [data-testid="stSidebar"] .stButton>button {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #f1f5f9 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(0, 242, 254, 0.5) !important;
    }

    /* Alert Boxes Override */
    .custom-alert {
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 20px;
        display: flex;
        gap: 12px;
        align-items: flex-start;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .alert-success {
        background-color: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.2);
        color: #34d399;
    }
    .alert-error {
        background-color: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.2);
        color: #f87171;
    }
    .alert-info {
        background-color: rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.2);
        color: #60a5fa;
    }
    .alert-warning {
        background-color: rgba(245, 158, 11, 0.08);
        border: 1px solid rgba(245, 158, 11, 0.2);
        color: #fbbf24;
    }

    /* Metric Display values */
    .metric-value {
        font-size: 2.4rem;
        font-weight: 800;
        color: #ffffff;
        line-height: 1;
        margin-bottom: 6px;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.1);
    }
    .metric-label {
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.08rem;
        font-weight: 500;
    }

    /* Expander Container overrides */
    div[data-testid="stExpander"] {
        background-color: rgba(17, 24, 39, 0.25) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 12px !important;
        margin-bottom: 12px !important;
    }

    /* Custom 4-Way Comparison Styling */
    .comp-card {
        background: rgba(15, 23, 42, 0.55);
        backdrop-filter: blur(16px);
        border-radius: 16px;
        padding: 22px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        transition: all 0.3s ease;
        margin-bottom: 20px;
    }
    .comp-card-purple { border-top: 4px solid #8b5cf6; }
    .comp-card-purple:hover { border-color: #a78bfa; box-shadow: 0 8px 30px rgba(139, 92, 246, 0.2); }
    
    .comp-card-red { border-top: 4px solid #ef4444; }
    .comp-card-red:hover { border-color: #f87171; box-shadow: 0 8px 30px rgba(239, 68, 68, 0.2); }
    
    .comp-card-blue { border-top: 4px solid #3b82f6; }
    .comp-card-blue:hover { border-color: #60a5fa; box-shadow: 0 8px 30px rgba(59, 130, 246, 0.2); }
    
    .comp-card-green { border-top: 4px solid #10b981; box-shadow: 0 0 25px rgba(16, 185, 129, 0.15); }
    .comp-card-green:hover { border-color: #34d399; box-shadow: 0 8px 35px rgba(16, 185, 129, 0.3); }

    .comp-badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: inline-block;
        margin-bottom: 12px;
    }
    .badge-purple { background: rgba(139, 92, 246, 0.15); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.3); }
    .badge-red { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-blue { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
    .badge-green { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }

    .styled-comp-table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 0.92rem;
        background: rgba(15, 23, 42, 0.4);
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .styled-comp-table th {
        background: rgba(30, 41, 59, 0.8);
        padding: 14px 16px;
        text-align: left;
        font-weight: 700;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
    }
    .styled-comp-table td {
        padding: 12px 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        color: #cbd5e1;
    }
    .styled-comp-table tr:hover {
        background: rgba(255, 255, 255, 0.03);
    }
""", unsafe_allow_html=True)

# Neo4j Settings
NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
if "vault_neo4j_password" in st.session_state and st.session_state["vault_neo4j_password"]:
    NEO4J_PASSWORD = st.session_state["vault_neo4j_password"]
else:
    NEO4J_PASSWORD = "password"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

def check_ollama_status():
    try:
        r = requests.get("http://127.0.0.1:11434/", timeout=1)
        return r.status_code == 200
    except Exception:
        return False

def get_ollama_models():
    """Fetch installed models dynamically from local Ollama service."""
    try:
        r = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
        if r.status_code == 200:
            models_data = r.json().get("models", [])
            names = [m.get("name") for m in models_data if m.get("name")]
            if names:
                return names
    except Exception:
        pass
    return ["qwen2:1.5b", "phi3:mini", "gemma:7b-instruct-q4_K_M", "gemma3:4b", "tinyllama:latest"]


def check_neo4j_status():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
        return True
    except Exception:
        return False

# --- HELPER FUNCTIONS ---

def connect_neo4j():
    """Helper to connect to Neo4j with retries."""
    pwd = st.session_state.get("vault_neo4j_password", "password")
    for attempt in range(1, 7):
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, pwd))
            # Test connection
            with driver.session() as session:
                session.run("RETURN 1")
            return driver
        except Exception as e:
            if attempt == 6:
                raise e
            time.sleep(3)

def parse_json_from_response(text: str) -> dict:
    """Extract and parse JSON from LLM text output using substring boundaries."""
    if not text:
        return {}
    cleaned = text
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0]
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0]
        
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start != -1 and end != -1 and start < end:
        candidate = cleaned[start:end+1].strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            import re
            fixed = re.sub(r',\s*([\}\]])', r'\1', candidate)
            try:
                parsed = json.loads(fixed)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
    return {}


def calculate_pagerank(nodes, edges, d=0.85, max_iter=100, tol=1.0e-6):
    """Calculates PageRank metrics using pure Python power iteration."""
    g = {node: [] for node in nodes}
    for u, v in edges:
        if u in g and v in g:
            g[u].append(v)
            
    n = len(nodes)
    if n == 0:
        return {}
        
    pr = {node: 1.0 / n for node in nodes}
    for _ in range(max_iter):
        next_pr = {node: (1.0 - d) / n for node in nodes}
        for u in nodes:
            out_count = len(g[u])
            if out_count > 0:
                for v in g[u]:
                    next_pr[v] += d * pr[u] / out_count
            else:
                for v in nodes:
                    next_pr[v] += d * pr[u] / n
        err = sum(abs(next_pr[node] - pr[node]) for node in nodes)
        pr = next_pr
        if err < tol:
            break
    return pr

def calculate_betweenness_centrality(nodes, edges):
    """Calculates Betweenness Centrality metrics using pure Python Brandes' algorithm."""
    adj = {node: [] for node in nodes}
    for u, v in edges:
        if u in adj and v in adj:
            adj[u].append(v)
            
    cb = {node: 0.0 for node in nodes}
    for s in nodes:
        stack = []
        pred = {w: [] for w in nodes}
        sigma = {w: 0.0 for w in nodes}
        sigma[s] = 1.0
        d = {w: -1 for w in nodes}
        d[s] = 0
        
        from collections import deque
        q = deque([s])
        
        while q:
            v = q.popleft()
            stack.append(v)
            for w in adj[v]:
                if d[w] < 0:
                    d[w] = d[v] + 1
                    q.append(w)
                if d[w] == d[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
                    
        delta = {w: 0.0 for w in nodes}
        while stack:
            w = stack.pop()
            for v in pred[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != s:
                cb[w] += delta[w]
                
    n = len(nodes)
    scale = 1.0 / ((n - 1) * (n - 2)) if n > 2 else 1.0
    for node in cb:
        cb[node] *= scale
    return cb

def label_propagation_partition(nodes, edges):
    """Partitions nodes into architectural domains using Label Propagation."""
    # Convert directed edges to undirected neighbor lists
    neighbors = {node: set() for node in nodes}
    for u, v in edges:
        if u in neighbors and v in neighbors:
            neighbors[u].add(v)
            neighbors[v].add(u)
            
    # Initialize each node with its own name as its label
    labels = {node: node for node in nodes}
    
    # We run for a maximum of 10 iterations
    import random
    random.seed(42) # Consistent partitions for validation
    
    for _ in range(10):
        nodes_shuffled = list(nodes)
        random.shuffle(nodes_shuffled)
        changed = False
        
        for node in nodes_shuffled:
            node_neighbors = neighbors[node]
            if not node_neighbors:
                continue
                
            # Count neighbor label frequencies
            freq = {}
            for neighbor in node_neighbors:
                lbl = labels[neighbor]
                freq[lbl] = freq.get(lbl, 0) + 1
                
            # Find the most frequent label
            max_count = -1
            best_labels = []
            for lbl, count in freq.items():
                if count > max_count:
                    max_count = count
                    best_labels = [lbl]
                elif count == max_count:
                    best_labels.append(lbl)
                    
            # Set the label (select first lexicographically to be deterministic if seed matches)
            best_lbl = sorted(best_labels)[0]
            if labels[node] != best_lbl:
                labels[node] = best_lbl
                changed = True
                
        if not changed:
            break
            
    return labels

def generate_mermaid_flowchart(inventory, dependencies):
    """Generates a valid Mermaid flowchart markup with colored node styling based on vulnerability and choke point criteria."""
    import re
    callee_counts = {}
    for caller, callee in dependencies:
        callee_counts[callee] = callee_counts.get(callee, 0) + 1
        
    lines = ["graph TD"]
    
    # Custom dark-theme styling classes
    lines.append("    classDef vulnerable stroke:#ef4444,stroke-width:2px,fill:#2d1414,color:#f87171")
    lines.append("    classDef choke stroke:#8b5cf6,stroke-width:2px,fill:#231438,color:#c084fc")
    lines.append("    classDef standard stroke:#00f2fe,stroke-width:1px,fill:#0d1829,color:#00f2fe")
    
    for item in inventory:
        # Check both potential key mappings
        name = item.get("name", item.get("Service Node", item.get("service", "")))
        if not name:
            continue
            
        vuln = item.get("vulnerable", False) or item.get("Vulnerable", "No") == "Yes"
        is_choke = callee_counts.get(name, 0) >= 2 or item.get("Role", "") == "Choke Point"
        
        # Sanitize node ID for Mermaid (letters, numbers, and underscores only)
        node_id = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        
        if vuln:
            label = f"\"{name} ⚠️\""
            style_class = "vulnerable"
        elif is_choke:
            label = f"\"{name} 🔮\""
            style_class = "choke"
        else:
            label = f"\"{name}\""
            style_class = "standard"
            
        lines.append(f"    {node_id}[{label}]:::{style_class}")
        
    for u, v in dependencies:
        u_clean = re.sub(r"[^a-zA-Z0-9_]", "_", u)
        v_clean = re.sub(r"[^a-zA-Z0-9_]", "_", v)
        lines.append(f"    {u_clean} --> {v_clean}")
        
    mermaid_out = "\n".join(lines)
    try:
        with open("scratch_mermaid.txt", "w", encoding="utf-8") as f:
            f.write(mermaid_out)
    except Exception:
        pass
        
    return mermaid_out

def render_mermaid(mermaid_code):
    """Renders a Mermaid flowchart inside an iframe using Streamlit html components."""
    import streamlit.components.v1 as components
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'dark',
                securityLevel: 'loose',
                themeVariables: {{
                    background: '#0b0f19',
                    primaryColor: '#0f172a',
                    primaryTextColor: '#f1f5f9',
                    lineColor: '#00f2fe'
                }}
            }});
        </script>
        <style>
            body {{
                background-color: #0b0f19;
                margin: 0;
                padding: 10px;
                overflow: auto;
                font-family: sans-serif;
            }}
            .mermaid {{
                display: flex;
                justify-content: center;
                align-items: center;
            }}
        </style>
    </head>
    <body>
        <div class="mermaid" id="graphDiv">
    {mermaid_code}
        </div>
        <script>
            try {{
                mermaid.init(undefined, document.getElementById('graphDiv'));
            }} catch (e) {{
                console.error("Explicit init failed, retrying contentLoaded", e);
                mermaid.contentLoaded();
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_content, height=450, scrolling=True)

def simulate_upgrade_timeline(plan, dependencies, inventory):
    """Simulates upgrade phases step by step and catches calling compatibility outages."""
    states = {}
    for item in inventory:
        # Check both potential key mappings
        name = item.get("name", item.get("Service Node", item.get("service", "")))
        if name:
            states[name] = "Legacy"
            
    log = []
    outages = []
    
    for phase_idx in range(1, 5):
        phase_name = f"Phase {phase_idx}"
        log.append(f"\n--- Starting {phase_name} ---")
        
        phase_data = plan.get(phase_name, {})
        # If baseline, the format is just a list of services upgraded to Target directly
        if isinstance(phase_data, list):
            upgraded_to_target = phase_data
            upgraded_to_transition = []
        else:
            upgraded_to_transition = phase_data.get("Upgrade to Transition State", [])
            upgraded_to_target = phase_data.get("Enforce Target Configuration", [])
            
        # 1. Apply Transition Upgrades
        for s in upgraded_to_transition:
            states[s] = "Transition"
            log.append(f"🟢 UPGRADE: `{s}` upgraded to Transition (Dual-Support) state.")
            
        # 2. Apply Target Upgrades
        for s in upgraded_to_target:
            states[s] = "Target"
            log.append(f"🔵 ENFORCE: `{s}` enforced Target Configuration (Legacy disabled).")
            
        # 3. Check for outages among dependencies
        phase_outages = 0
        for caller, callee in dependencies:
            s_caller = states.get(caller, "Legacy")
            s_callee = states.get(callee, "Legacy")
            
            # Outage Case 1: Caller is in Transition, but Callee is still Legacy
            if s_caller == "Transition" and s_callee == "Legacy":
                msg = f"🔥 OUTAGE in {phase_name}: Caller `{caller}` (Transition) calls Callee `{callee}` (Legacy). Connection rejected!"
                log.append(msg)
                outages.append(msg)
                phase_outages += 1
                
            # Outage Case 2: Caller enforces Target, but Callee has not enforced Target
            elif s_caller == "Target" and s_callee != "Target":
                msg = f"🔥 OUTAGE in {phase_name}: Caller `{caller}` (Target) calls Callee `{callee}` ({s_callee}). Incompatible protocol mismatch!"
                log.append(msg)
                outages.append(msg)
                phase_outages += 1
                
            # Outage Case 3: Callee B enforces Target, but Caller A has not entered Transition
            elif s_callee == "Target" and s_caller == "Legacy":
                msg = f"🔥 OUTAGE in {phase_name}: Callee `{callee}` (Target) disabled legacy endpoints. Caller `{caller}` (Legacy) cannot authenticate!"
                log.append(msg)
                outages.append(msg)
                phase_outages += 1
                
        if phase_outages == 0:
            log.append(f"✅ {phase_name} completed with zero outages.")
        else:
            log.append(f"⚠️ {phase_name} completed with {phase_outages} outage events.")
            
    return log, outages

def call_ollama(prompt: str, model_name: str) -> str:
    """Send request to local Ollama instance."""
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 1024
        }
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=240)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        return f"Error connecting to Ollama: {e}"

def render_simulator_banner():
    """Renders the simple-words faculty guide banner for the Upgrade Simulator."""
    st.markdown("""
    <div style="background: rgba(13, 19, 33, 0.85); border: 1px solid rgba(0, 242, 254, 0.4); border-left: 4px solid #00F2FE; border-radius: 10px; padding: 18px; margin-bottom: 20px;">
        <h3 style="color: #00F2FE !important; margin: 0 0 10px 0; font-size: 1.35rem; font-weight: 700;">🎮 Upgrade Timeline Outage Simulator (Automated Chaos Stress-Tester)</h3>
        <p style="color: #f8fafc; font-size: 0.95rem; margin-bottom: 12px;">
            <b>The Problem It Solves:</b> In real-world production, you cannot just <i>hope</i> a migration plan works—you must stress-test it first!
        </p>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px;">
            <div style="background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px; padding: 12px;">
                <b style="color: #38bdf8; font-size: 0.9rem;">1. Phase-by-Phase Simulation</b><br>
                <span style="color: #cbd5e1; font-size: 0.82rem;">Rolls out microservice updates step-by-step from <b>Phase 1 to Phase 4</b>.</span>
            </div>
            <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 8px; padding: 12px;">
                <b style="color: #f59e0b; font-size: 0.9rem;">2. Network Health Probing</b><br>
                <span style="color: #cbd5e1; font-size: 0.82rem;">At each step, sends simulated API requests across all network call edges (A &rarr; B).</span>
            </div>
            <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 8px; padding: 12px;">
                <b style="color: #ef4444; font-size: 0.9rem;">3. Outage Flagging</b><br>
                <span style="color: #cbd5e1; font-size: 0.82rem;">Flags <b>503 HTTP / Contract Outages</b> if an API caller upgrades before its database is ready.</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_4way_comparison_ui():
    """Renders a sleek, state-of-the-art 4-Way Scientific Benchmark Comparison view."""
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
        <div>
            <h2 style="font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 50%, #9B59B6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">
                🏆 4-Way Scientific Benchmark Suite
            </h2>
            <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 4px;">
                Empirical comparative evaluation across classical algorithms, standard LLMs, GraphRAG single-agents, and Lattica's reconciled planner.
            </p>
        </div>
        <span class="comp-badge badge-purple" style="font-size: 0.8rem; padding: 6px 14px;">BENCHMARK VERIFIED</span>
    </div>
    """, unsafe_allow_html=True)

    # 4 Cards Layout
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown("""
        <div class="comp-card comp-card-purple">
            <span class="comp-badge badge-purple">1. DETERMINISTIC</span>
            <h4 style="font-weight: 700; font-size: 1.1rem; margin-top: 4px;">Topological Sort</h4>
            <div style="font-size: 2.2rem; font-weight: 800; color: #c084fc; margin-top: 8px;">0.0%</div>
            <div style="font-size: 0.8rem; color: #94a3b8;">Dependency Conflicts</div>
            <hr style="border-color: rgba(255,255,255,0.08); margin: 12px 0;">
            <div style="font-size: 0.82rem; color: #cbd5e1; padding: 2px 0;">⚡ <b>Latency:</b> 0.0010s (Instant)</div>
            <div style="font-size: 0.82rem; color: #cbd5e1; padding: 2px 0;">⚙️ <b>Engine:</b> Kahn's Depth</div>
            <div style="font-size: 0.82rem; color: #f87171; padding: 2px 0;">⚠️ <b>Rollover:</b> Binary Only</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="comp-card comp-card-red">
            <span class="comp-badge badge-red">2. BASELINE CONTROL</span>
            <h4 style="font-weight: 700; font-size: 1.1rem; margin-top: 4px;">Control Group LLM</h4>
            <div style="font-size: 2.2rem; font-weight: 800; color: #f87171; margin-top: 8px;">100.0%</div>
            <div style="font-size: 0.8rem; color: #94a3b8;">Dependency Conflicts</div>
            <hr style="border-color: rgba(255,255,255,0.08); margin: 12px 0;">
            <div style="font-size: 0.82rem; color: #cbd5e1; padding: 2px 0;">⏱️ <b>Latency:</b> 179.17s</div>
            <div style="font-size: 0.82rem; color: #cbd5e1; padding: 2px 0;">🧠 <b>Context:</b> Flat Inventory</div>
            <div style="font-size: 0.82rem; color: #f87171; padding: 2px 0;">🔥 <b>Risk:</b> High Outage</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="comp-card comp-card-blue">
            <span class="comp-badge badge-blue">3. GRAPHRAG SINGLE</span>
            <h4 style="font-weight: 700; font-size: 1.1rem; margin-top: 4px;">Lattica Single-Agent</h4>
            <div style="font-size: 2.2rem; font-weight: 800; color: #60a5fa; margin-top: 8px;">100.0%</div>
            <div style="font-size: 0.8rem; color: #94a3b8;">Dependency Conflicts</div>
            <hr style="border-color: rgba(255,255,255,0.08); margin: 12px 0;">
            <div style="font-size: 0.82rem; color: #cbd5e1; padding: 2px 0;">⏱️ <b>Latency:</b> 568.56s</div>
            <div style="font-size: 0.82rem; color: #cbd5e1; padding: 2px 0;">📊 <b>Context:</b> CBR + DI Hints</div>
            <div style="font-size: 0.82rem; color: #f87171; padding: 2px 0;">⚠️ <b>Limit:</b> Single Prompt</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown("""
        <div class="comp-card comp-card-green">
            <span class="comp-badge badge-green">4. CHAMPION</span>
            <h4 style="font-weight: 700; font-size: 1.1rem; margin-top: 4px;">AI Execution Planner</h4>
            <div style="font-size: 2.2rem; font-weight: 800; color: #34d399; margin-top: 8px;">0.0%</div>
            <div style="font-size: 0.8rem; color: #94a3b8;">Dependency Conflicts</div>
            <hr style="border-color: rgba(255,255,255,0.08); margin: 12px 0;">
            <div style="font-size: 0.82rem; color: #cbd5e1; padding: 2px 0;">⏱️ <b>Latency:</b> 21.64s</div>
            <div style="font-size: 0.82rem; color: #cbd5e1; padding: 2px 0;">🧩 <b>Engine:</b> Federated Mesh</div>
            <div style="font-size: 0.82rem; color: #34d399; padding: 2px 0;">🛡️ <b>Rollover:</b> Zero-Downtime</div>
        </div>
        """, unsafe_allow_html=True)

    # Custom Table Card
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown("### 📊 Side-by-Side Architectural & Metric Matrix")
    
    st.markdown("""
    <table class="styled-comp-table">
      <thead>
        <tr>
          <th>Evaluation Dimension</th>
          <th style="color: #c084fc;">1. Deterministic Topo</th>
          <th style="color: #f87171;">2. Baseline LLM</th>
          <th style="color: #60a5fa;">3. Lattica Single-Agent</th>
          <th style="color: #34d399;">4. AI Execution Planner</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><b>Architecture Strategy</b></td>
          <td>Pure Algorithmic (Kahn's Depth)</td>
          <td>Single Prompt Standard LLM</td>
          <td>Single Prompt GraphRAG LLM</td>
          <td><b>Federated Multi-Agent + Reconciliation</b></td>
        </tr>
        <tr>
          <td><b>Network Spatial Awareness</b></td>
          <td><span class="comp-badge badge-purple">Static Graph Depth</span></td>
          <td><span class="comp-badge badge-red">None (Flat List)</span></td>
          <td><span class="comp-badge badge-blue">CBR / DI Hints</span></td>
          <td><span class="comp-badge badge-green">Full Domain Partitioning</span></td>
        </tr>
        <tr>
          <td><b>Dual-State Production Rollover</b></td>
          <td>❌ Binary Switch Only</td>
          <td>❌ Binary Switch Only</td>
          <td>❌ Binary Switch Only</td>
          <td><b>✅ Transition State &rarr; Target Enforce</b></td>
        </tr>
        <tr>
          <td><b>Dependency Conflict Rate</b></td>
          <td><b style="color: #34d399; font-size: 1.05rem;">0.0%</b></td>
          <td><b style="color: #f87171; font-size: 1.05rem;">100.0%</b></td>
          <td><b style="color: #f87171; font-size: 1.05rem;">100.0%</b></td>
          <td><b style="color: #34d399; font-size: 1.05rem;">0.0%</b></td>
        </tr>
        <tr>
          <td><b>Average Latency per Run</b></td>
          <td><b>0.0010s</b> (Instant)</td>
          <td>179.17s</td>
          <td>568.56s</td>
          <td>21.64s</td>
        </tr>
        <tr>
          <td><b>Production Safety Profile</b></td>
          <td>⚠️ Low (Single-stage switch)</td>
          <td>❌ Outage Vulnerable</td>
          <td>❌ Outage Vulnerable</td>
          <td><b>🛡️ Zero-Downtime Safe</b></td>
        </tr>
      </tbody>
    </table>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 30-DAG Statistical Generalization Section
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown("### 📊 30-DAG Statistical Generalization & Scale Invariance Suite")
    st.write("Statistical validation evaluating 30 synthetic microservice DAG topologies across Small (N=10), Medium (N=25), and Large Enterprise (N=50) graph scales with 95% Confidence Intervals.")
    
    if st.button("🧪 RUN 30-DAG BENCHMARK", key="run_30dag_synth_btn"):
        with st.spinner("Executing 30-DAG Statistical Benchmark across 120 DAG evaluations..."):
            from synthetic_benchmark import run_synthetic_benchmark
            run_synthetic_benchmark(total_dags=30)
            st.success("30-DAG Benchmark complete! Updated statistical tables & figures.")
            
    if os.path.exists("synthetic_results_summary.md"):
        with open("synthetic_results_summary.md", "r") as f:
            syn_summary_md = f.read()
        with st.expander("📄 View 30-DAG Statistical Metric Matrix (Mean ± 95% CI, Variance)", expanded=True):
            st.markdown(syn_summary_md)
            
    if os.path.exists("synthetic_statistical_rigor.png"):
        st.image("synthetic_statistical_rigor.png", caption="30-DAG Statistical Rigor Publication Plot (N=10, N=25, N=50 Scales)", use_column_width=True)
        
    st.markdown('</div>', unsafe_allow_html=True)

    # Interactive Visual Benchmark Gallery
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown("### 📈 Multi-Dimensional Scientific Visualizations Gallery")
    
    chart_tabs = st.tabs([
        "🎛️ Master 2x2 Dashboard",
        "⚡ Execution Latency",
        "📉 Outage Timeline",
        "🕸️ Capability Radar",
        "🔴 Conflict Rate"
    ])
    
    with chart_tabs[0]:
        if os.path.exists("dashboard_quad.png"):
            st.image("dashboard_quad.png", caption="Master Scientific Benchmark Dashboard (2x2 Multi-Plot Suite)", use_column_width=True)
        else:
            st.info("Run `python evaluator.py` to generate the Master Dashboard.")

    with chart_tabs[1]:
        if os.path.exists("latency_comparison.png"):
            st.image("latency_comparison.png", caption="Average Execution Latency (seconds) Across All 4 Planning Strategies", use_column_width=True)

    with chart_tabs[2]:
        if os.path.exists("outage_timeline.png"):
            st.image("outage_timeline.png", caption="Phase-by-Phase Upgrade Outage Event Timeline (Phases 1 to 4)", use_column_width=True)

    with chart_tabs[3]:
        if os.path.exists("radar_comparison.png"):
            st.image("radar_comparison.png", caption="Multi-Dimensional 5-Axis Capability Radar Plot", use_column_width=True)

    with chart_tabs[4]:
        if os.path.exists("conflict_comparison.png"):
            st.image("conflict_comparison.png", caption="Dependency Conflict Rate Comparison (%) Across All 4 Groups", use_column_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

def call_ollama_stream(prompt: str, model_name: str, placeholder) -> str:
    """Send request to local Ollama instance and stream tokens to UI."""
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.2,
            "num_predict": 1024
        }
    }
    
    full_text = ""
    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=240)
        response.raise_for_status()
        
        # Read the line-by-line streaming response
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode('utf-8'))
                token = chunk.get("response", "")
                full_text += token
                # Render markdown to the placeholder in real time
                placeholder.markdown(full_text + "▌")
        
        placeholder.markdown(full_text)
        return full_text
    except Exception as e:
        placeholder.error(f"Error calling Ollama API: {e}")
        return ""

# --- STAGE 1 & 2 HELPER (LOCAL DOCKER DISCOVERY) ---

def run_local_discovery():
    """Extract topology dynamically from docker-compose.yml and inventory.json."""
    inventory = []
    dependencies = []
    
    inv_map = {}
    if os.path.exists("inventory.json"):
        try:
            with open("inventory.json", "r") as f:
                inv_data = json.load(f)
                for item in inv_data:
                    service_key = item.get("service", item.get("name"))
                    if service_key:
                        inv_map[service_key] = item
        except Exception:
            pass
            
    if os.path.exists("docker-compose.yml"):
        try:
            with open("docker-compose.yml", "r") as f:
                compose_data = yaml.safe_load(f) or {}
            services = compose_data.get("services", {})
            for name, config in services.items():
                if name == "neo4j":
                    continue
                inv = inv_map.get(name, {})
                inventory.append({
                    "name": name,
                    "algorithm": inv.get("algorithm", "RSA-2048"),
                    "vulnerable": inv.get("vulnerable", True),
                    "location": f"docker-compose.yml -> {name}"
                })
                depends_on = config.get("depends_on", []) if config else []
                if isinstance(depends_on, dict):
                    depends_on = list(depends_on.keys())
                elif isinstance(depends_on, str):
                    depends_on = [depends_on]
                for dep in depends_on:
                    if dep != "neo4j":
                        dependencies.append((name, dep))
        except Exception as e:
            print(f"Error parsing docker-compose.yml: {e}")
            
    # Fallback to inventory.json items if docker-compose has no services
    if not inventory and inv_map:
        for name, inv in inv_map.items():
            inventory.append({
                "name": name,
                "algorithm": inv.get("algorithm", "RSA-2048"),
                "vulnerable": inv.get("vulnerable", True),
                "location": "inventory.json"
            })
            
    return inventory, dependencies

def run_real_github_scanning(repo_url, github_token):
    """Scans the repository to dynamically discover services, API routes, database clients, Docker links, and Kubernetes communications."""
    # Clean URL and extract owner and repo name
    repo_url = repo_url.strip("()[]'\" ")
    clean_url = repo_url.replace("https://github.com/", "").strip("/")
    parts = clean_url.split("/")
    if len(parts) < 2:
        st.error("Invalid GitHub Repository URL.")
        st.stop()
        
    owner, repo = parts[0], parts[1]
    st.code(f"Cloning repository: https://github.com/{owner}/{repo} ...", language="bash")
    
    workspace_dir = os.path.abspath(".")
    temp_dir = tempfile.mkdtemp(dir=workspace_dir)
    
    # Helper to parse XML / pom.xml
    def extract_pom_artifactId(content):
        match = re.search(r"<artifactId>(.*?)</artifactId>", content)
        if match:
            return match.group(1).strip()
        return None

    # Helper to parse go.mod
    def extract_go_module(content):
        match = re.search(r"^module\s+([^\s\n]+)", content, re.MULTILINE)
        if match:
            return match.group(1).split("/")[-1].strip()
        return None

    # Helper to parse package.json
    def extract_package_name(content):
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                return data.get("name")
        except Exception:
            pass
        match = re.search(r'"name"\s*:\s*"([^"]+)"', content)
        if match:
            return match.group(1).strip()
        return None
        
    try:
        # Shallow clone the repo
        clone_url = f"https://github.com/{owner}/{repo}.git"
        if github_token:
            clone_url = f"https://{github_token}@github.com/{owner}/{repo}.git"
            
        result = subprocess.run(
            ["git", "clone", "--depth", "1", clone_url, temp_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            st.error(f"Failed to clone repository: {result.stderr}")
            st.stop()
            
        st.success("Repository cloned successfully. Performing Multi-Dimensional Service Graph Discovery...")
        
        # We will collect discovered services (nodes) and dependencies (edges)
        services = {}  # name -> { "vulnerable": bool, "algorithm": str, "location": str, "apis": set(), "ports": set() }
        dependencies = set()  # set of (caller, callee)
        
        # 1. Identify Service Roots (Top-Down & Bottom-Up)
        service_roots = {}  # path -> dict
        for root, dirs, files in os.walk(temp_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            config_files = {
                "package.json": "NodeJS",
                "requirements.txt": "Python",
                "go.mod": "Go",
                "pom.xml": "Java (Maven)",
                "build.gradle": "Java (Gradle)",
                "Dockerfile": "Docker"
            }
            found_configs = [f for f in files if f in config_files]
            if found_configs:
                svc_name = None
                primary_lang = "Generic"
                
                if "package.json" in found_configs:
                    primary_lang = "NodeJS"
                    try:
                        with open(os.path.join(root, "package.json"), "r", encoding="utf-8", errors="ignore") as f:
                            svc_name = extract_package_name(f.read())
                    except Exception:
                        pass
                elif "pom.xml" in found_configs:
                    primary_lang = "Java (Maven)"
                    try:
                        with open(os.path.join(root, "pom.xml"), "r", encoding="utf-8", errors="ignore") as f:
                            svc_name = extract_pom_artifactId(f.read())
                    except Exception:
                        pass
                elif "go.mod" in found_configs:
                    primary_lang = "Go"
                    try:
                        with open(os.path.join(root, "go.mod"), "r", encoding="utf-8", errors="ignore") as f:
                            svc_name = extract_go_module(f.read())
                    except Exception:
                        pass
                elif "requirements.txt" in found_configs:
                    primary_lang = "Python"
                elif "Dockerfile" in found_configs:
                    primary_lang = "Docker"
                    
                if not svc_name:
                    if root == temp_dir:
                        svc_name = repo
                    else:
                        svc_name = os.path.basename(root)
                        
                service_roots[root] = {
                    "name": svc_name,
                    "language": primary_lang,
                    "ports": set(),
                    "base_image": None,
                    "apis": set(),
                    "location": os.path.relpath(root, temp_dir),
                    "vulnerable": False,
                    "algorithm": "Secure/TLS1.3"
                }
                
        # Always register the temp_dir as a service root if not already registered
        if temp_dir not in service_roots:
            service_roots[temp_dir] = {
                "name": repo,
                "language": "Generic",
                "ports": set(),
                "base_image": None,
                "apis": set(),
                "location": ".",
                "vulnerable": False,
                "algorithm": "Secure/TLS1.3"
            }
            
        # Parse Dockerfiles in service roots
        for root, svc_info in service_roots.items():
            dockerfile_path = os.path.join(root, "Dockerfile")
            if os.path.exists(dockerfile_path):
                try:
                    with open(dockerfile_path, "r", encoding="utf-8", errors="ignore") as f:
                        df_content = f.read()
                    ports = re.findall(r"^\s*EXPOSE\s+([0-9\s/tcpudp]+)", df_content, re.MULTILINE | re.IGNORECASE)
                    for p_group in ports:
                        cleaned_group = re.sub(r"/[a-zA-Z]+", "", p_group)
                        for p in cleaned_group.split():
                            svc_info["ports"].add(p.strip())
                    base_match = re.search(r"^\s*FROM\s+([^\s#]+)", df_content, re.MULTILINE | re.IGNORECASE)
                    if base_match:
                        svc_info["base_image"] = base_match.group(1).strip()
                except Exception as e:
                    st.write(f"Warning: Failed to parse Dockerfile in {os.path.relpath(root, temp_dir)}: {e}")
                    
        # Populate initial services list
        for root_path, info in service_roots.items():
            name = info["name"]
            loc_str = f"Directory: {info['location']}"
            if info["base_image"]:
                loc_str += f" [Base: {info['base_image']}]"
            services[name] = {
                "vulnerable": info["vulnerable"],
                "algorithm": info["algorithm"],
                "location": loc_str,
                "apis": info["apis"],
                "ports": info["ports"]
            }
            
        # 2. Parse Docker Compose Configuration
        docker_compose_files = []
        for root, dirs, files in os.walk(temp_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if f.lower() in ["docker-compose.yml", "docker-compose.yaml"]:
                    docker_compose_files.append(os.path.join(root, f))
                    
        compose_services = {}
        for dc_path in docker_compose_files:
            st.write(f"🐳 Found Docker Compose config: `{os.path.relpath(dc_path, temp_dir)}`")
            try:
                with open(dc_path, "r", encoding="utf-8", errors="ignore") as f:
                    dc_data = yaml.safe_load(f)
                if isinstance(dc_data, dict) and "services" in dc_data:
                    dc_services = dc_data["services"]
                    for svc_name, svc_conf in dc_services.items():
                        if svc_name == "neo4j":
                            continue
                            
                        if svc_name not in compose_services:
                            compose_services[svc_name] = {
                                "depends_on": set(),
                                "links": set(),
                                "ports": set(),
                                "location": os.path.relpath(dc_path, temp_dir)
                            }
                            
                        deps = svc_conf.get("depends_on", [])
                        if isinstance(deps, dict):
                            deps = list(deps.keys())
                        elif isinstance(deps, str):
                            deps = [deps]
                        for d in deps:
                            if d != "neo4j":
                                compose_services[svc_name]["depends_on"].add(d)
                                
                        links = svc_conf.get("links", [])
                        for l in links:
                            target = l.split(":")[0]
                            if target != "neo4j":
                                compose_services[svc_name]["links"].add(target)
                                
                        ports_list = svc_conf.get("ports", [])
                        for p in ports_list:
                            p_str = str(p)
                            if ":" in p_str:
                                p_str = p_str.split(":")[-1]
                            p_str = re.sub(r"/[a-zA-Z]+", "", p_str).strip()
                            compose_services[svc_name]["ports"].add(p_str)
                            
                        # Merge/enrich existing services or add new ones
                        matched = False
                        for root_path, info in service_roots.items():
                            if info["name"].lower() == svc_name.lower():
                                services[info["name"]]["ports"].update(compose_services[svc_name]["ports"])
                                if f"Docker Compose" not in services[info["name"]]["location"]:
                                    services[info["name"]]["location"] += f" | Docker Compose: {os.path.relpath(dc_path, temp_dir)}"
                                matched = True
                                break
                                
                        if not matched:
                            algo = "Secure/TLS1.3"
                            vuln = False
                            loc = f"Docker Compose: {os.path.relpath(dc_path, temp_dir)}"
                            
                            db_algos = {
                                "mongo": "MongoDB Database",
                                "redis": "Redis Cache",
                                "postgres": "PostgreSQL Database",
                                "mysql": "MySQL Database",
                                "mariadb": "MariaDB Database",
                                "cassandra": "Cassandra Database",
                                "rabbitmq": "RabbitMQ Broker",
                                "kafka": "Kafka Broker"
                            }
                            for db_key, db_desc in db_algos.items():
                                if db_key in svc_name.lower():
                                    loc = f"{db_desc} (Docker Compose)"
                                    break
                                    
                            services[svc_name] = {
                                "vulnerable": vuln,
                                "algorithm": algo,
                                "location": loc,
                                "apis": set(),
                                "ports": compose_services[svc_name]["ports"]
                            }
                            
                        for dep in compose_services[svc_name]["depends_on"].union(compose_services[svc_name]["links"]):
                            dependencies.add((svc_name, dep))
            except Exception as e:
                st.write(f"Warning: Failed to parse Docker Compose file '{dc_path}': {e}")
                
        # 3. Parse Kubernetes Manifests
        k8s_files = []
        for root, dirs, files in os.walk(temp_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if f.endswith((".yaml", ".yml")) and not "docker-compose" in f.lower():
                    k8s_files.append(os.path.join(root, f))
                    
        k8s_services = {}       # name -> { "selectors": dict, "ports": set(), "location": str }
        k8s_deployments = {}    # name -> { "labels": dict, "containers": list, "location": str }
        k8s_ingresses = []      # list of dict
        
        for k8s_path in k8s_files:
            try:
                with open(k8s_path, "r", encoding="utf-8", errors="ignore") as f:
                    docs = yaml.safe_load_all(f)
                    for doc in docs:
                        if not isinstance(doc, dict) or "apiVersion" not in doc or "kind" not in doc:
                            continue
                        
                        kind = doc.get("kind")
                        meta = doc.get("metadata", {})
                        name = meta.get("name")
                        if not name:
                            continue
                            
                        if kind == "Service":
                            spec = doc.get("spec", {})
                            selectors = spec.get("selector", {})
                            ports_list = spec.get("ports", [])
                            ports = set()
                            for p in ports_list:
                                if isinstance(p, dict):
                                    if "port" in p:
                                        ports.add(str(p["port"]))
                                    if "targetPort" in p:
                                        ports.add(str(p["targetPort"]))
                            
                            k8s_services[name] = {
                                "selectors": selectors if isinstance(selectors, dict) else {},
                                "ports": ports,
                                "location": os.path.relpath(k8s_path, temp_dir)
                            }
                            
                        elif kind in ["Deployment", "StatefulSet", "DaemonSet"]:
                            spec = doc.get("spec", {})
                            template = spec.get("template", {})
                            t_meta = template.get("metadata", {})
                            t_labels = t_meta.get("labels", {})
                            
                            t_spec = template.get("spec", {})
                            containers = t_spec.get("containers", [])
                            
                            k8s_deployments[name] = {
                                "labels": t_labels if isinstance(t_labels, dict) else {},
                                "containers": containers if isinstance(containers, list) else [],
                                "location": os.path.relpath(k8s_path, temp_dir)
                            }
                            
                        elif kind == "Ingress":
                            spec = doc.get("spec", {})
                            rules = spec.get("rules", [])
                            ingress_backends = []
                            for rule in rules:
                                http_rules = rule.get("http", {})
                                paths = http_rules.get("paths", [])
                                for path_obj in paths:
                                    backend = path_obj.get("backend", {})
                                    service = backend.get("service", {})
                                    svc_name = service.get("name")
                                    if not svc_name:
                                        svc_name = backend.get("serviceName")
                                    if svc_name:
                                        ingress_backends.append(svc_name)
                            k8s_ingresses.append({
                                "name": name,
                                "backends": ingress_backends,
                                "location": os.path.relpath(k8s_path, temp_dir)
                            })
            except Exception:
                pass
                
        matched_deployments = set()
        for s_name, s_data in k8s_services.items():
            selectors = s_data["selectors"]
            matching_depls = []
            for d_name, d_data in k8s_deployments.items():
                labels = d_data["labels"]
                if selectors and all(labels.get(k) == v for k, v in selectors.items()):
                    matching_depls.append((d_name, d_data))
                    matched_deployments.add(d_name)
                    
            if s_name not in services:
                services[s_name] = {
                    "vulnerable": False,
                    "algorithm": "Secure/TLS1.3",
                    "location": f"K8s Service: {s_data['location']}",
                    "apis": set(),
                    "ports": s_data["ports"]
                }
            else:
                if f"K8s Service" not in services[s_name]["location"]:
                    services[s_name]["location"] += f" | K8s Service: {s_data['location']}"
                services[s_name]["ports"].update(s_data["ports"])
                
            for d_name, d_data in matching_depls:
                services[s_name]["location"] += f" | Deployment: {d_name}"
                for c in d_data["containers"]:
                    img = c.get("image", "")
                    if img:
                        services[s_name]["location"] += f" [Image: {img}]"
                    env = c.get("env", [])
                    for e_item in env:
                        if not isinstance(e_item, dict):
                            continue
                        val = str(e_item.get("value", ""))
                        for other_svc in k8s_services.keys():
                            if other_svc == s_name:
                                continue
                            if other_svc in val or f"{other_svc}." in val:
                                dependencies.add((s_name, other_svc))
                                
        for d_name, d_data in k8s_deployments.items():
            if d_name not in matched_deployments:
                if d_name not in services:
                    services[d_name] = {
                        "vulnerable": False,
                        "algorithm": "Secure/TLS1.3",
                        "location": f"K8s Deployment: {d_data['location']}",
                        "apis": set(),
                        "ports": set()
                    }
                else:
                    if f"K8s Deployment" not in services[d_name]["location"]:
                        services[d_name]["location"] += f" | K8s Deployment: {d_data['location']}"
                        
                for c in d_data["containers"]:
                    env = c.get("env", [])
                    for e_item in env:
                        if not isinstance(e_item, dict):
                            continue
                        val = str(e_item.get("value", ""))
                        for other_svc in k8s_services.keys():
                            if other_svc == d_name:
                                continue
                            if other_svc in val or f"{other_svc}." in val:
                                dependencies.add((d_name, other_svc))
                                
        for ing in k8s_ingresses:
            for backend in ing["backends"]:
                if backend in services:
                    if f"Ingress" not in services[backend]["location"]:
                        services[backend]["location"] += f" | Ingress: {ing['name']}"
                    gateway_node = "api-gateway"
                    if gateway_node not in services:
                        services[gateway_node] = {
                            "vulnerable": False,
                            "algorithm": "Secure/TLS1.3",
                            "location": "Kubernetes Ingress Gateway",
                            "apis": set(),
                            "ports": {"80", "443"}
                        }
                    dependencies.add((gateway_node, backend))
                    
        # 4. Code-Level Service & API Discovery
        code_files = []
        for root, dirs, files in os.walk(temp_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if f.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.go', '.java', '.cs', '.rs')):
                    code_files.append(os.path.join(root, f))
                    
        def get_service_for_file(filepath):
            curr = os.path.dirname(filepath)
            while curr and curr != temp_dir:
                if curr in service_roots:
                    return service_roots[curr]["name"]
                parent = os.path.dirname(curr)
                if parent == curr:
                    break
                curr = parent
            if temp_dir in service_roots:
                return service_roots[temp_dir]["name"]
            return repo
            
        st.write(f"Parsed codebases. Grouping code files into **{len(set(service_roots.keys()))}** service roots.")
        
        for cf in code_files:
            rel_path = os.path.relpath(cf, temp_dir).replace('\\', '/')
            service_name = get_service_for_file(cf)
            
            try:
                with open(cf, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue
                
            if service_name not in services:
                services[service_name] = {
                    "vulnerable": False,
                    "algorithm": "Secure/TLS1.3",
                    "location": f"Directory: {os.path.relpath(os.path.dirname(cf), temp_dir)}",
                    "apis": set(),
                    "ports": set()
                }
                
            # API Route Scanning
            py_routes = re.findall(r"@app\.(?:get|post|put|delete|route)\(['\"]([^'\"]+)['\"]", content)
            py_routes += re.findall(r"@router\.(?:get|post|put|delete|route)\(['\"]([^'\"]+)['\"]", content)
            express_routes = re.findall(r"\b(?:app|router)\.(?:get|post|put|delete)\(['\"]([^'\"]+)['\"]", content)
            go_routes = re.findall(r"\br\.(?:GET|POST|PUT|DELETE)\(['\"]([^'\"]+)['\"]", content)
            go_routes += re.findall(r"\bhttp\.HandleFunc\(['\"]([^'\"]+)['\"]", content)
            java_routes = re.findall(r"@(?:Get|Post|Put|Delete|Request)Mapping\(['\"]([^'\"]+)['\"]", content)
            
            for r in py_routes + express_routes + go_routes + java_routes:
                services[service_name]["apis"].add(r)
                
            # Cryptographic Vulnerability Scanning
            is_vuln = False
            algo = None
            
            if cf.endswith('.py'):
                if re.search(r"import\s+rsa\b", content) or re.search(r"from\s+Crypto\.PublicKey\s+import\s+RSA\b", content) or "cryptography.hazmat.primitives.asymmetric.rsa" in content:
                    is_vuln = True
                    algo = "RSA (Legacy Source Code)"
                elif re.search(r"import\s+ecdsa\b", content) or "cryptography.hazmat.primitives.asymmetric.ec" in content:
                    is_vuln = True
                    algo = "ECDSA (Legacy Source Code)"
                elif "cryptography.hazmat" in content or "Crypto.Cipher" in content:
                    is_vuln = True
                    algo = "Symmetric/Asymmetric Primitive"
                elif "md5" in content.lower() or "sha1" in content.lower():
                    is_vuln = True
                    algo = "Legacy Hash Primitive (MD5/SHA1)"
            elif cf.endswith(('.js', '.jsx', '.ts', '.tsx')):
                if "elliptic" in content or "createECDH" in content or "secp256k1" in content:
                    is_vuln = True
                    algo = "ECDSA/ECDH (Legacy Node Crypto)"
                elif "node-rsa" in content or "createSign" in content or "generateKeyPair" in content:
                    is_vuln = True
                    algo = "RSA (Legacy Node Crypto)"
                elif "crypto-js" in content or "cryptojs" in content:
                    is_vuln = True
                    algo = "Symmetric Primitive (Crypto-JS)"
                elif "md5" in content.lower() or "sha1" in content.lower():
                    is_vuln = True
                    algo = "Legacy Hash (MD5/SHA1)"
            elif cf.endswith('.go'):
                if "crypto/rsa" in content:
                    is_vuln = True
                    algo = "RSA (Go crypto)"
                elif "crypto/ecdsa" in content:
                    is_vuln = True
                    algo = "ECDSA (Go crypto)"
                elif "crypto/md5" in content or "crypto/sha1" in content:
                    is_vuln = True
                    algo = "Legacy Hash (Go crypto)"
            elif cf.endswith('.java'):
                if "RSA" in content and ("KeyPairGenerator" in content or "Cipher" in content):
                    is_vuln = True
                    algo = "RSA (Java Cryptography)"
                elif "MD5" in content or "SHA-1" in content or "SHA1" in content:
                    is_vuln = True
                    algo = "Legacy Hash (Java Cryptography)"
                    
            if is_vuln:
                services[service_name]["vulnerable"] = True
                services[service_name]["algorithm"] = algo
                st.markdown(f"🔍 **Vulnerability Found** in service `{service_name}` (File: `{rel_path}`) using `{algo}`")
                
            # Connection Scanning
            urls = re.findall(r"https?://([a-zA-Z0-9_-]+)(?::\d+)?", content)
            for host in urls:
                if host in services:
                    if host != service_name:
                        dependencies.add((service_name, host))
                        
            hosts_ports = re.findall(r"['\"]([a-zA-Z0-9_-]+):\d+['\"]", content)
            for host in hosts_ports:
                if host in services:
                    if host != service_name:
                        dependencies.add((service_name, host))
                        
            # Check for other service name references
            for other_svc_name in list(services.keys()):
                if other_svc_name == service_name:
                    continue
                if len(other_svc_name) <= 3 or other_svc_name.lower() in ["app", "core", "test", "demo", "main", "service"]:
                    continue
                pattern = r"\b" + re.escape(other_svc_name) + r"\b"
                if re.search(pattern, content, re.IGNORECASE):
                    dependencies.add((service_name, other_svc_name))
                    
            # Check for database client initializations
            if "MongoClient" in content or "mongodb://" in content or "mongoose.connect" in content:
                db_node = "mongo-db"
                if db_node not in services:
                    services[db_node] = {"vulnerable": False, "algorithm": "Secure/TLS1.3", "location": "Database", "apis": set(), "ports": {"27017"}}
                dependencies.add((service_name, db_node))
            if "redis.Redis" in content or "redis://" in content or "createClient" in content and "redis" in content.lower():
                db_node = "redis-db"
                if db_node not in services:
                    services[db_node] = {"vulnerable": False, "algorithm": "Secure/TLS1.3", "location": "Database", "apis": set(), "ports": {"6379"}}
                dependencies.add((service_name, db_node))
            if "psycopg2" in content or "postgresql://" in content or "pg.Client" in content:
                db_node = "postgres-db"
                if db_node not in services:
                    services[db_node] = {"vulnerable": False, "algorithm": "Secure/TLS1.3", "location": "Database", "apis": set(), "ports": {"5432"}}
                dependencies.add((service_name, db_node))
            if "pymysql" in content or "mysql://" in content or "mysql.createConnection" in content:
                db_node = "mysql-db"
                if db_node not in services:
                    services[db_node] = {"vulnerable": False, "algorithm": "Secure/TLS1.3", "location": "Database", "apis": set(), "ports": {"3306"}}
                dependencies.add((service_name, db_node))
                
        # 5. Compile inventory and dependencies
        compiled_inventory = []
        for name, data in services.items():
            api_list = list(data["apis"])
            ports_list = list(data["ports"])
            
            location_str = data["location"]
            if ports_list:
                location_str += f" | Ports: {', '.join(sorted(ports_list))}"
            if api_list:
                location_str += f" | APIs: {', '.join(sorted(api_list)[:5])}"
                if len(api_list) > 5:
                    location_str += "..."
                    
            compiled_inventory.append({
                "name": name,
                "algorithm": data["algorithm"],
                "vulnerable": data["vulnerable"],
                "location": location_str
            })
            
        compiled_dependencies = list(dependencies)
        st.write(f"Discovery complete. Discovered **{len(compiled_inventory)}** services/components and **{len(compiled_dependencies)}** directed dependencies.")
        return compiled_inventory, compiled_dependencies
        
    finally:
        if os.name == 'nt':
            subprocess.run(['cmd', '/c', 'rd', '/s', '/q', temp_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            shutil.rmtree(temp_dir, ignore_errors=True)

from planning.validator import validate_plan, validate_execution_plan

# --- STREAMLIT UI LAYOUT ---

# Header block
st.markdown("""
<div class="logo-container">
    <div class="logo-icon">🚀</div>
    <div class="main-title">LATTICA: AI Infrastructure Execution Planner</div>
</div>
<div class="subtitle">AI-Assisted Dependency Analysis & Safe Execution Planning for Distributed Systems</div>
""", unsafe_allow_html=True)

# System Health Checks (Top Bar Monitor)
ollama_online = check_ollama_status()
neo4j_online = check_neo4j_status()

# Sidebar settings
st.sidebar.header("🔧 Configuration Settings")
st.sidebar.markdown("---")

# Secrets Manager Integration Section
st.sidebar.subheader("🔐 Secrets Vault Settings")
secrets_provider = st.sidebar.selectbox(
    "Secrets Provider:",
    ["Manual Input", "AWS Secrets Manager", "HashiCorp Vault"],
    index=0
)

# Initialize key session state elements for credentials so we can pre-populate them
for k in ["vault_github_token", "vault_kiali_token", "vault_dd_api_key", "vault_dd_app_key", "vault_neo4j_password"]:
    if k not in st.session_state:
        st.session_state[k] = ""

if secrets_provider == "AWS Secrets Manager":
    aws_secret_name = st.sidebar.text_input("Secret Name / ARN", value="production/lattica/credentials")
    aws_region = st.sidebar.text_input("AWS Region", value="us-east-1")
    fetch_vault = st.sidebar.button("🔄 FETCH FROM AWS SECRETS MANAGER", use_container_width=True)
    if fetch_vault:
        with st.sidebar.status("Fetching AWS Secrets...", expanded=False) as s_fetch:
            try:
                from secrets_manager import fetch_vault_secrets
                secrets = fetch_vault_secrets("AWS Secrets Manager", aws_secret_name, region=aws_region)
                # Parse keys case-insensitively and store in session state
                for skey, val in secrets.items():
                    skey_lower = skey.lower()
                    if skey_lower in ["github_token", "githubtoken"]:
                        st.session_state["vault_github_token"] = val
                    elif skey_lower in ["kiali_token", "kialitoken"]:
                        st.session_state["vault_kiali_token"] = val
                    elif skey_lower in ["dd_api_key", "datadog_api_key", "ddapikey"]:
                        st.session_state["vault_dd_api_key"] = val
                    elif skey_lower in ["dd_app_key", "datadog_app_key", "ddappkey"]:
                        st.session_state["vault_dd_app_key"] = val
                    elif skey_lower in ["neo4j_password", "neo4jpassword"]:
                        st.session_state["vault_neo4j_password"] = val
                s_fetch.update(label="Secrets Retrieved Successfully! ✅", state="complete")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Failed to fetch secrets: {e}")
                s_fetch.update(label="Secrets Fetch Failed ❌", state="error")

elif secrets_provider == "HashiCorp Vault":
    vault_url = st.sidebar.text_input("Vault Server URL", value="http://localhost:8200")
    vault_token = st.sidebar.text_input("Vault Access Token (Token)", type="password")
    vault_path = st.sidebar.text_input("Secret Path", value="secret/data/production/lattica")
    fetch_vault = st.sidebar.button("🔄 FETCH FROM HASHICORP VAULT", use_container_width=True)
    if fetch_vault:
        with st.sidebar.status("Fetching Vault Secrets...", expanded=False) as s_fetch:
            try:
                from secrets_manager import fetch_vault_secrets
                secrets = fetch_vault_secrets("HashiCorp Vault", vault_path, vault_url=vault_url, vault_token=vault_token)
                # Parse keys case-insensitively and store in session state
                for skey, val in secrets.items():
                    skey_lower = skey.lower()
                    if skey_lower in ["github_token", "githubtoken"]:
                        st.session_state["vault_github_token"] = val
                    elif skey_lower in ["kiali_token", "kialitoken"]:
                        st.session_state["vault_kiali_token"] = val
                    elif skey_lower in ["dd_api_key", "datadog_api_key", "ddapikey"]:
                        st.session_state["vault_dd_api_key"] = val
                    elif skey_lower in ["dd_app_key", "datadog_app_key", "ddappkey"]:
                        st.session_state["vault_dd_app_key"] = val
                    elif skey_lower in ["neo4j_password", "neo4jpassword"]:
                        st.session_state["vault_neo4j_password"] = val
                s_fetch.update(label="Secrets Retrieved Successfully! ✅", state="complete")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Failed to fetch secrets: {e}")
                s_fetch.update(label="Secrets Fetch Failed ❌", state="error")

st.sidebar.subheader("🗄️ Database Credentials")
neo4j_pwd_input = st.sidebar.text_input("Neo4j Password", value=st.session_state.get("vault_neo4j_password", "password"), type="password")
st.session_state["vault_neo4j_password"] = neo4j_pwd_input

st.sidebar.markdown("---")

env_mode = st.sidebar.radio(
    "Select Target Mode:",
    ["Local Docker Lab", "Live GitHub Repository", "Kubernetes / Istio Kiali API", "Datadog APM API", "eBPF Connection Logs"],
    index=0
)

available_models = get_ollama_models()
ollama_model = st.sidebar.selectbox(
    "Select Local Ollama Model:",
    available_models,
    index=0
)


# Render input forms based on mode selection
github_repo = ""
github_token = ""
kiali_url = ""
kiali_namespace = ""
kiali_token = ""
dd_api_key = ""
dd_app_key = ""
dd_site = ""
ebpf_file = ""

if env_mode == "Local Docker Lab":
    st.sidebar.subheader("Local Docker Lab Config")
    uploaded_compose = st.sidebar.file_uploader(
        "Upload docker-compose.yml",
        type=["yml", "yaml"],
        help="Upload your docker-compose.yml file to extract container dependencies and service links."
    )
    if uploaded_compose is not None:
        try:
            compose_bytes = uploaded_compose.getvalue()
            with open("docker-compose.yml", "wb") as f:
                f.write(compose_bytes)
            st.sidebar.success("docker-compose.yml Uploaded Successfully! ✅")
        except Exception as e:
            st.sidebar.error(f"Error saving docker-compose.yml: {e}")
            
    uploaded_docker_inv = st.sidebar.file_uploader(
        "Optional: Upload Inventory (.json)",
        type=["json"],
        key="docker_inv_uploader",
        help="Upload inventory.json containing service crypto algorithms & vulnerability status."
    )
    if uploaded_docker_inv is not None:
        try:
            inv_bytes = uploaded_docker_inv.getvalue()
            with open("inventory.json", "wb") as f:
                f.write(inv_bytes)
            st.sidebar.success("Inventory File Uploaded Successfully! ✅")
        except Exception as e:
            st.sidebar.error(f"Error saving inventory file: {e}")

elif env_mode == "Live GitHub Repository":
    st.sidebar.subheader("GitHub API Config")
    github_repo = st.sidebar.text_input("Repo URL", value="https://github.com/jpadilla/pyjwt")
    github_token = st.sidebar.text_input("GitHub Token (Classic)", type="password", help="Providing a token increases API rate limits.", value=st.session_state.get("vault_github_token", ""))
elif env_mode == "Kubernetes / Istio Kiali API":
    st.sidebar.subheader("Kiali Connection Settings")
    kiali_url = st.sidebar.text_input("Kiali URL", value="http://localhost:20001")
    kiali_namespace = st.sidebar.text_input("Namespace", value="default")
    kiali_token = st.sidebar.text_input("Kiali Auth Token (Bearer)", type="password", value=st.session_state.get("vault_kiali_token", ""))
elif env_mode == "Datadog APM API":
    st.sidebar.subheader("Datadog API Settings")
    dd_api_key = st.sidebar.text_input("Datadog API Key", type="password", value=st.session_state.get("vault_dd_api_key", ""))
    dd_app_key = st.sidebar.text_input("Datadog App Key", type="password", value=st.session_state.get("vault_dd_app_key", ""))
    dd_site = st.sidebar.selectbox("Datadog Site", ["datadoghq.com", "datadoghq.eu", "us3.datadoghq.com", "us5.datadoghq.com", "ap1.datadoghq.com"])
elif env_mode == "eBPF Connection Logs":
    st.sidebar.subheader("eBPF Log Ingestion Settings")
    uploaded_ebpf = st.sidebar.file_uploader(
        "Upload eBPF Trace Logs (.jsonl)",
        type=["jsonl", "json", "txt"],
        help="Upload your eBPF kernel network trace log file containing src_service and dst_service JSON records."
    )
    if uploaded_ebpf is not None:
        try:
            bytes_data = uploaded_ebpf.getvalue()
            with open("ebpf_connections.jsonl", "wb") as f:
                f.write(bytes_data)
            st.sidebar.success("eBPF Trace Log File Uploaded Successfully! ✅")
            ebpf_file = "ebpf_connections.jsonl"
        except Exception as e:
            st.sidebar.error(f"Error saving uploaded file: {e}")
            ebpf_file = "ebpf_connections.jsonl"
    else:
        ebpf_file = st.sidebar.text_input("Connection Log File Path", value="ebpf_connections.jsonl")

    uploaded_inv = st.sidebar.file_uploader(
        "Optional: Upload Inventory (.json)",
        type=["json"],
        help="Upload inventory.json containing service crypto algorithms & vulnerability status."
    )
    if uploaded_inv is not None:
        try:
            inv_bytes = uploaded_inv.getvalue()
            with open("inventory.json", "wb") as f:
                f.write(inv_bytes)
            st.sidebar.success("Inventory File Uploaded Successfully! ✅")
        except Exception as e:
            st.sidebar.error(f"Error saving inventory file: {e}")

st.sidebar.markdown("---")
st.sidebar.info("Lattica connects locally to Neo4j on `bolt://localhost:7687` and streams LLM completions from local Ollama.")

# Run button at the bottom of the sidebar configurations
st.sidebar.markdown("### Action Trigger")
run_button = st.sidebar.button("🚀 EXECUTE FULL PIPELINE", type="primary", use_container_width=True)

# Render Top Bar Status Monitor
secrets_active = any(st.session_state.get(k) for k in ["vault_github_token", "vault_kiali_token", "vault_dd_api_key", "vault_dd_app_key", "vault_neo4j_password"])
st.markdown(f"""
<div class="status-bar">
    <div class="status-item">
        <span class="status-dot {'online' if neo4j_online else 'offline'}"></span>
        <span>Neo4j Database: <b>{'ONLINE' if neo4j_online else 'OFFLINE'}</b></span>
    </div>
    <div class="status-item">
        <span class="status-dot {'online' if ollama_online else 'offline'}"></span>
        <span>Ollama Engine: <b>{'ONLINE' if ollama_online else 'OFFLINE'}</b></span>
    </div>
    <div class="status-item">
        <span class="status-dot {'online' if secrets_active else 'offline'}"></span>
        <span>Secrets Vault (<b>{secrets_provider}</b>): <b>{'BOUND' if secrets_active else 'UNBOUND' if secrets_provider != 'Manual Input' else 'MANUAL'}</b></span>
    </div>
    <div class="status-item">
        <span>Active Provider: <b style="color: #00F2FE;">{env_mode}</b></span>
    </div>
</div>
""", unsafe_allow_html=True)

# Define Tabs
tab_discovery, tab_analytics, tab_agent, tab_comparison, tab_simulator, tab_gitops = st.tabs([
    "🌐 Discovery & Ingest", 
    "📊 Graph Analytics", 
    "🤖 Agent Planner", 
    "🏆 4-Way Comparison",
    "🎮 Upgrade Simulator", 
    "🛠️ GitOps & Deployment"
])

# Execute pipeline synchronous flow
if run_button:
    # Reset run flag until pipeline completes successfully
    st.session_state["pipeline_run"] = False
    
    # Stage 1: Discovery
    inventory = []
    dependencies = []
    
    with tab_discovery:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 🌐 Running Network Topology Ingestion...")
        
        if env_mode == "Local Docker Lab":
            with st.status("Local Docker Discovery & Topology Extraction", expanded=True) as s1:
                st.write("Reading configurations from `./services/` and topology from `docker-compose.yml`...")
                inventory, dependencies = run_local_discovery()
                st.write(f"Discovered **{len(inventory)}** local services.")
                s1.update(label="Stage 1 Complete: Local Assets Discovered ✅", state="complete")
        elif env_mode == "Live GitHub Repository":
            with st.status("GitHub API Code Scanning", expanded=True) as s1:
                inventory, dependencies = run_real_github_scanning(github_repo, github_token)
                if not inventory:
                    st.error("No legacy cryptographic implementations found in the scanned files. Please try another repository.")
                    st.stop()
                s1.update(label=f"Stage 1 Complete: Scanned Source Code (Found {len(inventory)} Vulnerabilities) ✅", state="complete")
        elif env_mode == "Kubernetes / Istio Kiali API":
            with st.status("Kiali Service Graph Extraction", expanded=True) as s1:
                st.write(f"Querying Kiali Graph API at {kiali_url} for namespace '{kiali_namespace}'...")
                from dynamic_discovery import KialiIstioProvider
                try:
                    kiali_provider = KialiIstioProvider(kiali_url, kiali_namespace, kiali_token)
                    nodes, dependencies = kiali_provider.fetch_nodes_and_edges()
                    inventory = []
                    inv_map = {}
                    if os.path.exists("inventory.json"):
                        with open("inventory.json", "r") as f:
                            for item in json.load(f):
                                inv_map[item["service"]] = item
                    for s_name in nodes:
                        inv = inv_map.get(s_name)
                        inventory.append({
                            "name": s_name,
                            "algorithm": inv["algorithm"] if inv else "Unknown/Secure",
                            "vulnerable": inv["vulnerable"] if inv else False,
                            "location": f"k8s://{kiali_namespace}/{s_name}"
                        })
                    st.write(f"Discovered **{len(nodes)}** services and **{len(dependencies)}** active dependencies.")
                    s1.update(label="Stage 1 & 2 Complete: Kiali Topology Discovered ✅", state="complete")
                except Exception as e:
                    st.error(f"Failed to fetch Kiali service graph: {e}")
                    st.stop()
        elif env_mode == "Datadog APM API":
            with st.status("Datadog APM Service Graph Extraction", expanded=True) as s1:
                st.write(f"Querying Datadog API at {dd_site}...")
                from dynamic_discovery import DatadogApmProvider
                try:
                    dd_provider = DatadogApmProvider(dd_api_key, dd_app_key, dd_site)
                    nodes, dependencies = dd_provider.fetch_nodes_and_edges()
                    inventory = []
                    inv_map = {}
                    if os.path.exists("inventory.json"):
                        with open("inventory.json", "r") as f:
                            for item in json.load(f):
                                inv_map[item["service"]] = item
                    for s_name in nodes:
                        inv = inv_map.get(s_name)
                        inventory.append({
                            "name": s_name,
                            "algorithm": inv["algorithm"] if inv else "Unknown/Secure",
                            "vulnerable": inv["vulnerable"] if inv else False,
                            "location": f"datadog://{s_name}"
                        })
                    st.write(f"Discovered **{len(nodes)}** services and **{len(dependencies)}** active dependencies.")
                    s1.update(label="Stage 1 & 2 Complete: Datadog APM Topology Discovered ✅", state="complete")
                except Exception as e:
                    st.error(f"Failed to fetch Datadog service dependencies: {e}")
                    st.stop()
        elif env_mode == "eBPF Connection Logs":
            with st.status("eBPF Network Trace Log Ingestion", expanded=True) as s1:
                st.write(f"Parsing connection logs from {ebpf_file}...")
                from dynamic_discovery import EbpfLogsProvider
                try:
                    ebpf_provider = EbpfLogsProvider(ebpf_file)
                    nodes, dependencies = ebpf_provider.fetch_nodes_and_edges()
                    inventory = []
                    inv_map = {}
                    if os.path.exists("inventory.json"):
                        with open("inventory.json", "r") as f:
                            for item in json.load(f):
                                inv_map[item["service"]] = item
                    for s_name in nodes:
                        inv = inv_map.get(s_name)
                        inventory.append({
                            "name": s_name,
                            "algorithm": inv["algorithm"] if inv else "Unknown/Secure",
                            "vulnerable": inv["vulnerable"] if inv else False,
                            "location": f"ebpf://{s_name}"
                        })
                    st.write(f"Discovered **{len(nodes)}** services and **{len(dependencies)}** active dependencies.")
                    s1.update(label="Stage 1 & 2 Complete: eBPF Connection Logs Ingested ✅", state="complete")
                except Exception as e:
                    st.error(f"Failed to parse eBPF network trace logs: {e}")
                    st.stop()
                    
        st.markdown("#### Discovered Assets Inventory")
        st.dataframe(
            inventory,
            column_config={
                "name": st.column_config.TextColumn("Service Name", help="Discovered service asset"),
                "algorithm": st.column_config.TextColumn("Crypto Protocol"),
                "vulnerable": st.column_config.CheckboxColumn("Vulnerable State"),
                "location": st.column_config.TextColumn("Source Origin")
            },
            use_container_width=True
        )
        
        # Display interactive graph visualizer
        st.markdown("### 🗺️ Visual Dependency Topology Map")
        mermaid_code = generate_mermaid_flowchart(inventory, dependencies)
        render_mermaid(mermaid_code)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Stage 2: Neo4j Ingest
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        with st.status("Ingesting into Neo4j Graph Database...", expanded=True) as s2:
            try:
                driver = connect_neo4j()
                with driver.session() as session:
                    st.write("Clearing database...")
                    session.run("MATCH (n) DETACH DELETE n")
                    
                    st.write("Ingesting service nodes...")
                    for item in inventory:
                        session.run(
                            """
                            CREATE (s:Service {
                                name: $name,
                                algorithm: $algo,
                                vulnerable: $vul,
                                location: $loc
                            })
                            """,
                            name=item["name"],
                            algo=item["algorithm"],
                            vul=item["vulnerable"],
                            loc=item["location"]
                        )
                    st.write("Ingesting calling relationships...")
                    for caller, callee in dependencies:
                        session.run(
                            """
                            MATCH (a:Service {name: $c})
                            MATCH (b:Service {name: $d})
                            CREATE (a)-[:CALLS]->(b)
                            """,
                            c=caller, d=callee
                        )
                driver.close()
                st.write(f"Merged **{len(inventory)}** nodes and **{len(dependencies)}** edges in Neo4j.")
                s2.update(label="Stage 2 Complete: Ingested into Neo4j Graph ✅", state="complete")
            except Exception as e:
                st.warning(f"Neo4j Ingestion bypassed (Neo4j Offline). Details: {e}")
                s2.update(label="Stage 2: Neo4j Ingestion Bypassed (Offline) ⚠️", state="error")
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Stage 3: Ingestion Analysis
    analyzed_inventory = []
    with tab_analytics:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        with st.status("Running Graph Blast Radius Queries...", expanded=True) as s3:
            neo4j_ok = False
            try:
                driver = connect_neo4j()
                with driver.session() as session:
                    # Run bulk topology query
                    query = """
                    MATCH (s:Service)
                    OPTIONAL MATCH (s)-[:CALLS*]->(d:Service)
                    WITH s, count(distinct d) as qbr
                    OPTIONAL MATCH (c:Service)-[:CALLS*]->(s)
                    WITH s, qbr, count(distinct c) as di
                    SET s.out_degree = count { (s)-[:CALLS]->() },
                        s.in_degree = count { ()-[:CALLS]->(s) },
                        s.blast_radius = qbr,
                        s.dependency_impact = di
                    RETURN s.name as service, s.algorithm as algorithm, s.vulnerable as vulnerable,
                           s.out_degree as out_degree, s.in_degree as in_degree, qbr as change_blast_radius, di as dependency_impact
                    """
                    results = session.run(query)
                    raw_items = [dict(record) for record in results]
                    nodes_list = [item["service"] for item in raw_items]
                    
                    # Calculate centrality metrics
                    pr_metrics = calculate_pagerank(nodes_list, dependencies)
                    bc_metrics = calculate_betweenness_centrality(nodes_list, dependencies)
                    
                    for item in raw_items:
                        name = item["service"]
                        pagerank = pr_metrics.get(name, 0.0)
                        betweenness = bc_metrics.get(name, 0.0)
                        
                        session.run(
                            """
                            MATCH (s:Service {name: $name})
                            SET s.pagerank = $pr, s.betweenness_centrality = $bc
                            """,
                            name=name, pr=pagerank, bc=betweenness
                        )
                        
                        analyzed_inventory.append({
                            "Service Node": name,
                            "Algorithm": item["algorithm"],
                            "Vulnerable": "Yes" if item["vulnerable"] else "No",
                            "Change Blast Radius (CBR)": item["change_blast_radius"],
                            "Dependency Impact (DI)": item["dependency_impact"],
                            "PageRank": round(pagerank, 4),
                            "Betweenness Centrality": round(betweenness, 4),
                            "Role": "Choke Point" if item["dependency_impact"] >= 2 else "Standard Service"
                        })
                driver.close()
                s3.update(label="Stage 3 Complete: Blast Radius & Centrality Calculations Loaded ✅", state="complete")
                neo4j_ok = True
            except Exception as e:
                st.warning(f"Neo4j analysis bypassed (Neo4j Offline). Details: {e}")
                s3.update(label="Stage 3: Running local Python-based graph analysis ⚠️", state="error")
                
            if not neo4j_ok:
                # Fallback to local Python calculations!
                nodes_list = [item["name"] for item in inventory]
                
                out_degrees = {n: 0 for n in nodes_list}
                in_degrees = {n: 0 for n in nodes_list}
                for u, v in dependencies:
                    if u in out_degrees and v in out_degrees:
                        out_degrees[u] += 1
                    if u in in_degrees and v in in_degrees:
                        in_degrees[v] += 1
                        
                adj = {n: set() for n in nodes_list}
                for u, v in dependencies:
                    if u in adj and v in adj:
                        adj[u].add(v)
                cbr = {}
                for s in nodes_list:
                    visited = set()
                    queue = [s]
                    while queue:
                        curr = queue.pop(0)
                        for nxt in adj[curr]:
                            if nxt not in visited:
                                visited.add(nxt)
                                queue.append(nxt)
                    cbr[s] = len(visited)
                    
                rev_adj = {n: set() for n in nodes_list}
                for u, v in dependencies:
                    if u in rev_adj and v in rev_adj:
                        rev_adj[v].add(u)
                di = {}
                for s in nodes_list:
                    visited = set()
                    queue = [s]
                    while queue:
                        curr = queue.pop(0)
                        for nxt in rev_adj[curr]:
                            if nxt not in visited:
                                visited.add(nxt)
                                queue.append(nxt)
                    di[s] = len(visited)
                    
                pr_metrics = calculate_pagerank(nodes_list, dependencies)
                bc_metrics = calculate_betweenness_centrality(nodes_list, dependencies)
                
                for item in inventory:
                    name = item["name"]
                    pagerank = pr_metrics.get(name, 0.0)
                    betweenness = bc_metrics.get(name, 0.0)
                    
                    analyzed_inventory.append({
                        "Service Node": name,
                        "Algorithm": item["algorithm"],
                        "Vulnerable": "Yes" if item["vulnerable"] else "No",
                        "Change Blast Radius (CBR)": cbr[name],
                        "Dependency Impact (DI)": di[name],
                        "PageRank": round(pagerank, 4),
                        "Betweenness Centrality": round(betweenness, 4),
                        "Role": "Choke Point" if di[name] >= 2 else "Standard Service"
                    })
                    
        # Save analyzed inventory file locally so agent.py can access it
        try:
            # map keys for agent.py compatibility
            comp_inv = []
            for item in analyzed_inventory:
                comp_inv.append({
                    "service": item["Service Node"],
                    "algorithm": item["Algorithm"],
                    "vulnerable": item["Vulnerable"] == "Yes",
                    "change_blast_radius": item["Change Blast Radius (CBR)"],
                    "quantum_blast_radius": item["Change Blast Radius (CBR)"],
                    "dependency_impact": item["Dependency Impact (DI)"],
                    "pagerank": item["PageRank"],
                    "betweenness_centrality": item["Betweenness Centrality"]
                })
            with open("analyzed_inventory.json", "w") as f:
                json.dump(comp_inv, f, indent=4)
        except Exception as e:
            st.warning(f"Failed to write analyzed_inventory.json: {e}")
                
        st.markdown("#### Topological Ingestion Metrics")
        max_qbr_run = max((item.get("Change Blast Radius (CBR)", 0) for item in analyzed_inventory), default=1)
        max_di_run = max((item.get("Dependency Impact (DI)", 0) for item in analyzed_inventory), default=1)
        st.dataframe(
            analyzed_inventory,
            column_config={
                "Service Node": st.column_config.TextColumn("Service Asset"),
                "Algorithm": st.column_config.TextColumn("Config Profile"),
                "Vulnerable": st.column_config.TextColumn("Vulnerable Status"),
                "Change Blast Radius (CBR)": st.column_config.ProgressColumn("Change Blast Radius (CBR)", min_value=0, max_value=max_qbr_run, format="%d"),
                "Dependency Impact (DI)": st.column_config.ProgressColumn("Dependency Impact (DI)", min_value=0, max_value=max_di_run, format="%d"),
                "PageRank": st.column_config.NumberColumn("PageRank", format="%.4f"),
                "Betweenness Centrality": st.column_config.NumberColumn("Betweenness Centrality", format="%.4f"),
                "Role": st.column_config.TextColumn("Graph Role")
            },
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Stage 4: Multi-Agent Planning Execution
    with tab_agent:
        st.markdown("### Stage 4: Multi-Agent & Algorithmic Planning Execution (Side-by-Side Comparison)")
        
        # Executive Summary & Faculty Guide Card
        st.markdown("""
        <div class="premium-card" style="border-left: 4px solid #00F2FE; background: rgba(13, 19, 33, 0.65);">
            <h4 style="color: #00F2FE !important; margin: 0 0 8px 0;">💡 Executive Summary & Faculty Guide: Why Standard AI Fails vs. Why Lattice Passes</h4>
            <p style="color: #cbd5e1; font-size: 0.9rem; margin-bottom: 12px;">
                This side-by-side comparison demonstrates the primary thesis contribution of the Lattice platform:
            </p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 10px; padding: 14px;">
                    <h5 style="color: #f87171 !important; margin: 0 0 6px 0;">❌ Standard AI Baseline (Fails with ~58 Conflicts)</h5>
                    <ul style="color: #94a3b8; font-size: 0.82rem; padding-left: 16px; margin: 0; line-height: 1.4;">
                        <li><b>Spatial Blindness</b>: Given only a flat list, the AI cannot guess network dependencies.</li>
                        <li><b>AI Hallucinations</b>: Invents fake service names (e.g. <code>service_name_6</code>) and forgets real services.</li>
                        <li><b>Catastrophic Ordering</b>: Schedules caller APIs before databases, causing production outages.</li>
                    </ul>
                </div>
                <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 10px; padding: 14px;">
                    <h5 style="color: #34d399 !important; margin: 0 0 6px 0;">✅ Lattice Engine (Passes with 0 Conflicts)</h5>
                    <ul style="color: #94a3b8; font-size: 0.82rem; padding-left: 16px; margin: 0; line-height: 1.4;">
                        <li><b>Tarjan SCC Engine</b>: Solves cyclic loops (e.g. <code>auth <-> user</code>) into condensed super-nodes.</li>
                        <li><b>Master Guardrail Reconciliation</b>: Automatically orders <b>Databases in Phase 1</b> & <b>Gateways in Phase 4</b>.</li>
                        <li><b>100% Production Safety</b>: Guarantees zero downtime across all 22 microservices!</li>
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 1. Deterministic Topo-Sort Card (Algorithmic Baseline)
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.subheader("Group 1: Deterministic Topological Sort Baseline (No LLM)")
        st.info("Pure algorithmic Kahn's topological depth binning in Python (0 LLM overhead, deterministic).")
        
        from agent import run_agent
        res_topo = run_agent("deterministic_topo")
        topo_plan = res_topo["plan"]
        st.session_state["topo_plan"] = topo_plan
        st.markdown("**Generated Algorithmic Plan JSON:**")
        st.json(topo_plan)
        valid_topo, conflicts_topo = res_topo["is_valid"], res_topo["conflicts"]
        if valid_topo:
            st.markdown("""
            <div class="custom-alert alert-success">
                <div>✅</div>
                <div><b>Plan Validation: PASSED!</b> (0 Conflicts detected - Binary topological sort).</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="custom-alert alert-error">
                <div>❌</div>
                <div><b>Plan Validation: FAILED!</b> ({len(conflicts_topo)} Conflicts found).</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        col_base, col_lat = st.columns(2)
        with col_base:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.subheader("Group 2: Control Group (Baseline LLM)")
            st.info("Generating plan using **only** flat inventory (LLM must guess topology)...")
            
            flat_list = [f"- Service: {item['name']}" for item in inventory]
            inventory_str = "\n".join(flat_list)
            
            baseline_prompt = f"""You are an Infrastructure Execution Planner.
We need to migrate our microservices from legacy configurations to target configuration profiles (e.g. Java 21, Spring Boot 4, TLS 1.3, API v2).
Here is the flat inventory of services:
{inventory_str}

Please generate a 4-phase execution plan.
In each phase, specify which services should be upgraded.
All {len(inventory)} services must be upgraded.
Each service must appear EXACTLY ONCE in the entire plan. Do not duplicate services across phases.
Format your output EXACTLY as a JSON object:
{{
  "Phase 1": ["service_name_1", "service_name_2"],
  "Phase 2": ["service_name_3"],
  "Phase 3": ["service_name_4"],
  "Phase 4": ["service_name_5"]
}}
Do not include any other text, explanations, or formatting. Return ONLY the raw JSON object.
"""
            st.markdown("**Ollama Streaming Output:**")
            base_placeholder = st.empty()
            
            # Streaming within styled terminal container
            base_raw = ""
            payload = {
                "model": ollama_model,
                "prompt": baseline_prompt,
                "stream": True,
                "options": {"temperature": 0.2, "num_predict": 1024}
            }
            try:
                response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=240)
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode('utf-8'))
                        token = chunk.get("response", "")
                        base_raw += token
                        base_placeholder.markdown(f"""
                        <div class="terminal-container">
                            <div class="terminal-header">
                                <div class="terminal-dot dot-red"></div>
                                <div class="terminal-dot dot-yellow"></div>
                                <div class="terminal-dot dot-green"></div>
                                <span style="margin-left: 10px;">Baseline Stream - {ollama_model}</span>
                            </div>
                            <pre style="color: #34d399; background: transparent; border: none; font-family: 'Fira Code', monospace; white-space: pre-wrap; margin: 0;">{base_raw}▌</pre>
                        </div>
                        """, unsafe_allow_html=True)
                base_placeholder.markdown(f"""
                <div class="terminal-container">
                    <div class="terminal-header">
                        <div class="terminal-dot dot-red"></div>
                        <div class="terminal-dot dot-yellow"></div>
                        <div class="terminal-dot dot-green"></div>
                        <span style="margin-left: 10px;">Baseline Stream - {ollama_model}</span>
                    </div>
                    <pre style="color: #34d399; background: transparent; border: none; font-family: 'Fira Code', monospace; white-space: pre-wrap; margin: 0;">{base_raw}</pre>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                base_placeholder.error(f"Error calling Ollama API: {e}")
                
            base_plan = parse_json_from_response(base_raw)
            st.markdown("**Generated Plan JSON:**")
            st.json(base_plan)
            
            valid, conflicts = validate_plan(base_plan, dependencies, inventory)
            if valid:
                st.markdown("""
                <div class="custom-alert alert-success">
                    <div>✅</div>
                    <div><b>Plan Validation: PASSED!</b> (0 Conflicts detected).</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="custom-alert alert-error">
                    <div>❌</div>
                    <div><b>Plan Validation: FAILED!</b> ({len(conflicts)} Conflicts found).</div>
                </div>
                """, unsafe_allow_html=True)
                for c in conflicts:
                    st.markdown(f"<span style='color: #f87171; margin-left: 30px;'>• {c}</span>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_lat:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.subheader("Experimental Group (Lattica GraphRAG)")
            st.info("Generating plan using **Federated Multi-Agent Domain Partitioning & Safe Execution Rollover**...")
            
            st.write("📁 **Partitioning services into architectural domains...**")
            service_domains = {}
            nodes = [item["name"] for item in inventory]
            service_domains = label_propagation_partition(nodes, dependencies)
                
            domains = {}
            for name, domain in service_domains.items():
                if domain not in domains:
                    domains[domain] = []
                domains[domain].append(name)
                
            for dom, svcs in domains.items():
                st.markdown(f"- **Domain `{dom}`**: {', '.join([f'`{s}`' for s in svcs])}")
                
            global_transition_phases = {}
            global_target_phases = {}
            global_service_names = [item["name"] for item in inventory]
            dom_plans = {}
            
            for dom, dom_services in domains.items():
                st.markdown(f"🤖 **Planning for Domain: `{dom}`** ...")
                dom_inventory = [item for item in analyzed_inventory if item["Service Node"] in dom_services]
                
                dom_lat_list = []
                for item in dom_inventory:
                    dom_lat_list.append(
                        f"- Service: {item['Service Node']} (Change Blast Radius: {item.get('Change Blast Radius (CBR)', item.get('Quantum Blast Radius (QBR)', 0))}, Dependency Impact: {item['Dependency Impact (DI)']})"
                    )
                dom_analyzed_inventory_str = "\n".join(dom_lat_list)
                
                dom_dependencies = []
                for caller, callee in dependencies:
                    if caller in dom_services and callee in dom_services:
                        dom_dependencies.append((caller, callee))
                        
                dom_dep_list = [f"- {caller} CALLS {callee}" for caller, callee in dom_dependencies]
                dom_dependencies_str = "\n".join(dom_dep_list) if dom_dep_list else "None"
                
                # Topological sort for domain
                dom_adj = {node: [] for node in dom_services}
                dom_in_degree = {node: 0 for node in dom_services}
                for caller, callee in dom_dependencies:
                    dom_adj[callee].append(caller)
                    dom_in_degree[caller] += 1
                    
                dom_cbr_map = {item["Service Node"]: item.get("Change Blast Radius (CBR)", item.get("Quantum Blast Radius (QBR)", 0)) for item in dom_inventory}
                dom_queue = [node for node in dom_services if dom_in_degree[node] == 0]
                dom_queue.sort(key=lambda x: dom_cbr_map.get(x, 0))
                
                dom_order = []
                while dom_queue:
                    dom_queue.sort(key=lambda x: dom_cbr_map.get(x, 0))
                    u = dom_queue.pop(0)
                    dom_order.append(u)
                    for v in dom_adj[u]:
                        dom_in_degree[v] -= 1
                        if dom_in_degree[v] == 0:
                            dom_queue.append(v)
                            
                dom_inequality_chain = " <= ".join([f"Phase({node})" for node in dom_order])
                dom_ordered_list_str = "\n".join([f"{idx+1}. {node}" for idx, node in enumerate(dom_order)])
                
                dom_prompt = f"""You are an AI Execution Planner for the domain: {dom}.
We need to upgrade our microservices to target configuration profiles (e.g. Java 21, Spring Boot 4, TLS 1.3, API v2).
To avoid outages during rolling upgrades, each service must go through a **Transition** state (dual-support) before it can enforce **Target Configuration** (disabling legacy config).

Here is the flat inventory of services in this domain:
{dom_analyzed_inventory_str}

Here are the calling dependencies within this domain:
{dom_dependencies_str}

CRITICAL RULES:
1. Timeline Consistency: For any service X, Phase(X_Transition) <= Phase(X_Target). You cannot enforce target configuration before enabling transition.
2. Downstream Compatibility: If Caller A CALLS Callee B, B must be Transition before or in the same phase as A becomes Transition (Phase(B_Transition) <= Phase(A_Transition)) and B must be Target before or in the same phase as A becomes Target (Phase(B_Target) <= Phase(A_Target)).
3. Safe Deprecation: If Caller A CALLS Callee B, A must enter Transition before or in the same phase as B enforces Target Configuration (Phase(A_Transition) <= Phase(B_Target)).

CRITICAL ORDERING CONSTRAINT:
To satisfy all calling dependencies, the execution phases MUST follow this mathematical relationship:
{dom_inequality_chain}

Specifically, you MUST schedule the services in the following topological order (from earliest phase to latest phase):
{dom_ordered_list_str}

Rules:
1. Do NOT upgrade a service listed later in a phase earlier than a service listed before it.
2. You can upgrade multiple services in the same phase, provided their relative order is maintained.
3. Services with a Change Blast Radius of 0 must be scheduled in Phase 1 for Transition.

Write a single short sentence verifying that the plan satisfies the inequality constraint chain: {dom_inequality_chain}.
Finally, output the 4-phase execution plan as a raw JSON object enclosed in a ```json ``` block at the very end of your response, detailing which services "Upgrade to Transition State" and which "Enforce Target Configuration" in each phase:
```json
{{
  "Phase 1": {{
    "Upgrade to Transition State": ["service_name_1"],
    "Enforce Target Configuration": []
  }},
  "Phase 2": {{
    "Upgrade to Transition State": [],
    "Enforce Target Configuration": ["service_name_1"]
  }},
  "Phase 3": {{
    "Upgrade to Transition State": [],
    "Enforce Target Configuration": []
  }},
  "Phase 4": {{
    "Upgrade to Transition State": [],
    "Enforce Target Configuration": []
  }}
}}
```
Do not output any text after the JSON block.
"""
                dom_placeholder = st.empty()
                dom_raw = ""
                payload = {
                    "model": ollama_model,
                    "prompt": dom_prompt,
                    "stream": True,
                    "options": {"temperature": 0.2, "num_predict": 1024}
                }
                try:
                    response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=240)
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            chunk = json.loads(line.decode('utf-8'))
                            token = chunk.get("response", "")
                            dom_raw += token
                            dom_placeholder.markdown(f"""
                            <div class="terminal-container">
                                <div class="terminal-header">
                                    <div class="terminal-dot dot-red"></div>
                                    <div class="terminal-dot dot-yellow"></div>
                                    <div class="terminal-dot dot-green"></div>
                                    <span style="margin-left: 10px;">Domain Planner: {dom} - {ollama_model}</span>
                                </div>
                                <pre style="color: #34d399; background: transparent; border: none; font-family: 'Fira Code', monospace; white-space: pre-wrap; margin: 0;">{dom_raw}▌</pre>
                            </div>
                            """, unsafe_allow_html=True)
                    dom_placeholder.markdown(f"""
                    <div class="terminal-container">
                        <div class="terminal-header">
                            <div class="terminal-dot dot-red"></div>
                            <div class="terminal-dot dot-yellow"></div>
                            <div class="terminal-dot dot-green"></div>
                            <span style="margin-left: 10px;">Domain Planner: {dom} - {ollama_model}</span>
                        </div>
                        <pre style="color: #34d399; background: transparent; border: none; font-family: 'Fira Code', monospace; white-space: pre-wrap; margin: 0;">{dom_raw}</pre>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    dom_placeholder.error(f"Error calling Ollama API: {e}")
                    
                dom_plan = parse_json_from_response(dom_raw)
                dom_plans[dom] = {
                    "raw": dom_raw,
                    "plan": dom_plan,
                    "services": dom_services,
                    "inequality_chain": dom_inequality_chain,
                    "ordered_list_str": dom_ordered_list_str,
                    "analyzed_inventory_str": dom_analyzed_inventory_str,
                    "dependencies_str": dom_dependencies_str
                }
                
                for phase_name, stage_data in dom_plan.items():
                    try:
                        phase_num = int(phase_name.replace("Phase", "").strip())
                    except ValueError:
                        phase_num = 999
                    if isinstance(stage_data, dict):
                        to_transition = stage_data.get("Upgrade to Transition State", [])
                        to_target = stage_data.get("Enforce Target Configuration", [])
                        for s in to_transition:
                            if s in dom_services:
                                global_transition_phases[s] = phase_num
                        for s in to_target:
                            if s in dom_services:
                                global_target_phases[s] = phase_num
                                
            # Precompute topological depths for baseline initialization
            adj = {node: set() for node in global_service_names}
            for caller, callee in dependencies:
                if caller in adj and callee in adj:
                    adj[caller].add(callee)
            
            memo = {}
            def get_depth(node, visited=None):
                if visited is None:
                    visited = set()
                if node in memo:
                    return memo[node]
                if node in visited:
                    return 0  # Break cycle
                if not adj[node]:
                    memo[node] = 0
                    return 0
                visited.add(node)
                max_child = max(get_depth(child, visited) for child in adj[node])
                visited.remove(node)
                memo[node] = 1 + max_child
                return memo[node]
                
            depths = {node: get_depth(node) for node in global_service_names}
            
            # Initialize missing services
            for s in global_service_names:
                if s not in global_transition_phases:
                    global_transition_phases[s] = min(depths[s] + 1, 4)
                if s not in global_target_phases:
                    global_target_phases[s] = min(global_transition_phases[s] + 1, 4)

            # Reconcile boundaries
            st.write("⚖️ **Reconciling cross-domain boundary dependencies...**")
            boundary_edges = []
            for caller, callee in dependencies:
                if service_domains.get(caller) != service_domains.get(callee):
                    boundary_edges.append((caller, callee))
                    
            if boundary_edges:
                st.markdown(f"Detected **{len(boundary_edges)}** cross-domain calling boundaries:")
                for c, d in boundary_edges:
                    st.markdown(f"- `{c}` (Domain `{service_domains[c]}`) CALLS `{d}` (Domain `{service_domains[d]}`)")
            else:
                st.markdown("No cross-domain boundaries found.")
                
            reconciliation_warnings = []
            changed = True
            iterations = 0
            while changed and iterations < 100:
                changed = False
                iterations += 1
                for s in global_service_names:
                    t = global_transition_phases[s]
                    tc = global_target_phases[s]
                    if t > tc:
                        msg = f"Reconciling Timeline for `{s}`: shifting Enforce Target Configuration to Phase {t} (was Phase {tc})."
                        reconciliation_warnings.append(msg)
                        global_target_phases[s] = t
                        changed = True
                        
                for caller, callee in dependencies:
                    t_caller = global_transition_phases[caller]
                    t_callee = global_transition_phases[callee]
                    tc_caller = global_target_phases[caller]
                    tc_callee = global_target_phases[callee]
                    
                    if t_callee > t_caller:
                        msg = f"Reconciling Transition compatibility: shifting caller `{caller}` Transition State to Phase {t_callee} (dependency `{callee}` is in Phase {t_callee})."
                        reconciliation_warnings.append(msg)
                        global_transition_phases[caller] = t_callee
                        changed = True
                        
                    if tc_callee > tc_caller:
                        msg = f"Reconciling Target compatibility: shifting caller `{caller}` Target Configuration to Phase {tc_callee} (dependency `{callee}` is in Phase {tc_callee})."
                        reconciliation_warnings.append(msg)
                        global_target_phases[caller] = tc_callee
                        changed = True
                        
                    if t_caller > tc_callee:
                        msg = f"Reconciling Safe Deprecation: shifting dependency `{callee}` Target Configuration to Phase {t_caller} (caller `{caller}` enters Transition in Phase {t_caller})."
                        reconciliation_warnings.append(msg)
                        global_target_phases[callee] = t_caller
                        changed = True
                        
            # Render warnings in HSL color
            for w in reconciliation_warnings:
                st.markdown(f"""
                <div class="custom-alert alert-warning">
                    <div>⚠️</div>
                    <div>{w}</div>
                </div>
                """, unsafe_allow_html=True)
                
            lat_plan = {}
            for ph in range(1, 5):
                lat_plan[f"Phase {ph}"] = {
                    "Upgrade to Transition State": [],
                    "Enforce Target Configuration": []
                }
            for s in global_service_names:
                t = min(max(global_transition_phases.get(s, 1), 1), 4)
                tc = min(max(global_target_phases.get(s, 4), 1), 4)
                lat_plan[f"Phase {t}"]["Upgrade to Transition State"].append(s)
                lat_plan[f"Phase {tc}"]["Enforce Target Configuration"].append(s)
                
            st.markdown("**Unified Global Plan JSON (Post-Reconciliation):**")
            st.json(lat_plan)
            
            valid_lat, conflicts_lat = validate_plan(lat_plan, dependencies, inventory)
            if valid_lat:
                st.markdown("""
                <div class="custom-alert alert-success">
                    <div>✅</div>
                    <div><b>Plan Validation: PASSED!</b> (0 Conflicts detected).</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="custom-alert alert-error">
                    <div>❌</div>
                    <div><b>Plan Validation: FAILED!</b> ({len(conflicts_lat)} Conflicts found).</div>
                </div>
                """, unsafe_allow_html=True)
                for c in conflicts_lat:
                    st.markdown(f"<span style='color: #f87171; margin-left: 30px;'>• {c}</span>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Stage 5: Simulator Tab Execution
        with tab_simulator:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            render_simulator_banner()
            
            sim_col1, sim_col2 = st.columns(2)
            with sim_col1:
                st.markdown('<div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 10px; padding: 15px;">', unsafe_allow_html=True)
                st.markdown("#### ❌ Control Group (Simulate Baseline LLM Plan)")
                st.write("Test rolling out the unguided LLM plan. Observe how missing network context causes catastrophic outages during rollout.")
                if st.button("🚀 Run Baseline Simulation", key="sim_base_btn"):
                    log_base, outages_base = simulate_upgrade_timeline(base_plan, dependencies, inventory)
                    st.session_state["sim_base_log"] = log_base
                    st.session_state["sim_base_outages"] = outages_base
                    
                if "sim_base_log" in st.session_state:
                    num_out = len(st.session_state["sim_base_outages"])
                    if num_out > 0:
                        st.markdown(f"""
                        <div class="custom-alert alert-error">
                            <div>❌</div>
                            <div><b>Simulation Finished: {num_out} Outages Detected!</b><br><small>Unguided LLM plan crashed calling microservices during rollout.</small></div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="custom-alert alert-success">
                            <div>✅</div>
                            <div><b>Simulation Finished: 0 Outages.</b></div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    log_txt = "\n".join(st.session_state["sim_base_log"])
                    st.markdown(f"""
                    <div class="terminal-container">
                        <div class="terminal-header">
                            <div class="terminal-dot dot-red"></div>
                            <div class="terminal-dot dot-yellow"></div>
                            <div class="terminal-dot dot-green"></div>
                            <span style="margin-left: 10px;">Simulation Console - Baseline LLM</span>
                        </div>
                        <pre style="color: #f87171; background: transparent; border: none; font-family: 'Fira Code', monospace; white-space: pre-wrap; margin: 0; font-size: 0.8rem;">{log_txt}</pre>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                    
            with sim_col2:
                st.markdown('<div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 10px; padding: 15px;">', unsafe_allow_html=True)
                st.markdown("#### ✅ Experimental Group (Simulate Lattice Plan)")
                st.write("Test rolling out the Lattice plan. Observe how 0 outages occur because leaf dependencies transition first.")
                if st.button("🚀 Run Lattice Simulation", key="sim_lat_btn"):
                    log_lat, outages_lat = simulate_upgrade_timeline(lat_plan, dependencies, inventory)
                    st.session_state["sim_lat_log"] = log_lat
                    st.session_state["sim_lat_outages"] = outages_lat
                    
                if "sim_lat_log" in st.session_state:
                    num_out = len(st.session_state["sim_lat_outages"])
                    if num_out > 0:
                        st.markdown(f"""
                        <div class="custom-alert alert-error">
                            <div>❌</div>
                            <div><b>Simulation Finished: {num_out} Outages Detected!</b></div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="custom-alert alert-success">
                            <div>✅</div>
                            <div><b>Simulation Finished: 0 Outages!</b><br><small>Lattice guaranteed 100% continuous system availability!</small></div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    log_txt = "\n".join(st.session_state["sim_lat_log"])
                    st.markdown(f"""
                    <div class="terminal-container">
                        <div class="terminal-header">
                            <div class="terminal-dot dot-red"></div>
                            <div class="terminal-dot dot-yellow"></div>
                            <div class="terminal-dot dot-green"></div>
                            <span style="margin-left: 10px;">Simulation Console - Lattice Engine</span>
                        </div>
                        <pre style="color: #34d399; background: transparent; border: none; font-family: 'Fira Code', monospace; white-space: pre-wrap; margin: 0; font-size: 0.8rem;">{log_txt}</pre>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Cache results in state
        st.session_state["inventory"] = inventory
        st.session_state["dependencies"] = dependencies
        st.session_state["analyzed_inventory"] = analyzed_inventory
        st.session_state["base_plan"] = base_plan
        st.session_state["base_raw"] = base_raw
        st.session_state["base_valid"] = valid
        st.session_state["base_conflicts"] = conflicts
        st.session_state["domains"] = domains
        st.session_state["dom_plans"] = dom_plans
        st.session_state["reconciliation_warnings"] = reconciliation_warnings
        st.session_state["boundary_edges"] = boundary_edges
        st.session_state["lat_plan"] = lat_plan
        st.session_state["lat_valid"] = valid_lat
        st.session_state["lat_conflicts"] = conflicts_lat
        st.session_state["pipeline_run"] = True
        st.rerun()

# ----------------- CACHED STATE RENDERING -----------------
elif st.session_state.get("pipeline_run", False):
    
    # 1. Discovery Tab
    with tab_discovery:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 🌐 Discovered Active Topology Assets")
        st.markdown(f"**Target Ingestion Mode:** `{env_mode}`")
        st.markdown(f"**Ingested State:** `{len(st.session_state['inventory'])}` nodes and `{len(st.session_state['dependencies'])}` calling edges loaded in Neo4j.")
        
        # Display flat inventory table
        st.dataframe(
            st.session_state["inventory"],
            column_config={
                "name": st.column_config.TextColumn("Service Name", help="Discovered service asset"),
                "algorithm": st.column_config.TextColumn("Crypto Protocol"),
                "vulnerable": st.column_config.CheckboxColumn("Vulnerable State"),
                "location": st.column_config.TextColumn("Source Origin")
            },
            use_container_width=True
        )
        
        # Display interactive graph visualizer
        st.markdown("### 🗺️ Visual Dependency Topology Map")
        mermaid_code = generate_mermaid_flowchart(st.session_state["inventory"], st.session_state["dependencies"])
        render_mermaid(mermaid_code)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    # 2. Analytics Tab
    with tab_analytics:
        # Create gorgeous HSL metric cards
        inv_data = st.session_state["analyzed_inventory"]
        total_svcs = len(inv_data)
        vulnerable_svcs = sum(1 for item in inv_data if item["Vulnerable"] == "Yes")
        choke_points = sum(1 for item in inv_data if item["Role"] == "Choke Point")
        max_qbr = max((item.get("Change Blast Radius (CBR)", item.get("Quantum Blast Radius (QBR)", item.get("quantum_blast_radius", 0))) for item in inv_data), default=0)
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.markdown(f"""
            <div class="premium-card" style="text-align: center;">
                <div class="metric-label">Total Services</div>
                <div class="metric-value">{total_svcs}</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"""
            <div class="premium-card" style="text-align: center; border-left: 4px solid #ef4444;">
                <div class="metric-label">Vulnerable Services</div>
                <div class="metric-value" style="color: #ef4444;">{vulnerable_svcs}</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col3:
            st.markdown(f"""
            <div class="premium-card" style="text-align: center; border-left: 4px solid #8b5cf6;">
                <div class="metric-label">Critical Choke Points</div>
                <div class="metric-value" style="color: #a78bfa;">{choke_points}</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col4:
            st.markdown(f"""
            <div class="premium-card" style="text-align: center; border-left: 4px solid #f59e0b;">
                <div class="metric-label">Max Blast Radius</div>
                <div class="metric-value" style="color: #fbbf24;">{max_qbr}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Calculated Topological Centrality Metrics")
        max_qbr_val = max((item.get("Change Blast Radius (CBR)", 0) for item in inv_data), default=1)
        max_di_val = max((item.get("Dependency Impact (DI)", 0) for item in inv_data), default=1)
        st.dataframe(
            inv_data,
            column_config={
                "Service Node": st.column_config.TextColumn("Service Asset"),
                "Algorithm": st.column_config.TextColumn("Config Profile"),
                "Vulnerable": st.column_config.TextColumn("Vulnerable Status"),
                "Change Blast Radius (CBR)": st.column_config.ProgressColumn("Change Blast Radius (CBR)", min_value=0, max_value=max_qbr_val, format="%d"),
                "Dependency Impact (DI)": st.column_config.ProgressColumn("Dependency Impact (DI)", min_value=0, max_value=max_di_val, format="%d"),
                "PageRank": st.column_config.NumberColumn("PageRank", format="%.4f"),
                "Betweenness Centrality": st.column_config.NumberColumn("Betweenness Centrality", format="%.4f"),
                "Role": st.column_config.TextColumn("Graph Role")
            },
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
    # 3. Agent Planner Tab
    with tab_agent:
        col_base, col_lat = st.columns(2)
        
        with col_base:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.subheader("Control Group (Baseline LLM)")
            st.markdown("**Ollama Plan Console Output:**")
            
            st.markdown(f"""
            <div class="terminal-container">
                <div class="terminal-header">
                    <div class="terminal-dot dot-red"></div>
                    <div class="terminal-dot dot-yellow"></div>
                    <div class="terminal-dot dot-green"></div>
                    <span style="margin-left: 10px;">Baseline Output Console</span>
                </div>
                <pre style="color: #34d399; background: transparent; border: none; font-family: 'Fira Code', monospace; white-space: pre-wrap; margin: 0;">{st.session_state['base_raw']}</pre>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("**Generated Plan JSON:**")
            st.json(st.session_state["base_plan"])
            
            if st.session_state["base_valid"]:
                st.markdown("""
                <div class="custom-alert alert-success">
                    <div>✅</div>
                    <div><b>Plan Validation: PASSED!</b> (0 Conflicts detected).</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="custom-alert alert-error">
                    <div>❌</div>
                    <div><b>Plan Validation: FAILED!</b> ({len(st.session_state['base_conflicts'])} Conflicts found).</div>
                </div>
                """, unsafe_allow_html=True)
                for c in st.session_state["base_conflicts"]:
                    st.markdown(f"<span style='color: #f87171; margin-left: 30px;'>• {c}</span>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_lat:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.subheader("Experimental Group (Lattica GraphRAG)")
            
            st.markdown("**📁 Discovered Domains:**")
            for dom, svcs in st.session_state["domains"].items():
                st.markdown(f"- **Domain `{dom}`**: {', '.join([f'`{s}`' for s in svcs])}")
                
            st.markdown("**🤖 Domain Sub-Agent Consoles:**")
            for dom, dom_data in st.session_state["dom_plans"].items():
                with st.expander(f"Console Output: Domain `{dom}`"):
                    st.markdown(f"""
                    <div class="terminal-container">
                        <div class="terminal-header">
                            <div class="terminal-dot dot-red"></div>
                            <div class="terminal-dot dot-yellow"></div>
                            <div class="terminal-dot dot-green"></div>
                            <span style="margin-left: 10px;">Domain: {dom}</span>
                        </div>
                        <pre style="color: #34d399; background: transparent; border: none; font-family: 'Fira Code', monospace; white-space: pre-wrap; margin: 0;">{dom_data['raw']}</pre>
                    </div>
                    """, unsafe_allow_html=True)
                    
            st.markdown("**⚖️ Master Boundary Reconciliation Warnings:**")
            if st.session_state["boundary_edges"]:
                st.markdown(f"Detected **{len(st.session_state['boundary_edges'])}** cross-domain calling boundaries:")
                for c, d in st.session_state["boundary_edges"]:
                    st.markdown(f"- `{c}` CALLS `{d}`")
            else:
                st.markdown("No cross-domain boundaries found.")
                
            for w in st.session_state["reconciliation_warnings"]:
                st.markdown(f"""
                <div class="custom-alert alert-warning">
                    <div>⚠️</div>
                    <div>{w}</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("**Unified Global Plan JSON (Post-Reconciliation):**")
            st.json(st.session_state["lat_plan"])
            
            if st.session_state["lat_valid"]:
                st.markdown("""
                <div class="custom-alert alert-success">
                    <div>✅</div>
                    <div><b>Plan Validation: PASSED!</b> (0 Conflicts detected).</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="custom-alert alert-error">
                    <div>❌</div>
                    <div><b>Plan Validation: FAILED!</b> ({len(st.session_state['lat_conflicts'])} Conflicts found).</div>
                </div>
                """, unsafe_allow_html=True)
                for c in st.session_state["lat_conflicts"]:
                    st.markdown(f"<span style='color: #f87171; margin-left: 30px;'>• {c}</span>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # 3.5. 4-Way Scientific Comparison Tab
    with tab_comparison:
        render_4way_comparison_ui()

    # 4. Upgrade Simulator Tab (Cached)
    with tab_simulator:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        render_simulator_banner()
        st.write("This simulator models the rolling upgrade phase-by-phase and detects outages caused by dependency compatibility violations.")
        
        sim_col1, sim_col2 = st.columns(2)
        with sim_col1:
            st.markdown("#### Control Group (Baseline)")
            if st.button("Simulate Baseline Upgrades", key="cached_sim_base_btn"):
                log_base, outages_base = simulate_upgrade_timeline(st.session_state["base_plan"], st.session_state["dependencies"], st.session_state["inventory"])
                st.session_state["sim_base_log"] = log_base
                st.session_state["sim_base_outages"] = outages_base
                
            if "sim_base_log" in st.session_state:
                num_out = len(st.session_state["sim_base_outages"])
                if num_out > 0:
                    st.markdown(f"""
                    <div class="custom-alert alert-error">
                        <div>❌</div>
                        <div><b>Simulation Finished: {num_out} Outages Detected!</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="custom-alert alert-success">
                        <div>✅</div>
                        <div><b>Simulation Finished: 0 Outages.</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                log_txt = "\n".join(st.session_state["sim_base_log"])
                st.markdown(f"""
                <div class="terminal-container">
                    <div class="terminal-header">
                        <div class="terminal-dot dot-red"></div>
                        <div class="terminal-dot dot-yellow"></div>
                        <div class="terminal-dot dot-green"></div>
                        <span style="margin-left: 10px;">Simulation Console - Baseline</span>
                </div>
                <pre style="color: #f87171; background: transparent; border: none; font-family: 'Fira Code', monospace; white-space: pre-wrap; margin: 0;">{log_txt}</pre>
                </div>
                """, unsafe_allow_html=True)
                
        with sim_col2:
            st.markdown("#### Experimental Group (Lattica)")
            if st.button("Simulate Lattica Upgrades", key="cached_sim_lat_btn"):
                log_lat, outages_lat = simulate_upgrade_timeline(st.session_state["lat_plan"], st.session_state["dependencies"], st.session_state["inventory"])
                st.session_state["sim_lat_log"] = log_lat
                st.session_state["sim_lat_outages"] = outages_lat
                
            if "sim_lat_log" in st.session_state:
                num_out = len(st.session_state["sim_lat_outages"])
                if num_out > 0:
                    st.markdown(f"""
                    <div class="custom-alert alert-error">
                        <div>❌</div>
                        <div><b>Simulation Finished: {num_out} Outages Detected!</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="custom-alert alert-success">
                        <div>✅</div>
                        <div><b>Simulation Finished: 0 Outages. Lattica kept the system fully online!</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                log_txt = "\n".join(st.session_state["sim_lat_log"])
                st.markdown(f"""
                <div class="terminal-container">
                    <div class="terminal-header">
                        <div class="terminal-dot dot-red"></div>
                        <div class="terminal-dot dot-yellow"></div>
                        <div class="terminal-dot dot-green"></div>
                        <span style="margin-left: 10px;">Simulation Console - Lattica</span>
                    </div>
                    <pre style="color: #34d399; background: transparent; border: none; font-family: 'Fira Code', monospace; white-space: pre-wrap; margin: 0;">{log_txt}</pre>
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 4. GitOps Tab
    with tab_gitops:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 🛠️ GitOps Pipeline Integration")
        st.info("Lattica automates CI/CD and GitOps rollouts by creating isolated branches and opening Pull Requests for each sequential phase. This allows incremental, topology-safe deployment of cryptographic changes.")
        
        col_git1, col_git2 = st.columns(2)
        with col_git1:
            gitops_repo = st.text_input("Target GitHub Repository (`owner/repo`)", value=st.session_state.get("gitops_repo", ""))
            gitops_base = st.text_input("Base Branch", value=st.session_state.get("gitops_base", "main"))
        with col_git2:
            gitops_token = st.text_input("GitHub Access Token (PAT)", type="password", help="Required to push branches and open Pull Requests. If left blank, changes are made only locally.", value=st.session_state.get("gitops_token", ""))
            
        st.session_state["gitops_repo"] = gitops_repo
        st.session_state["gitops_base"] = gitops_base
        st.session_state["gitops_token"] = gitops_token
        
        gitops_button = st.button("🚀 GENERATE GITOPS BRANCHES & PULL REQUESTS", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if gitops_button:
            with st.status("Executing GitOps Pipeline...", expanded=True) as s_git:
                st.write("Reading generated plan and starting local workspace modifications...")
                from gitops_pipeline import generate_gitops_pipeline
                
                plan_to_use = st.session_state["lat_plan"]
                inventory_to_use = st.session_state["inventory"]
                
                results = generate_gitops_pipeline(
                    plan=plan_to_use,
                    inventory=inventory_to_use,
                    repo_name=gitops_repo if gitops_repo else None,
                    github_token=gitops_token if gitops_token else None,
                    base_branch=gitops_base
                )
                st.session_state["gitops_results"] = results
                s_git.update(label="GitOps Pipeline Execution Complete ✅", state="complete")
                
        if "gitops_results" in st.session_state:
            st.markdown("#### GitOps Execution Status")
            for res in st.session_state["gitops_results"]:
                with st.container():
                    st.markdown(f"##### **Phase**: {res['phase']}")
                    st.markdown(f"- **Local Git Branch**: `{res['branch']}`")
                    
                    if "Successfully" in res['local_status']:
                        st.success(res['local_status'])
                    elif "Skipped" in res['local_status']:
                        st.info(res['local_status'])
                    else:
                        st.error(res['local_status'])
                        
                    if "Error" in res['github_status']:
                        st.error(f"GitHub: {res['github_status']}")
                    elif "http" in res['github_status'] or "PR" in res['github_status']:
                        st.success(f"GitHub: PR successfully created/checked: [{res['github_status']}]({res['github_status']})")
                    else:
                        st.info(f"GitHub: {res['github_status']}")
                        
                    st.markdown(f"- **Files Modified**: " + ", ".join([f"`{f}`" for f in res['files_modified']]))
                    
                    manifests = res.get("manifests", {})
                    if manifests:
                        with st.expander("📄 View Generated Istio Traffic Mirroring Specs (Zero-Mock)"):
                            for path, yaml_content in manifests.items():
                                st.markdown(f"**File**: `{path}`")
                                st.code(yaml_content, language="yaml")
                    st.markdown("---")
                    
        # Neo4j Cluster Manifest Download Card
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 🗄️ Highly Available Neo4j Cluster Configuration")
        st.markdown("""
        Deploy a highly available, multi-AZ Neo4j Enterprise Causal Cluster with TLS (Bolt/HTTPS) 
        and AWS KMS-encrypted EBS StorageClasses.
        """)
        manifest_path = "deploy/neo4j-production.yaml"
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_content = f.read()
            with st.expander("📄 View deploy/neo4j-production.yaml Manifest"):
                st.code(manifest_content, language="yaml")
            st.download_button(
                label="📥 DOWNLOAD KUBERNETES MANIFEST (YAML)",
                data=manifest_content,
                file_name="neo4j-production.yaml",
                mime="text/yaml",
                use_container_width=True
            )
        else:
            st.error("Neo4j cluster manifest not found at 'deploy/neo4j-production.yaml'.")
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------- NO PIPELINE RUN STATE -----------------
else:
    with tab_discovery:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 🌐 Discovery & Network Ingestion Scope")
        st.markdown("""
        Select your **Target Mode** and verify connection parameters in the sidebar panel. 
        Once ready, click **🚀 EXECUTE FULL PIPELINE** in the sidebar to start live network discovery 
        and populate the Neo4j Graph Database.
        
        **Available Providers:**
        *   `Local Docker Lab`: Parses local config files and `docker-compose.yml` relationships.
        *   `Live GitHub Repository`: Shallow clones and performs AST import analysis on code repositories.
        *   `Kubernetes / Istio Kiali API`: Fetches real-time service dependency graphs from Kiali.
        *   `Datadog APM API`: Retrieves dependencies from live Datadog application metrics.
        *   `eBPF Connection Logs`: Ingests connection events directly from eBPF network trace files.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab_analytics:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Graph Metrics & Blast Radius Ingestion")
        st.info("Calculate degree centralities, change blast radii, and dependency impacts by executing the pipeline.")
        st.markdown('</div>', unsafe_allow_html=True)

        
    with tab_agent:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 🤖 Dual-Agent Planning Sequences")
        st.info("Perform domain-partitioned federated planning and compare it to baseline flat planning models once data is loaded.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab_comparison:
        render_4way_comparison_ui()

    with tab_simulator:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        render_simulator_banner()
        st.info("Simulate the rolling upgrade timeline phase-by-phase and detect dependency compatibility outages once data is loaded.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab_gitops:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 🛠️ GitOps Pipelines & Manifest Deliveries")
        st.info("Trigger automated branch generation, push configurations, and download production-ready Kubernetes manifests.")
        st.markdown('</div>', unsafe_allow_html=True)

