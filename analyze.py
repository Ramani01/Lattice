from neo4j import GraphDatabase
import json
import time
from tabulate import tabulate

import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
ANALYZED_INVENTORY_FILE = "analyzed_inventory.json"

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

def run_blast_radius_analysis():
    driver = None
    neo4j_available = True
    for attempt in range(1, 7):
        try:
            print(f"Connecting to Neo4j for Blast Radius Analysis (Attempt {attempt}/6)...")
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            # Test session
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
            
    analyzed_inventory = []

    if neo4j_available:
        with driver.session() as session:
            # Get all services and edges
            edges_result = session.run("MATCH (a:Service)-[:CALLS]->(b:Service) RETURN a.name as caller, b.name as callee")
            edges = [(record["caller"], record["callee"]) for record in edges_result]
            
            print("Running bulk Cypher query to analyze topology metrics...")
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
            nodes = [item["service"] for item in raw_items]
            
            print(f"Calculating Centrality Metrics for {len(nodes)} services...")
            pr_metrics = calculate_pagerank(nodes, edges)
            bc_metrics = calculate_betweenness_centrality(nodes, edges)
            
            # Write centrality back to Neo4j and build final inventory items
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
                # Map legacy key for backward compatibility
                item["quantum_blast_radius"] = item["change_blast_radius"]
                analyzed_inventory.append(item)
                
        driver.close()
    else:
        # PURE PYTHON IN-MEMORY GRAPH ANALYSIS FALLBACK!
        print("Performing pure Python local topological calculations...")
        # Resolve nodes and edges
        nodes = []
        edges = []
        inventory_data = {}
        if os.path.exists("inventory.json"):
            try:
                with open("inventory.json", "r") as f:
                    inv = json.load(f)
                    nodes = [item["service"] for item in inv]
                    inventory_data = {item["service"]: item for item in inv}
            except Exception as e:
                print(f"Warning: Failed to load inventory.json: {e}")
        
        if not nodes:
            from discovery import scan_services
            try:
                inv = scan_services()
                nodes = [item["service"] for item in inv]
                inventory_data = {item["service"]: item for item in inv}
            except Exception as e:
                print(f"Warning: Failed to scan services: {e}")
                
        if os.path.exists("docker-compose.yml"):
            try:
                import yaml
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
                            edges.append((service_name, dep))
            except Exception as e:
                print(f"Warning: Failed to parse docker-compose.yml: {e}")

        # Degrees
        out_degrees = {n: 0 for n in nodes}
        in_degrees = {n: 0 for n in nodes}
        for u, v in edges:
            if u in out_degrees and v in out_degrees:
                out_degrees[u] += 1
            if u in in_degrees and v in in_degrees:
                in_degrees[v] += 1
                
        # Downstream reachability (CBR)
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
            
        # Upstream reachability (DI)
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
            
        # PageRank & Betweenness Centrality
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
            
    # Save the analyzed inventory to JSON file
    with open(ANALYZED_INVENTORY_FILE, "w") as f:
        json.dump(analyzed_inventory, f, indent=4)
        
    print(f"\nAnalysis completed. Results saved to '{ANALYZED_INVENTORY_FILE}'.")
    
    # Sort by Betweenness Centrality for clear output (biggest choke points first)
    analyzed_inventory.sort(key=lambda x: x["betweenness_centrality"], reverse=True)
    
    # Print the table to console
    table_data = [
        [
            item["service"],
            item["algorithm"],
            "Yes" if item["vulnerable"] else "No",
            item["change_blast_radius"],
            item["dependency_impact"],
            f"{item['pagerank']:.4f}",
            f"{item['betweenness_centrality']:.4f}"
        ]
        for item in analyzed_inventory
    ]
    
    print(tabulate(
        table_data,
        headers=["Service", "Algorithm", "Vulnerable", "Change Blast Radius", "Dependency Impact", "PageRank", "Betweenness"],
        tablefmt="grid"
    ))
    
    return analyzed_inventory

if __name__ == "__main__":
    try:
        run_blast_radius_analysis()
    except Exception as e:
        print(f"Analysis failed: {e}")
