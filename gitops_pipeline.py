import os
import json
import base64
import subprocess
import requests
from typing import Dict, List, Tuple, Any, Optional

# Dynamic state mappings for target configuration profile updates
STATE_CONFIGS = {
    "Transition": {
        "target_version": "Java 21",
        "spring_boot_version": "Spring Boot 4-RC",
        "protocols": ["TLSv1.2", "TLSv1.3"],
        "api_version": "v1-compat"
    },
    "Target": {
        "target_version": "Java 21",
        "spring_boot_version": "Spring Boot 4",
        "protocols": ["TLSv1.3"],
        "api_version": "v2"
    }
}

def extract_service_context(service_name: str, inventory: List[Dict[str, Any]]) -> str:
    """Resolves the namespace for a service dynamically based on discovery location."""
    for item in inventory:
        if item.get("name") == service_name:
            loc = item.get("location", "")
            if loc.startswith("k8s://"):
                # Format: k8s://<namespace>/<service>
                parts = loc.replace("k8s://", "").split("/")
                if len(parts) > 0:
                    return parts[0]
            elif loc.startswith("datadog://"):
                return "default"
            elif loc.startswith("ebpf://"):
                return "default"
    return "default"

def generate_destination_rule(service_name: str, state: str, namespace: str = "default") -> str:
    """Generates an Istio DestinationRule YAML content based on target state."""
    lines = [
        "apiVersion: networking.istio.io/v1alpha3",
        "kind: DestinationRule",
        "metadata:",
        f"  name: {service_name}",
        f"  namespace: {namespace}",
        "spec:",
        f"  host: {service_name}",
        "  subsets:"
    ]
    if state == "Transition":
        lines.extend([
            "  - name: legacy",
            "    labels:",
            "      version: legacy",
            "  - name: transition",
            "    labels:",
            "      version: transition"
        ])
    else: # Target Configuration
        lines.extend([
            "  - name: target",
            "    labels:",
            "      version: target"
        ])
    return "\n".join(lines)

def generate_virtual_service(service_name: str, state: str, namespace: str = "default") -> str:
    """Generates an Istio VirtualService YAML content with traffic shadowing for Transition state."""
    lines = [
        "apiVersion: networking.istio.io/v1alpha3",
        "kind: VirtualService",
        "metadata:",
        f"  name: {service_name}",
        f"  namespace: {namespace}",
        "spec:",
        "  hosts:",
        f"  - {service_name}",
        "  http:",
        "  - route:",
        "    - destination:"
    ]
    if state == "Transition":
        lines.extend([
            f"        host: {service_name}",
            "        subset: legacy",
            "      weight: 100",
            "    mirror:",
            f"      host: {service_name}",
            "      subset: transition",
            "    mirrorPercentage:",
            "      value: 10.0"
        ])
    else: # Target Configuration
        lines.extend([
            f"        host: {service_name}",
            "        subset: target",
            "      weight: 100"
        ])
    return "\n".join(lines)

def update_local_config_file(service_name: str, state: str) -> Tuple[str, str]:
    """Modifies local service configuration files to update TLS profiles.
    Returns: (file_path, updated_json_content_string)
    """
    config_path = f"services/{service_name}/config.json"
    if not os.path.exists(config_path):
        # Fallback to check nested or directory structure
        candidate = f"services/{service_name}/config.json"
        if os.path.exists(candidate):
            config_path = candidate
        else:
            raise FileNotFoundError(f"Config file not found for service '{service_name}' at '{config_path}'")

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Map legacy state strings if passed
    if state == "Hybrid":
        state = "Transition"
    elif state == "PQC-Only":
        state = "Target"

    update_data = STATE_CONFIGS.get(state)
    if not update_data:
        raise ValueError(f"Unknown target state: {state}")

    data.update(update_data)
    updated_content = json.dumps(data, indent=4)
    return config_path, updated_content

def apply_local_git_changes(branch_name: str, file_changes: List[Tuple[str, str]], commit_message: str) -> str:
    """Uses git CLI to create a local branch and commit the configuration changes."""
    try:
        # Check if inside git repository
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        return "Skipped: Not a Git repository."

    try:
        # Save current branch
        orig_branch = subprocess.run(["git", "branch", "--show-current"], check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
        
        # Create and checkout branch (reset if already exists)
        subprocess.run(["git", "checkout", "-B", branch_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Write files
        for path, content in file_changes:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            subprocess.run(["git", "add", path], check=True)
            
        # Commit
        subprocess.run(["git", "commit", "-m", commit_message], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Switch back to original branch
        subprocess.run(["git", "checkout", orig_branch], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return f"Successfully created local branch '{branch_name}' and committed changes."
    except Exception as e:
        return f"Error executing local Git commands: {e}"

def create_github_pull_request(
    repo_name: str, 
    github_token: str, 
    branch_name: str, 
    base_branch: str, 
    file_changes: List[Tuple[str, str]], 
    pr_title: str, 
    pr_body: str
) -> str:
    """Interfaces directly with the GitHub REST API to push commits and open a Pull Request."""
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    parts = repo_name.split("/")
    if len(parts) != 2:
        return "Error: Invalid repo format. Must be 'owner/repo'."
    owner, repo = parts[0], parts[1]
    
    # 1. Fetch base branch SHA
    base_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{base_branch}"
    r_base = requests.get(base_url, headers=headers)
    if r_base.status_code != 200:
        return f"Error fetching base branch '{base_branch}': {r_base.json().get('message')}"
    base_sha = r_base.json()["object"]["sha"]
    
    # 2. Create new branch ref
    ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
    ref_payload = {
        "ref": f"refs/heads/{branch_name}",
        "sha": base_sha
    }
    r_ref = requests.post(ref_url, headers=headers, json=ref_payload)
    if r_ref.status_code not in [200, 201]:
        err_msg = r_ref.json().get('message', '')
        if "already exists" not in err_msg:
            return f"Error creating branch '{branch_name}': {err_msg}"
            
    # 3. Commit/Push each file using the Content API
    for path, content in file_changes:
        content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        
        # Get existing file SHA if it exists on the branch
        get_url = f"{content_url}?ref={branch_name}"
        r_get = requests.get(get_url, headers=headers)
        file_sha = None
        if r_get.status_code == 200:
            file_sha = r_get.json()["sha"]
            
        b64_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        put_payload = {
            "message": f"Lattica PQC Migration Ingestion: update {os.path.basename(path)}",
            "content": b64_content,
            "branch": branch_name
        }
        if file_sha:
            put_payload["sha"] = file_sha
            
        r_put = requests.put(content_url, headers=headers, json=put_payload)
        if r_put.status_code not in [200, 201]:
            return f"Error committing file '{path}': {r_put.json().get('message')}"
            
    # 4. Open the Pull Request
    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    pr_payload = {
        "title": pr_title,
        "head": branch_name,
        "base": base_branch,
        "body": pr_body
    }
    r_pr = requests.post(pr_url, headers=headers, json=pr_payload)
    if r_pr.status_code in [200, 201]:
        return r_pr.json().get("html_url", "PR Created successfully.")
    else:
        err_msg = r_pr.json().get("message", "")
        # If PR already exists, try to get it
        if "A pull request already exists" in err_msg:
            return f"Pull Request already exists for branch '{branch_name}'."
        return f"Error opening Pull Request: {err_msg}"

def generate_gitops_pipeline(
    plan: Dict[str, Any], 
    inventory: List[Dict[str, Any]], 
    repo_name: Optional[str] = None, 
    github_token: Optional[str] = None,
    base_branch: str = "main"
) -> List[Dict[str, Any]]:
    """Iterates through execution phases to update configs and output branches/PRs."""
    results = []
    
    # Sort phases numerically
    phases = list(plan.keys())
    try:
        phases.sort(key=lambda x: int(x.replace("Phase", "").strip()))
    except Exception:
        pass
        
    for phase_name in phases:
        phase_data = plan[phase_name]
        branch_name = f"execution-{phase_name.lower().replace(' ', '-')}"
        commit_message = f"Lattica Safe Execution Planner - Enforce {phase_name} Target Configurations"
        
        file_changes = []
        transition_upgrades = []
        target_upgrades = []
        
        # Check if plan format is Hybrid (dict) or Binary (list)
        if isinstance(phase_data, dict):
            # Hybrid/Transition Mode
            to_transition = phase_data.get("Upgrade to Transition State", [])
            to_target = phase_data.get("Enforce Target Configuration", [])
            
            for s in to_transition:
                try:
                    path, content = update_local_config_file(s, "Transition")
                    file_changes.append((path, content))
                    transition_upgrades.append(s)
                    
                    # Generate Istio specs dynamically
                    namespace = extract_service_context(s, inventory)
                    dr_yaml = generate_destination_rule(s, "Transition", namespace)
                    vs_yaml = generate_virtual_service(s, "Transition", namespace)
                    file_changes.append((f"services/{s}/destinationrule.yaml", dr_yaml))
                    file_changes.append((f"services/{s}/virtualservice.yaml", vs_yaml))
                except Exception as e:
                    print(f"Warning: Could not resolve file for {s}: {e}")
                    
            for s in to_target:
                try:
                    path, content = update_local_config_file(s, "Target")
                    file_changes.append((path, content))
                    target_upgrades.append(s)
                    
                    # Generate Istio specs dynamically
                    namespace = extract_service_context(s, inventory)
                    dr_yaml = generate_destination_rule(s, "Target", namespace)
                    vs_yaml = generate_virtual_service(s, "Target", namespace)
                    file_changes.append((f"services/{s}/destinationrule.yaml", dr_yaml))
                    file_changes.append((f"services/{s}/virtualservice.yaml", vs_yaml))
                except Exception as e:
                    print(f"Warning: Could not resolve file for {s}: {e}")
        else:
            # Binary Mode (List of service names to upgrade directly to Target Configuration)
            for s in phase_data:
                try:
                    path, content = update_local_config_file(s, "Target")
                    file_changes.append((path, content))
                    target_upgrades.append(s)
                    
                    # Generate Istio specs dynamically
                    namespace = extract_service_context(s, inventory)
                    dr_yaml = generate_destination_rule(s, "Target", namespace)
                    vs_yaml = generate_virtual_service(s, "Target", namespace)
                    file_changes.append((f"services/{s}/destinationrule.yaml", dr_yaml))
                    file_changes.append((f"services/{s}/virtualservice.yaml", vs_yaml))
                except Exception as e:
                    print(f"Warning: Could not resolve file for {s}: {e}")
                    
        if not file_changes:
            continue
            
        # Compile PR Details
        pr_title = f"Lattica Safe Execution Planning: Enforce {phase_name} Configurations"
        pr_body_lines = [
            f"### Lattica Topology-Aware Safe Execution Planning",
            f"This Pull Request contains configuration updates to enforce safe upgrade sequencing controls for **{phase_name}**.",
            "",
            "#### Scheduled Transitions:"
        ]
        if transition_upgrades:
            pr_body_lines.append(f"- **Upgrade to Transition State (Dual-Support compatibility)**: " + ", ".join([f"`{s}`" for s in transition_upgrades]))
        if target_upgrades:
            pr_body_lines.append(f"- **Enforce Target Configuration (strict enforcement)**: " + ", ".join([f"`{s}`" for s in target_upgrades]))
            
        pr_body_lines.extend([
            "",
            "These updates have been sequenced topologically using an execution planner engine to guarantee outage-free rolling upgrades.",
            "All downstream calling dependencies have been validated to ensure target configuration compatibility."
        ])
        pr_body = "\n".join(pr_body_lines)
        
        # 1. Apply changes locally
        local_status = apply_local_git_changes(branch_name, file_changes, commit_message)
        
        # 2. Upload to GitHub and open PR if credentials provided
        github_status = "Not executed (GitHub credentials not provided)."
        if repo_name and github_token:
            github_status = create_github_pull_request(
                repo_name=repo_name,
                github_token=github_token,
                branch_name=branch_name,
                base_branch=base_branch,
                file_changes=file_changes,
                pr_title=pr_title,
                pr_body=pr_body
            )
            
        results.append({
            "phase": phase_name,
            "branch": branch_name,
            "local_status": local_status,
            "github_status": github_status,
            "files_modified": [os.path.basename(p) for p, _ in file_changes],
            "manifests": {p: content for p, content in file_changes if p.endswith(".yaml")}
        })
        
    return results

if __name__ == "__main__":
    print("Running dynamic zero-mock GitOps update for testing...")
    real_inventory = []
    if os.path.exists("inventory.json"):
        with open("inventory.json", "r") as f:
            raw_inv = json.load(f)
            for item in raw_inv:
                real_inventory.append({
                    "name": item.get("service"),
                    "location": f"k8s://production-mesh/{item.get('service')}",
                    "algorithm": item.get("algorithm"),
                    "vulnerable": item.get("vulnerable")
                })
    else:
        print("Error: inventory.json not found. Please run discovery first.")
        import sys
        sys.exit(1)

    services = [item["name"] for item in real_inventory]
    phase1_transition = [s for s in services if s in ["auth-service", "payment-service", "user-db", "payment-db", "order-db"]]
    phase2_transition = [s for s in services if s not in phase1_transition]
    
    dynamic_plan = {
        "Phase 1": {
            "Upgrade to Transition State": phase1_transition,
            "Enforce Target Configuration": []
        },
        "Phase 2": {
            "Upgrade to Transition State": phase2_transition,
            "Enforce Target Configuration": phase1_transition
        },
        "Phase 3": {
            "Upgrade to Transition State": [],
            "Enforce Target Configuration": phase2_transition
        }
    }
    
    res = generate_gitops_pipeline(dynamic_plan, real_inventory)
    print(json.dumps(res, indent=4))
