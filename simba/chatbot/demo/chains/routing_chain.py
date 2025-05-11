from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from simba.core.factories.llm_factory import get_llm

llm = get_llm()

class Route(BaseModel):
    route: str = Field(description="The route to take, either 'transform_query' or 'fallback'")

routing_prompt = ChatPromptTemplate.from_template(
    """
    You are a router for insurance company  assistant.
    You are member of the company and you talk to internal employees
    All the questions are related to insurance.
    If user ask a question like who's the CEO ? should guess that's it's related to atlanta
    Your task is to analyze the user's message and determine the appropriate route:

    - Choose 'transform_query' if the message is:
      * Related to Atlanta (the city, events, travel, etc.)
      * Related to insurance (questions about insurance, coverage, claims, etc.)

    - Choose 'fallback' if the message is:
      * Not related to Atlanta or insurance
      * Off-topic, general, or cannot be answered by the system

    User message: {question}
    Route (respond with only 'transform_query' or 'fallback'):
    """
)


routing_chain = routing_prompt | llm.with_structured_output(Route)