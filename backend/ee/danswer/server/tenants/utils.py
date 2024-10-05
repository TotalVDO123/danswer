import requests

from danswer.configs.app_configs import CONTROLPLANE_API_URL
from danswer.utils.logger import setup_logger
from ee.danswer.server.tenants.access import generate_data_plane_token

logger = setup_logger()


def fetch_tenant_stripe_information(tenant_id: str) -> dict:
    token = generate_data_plane_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",  # Include if sending JSON data
    }
    url = f"{CONTROLPLANE_API_URL}/tenant-stripe-information"
    params = {"tenant_id": tenant_id}  # Use params for query parameters
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def fetch_billing_information(tenant_id: str) -> dict:
    logger.info("Fetching billing information")
    token = generate_data_plane_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    url = f"{CONTROLPLANE_API_URL}/billing-information"
    params = {"tenant_id": tenant_id}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    billing_info = response.json()
    logger.info("Billing information fetched", billing_info)
    return billing_info
