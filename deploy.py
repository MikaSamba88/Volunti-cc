import requests
import os
import sys
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# From Gitlab CI/CD
PORTAINER_URL = os.getenv("PORTAINER_URL")
API_KEY = os.getenv("PORTAINER_TOKEN")

DEFAULT_STACK_NAME = f"volunti-{os.getenv('CI_PROJECT_NAME')}'{os.getenv('CI_COMMIT_REF_SLUG')}"
STACK_NAME = os.getenv("STACK_NAME", DEFAULT_STACK_NAME)
COMPOSE_FILE = os.getenv("COMPOSE_FILE", "docker-compose.yml")

SUBSTITUTE_VARS = os.getenv("SUBSTITUTE_VARS", "false").lower() == "true"
PUBLIC_HOST = os.getenv("PUBLIC_HOST")
mssql_sa_password = os.getenv("MSSQL_SA_PASSWORD", "")
jwt_signing_key = os.getenv("JWT_SIGNING_KEY", "")
ENDPOINT_ID = 8

# Load the compose-file
COMPOSE_FILE = "docker-compose.yml"

if not PORTAINER_URL or not API_KEY:
    print("Error: PORTAINER_URL and PORTAINER_API_TOKEN environment variables must be set.")
    sys.exit(1)

headers = {
    "X-API-Key": API_KEY
}

def get_endpoint_id():
    """Finding ID for Environment"""
    url = f"{PORTAINER_URL}/api/endpoints"
    print(f"Debug: URL is {url}") # Kolla om det blir dubbla // här
    print(f"Debug: Token length is {len(API_KEY) if API_KEY else 'EMPTY'}")
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()

        endpoints = response.json()
        for ep in endpoints:
            if ep["Name"] == "local-swarm":
                return ep["Id"]
            
        # If Endpoint not found, take first available
        return endpoints[0]["Id"] if endpoints else None
    except Exception as e:
        print(f"Error fetching endpoints: {e}")
        sys.exit(1)

def get_swarm_id(endpoint_id):
    """Get Swarm ID from the endpoint"""
    url = f"{PORTAINER_URL}/api/endpoints/{endpoint_id}/docker/swarm"
    print(f"Debug: Fetching swarm ID from {url}")
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        swarm_data = response.json()
        swarm_id = swarm_data.get("ID")
        print(f"Debug: Swarm ID = {swarm_id}")
        return swarm_id
    except Exception as e:
        print(f"Error fetching swarm ID: {e}")
        return None

def deploy_stack(endpoint_id, swarm_id):
# Deploying stack to Portainer
    with open(COMPOSE_FILE, 'r') as f:
        compose_content = f.read()

    if SUBSTITUTE_VARS:
        image_path = os.getenv("CI_REGISTRY_IMAGE", "")
        image_tag = os.getenv("IMAGE_TAG", "latest")
        project_slug = os.getenv("CI_PROJECT_NAME", "my-project").lower()


    compose_content = compose_content.replace("${CI_REGISTRY_IMAGE}", image_path)
    compose_content = compose_content.replace("${IMAGE_TAG}", image_tag)
    compose_content = compose_content.replace("${STACK_NAME}", STACK_NAME)
    compose_content = compose_content.replace("${PUBLIC_HOST}", PUBLIC_HOST)
    compose_content = compose_content.replace("${PROJECT_SLUG}", project_slug)
    compose_content = compose_content.replace("${MSSQL_SA_PASSWORD}", mssql_sa_password)
    compose_content = compose_content.replace("${JWT_SIGNING_KEY}", jwt_signing_key)
    print(f"DEBUG: Image line is: {[line for line in compose_content.splitlines() if 'image:' in line]}")


    stack_url = f"{PORTAINER_URL}/api/stacks"
    params = {"filters": json.dumps({"Name": [STACK_NAME]})}
    r_list = requests.get(stack_url, headers=headers, params=params, verify=False)
    all_stacks = r_list.json()
    existing_stacks = [s for s in all_stacks if s["Name"] == STACK_NAME]

    if existing_stacks:
        stack_id = existing_stacks[0]["Id"]
        print(f"Updating existing stack '{STACK_NAME}' (ID: {stack_id})")
        url = f"{PORTAINER_URL}/api/stacks/{stack_id}?endpointId={endpoint_id}"
        payload = {
            "StackFileContent": compose_content,
            "prune": True,
            "PullImage": True
        }
        r = requests.put(url, headers=headers, json=payload, verify=False)
    else:
        print(f"Creating new stack '{STACK_NAME}'")
        url = f"{PORTAINER_URL}/api/stacks/create/swarm/string?endpointId={endpoint_id}"
        payload = {
            "Name": STACK_NAME,
            "StackFileContent": compose_content,
            "SwarmID": swarm_id,
            "Prune": True
        }
        print(url)
        r = requests.post(url, headers=headers, json=payload, verify=False)
    if r.status_code in [200, 204]:
        print(f"Stack '{STACK_NAME}' deployed successfully.")
    else:
        print(f"Failed to deploy stack '{STACK_NAME}'. Status code: {r.status_code}, Response: {r.text}")
        sys.exit(1)

if __name__ == "__main__":
    eid = get_endpoint_id()
    if eid:
        sid = get_swarm_id(eid)
        print(f"Using Endpoint ID: {eid} with Swarm ID: {sid}")
        deploy_stack(eid, sid)
    else:
        print("No endpoints found in Portainer.")
        sys.exit(1)
