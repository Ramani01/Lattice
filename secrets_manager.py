import os
import json
import requests
import boto3
from typing import Dict, Any, Optional

# Ensure that boto3 is only imported if needed, or handles import error gracefully
try:
    import boto3
except ImportError:
    boto3 = None

def get_aws_secret(secret_name: str, region_name: str = "us-east-1") -> Dict[str, Any]:
    """Retrieves credentials in real-time from AWS Secrets Manager using boto3.
    Raises exceptions directly on connection, authentication, or missing secret errors.
    """
    if boto3 is None:
        raise ImportError("The 'boto3' package is not installed. Run 'pip install boto3' to support AWS Secrets Manager.")
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    response = client.get_secret_value(SecretId=secret_name)
    
    # Parse the secret content
    if 'SecretString' in response:
        secret_content = response['SecretString']
    else:
        # Binary secret fallback
        import base64
        secret_content = base64.b64decode(response['SecretBinary']).decode('utf-8')
        
    try:
        return json.loads(secret_content)
    except json.JSONDecodeError:
        # Return as raw value mapped to a default key if not a structured JSON string
        return {"secret_value": secret_content}

def get_hashicorp_secret(vault_url: str, token: str, secret_path: str) -> Dict[str, Any]:
    """Retrieves credentials from HashiCorp Vault via requests GET."""
    url = f"{vault_url.rstrip('/')}/v1/{secret_path}"
    headers = {"X-Vault-Token": token}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json().get("data", {})
    if isinstance(data, dict) and "data" in data:
        return data["data"] # Support KV version 2 wrapper
    return data

def fetch_vault_secrets(
    provider: str, 
    secret_id: str, 
    region: str = "us-east-1", 
    vault_url: Optional[str] = None, 
    vault_token: Optional[str] = None
) -> Dict[str, Any]:
    """Unified entrypoint to fetch secrets in real-time.
    No mock data or static dictionaries are returned.
    """
    if provider == "AWS Secrets Manager":
        if not secret_id:
            raise ValueError("Secret Name / ARN is required for AWS Secrets Manager.")
        return get_aws_secret(secret_id, region)
        
    elif provider == "HashiCorp Vault":
        if not vault_url or not vault_token or not secret_id:
            raise ValueError("Vault URL, Access Token, and Secret Path are all required for HashiCorp Vault.")
        return get_hashicorp_secret(vault_url, vault_token, secret_id)
        
    else:
        raise ValueError(f"Unsupported secrets provider: {provider}")

if __name__ == "__main__":
    # Small test CLI to verify secrets manager loading
    import sys
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python secrets_manager.py aws <secret_name> [region]")
        print("  python secrets_manager.py vault <vault_url> <token> <path>")
        sys.exit(0)
        
    prov = sys.argv[1].lower()
    try:
        if prov == "aws":
            sec_name = sys.argv[2]
            reg = sys.argv[3] if len(sys.argv) > 3 else "us-east-1"
            print(f"Fetching AWS secret '{sec_name}' in region '{reg}'...")
            res = fetch_vault_secrets("AWS Secrets Manager", sec_name, region=reg)
            print("Successfully retrieved secret keys:", list(res.keys()))
        elif prov == "vault":
            v_url = sys.argv[2]
            v_tok = sys.argv[3]
            v_path = sys.argv[4]
            print(f"Fetching Vault path '{v_path}' from {v_url}...")
            res = fetch_vault_secrets("HashiCorp Vault", v_path, vault_url=v_url, vault_token=v_tok)
            print("Successfully retrieved secret keys:", list(res.keys()))
    except Exception as ex:
        print(f"Error fetching secret in real-time: {ex}")
