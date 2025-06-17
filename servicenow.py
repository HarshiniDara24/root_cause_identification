import os
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SERVICENOW_INSTANCE = os.getenv("SERVICENOW_INSTANCE")
SERVICENOW_USERNAME = os.getenv("SERVICENOW_USERNAME")
SERVICENOW_PASSWORD = os.getenv("SERVICENOW_PASSWORD")

if not SERVICENOW_INSTANCE or not SERVICENOW_USERNAME or not SERVICENOW_PASSWORD:
    raise ValueError("Missing ServiceNow credentials. Check your .env file.")

async def fetch_defects(limit=10):
    """
    Fetch defect (incident) details from ServiceNow.
    """
    url = f"https://{SERVICENOW_INSTANCE}/api/now/table/incident.json"
    params = {
        "sysparm_limit": limit,
        "sysparm_query": "",  # Add query filters if needed
        "sysparm_fields": "sys_id,number,short_description,state,priority"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            auth=(SERVICENOW_USERNAME, SERVICENOW_PASSWORD),
            headers={"Accept": "application/json"},
            params=params,
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
