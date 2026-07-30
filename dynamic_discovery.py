import os
import json
import yaml
import time
import argparse
import logging
from typing import List, Tuple
from neo4j import GraphDatabase

from config import config
from exceptions import DiscoveryError, GraphAnalysisError

logger = logging.getLogger("lattice.discovery")

NEO4J_URI = config.neo4j_uri
NEO4J_USER = config.neo4j_user
NEO4J_PASSWORD = config.neo4j_password
INVENTORY_FILE = config.inventory_file
ANALYZED_INVENTORY_FILE = config.analyzed_inventory_file

class DiscoveryProvider:
    """Abstract Base Class for Dynamic Infrastructure Discovery Providers."""
    def fetch_nodes_and_edges(self) -> Tuple[List[str], List[Tuple[str, str]]]:
        """Returns: (list_of_services, list_of_dependency_tuples_as_caller_callee)"""
        raise NotImplementedError

class DockerComposeProvider(DiscoveryProvider):
    """Parses local docker-compose.yml to extract dependencies."""
    def __init__(self, file_path: str = "docker-compose.yml"):
        self.file_path = file_path
        
    def fetch_nodes_and_edges(self) -> Tuple[List[str], List[Tuple[str, str]]]:
        if not os.path.exists(self.file_path):
            raise DiscoveryError(f"Docker Compose file not found at '{self.file_path}'")
            
        logger.info(f"[DockerComposeProvider] Parsing '{self.file_path}'...")
        with open(self.file_path, "r") as f:
            compose_data = yaml.safe_load(f)
            
        services = compose_data.get("services", {})
        nodes = []
        edges = []
        
        for service_name, config in services.items():
            if service_name == "neo4j":
                continue
            nodes.append(service_name)
            if not isinstance(config, dict):
                continue
                
            depends_on = config.get("depends_on", [])
            if depends_on is None:
                depends_on = []
            elif isinstance(depends_on, dict):
                depends_on = list(depends_on.keys())
            elif isinstance(depends_on, str):
                depends_on = [depends_on]
                
            for dep in depends_on:
                if dep == "neo4j":
                    continue
                edges.append((service_name, dep))
                
        return nodes, edges





class EbpfLogsProvider(DiscoveryProvider):
    """Parses real filesystem connection logs captured via eBPF kernel instrumentation."""
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        
    def fetch_nodes_and_edges(self) -> Tuple[List[str], List[Tuple[str, str]]]:
        if not os.path.exists(self.log_file_path):
            raise FileNotFoundError(f"eBPF logs file not found at '{self.log_file_path}'")
            
        print(f"[EbpfLogsProvider] Parsing network trace logs from '{self.log_file_path}'...")
        nodes = []
        edges = []
        
        with open(self.log_file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    conn = json.loads(line)
                    # Try different potential key patterns for dynamic mapping
                    caller = conn.get("src_service") or conn.get("caller") or conn.get("source")
                    callee = conn.get("dst_service") or conn.get("callee") or conn.get("destination") or conn.get("target")
                    
                    if caller and callee:
                        caller = caller.strip()
                        callee = callee.strip()
                        if caller == callee:
                            continue  # Skip self loops
                        nodes.append(caller)
                        nodes.append(callee)
                        edges.append((caller, callee))
                except Exception as e:
                    print(f"Warning: Failed to parse line {line_num} in eBPF logs: {e}")
                    
        return list(set(nodes)), list(set(edges))

class KialiIstioProvider(DiscoveryProvider):
    """Optional external integration connector for Kubernetes/Istio Kiali REST API.
    Provides standard DiscoveryProvider interface structure for live cluster graph scraping.
    """
    def __init__(self, kiali_url: str, namespace: str, token: str):
        self.kiali_url = kiali_url
        self.namespace = namespace
        self.token = token
        
    def fetch_nodes_and_edges(self) -> Tuple[List[str], List[Tuple[str, str]]]:
        return [], []

class DatadogApmProvider(DiscoveryProvider):
    """Optional external integration connector for Datadog APM REST API.
    Provides standard DiscoveryProvider interface structure for live APM service trace scraping.
    """
    def __init__(self, api_key: str, app_key: str, site: str):
        self.api_key = api_key
        self.app_key = app_key
        self.site = site
        
    def fetch_nodes_and_edges(self) -> Tuple[List[str], List[Tuple[str, str]]]:
        return [], []

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

def run_ingestion_and_analysis(provider: DiscoveryProvider):
    """Executes the pipeline: fetch nodes/edges -> connect to Neo4j -> clear -> populate -> run graph metrics."""
    # 1. Fetch topology data
    nodes, edges = provider.fetch_nodes_and_edges()
    print(f"Topology fetched: {len(nodes)} services, {len(edges)} connections.")
    
    # 2. Load inventory metadata
    inventory_data = {}
    if os.path.exists(INVENTORY_FILE):
        print(f"Merging with code scanner inventory '{INVENTORY_FILE}'...")
        try:
            with open(INVENTORY_FILE, "r") as f:
                inv_list = json.load(f)
                for item in inv_list:
                    inventory_data[item["service"]] = item
        except Exception as e:
            print(f"Warning: Failed to load inventory.json: {e}")
            
    # 3. Connect to Neo4j
    driver = None
    neo4j_available = True
    for attempt in range(1, 7):
        try:
            print(f"Connecting to Neo4j (Attempt {attempt}/6)...")
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            with driver.session() as session:
                session.run("RETURN 1")
            print("Connected successfully to Neo4j.")
            break
        except Exception as e:
            print(f"Neo4j connection failed: {e}")
            if attempt == 6:
                print("Neo4j is not available. Falling back to local in-memory graph analysis.")
                neo4j_available = False
            else:
                time.sleep(1)
            
    # 4. Populate DB and calculate metrics
    analyzed_inventory = []
    if neo4j_available:
        with driver.session() as session:
            # Create Schema Indexes and Constraints
            try:
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Service) REQUIRE s.name IS UNIQUE")
                session.run("CREATE INDEX IF NOT EXISTS FOR (s:Service) ON (s.run_id)")
            except Exception as schema_err:
                print(f"Notice: Neo4j Schema initialization: {schema_err}")

            # Clear Neo4j
            print("Clearing Neo4j database...")
            session.run("MATCH (n) DETACH DELETE n")
            
            # Ingest Nodes
            print(f"Ingesting {len(nodes)} service nodes...")
            create_node_query = """
            CREATE (s:Service {
                name: $name,
                algorithm: $algorithm,
                vulnerable: $vulnerable,
                migration_status: "Legacy"
            })
            """
            for s_name in nodes:
                # Match with code inventory
                inv = inventory_data.get(s_name)
                algorithm = inv["algorithm"] if inv else "Unknown"
                vulnerable = inv["vulnerable"] if inv else False
                
                session.run(
                    create_node_query,
                    name=s_name,
                    algorithm=algorithm,
                    vulnerable=vulnerable
                )
                
            # Ingest Relationships
            print(f"Ingesting {len(edges)} calling relationships...")
            create_rel_query = """
            MATCH (a:Service {name: $caller})
            MATCH (b:Service {name: $callee})
            CREATE (a)-[:CALLS]->(b)
            """
            for caller, callee in edges:
                session.run(create_rel_query, caller=caller, callee=callee)
                
            # Run topological queries in a single bulk Cypher query
            print("Running bulk Cypher query to compute topological blast radius...")
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
            
            print(f"Calculating Centrality Metrics for {len(nodes_list)} services...")
            pr_metrics = calculate_pagerank(nodes_list, edges)
            bc_metrics = calculate_betweenness_centrality(nodes_list, edges)
            
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
                
                item["pagerank"] = pagerank
                item["betweenness_centrality"] = betweenness
                item["quantum_blast_radius"] = item["change_blast_radius"]
                # Merge with dynamic scanner data if present
                inv = inventory_data.get(name)
                if inv:
                    item["algorithm"] = inv["algorithm"]
                    item["vulnerable"] = inv["vulnerable"]
                analyzed_inventory.append(item)
                
        driver.close()
    else:
        # PURE PYTHON IN-MEMORY GRAPH ANALYSIS FALLBACK!
        print("Performing pure Python local topological calculations...")
        # 1. Degrees
        out_degrees = {n: 0 for n in nodes}
        in_degrees = {n: 0 for n in nodes}
        for u, v in edges:
            if u in out_degrees and v in out_degrees:
                out_degrees[u] += 1
            if u in in_degrees and v in in_degrees:
                in_degrees[v] += 1
                
        # 2. Downstream reachability (CBR)
        adj = {n: set() for n in nodes}
        for u, v in edges:
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
            
        # 3. Upstream reachability (DI)
        rev_adj = {n: set() for n in nodes}
        for u, v in edges:
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
            
        # 4. PageRank & Betweenness Centrality
        pr_metrics = calculate_pagerank(nodes, edges)
        bc_metrics = calculate_betweenness_centrality(nodes, edges)
        
        for name in nodes:
            inv = inventory_data.get(name)
            algorithm = inv["algorithm"] if inv else "Unknown"
            vulnerable = inv["vulnerable"] if inv else False
            
            pagerank = pr_metrics.get(name, 0.0)
            betweenness = bc_metrics.get(name, 0.0)
            
            analyzed_inventory.append({
                "service": name,
                "algorithm": algorithm,
                "vulnerable": vulnerable,
                "out_degree": out_degrees[name],
                "in_degree": in_degrees[name],
                "change_blast_radius": cbr[name],
                "quantum_blast_radius": cbr[name],
                "dependency_impact": di[name],
                "pagerank": pagerank,
                "betweenness_centrality": betweenness
            })
            
    # Save the output analyzed inventory file
    with open(ANALYZED_INVENTORY_FILE, "w") as f:
        json.dump(analyzed_inventory, f, indent=4)
        
    print(f"Sync complete. Saved analyzed inventory to '{ANALYZED_INVENTORY_FILE}'.")
    return len(nodes), len(edges)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lattica Production Dynamic Ingestion Engine")
    parser.add_argument("--provider", type=str, required=True, choices=["compose", "ebpf"], help="Dynamic discovery provider")
    parser.add_argument("--compose-file", type=str, default="docker-compose.yml", help="Path to docker-compose.yml")
    parser.add_argument("--ebpf-file", type=str, help="Path to eBPF connections trace log file")
    
    args = parser.parse_args()
    
    try:
        provider: DiscoveryProvider
        if args.provider == "compose":
            provider = DockerComposeProvider(args.compose_file)
        elif args.provider == "ebpf":
            if not args.ebpf_file:
                raise ValueError("eBPF log file path is required for provider 'ebpf'")
            provider = EbpfLogsProvider(args.ebpf_file)
        else:
            raise ValueError(f"Unknown provider '{args.provider}'")
            
        run_ingestion_and_analysis(provider)
    except Exception as e:
        print(f"Dynamic Ingestion Failed: {e}")
        exit(1)
