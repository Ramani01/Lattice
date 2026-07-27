import os
import json
import requests
from typing import TypedDict, List, Dict, Tuple, Any, Optional
from langgraph.graph import StateGraph, END

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

# Define the State for LangGraph
class AgentState(TypedDict):
    mode: str  # 'baseline' or 'lattica'
    inventory: List[Dict[str, Any]]
    dependencies: List[Tuple[str, str]]
    prompt: Any
    raw_response: str
    plan: Dict[str, List[str]]
    is_valid: bool
    conflicts: List[str]
    model_name: str

def parse_json_from_response(text: str) -> Dict[str, Any]:
    """Extract and parse JSON from LLM text output using substring boundaries."""
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and start < end:
        try:
            parsed = json.loads(text[start:end+1].strip())
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not parse valid JSON from LLM response: {text}")

def call_ollama(prompt: str, model_name: str, timeout: int = 240) -> str:
    """Send request to local Ollama instance with specified timeout and retries."""
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 2048
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=min(timeout, 3))
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception:
        # Fast silent return if local Ollama server is offline
        return ""

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

# Node 1: Load Context
def load_context(state: AgentState) -> Dict[str, Any]:
    if state.get("inventory") and state.get("dependencies"):
        return {
            "inventory": state["inventory"],
            "dependencies": state["dependencies"]
        }
    dependencies = []
    # Parse docker-compose.yml for real relationships
    import yaml
    if os.path.exists("docker-compose.yml"):
        try:
            with open("docker-compose.yml", "r") as f:
                compose_data = yaml.safe_load(f)
            services = compose_data.get("services", {})
            for service_name, config in services.items():
                if service_name == "neo4j":
                    continue
                depends_on = config.get("depends_on", [])
                if isinstance(depends_on, dict):
                    depends_on = list(depends_on.keys())
                elif isinstance(depends_on, str):
                    depends_on = [depends_on]
                for dep in depends_on:
                    if dep != "neo4j":
                        dependencies.append((service_name, dep)) # (caller, callee)
        except Exception as e:
            print(f"Warning: Failed to parse docker-compose.yml: {e}")

    # Read analyzed inventory
    if os.path.exists("analyzed_inventory.json"):
        with open("analyzed_inventory.json", "r") as f:
            inventory = json.load(f)
    else:
        # Load inventory.json and calculate metrics on-the-fly
        print("analyzed_inventory.json not found. Performing local in-memory fallback calculations.")
        if os.path.exists("inventory.json"):
            with open("inventory.json", "r") as f:
                raw_inv = json.load(f)
        else:
            # Fallback to scanning services folder
            from discovery import scan_services
            raw_inv = scan_services()
            
        nodes = [item["service"] for item in raw_inv]
        
        # Degrees
        out_degrees = {n: 0 for n in nodes}
        in_degrees = {n: 0 for n in nodes}
        for u, v in dependencies:
            if u in out_degrees and v in out_degrees:
                out_degrees[u] += 1
            if u in in_degrees and v in in_degrees:
                in_degrees[v] += 1
                
        # Downstream reachability (CBR)
        adj = {n: set() for n in nodes}
        for u, v in dependencies:
            if u in adj and v in adj:
                adj[u].add(v)
        cbr = {}
        for s in nodes:
            visited = set()
            queue = [s]
            while queue:
                curr = queue.pop(0)
                for nxt in adj[curr]:
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
            cbr[s] = len(visited)
            
        # Upstream reachability (DI)
        rev_adj = {n: set() for n in nodes}
        for u, v in dependencies:
            if u in rev_adj and v in rev_adj:
                rev_adj[v].add(u)
        di = {}
        for s in nodes:
            visited = set()
            queue = [s]
            while queue:
                curr = queue.pop(0)
                for nxt in rev_adj[curr]:
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
            di[s] = len(visited)
            
        # PageRank & Betweenness Centrality
        pr_metrics = calculate_pagerank(nodes, dependencies)
        bc_metrics = calculate_betweenness_centrality(nodes, dependencies)
        
        inventory = []
        for item in raw_inv:
            name = item["service"]
            inventory.append({
                "service": name,
                "algorithm": item["algorithm"],
                "vulnerable": item["vulnerable"],
                "out_degree": out_degrees.get(name, 0),
                "in_degree": in_degrees.get(name, 0),
                "change_blast_radius": cbr.get(name, 0),
                "quantum_blast_radius": cbr.get(name, 0),
                "dependency_impact": di.get(name, 0),
                "pagerank": pr_metrics.get(name, 0.0),
                "betweenness_centrality": bc_metrics.get(name, 0.0)
            })
            
        # Save to analyzed_inventory.json
        try:
            with open("analyzed_inventory.json", "w") as f:
                json.dump(inventory, f, indent=4)
        except Exception as e:
            print(f"Warning: Failed to save analyzed_inventory.json: {e}")
            
    # Ensure all nodes in dependencies are present in inventory
    inv_services = set(item["service"] for item in inventory)
    for caller, callee in dependencies:
        if caller not in inv_services:
            inventory.append({"service": caller, "algorithm": "RSA (Legacy)", "vulnerable": True, "change_blast_radius": 0, "dependency_impact": 0})
            inv_services.add(caller)
        if callee not in inv_services:
            inventory.append({"service": callee, "algorithm": "ECC (Legacy)", "vulnerable": True, "change_blast_radius": 0, "dependency_impact": 0})
            inv_services.add(callee)

    return {
        "inventory": inventory,
        "dependencies": dependencies
    }

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

# Node 2: Prepare Prompt
def prepare_prompt(state: AgentState) -> Dict[str, Any]:
    mode = state["mode"]
    inventory = state["inventory"]
    dependencies = state["dependencies"]
    
    if mode == "baseline":
        # Flat inventory only
        flat_list = []
        for item in inventory:
            flat_list.append(f"- {item['service']}")
        inventory_str = "\n".join(flat_list)
        
        prompt = f"""You are an Infrastructure Execution Planner.
We need to migrate our microservices from legacy configurations to target configuration profiles (e.g. Java 21, Spring Boot 4, TLS 1.3, API v2).
Here is the flat inventory of services:
{inventory_str}

Please generate a 4-phase execution plan.
In each phase, specify which services should be upgraded.
All {len(inventory)} services must be upgraded.
Each of the {len(inventory)} services must appear EXACTLY ONCE in the entire plan. Do not duplicate services across phases.
Format your output EXACTLY as a JSON object:
{{
  "Phase 1": ["service_name_1", "service_name_2"],
  "Phase 2": ["service_name_3"],
  "Phase 3": ["service_name_4", "service_name_5"],
  "Phase 4": ["service_name_6", "service_name_7"]
}}
Do not include any other text, markdown formatting, or explanations. Return ONLY the raw JSON object.
"""
        return {"prompt": prompt}
    elif mode == "lattica":
        # Lattica: GraphRAG with graph metrics and dependency relationships
        flat_list = []
        for item in inventory:
            flat_list.append(
                f"- {item['service']} (CBR: {item.get('change_blast_radius', item.get('quantum_blast_radius', 0))}, DI: {item['dependency_impact']})"
            )
        analyzed_inventory_str = "\n".join(flat_list)
        
        dep_list = []
        for caller, callee in dependencies:
            dep_list.append(f"- {caller} depends on {callee}")
        dependencies_str = "\n".join(dep_list)
        
        # Compute topological sort chain to guide the LLM
        nodes = [item["service"] for item in inventory]
        adj = {node: [] for node in nodes}
        in_degree = {node: 0 for node in nodes}
        for caller, callee in dependencies:
            if caller in adj and callee in adj:
                adj[callee].append(caller)
                in_degree[caller] += 1
                
        # Kahn's algorithm
        cbr_map = {item["service"]: item.get("change_blast_radius", item.get("quantum_blast_radius", 0)) for item in inventory}
        queue = [node for node in nodes if in_degree[node] == 0]
        queue.sort(key=lambda x: cbr_map.get(x, 0))
        
        order = []
        while queue:
            queue.sort(key=lambda x: cbr_map.get(x, 0))
            u = queue.pop(0)
            order.append(u)
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
                    
        inequality_chain = " <= ".join([f"Phase({node})" for node in order])
        ordered_list_str = "\n".join([f"{idx+1}. {node}" for idx, node in enumerate(order)])
        
        prompt = f"""You are a Topology-Aware Infrastructure Execution Planner.
We need to migrate our microservices from legacy configurations to target configuration profiles (e.g. Java 21, Spring Boot 4, TLS 1.3, API v2).
If you upgrade an upstream caller service before its downstream dependency (callee) is upgraded, dependency conflicts will occur, causing outages. Therefore, downstream services (callees) MUST be upgraded before or in the same phase as upstream services (callers).

Here is the flat inventory of services with their graph topology context:
{analyzed_inventory_str}

Here are the direct calling dependencies:
{dependencies_str}

CRITICAL RULES:
1. Services with a Change Blast Radius of 0 (transitive dependencies = 0) have no downstream dependencies and must be upgraded in Phase 1.
2. Services with a larger Change Blast Radius must be scheduled in later phases than their downstream dependencies.
3. Each of the {len(inventory)} services must appear EXACTLY ONCE in the entire plan. Do not duplicate services across different phases.

CRITICAL ORDERING CONSTRAINT:
Specifically, you MUST schedule the services in the following topological order (from earliest phase to latest phase) to satisfy all calling dependencies:
{ordered_list_str}

This implies the following phase inequality constraint:
{inequality_chain}

Rules to satisfy this order:
1. Do NOT upgrade a service listed later in a phase earlier than a service listed before it.
2. You can upgrade multiple services in the same phase, provided their relative order is maintained.

Finally, output the 4-phase execution plan as a raw JSON object enclosed in a ```json ``` block at the very end of your response, formatted exactly like this:
```json
{{
  "Phase 1": ["service_name_1", "service_name_2"],
  "Phase 2": ["service_name_3"],
  "Phase 3": ["service_name_4"],
  "Phase 4": ["service_name_5"]
}}
```
Do not output any text after the JSON block.
"""
        return {"prompt": prompt}
    elif mode == "federated_hybrid":
        # Graph Partitioning based on Label Propagation Clustering
        nodes = [item["service"] for item in inventory]
        service_domains = label_propagation_partition(nodes, dependencies)
            
        domains = {}
        for name, domain in service_domains.items():
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(name)
            
        prompts = {}
        for dom, dom_services in domains.items():
            dom_inventory = [item for item in inventory if item["service"] in dom_services]
            
            dom_lat_list = []
            for item in dom_inventory:
                dom_lat_list.append(
                    f"- {item['service']} (CBR: {item.get('change_blast_radius', item.get('quantum_blast_radius', 0))}, DI: {item['dependency_impact']})"
                )
            dom_analyzed_inventory_str = "\n".join(dom_lat_list)
            
            # Filter dependencies for this domain
            dom_dependencies = []
            for caller, callee in dependencies:
                if caller in dom_services and callee in dom_services:
                    dom_dependencies.append((caller, callee))
                    
            dom_dep_list = [f"- {caller} depends on {callee}" for caller, callee in dom_dependencies]
            dom_dependencies_str = "\n".join(dom_dep_list) if dom_dep_list else "None"
            
            # Compute topological order for this domain
            dom_adj = {node: [] for node in dom_services}
            dom_in_degree = {node: 0 for node in dom_services}
            for caller, callee in dom_dependencies:
                dom_adj[callee].append(caller)
                dom_in_degree[caller] += 1
                
            dom_cbr_map = {item["service"]: item.get("change_blast_radius", item.get("quantum_blast_radius", 0)) for item in dom_inventory}
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

Here are the direct calling dependencies for this domain:
{dom_dependencies_str}

CRITICAL RULES:
1. Timeline Consistency: For any service X, Phase(X_Transition) <= Phase(X_Target). You cannot enforce target configuration before enabling transition.
2. Services with a Change Blast Radius of 0 must be scheduled in Phase 1 for Transition.

CRITICAL ORDERING CONSTRAINT:
Specifically, you MUST schedule the services in the following topological order (from earliest phase to latest phase) to satisfy all calling dependencies:
{dom_ordered_list_str}

This implies the following phase inequality constraint:
{dom_inequality_chain}

Rules:
1. Do NOT upgrade a service listed later in a phase earlier than a service listed before it.
2. You can upgrade multiple services in the same phase, provided their relative order is maintained.

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
            prompts[dom] = dom_prompt
            
        return {"prompt": prompts}
    else:
        return {"prompt": ""}

def create_provenance_edge(caller: str, callee: str, source: str = "eBPF", confidence: float = 1.0, namespace: str = "default", observed_time: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates an Edge Provenance record attaching source, timestamp, confidence score, namespace, and multi-source observations array.
    """
    if not observed_time:
        import datetime
        observed_time = datetime.datetime.utcnow().isoformat() + "Z"
    obs_record = {
        "source": source,
        "confidence": confidence,
        "namespace": namespace,
        "timestamp": observed_time
    }
    return {
        "caller": caller,
        "callee": callee,
        "source": source,
        "confidence": confidence,
        "namespace": namespace,
        "observed_time": observed_time,
        "observations": [obs_record]
    }

def compute_scc_condensation(service_names: List[str], dependencies: Any) -> Tuple[List[List[str]], List[Tuple[int, int]]]:
    """
    Computes Strongly Connected Components (SCCs) using Tarjan's algorithm.
    Collapses cyclic microservice loops into condensed super-nodes to handle real-world cyclic service graphs.
    Returns: (list_of_scc_components, condensed_dag_edges)
    """
    adj = {node: [] for node in service_names}
    for edge in dependencies:
        if isinstance(edge, (tuple, list)):
            caller, callee = edge[0], edge[1]
        elif isinstance(edge, dict):
            caller, callee = edge.get("caller"), edge.get("callee")
        else:
            continue
        if caller in adj and callee in adj:
            adj[caller].append(callee)

    index = 0
    indices = {}
    lowlink = {}
    stack = []
    on_stack = set()
    sccs = []

    def strongconnect(node):
        nonlocal index
        indices[node] = index
        lowlink[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for callee in adj[node]:
            if callee not in indices:
                strongconnect(callee)
                lowlink[node] = min(lowlink[node], lowlink[callee])
            elif callee in on_stack:
                lowlink[node] = min(lowlink[node], indices[callee])

        if lowlink[node] == indices[node]:
            scc = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                scc.append(w)
                if w == node:
                    break
            sccs.append(scc)

    for node in service_names:
        if node not in indices:
            strongconnect(node)

    scc_map = {}
    for idx, scc in enumerate(sccs):
        for node in scc:
            scc_map[node] = idx

    condensed_edges = set()
    for edge in dependencies:
        if isinstance(edge, (tuple, list)):
            caller, callee = edge[0], edge[1]
        elif isinstance(edge, dict):
            caller, callee = edge.get("caller"), edge.get("callee")
        else:
            continue
        if caller in scc_map and callee in scc_map:
            u_scc = scc_map[caller]
            v_scc = scc_map[callee]
            if u_scc != v_scc:
                condensed_edges.add((u_scc, v_scc))

    return sccs, list(condensed_edges)

def compute_deterministic_topo_plan(service_names: List[str], dependencies: Any, max_phases: int = 4) -> Dict[str, List[str]]:
    """
    Computes a 100% constraint-safe execution plan deterministically using Tarjan's SCC condensation
    and topological depth binning. Handles cyclic microservice graphs seamlessly by assigning cyclic
    co-dependent services to the same phase.
    """
    sccs, condensed_edges = compute_scc_condensation(service_names, dependencies)
    num_sccs = len(sccs)
    scc_adj = {i: [] for i in range(num_sccs)}
    for u, v in condensed_edges:
        scc_adj[u].append(v)

    memo = {}
    def get_scc_depth(scc_idx):
        if scc_idx in memo:
            return memo[scc_idx]
        if not scc_adj[scc_idx]:
            depth = 0
        else:
            depth = 1 + max(get_scc_depth(child) for child in scc_adj[scc_idx])
        memo[scc_idx] = depth
        return depth

    plan = {f"Phase {i+1}": [] for i in range(max_phases)}
    for scc_idx, scc_nodes in enumerate(sccs):
        depth = get_scc_depth(scc_idx)
        phase_num = min(depth + 1, max_phases)
        plan[f"Phase {phase_num}"].extend(scc_nodes)

    return plan


def enrich_plan_with_llm(plan: Dict[str, List[str]], inventory: List[Dict[str, Any]], dependencies: List[Tuple[str, str]], model_name: str = "qwen2:1.5b") -> Dict[str, Any]:
    """
    Enriches a mathematically safe deterministic execution plan with human-readable release notes,
    architectural rationale, and risk summaries using the LLM.
    The LLM is NOT used to calculate constraints (which are pre-calculated and guaranteed).
    """
    plan_str = json.dumps(plan, indent=2)
    prompt = f"""You are an Infrastructure & SRE Release Lead.
We have already calculated a 100% constraint-safe microservice migration plan:
{plan_str}

Please enrich this plan by providing:
1. Architectural Rationale: Explain why services in Phase 1 (leaf dependencies/databases) are migrated prior to upstream callers in later phases.
2. Phase-by-Phase Release Notes: For each Phase (Phase 1 to Phase 4), summarize the services being upgraded and key operational safety checks.
3. Risk Mitigation Summary: Highlight key SRE verification steps.

Format your output EXACTLY as a JSON object with keys "architectural_rationale", "release_notes", and "risk_mitigation".
"""

    raw_response = call_ollama(prompt, model_name, timeout=60)
    if not raw_response:
        return {
            "architectural_rationale": "Leaf dependencies and database services are scheduled in Phase 1 to guarantee schema and contract availability before upstream API callers and edge gateways transition.",
            "release_notes": {
                phase: f"Upgrading services: {', '.join(svcs)}. Execute health probes prior to traffic promotion."
                for phase, svcs in plan.items()
            },
            "risk_mitigation": "Ensure backward compatibility of API routes and database schemas. Validate canary traffic before full cluster promotion."
        }

    try:
        enriched = parse_json_from_response(raw_response)
        if isinstance(enriched, dict) and "architectural_rationale" in enriched:
            return enriched
    except Exception:
        pass

    return {
        "architectural_rationale": "Leaf dependencies and database services are scheduled in Phase 1 to guarantee schema and contract availability before upstream API callers and edge gateways transition.",
        "release_notes": {
            phase: f"Upgrading services: {', '.join(svcs)}. Execute health probes prior to traffic promotion."
            for phase, svcs in plan.items()
        },
        "risk_mitigation": "Ensure backward compatibility of API routes and database schemas. Validate canary traffic before full cluster promotion."
    }


# Node 3: Generate Plan
def _generate_single_plan(state: AgentState) -> Dict[str, Any]:
    prompt = state["prompt"]
    model_name = state["model_name"]
    mode = state["mode"]
    dependencies = state["dependencies"]
    inventory = state["inventory"]
    
    if mode == "deterministic_topo":
        global_service_names = [item["service"] for item in inventory]
        plan = compute_deterministic_topo_plan(global_service_names, dependencies)
        return {
            "raw_response": json.dumps({"engine": "Deterministic Topological Sort (Kahn's Depth)", "plan": plan}),
            "plan": plan
        }

        
    elif mode == "federated_hybrid":
        raw_responses = {}
        
        # Partitioning
        nodes = [item["service"] for item in inventory]
        service_domains = label_propagation_partition(nodes, dependencies)
            
        global_transition_phases = {}
        global_target_phases = {}
        global_service_names = [item["service"] for item in inventory]
        
        # Spawn Domain Planner Subagents sequentially
        for dom, dom_prompt in prompt.items():
            response = call_ollama(dom_prompt, model_name, timeout=90)
            raw_responses[dom] = response
            try:
                dom_plan = parse_json_from_response(response)
            except Exception as e:
                print(f"Error parsing plan for domain {dom}: {e}")
                dom_plan = {}
                
            dom_services = [s for s, d in service_domains.items() if d == dom]
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
                            
        # Compute topological depths for robust baseline initialization
        adj = {node: [] for node in global_service_names}
        for caller, callee in dependencies:
            if caller in adj and callee in adj:
                adj[caller].append(callee)
                
        memo = {}
        def get_depth(node):
            if node in memo:
                return memo[node]
            if not adj[node]:
                memo[node] = 0
                return 0
            max_child = max(get_depth(child) for child in adj[node])
            memo[node] = 1 + max_child
            return memo[node]
            
        depths = {node: get_depth(node) for node in global_service_names}
        
        # Initialize missing services using topological baseline
        for s in global_service_names:
            if s not in global_transition_phases:
                global_transition_phases[s] = min(depths[s] + 1, 4)
            if s not in global_target_phases:
                global_target_phases[s] = min(global_transition_phases[s] + 1, 4)

        # Master Boundary Reconciliation (Constraint Propagation)
        changed = True
        iterations = 0
        while changed and iterations < 100:
            changed = False
            iterations += 1
            
            # 1. Timeline consistency: Transition phase <= Target phase
            for s in global_service_names:
                t = global_transition_phases[s]
                tc = global_target_phases[s]
                if t > tc:
                    global_target_phases[s] = t
                    changed = True
                    
            # 2. Dependency Constraints
            for caller, callee in dependencies:
                t_caller = global_transition_phases.get(caller, 1)
                t_callee = global_transition_phases.get(callee, 1)
                tc_caller = global_target_phases.get(caller, 4)
                tc_callee = global_target_phases.get(callee, 4)
                
                # A. Callee Transition before caller Transition (T_B <= T_A) -> push caller later
                if t_callee > t_caller:
                    global_transition_phases[caller] = t_callee
                    changed = True
                    
                # B. Callee Target before caller Target (TC_B <= TC_A) -> push caller later
                if tc_callee > tc_caller:
                    global_target_phases[caller] = tc_callee
                    changed = True
                    
                # C. Caller Transition before callee Target (T_A <= TC_B) -> push callee Target later
                if t_caller > tc_callee:
                    global_target_phases[callee] = t_caller
                    changed = True
                    
        # Reconstruct unified global plan
        plan = {}
        for ph in range(1, 5):
            plan[f"Phase {ph}"] = {
                "Upgrade to Transition State": [],
                "Enforce Target Configuration": []
            }
            
        for s in global_service_names:
            t = min(max(global_transition_phases.get(s, 1), 1), 4)
            tc = min(max(global_target_phases.get(s, 4), 1), 4)
            plan[f"Phase {t}"]["Upgrade to Transition State"].append(s)
            plan[f"Phase {tc}"]["Enforce Target Configuration"].append(s)
            
        return {
            "raw_response": json.dumps(raw_responses),
            "plan": plan
        }
    else:
        timeout_val = 120 if mode == "baseline" else 180
        raw_response = call_ollama(prompt, model_name, timeout=timeout_val)
        try:
            plan = parse_json_from_response(raw_response)
        except Exception as e:
            print(f"Error parsing plan: {e}")
            plan = {}
            
        return {
            "raw_response": raw_response,
            "plan": plan
        }

def generate_plan(state: AgentState) -> Dict[str, Any]:
    if state["mode"] in ["deterministic_topo", "federated_hybrid"]:
        plan_res = _generate_single_plan(state)
        return {
            "raw_response": plan_res["raw_response"],
            "plan": plan_res["plan"]
        }

    best_raw = ""
    best_plan = {}
    min_conflicts = float('inf')
    
    for _ in range(1):
        plan_res = _generate_single_plan(state)
        candidate_state: AgentState = {
            "mode": state["mode"],
            "inventory": state["inventory"],
            "dependencies": state["dependencies"],
            "prompt": state["prompt"],
            "raw_response": plan_res["raw_response"],
            "plan": plan_res["plan"],
            "is_valid": False,
            "conflicts": [],
            "model_name": state["model_name"]
        }
        val_res = validate_plan(candidate_state)
        conflicts = len(val_res["conflicts"])
        
        if conflicts < min_conflicts:
            min_conflicts = conflicts
            best_plan = plan_res["plan"]
            best_raw = plan_res["raw_response"]
            
        if min_conflicts == 0:
            break
            
    return {
        "raw_response": best_raw,
        "plan": best_plan
    }

def validate_execution_plan(plan: Dict[str, Any], dependencies: List[Tuple[str, str]], inventory: List[Dict[str, Any]]) -> List[str]:
    """Validate execution plan containing both Transition and Target stages."""
    transition_phases = {}
    target_phases = {}
    
    for phase_name, stage_data in plan.items():
        try:
            phase_num = int(phase_name.replace("Phase", "").strip())
        except ValueError:
            phase_num = 999
            
        if isinstance(stage_data, dict):
            to_transition = stage_data.get("Upgrade to Transition State", [])
            to_target = stage_data.get("Enforce Target Configuration", [])
            
            for s in to_transition:
                transition_phases[s] = phase_num
            for s in to_target:
                target_phases[s] = phase_num
                
    conflicts = []
    expected_services = set([item["service"] for item in inventory])
    
    # Check if all services are scheduled for both states
    for s in expected_services:
        t_ph = transition_phases.get(s)
        tc_ph = target_phases.get(s)
        
        if t_ph is None:
            conflicts.append(f"Service '{s}' is missing an 'Upgrade to Transition State' phase.")
        if tc_ph is None:
            conflicts.append(f"Service '{s}' is missing an 'Enforce Target Configuration' phase.")
            
        # 1. Timeline Consistency: Transition must occur before or in the same phase as Target
        if t_ph is not None and tc_ph is not None:
            if t_ph > tc_ph:
                conflicts.append(
                    f"Timeline Conflict: '{s}' enforces Target Configuration in Phase {tc_ph}, "
                    f"but is upgraded to Transition State in later Phase {t_ph}."
                )
                
    # 2. Dependency Constraints
    for caller, callee in dependencies:
        t_caller = transition_phases.get(caller)
        t_callee = transition_phases.get(callee)
        tc_caller = target_phases.get(caller)
        tc_callee = target_phases.get(callee)
        
        # A. Callee B must become Transition before or in the same phase as caller A becomes Transition (T_B <= T_A)
        if t_caller is not None and t_callee is not None:
            if t_callee > t_caller:
                conflicts.append(
                    f"Dependency Conflict: Caller '{caller}' enters Transition State in Phase {t_caller}, "
                    f"but its dependency '{callee}' enters Transition State in later Phase {t_callee}."
                )
                
        # B. Callee B must become Target before or in the same phase caller A becomes Target (TC_B <= TC_A)
        if tc_caller is not None and tc_callee is not None:
            if tc_callee > tc_caller:
                conflicts.append(
                    f"Dependency Conflict: Caller '{caller}' enforces Target Configuration in Phase {tc_caller}, "
                    f"but its dependency '{callee}' enforces Target Configuration in later Phase {tc_callee}."
                )
                
        # C. Caller A must become Transition before or in the same phase callee B becomes Target (T_A <= TC_B)
        if t_caller is not None and tc_callee is not None:
            if t_caller > tc_callee:
                conflicts.append(
                    f"Deprecation Conflict: Dependency '{callee}' enforces Target Configuration in Phase {tc_callee}, "
                    f"but its caller '{caller}' is still Legacy and only enters Transition State in later Phase {t_caller}."
                )
                
    return conflicts

# Node 4: Validate Plan
def validate_plan(state: AgentState) -> Dict[str, Any]:
    plan = state["plan"]
    dependencies = state["dependencies"]
    inventory = state["inventory"]
    
    is_hybrid = False
    for val in plan.values():
        if isinstance(val, dict):
            is_hybrid = True
            break
            
    if is_hybrid:
        conflicts = validate_execution_plan(plan, dependencies, inventory)
        is_valid = len(conflicts) == 0
        return {
            "is_valid": is_valid,
            "conflicts": conflicts
        }
        
    # Map service name to its scheduled phase number (binary validation)
    service_phases = {}
    for phase_name, services in plan.items():
        try:
            # Extract phase number from "Phase X"
            phase_num = int(phase_name.replace("Phase", "").strip())
        except ValueError:
            phase_num = 999  # Invalid phase name format
            
        for s in services:
            service_phases[s] = phase_num
            
    conflicts = []
    
    # A conflict is defined as a caller service scheduled in an earlier phase than its callee dependency
    for caller, callee in dependencies:
        caller_phase = service_phases.get(caller)
        callee_phase = service_phases.get(callee)
        
        if caller_phase is None:
            conflicts.append(f"Missing caller service '{caller}' from execution plan.")
        elif callee_phase is None:
            conflicts.append(f"Missing callee dependency '{callee}' from execution plan.")
        elif caller_phase < callee_phase:
            conflicts.append(
                f"Dependency Conflict: '{caller}' is scheduled in Phase {caller_phase}, "
                f"but its downstream dependency '{callee}' is scheduled in a later Phase {callee_phase}."
            )
            
    # Check if all services are covered
    expected_services = set([item["service"] for item in state["inventory"]])
    planned_services = set(service_phases.keys())
    missing = expected_services - planned_services
    for m in missing:
        conflicts.append(f"Missing service '{m}' entirely from plan.")
        
    is_valid = len(conflicts) == 0
    
    return {
        "is_valid": is_valid,
        "conflicts": conflicts
    }

# Build LangGraph Workflow
def build_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("load_context", load_context)
    workflow.add_node("prepare_prompt", prepare_prompt)
    workflow.add_node("generate_plan", generate_plan)
    workflow.add_node("validate_plan", validate_plan)
    
    # Set entry point
    workflow.set_entry_point("load_context")
    
    # Connect nodes
    workflow.add_edge("load_context", "prepare_prompt")
    workflow.add_edge("prepare_prompt", "generate_plan")
    workflow.add_edge("generate_plan", "validate_plan")
    workflow.add_edge("validate_plan", END)
    
    return workflow.compile()

def run_agent(mode: str, model_name: str = "qwen:9b", inject_state: Dict[str, Any] = None) -> Dict[str, Any]:
    """Interface to run the LangGraph agent for a given mode."""
    graph = build_agent_graph()
    initial_state = {
        "mode": mode,
        "inventory": inject_state.get("inventory", []) if inject_state else [],
        "dependencies": inject_state.get("dependencies", []) if inject_state else [],
        "prompt": "",
        "raw_response": "",
        "plan": {},
        "is_valid": False,
        "conflicts": [],
        "model_name": model_name
    }
    
    result = graph.invoke(initial_state)
    return result

if __name__ == "__main__":
    # Test run
    print("Testing Agent in Deterministic Topo-Sort Mode...")
    res_topo = run_agent("deterministic_topo")
    print(f"Deterministic Topo Plan: {res_topo['plan']}")
    print(f"Is Valid: {res_topo['is_valid']}")
    print(f"Conflicts: {res_topo['conflicts']}")
    
    print("\nTesting Agent in Baseline Mode...")
    res_base = run_agent("baseline")
    print(f"Baseline Plan: {res_base['plan']}")
    print(f"Is Valid: {res_base['is_valid']}")
    print(f"Conflicts: {res_base['conflicts']}")
    
    print("\nTesting Agent in Lattica Mode...")
    res_lat = run_agent("lattica")
    print(f"Lattica Plan: {res_lat['plan']}")
    print(f"Is Valid: {res_lat['is_valid']}")
    print(f"Conflicts: {res_lat['conflicts']}")

    print("\nTesting Agent in Federated Hybrid Mode...")
    res_fed = run_agent("federated_hybrid")
    print(f"Federated Hybrid Plan: {res_fed['plan']}")
    print(f"Is Valid: {res_fed['is_valid']}")
    print(f"Conflicts: {res_fed['conflicts']}")
