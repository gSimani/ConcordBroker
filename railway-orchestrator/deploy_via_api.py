#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway Deployment via GraphQL API
Deploys the orchestrator using Railway's API instead of CLI
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Load environment
load_dotenv('../.env.mcp')

# Railway configuration
RAILWAY_API_TOKEN = os.getenv('RAILWAY_API_TOKEN')
RAILWAY_PROJECT_ID = os.getenv('RAILWAY_PROJECT_ID')
RAILWAY_ENVIRONMENT = os.getenv('RAILWAY_ENVIRONMENT', 'production')

RAILWAY_API_URL = 'https://backboard.railway.app/graphql/v2'

def graphql_query(query, variables=None):
    """Execute a GraphQL query against Railway API"""
    headers = {
        'Authorization': f'Bearer {RAILWAY_API_TOKEN}',
        'Content-Type': 'application/json',
    }

    payload = {
        'query': query,
        'variables': variables or {}
    }

    response = requests.post(RAILWAY_API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"❌ API Error: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    if 'errors' in data:
        print(f"❌ GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
        return None

    return data.get('data')

def get_project_info():
    """Get project information"""
    query = """
    query project($id: String!) {
      project(id: $id) {
        id
        name
        services {
          edges {
            node {
              id
              name
            }
          }
        }
      }
    }
    """

    result = graphql_query(query, {'id': RAILWAY_PROJECT_ID})
    if result:
        return result.get('project')
    return None

def create_service():
    """Create a new service in the project"""
    query = """
    mutation serviceCreate($input: ServiceCreateInput!) {
      serviceCreate(input: $input) {
        id
        name
      }
    }
    """

    variables = {
        'input': {
            'projectId': RAILWAY_PROJECT_ID,
            'name': 'concordbroker-orchestrator',
            'source': {
                'repo': 'gSimani/ConcordBroker',
                'rootDirectory': 'railway-orchestrator'
            }
        }
    }

    result = graphql_query(query, variables)
    if result:
        return result.get('serviceCreate')
    return None

def set_environment_variables(service_id):
    """Set environment variables for the service"""
    env_vars = {
        'SUPABASE_HOST': 'aws-1-us-east-1.pooler.supabase.com',
        'SUPABASE_DB': 'postgres',
        'SUPABASE_USER': 'postgres.pmispwtdngkcmsrsjwbp',
        'SUPABASE_PASSWORD': 'West@Boca613!',
        'SUPABASE_PORT': '5432',
        'DB_POOL_MIN': '5',
        'DB_POOL_MAX': '20',
        'PYTHONUNBUFFERED': '1'
    }

    query = """
    mutation variableUpsert($input: VariableUpsertInput!) {
      variableUpsert(input: $input)
    }
    """

    for key, value in env_vars.items():
        variables = {
            'input': {
                'projectId': RAILWAY_PROJECT_ID,
                'environmentId': RAILWAY_ENVIRONMENT,
                'serviceId': service_id,
                'name': key,
                'value': value
            }
        }

        result = graphql_query(query, variables)
        if result:
            print(f"  ✅ Set {key}")
        else:
            print(f"  ❌ Failed to set {key}")

def deploy_service(service_id):
    """Trigger a deployment"""
    query = """
    mutation serviceInstanceDeploy($serviceId: String!) {
      serviceInstanceDeploy(serviceId: $serviceId) {
        id
      }
    }
    """

    result = graphql_query(query, {'serviceId': service_id})
    if result:
        return result.get('serviceInstanceDeploy')
    return None

def main():
    print("🚂 Railway Deployment via API")
    print("=" * 70)
    print()

    if not RAILWAY_API_TOKEN:
        print("❌ RAILWAY_API_TOKEN not found in .env.mcp")
        sys.exit(1)

    if not RAILWAY_PROJECT_ID:
        print("❌ RAILWAY_PROJECT_ID not found in .env.mcp")
        sys.exit(1)

    print(f"📋 Project ID: {RAILWAY_PROJECT_ID}")
    print()

    # Get project info
    print("[1/4] Getting project information...")
    project = get_project_info()
    if not project:
        print("❌ Failed to get project info")
        sys.exit(1)

    print(f"  ✅ Project: {project['name']}")
    print()

    # Check if service already exists
    existing_services = [s['node'] for s in project.get('services', {}).get('edges', [])]
    orchestrator_service = next((s for s in existing_services if 'orchestrator' in s['name'].lower()), None)

    if orchestrator_service:
        print(f"  ℹ️  Service already exists: {orchestrator_service['name']}")
        service_id = orchestrator_service['id']
    else:
        # Create service
        print("[2/4] Creating service...")
        service = create_service()
        if not service:
            print("❌ Failed to create service")
            print("\nNote: You may need to create the service manually via Railway dashboard")
            print("      or use the CLI with: railway login && railway up")
            sys.exit(1)

        print(f"  ✅ Service created: {service['name']}")
        service_id = service['id']

    print()

    # Set environment variables
    print("[3/4] Setting environment variables...")
    set_environment_variables(service_id)
    print()

    # Deploy
    print("[4/4] Triggering deployment...")
    deployment = deploy_service(service_id)
    if deployment:
        print(f"  ✅ Deployment started: {deployment['id']}")
    else:
        print("  ⚠️  Could not trigger deployment via API")
        print("     Please deploy manually via Railway dashboard or CLI")

    print()
    print("=" * 70)
    print("Next steps:")
    print("1. Check deployment status in Railway dashboard")
    print("2. View logs: railway logs")
    print("3. Monitor health: Check agent_registry in Supabase")
    print()

if __name__ == "__main__":
    main()
