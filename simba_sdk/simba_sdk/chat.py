from typing import Dict, Any, Optional

class ChatManager:
    """
    A class that provides chat functionality for interacting with Simba.
    Handles queries and conversations with the Simba AI.
    """

    def __init__(self, client):
        """
        Initialize the ChatManager with a SimbaClient instance.
        
        Args:
            client: An instance of SimbaClient
        """
        self.client = client
        
    def ask(self, query: str) -> Dict[str, Any]:
        """
        Send a query to the Simba chat endpoint.
        
        Args:
            query (str): The query to send to Simba.
        
        Returns:
            Dict[str, Any]: The response from the server.
        """
        return self.client._make_request(
            "POST", 
            "chat", 
            json={"message": query}
        )
        
    # Future chat methods could go here, such as:
    # - create_conversation()
    # - continue_conversation()
    # - get_chat_history() 