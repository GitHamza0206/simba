from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from simba.core.factories.llm_factory import get_llm


# Data model
class GradeCorrectness(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(description="Documents are relevant to the question, 'yes' or 'no'")


llm = get_llm()
structured_llm_grader = llm.with_structured_output(GradeCorrectness)

# Prompt
system = """You are a grader assessing whether a response actually answers the user's question. \n
    Your task is to determine if the response directly addresses and provides a meaningful answer to the question asked. \n
    Consider if the response: \n
    - Directly addresses the question's intent \n
    - Provides relevant information that answers the question \n
    - Avoids being off-topic or providing irrelevant information \n
    Give a binary score 'yes' or 'no' to indicate whether the response properly answers the question."""
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        (
            "human",
            "User question: {question} \n\n Response: {generation}",
        ),
    ]
)

correctness_chain = grade_prompt | structured_llm_grader
