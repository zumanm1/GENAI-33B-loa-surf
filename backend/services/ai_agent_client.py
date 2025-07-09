import requests
import logging
import os

logger = logging.getLogger(__name__)

class AIAgentClient:
    """
    A client for interacting with the AI Agent microservice.
    """
    def __init__(self, base_url=None):
        """
        Initializes the client.

        Args:
            base_url (str): The base URL of the AI Agent service (e.g., http://localhost:5052).
                            If not provided, it will be read from the AI_AGENT_URL environment variable.
        """
        self.base_url = base_url or os.getenv('AI_AGENT_URL', 'http://127.0.0.1:5052')
        logger.info(f"AI Agent Client initialized for URL: {self.base_url}")

    def check_health(self):
        """
        Checks the health of the AI Agent and its dependent services.
        """
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to AI Agent for health check: {e}")
            return {"status": "unreachable", "error": str(e)}

    def query_rag(self, query, n_results=3):
        """
        Performs a RAG query through the AI Agent.

        Args:
            query (str): The user's query.
            n_results (int): The number of context documents to retrieve.

        Returns:
            dict: The JSON response from the AI Agent.
        """
        payload = {"query": query, "n_results": n_results}
        try:
            response = requests.post(f"{self.base_url}/api/rag/query", json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"AI Agent RAG query failed: {e}")
            return {"success": False, "error": f"Failed to connect to AI Agent: {str(e)}"}

    def analyze_config(self, config_text, device_name="Unknown"):
        """
        Sends a device configuration to the AI Agent for analysis.

        Args:
            config_text (str): The raw text of the device configuration.
            device_name (str): The name of the device.

        Returns:
            dict: The JSON response from the AI Agent.
        """
        payload = {"config_text": config_text, "device_name": device_name}
        try:
            response = requests.post(f"{self.base_url}/api/ai/analyze-config", json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"AI Agent config analysis failed: {e}")
            return {"success": False, "error": f"Failed to connect to AI Agent: {str(e)}"}
