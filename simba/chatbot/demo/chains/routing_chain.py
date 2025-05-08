from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from simba.core.factories.llm_factory import get_llm

llm = get_llm()

class Route(BaseModel):
    route: str = Field(description="The route to take, either 'transform_query' or 'fallback'")

routing_prompt = ChatPromptTemplate.from_template(
    """
      You are an assistant router for a document management system.
      You are tasked with analyzing user queries related to various types of documents.

      Your task is to analyze the user's message and determine the appropriate route:

      - Choose 'transform_query' if the message is:
        * Related to the specific type of documents managed (e.g., legal documents, technical manuals, research papers).
        * Pertains to document retrieval, content specifics, summaries, etc.

      - Choose 'fallback' if the message is:
        * Not directly related to document management or retrieval.
        * Off-topic, general, or cannot be answered within the document context.

      User message: {question}
      Route (respond with only 'transform_query' or 'fallback'):
      """
)


routing_chain = routing_prompt | llm.with_structured_output(Route)