import os
import json
from tabulate import tabulate

SERVICES_DIR = "./services"
INVENTORY_FILE = "inventory.json"

def scan_services():
    """Scan the services directory for crypto configurations."""
    inventory = []
    
    if not os.path.exists(SERVICES_DIR) or not os.listdir(SERVICES_DIR):
        print(f"Error: Services directory '{SERVICES_DIR}' is empty or missing. Please add real service configurations.")
        os.makedirs(SERVICES_DIR, exist_ok=True)
        # Write empty inventory to JSON file
        with open(INVENTORY_FILE, "w") as f:
            json.dump(inventory, f, indent=4)
        return inventory
        
    for service_name in os.listdir(SERVICES_DIR):
        service_path = os.path.join(SERVICES_DIR, service_name)
        if not os.path.isdir(service_path):
            continue
        
        config_path = os.path.join(service_path, "config.json")
        if not os.path.exists(config_path):
            continue
            
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
                
            service_id = data.get("service_name", service_name)
            algo = data.get("crypto_algorithm", "Unknown")
            # We flag RSA or ECC as vulnerable to quantum attacks (Harvest Now, Decrypt Later)
            is_vulnerable = algo.startswith("RSA") or algo.startswith("ECC")
            
            inventory.append({
                "service": service_id,
                "algorithm": algo,
                "vulnerable": is_vulnerable
            })
        except Exception as e:
            print(f"Error scanning service {service_name}: {e}")
            
    # Write inventory to JSON file
    with open(INVENTORY_FILE, "w") as f:
        json.dump(inventory, f, indent=4)
        
    print(f"\nScan completed. Flat inventory saved to '{INVENTORY_FILE}'.")
    
    # Print the table to console
    if inventory:
        table_data = [[item["service"], item["algorithm"], "VULNERABLE (Quantum Risk)" if item["vulnerable"] else "Secure"] for item in inventory]
        print(tabulate(table_data, headers=["Service", "Cryptographic Algorithm", "Status"], tablefmt="grid"))
    else:
        print("No service configurations found.")
    
    return inventory

if __name__ == "__main__":
    scan_services()
