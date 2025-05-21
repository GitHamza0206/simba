from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from simba.core.factories.llm_factory import get_llm

llm = get_llm()

class Route(BaseModel):
    route: str = Field(description="The route to take, either 'transform_query' or 'generate'")

routing_prompt = ChatPromptTemplate.from_template(
    """
     # Universal Query Router Prompt

      ## Role
      You are an intelligent routing system that determines whether user queries require specialized processing or should use a fallback pathway.

      ## Task
      Analyze the user's message and determine the appropriate routing pathway based on the query content and intent.

      ## Routing Criteria
      - Choose 'transform_query' if the message:
        * Contains a clear, answerable question
        * Requests specific information, instructions, or assistance
        * Falls within the scope of topics that can be addressed by the system
        * Would benefit from additional processing or retrieval of information

      - Choose 'generate' if the message:
        * The user is greeting and saying hello or hi or goodbye or thank you 
        * Is ambiguous or unclear in intent
        * Contains inappropriate content
        * Requests information beyond the system's capabilities
        * Is clearly off-topic or unrelated to supported domains
        * Is too generic to be processed effectively

      ## Output Format
      Respond with only 'transform_query' or 'generate' as the route value.

      User message: {question}
      Route:
    """
)


routing_chain = routing_prompt | llm.with_structured_output(Route)