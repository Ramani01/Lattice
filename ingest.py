import json
import yaml
import time
from neo4j import GraphDatabase

NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"
INVENTORY_FILE = "inventory.json"
DOCKER_COMPOSE_FILE = "docker-compose.yml"

def parse_docker_compose():
    """Parse docker-compose.yml to extract service dependencies."""
    print(f"Parsing dependencies from '{DOCKER_COMPOSE_FILE}'...")
    with open(DOCKER_COMPOSE_FILE, "r") as f:
        compose_data = yaml.safe_load(f)
        
    services = compose_data.get("services", {})
    dependencies = []
    
    for service_name, config in services.items():
        if service_name == "neo4j":
            continue
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
            dependencies.append((service_name, dep))
            
    print(f"Found {len(dependencies)} dependency relationships.")
    return dependencies

def load_inventory():
    """Load discovery inventory JSON."""
    print(f"Loading cryptographic inventory from '{INVENTORY_FILE}'...")
    with open(INVENTORY_FILE, "r") as f:
        return json.load(f)

def ingest_to_neo4j(inventory, dependencies):
    """Ingest inventory and dependencies into Neo4j."""
    # Attempt connection with retries (in case Neo4j is still starting up)
    driver = None
    for attempt in range(1, 7):
        try:
            print(f"Connecting to Neo4j (Attempt {attempt}/6)...")
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            # Test session
            with driver.session() as session:
                session.run("RETURN 1")
            print("Connected successfully to Neo4j.")
            break
        except Exception as e:
            print(f"Neo4j connection failed: {e}")
            if attempt == 6:
                raise e
            time.sleep(5)

    with driver.session() as session:
        # 1. Clear database
        print("Clearing Neo4j database...")
        session.run("MATCH (n) DETACH DELETE n")
        
        # 2. Ingest Nodes
        print("Ingesting service nodes...")
        create_node_query = """
        CREATE (s:Service {
            name: $name,
            algorithm: $algorithm,
            vulnerable: $vulnerable,
            migration_status: "Legacy"
        })
        """
        for item in inventory:
            session.run(
                create_node_query,
                name=item["service"],
                algorithm=item["algorithm"],
                vulnerable=item["vulnerable"]
            )
            print(f"  Created node: {item['service']} ({item['algorithm']})")
            
        # 3. Ingest Relationships
        print("Ingesting calling relationships...")
        create_rel_query = """
        MATCH (a:Service {name: $caller})
        MATCH (b:Service {name: $callee})
        CREATE (a)-[:CALLS]->(b)
        """
        for caller, callee in dependencies:
            session.run(create_rel_query, caller=caller, callee=callee)
            print(f"  Created relationship: {caller} -[:CALLS]-> {callee}")
            
    driver.close()
    print("Ingestion completed successfully.")

if __name__ == "__main__":
    try:
        inventory = load_inventory()
        dependencies = parse_docker_compose()
        ingest_to_neo4j(inventory, dependencies)
    except FileNotFoundError as e:
        print(f"Error: Missing input file. Make sure you ran discovery.py and docker-compose.yml exists. Details: {e}")
    except Exception as e:
        print(f"Ingestion failed: {e}")
