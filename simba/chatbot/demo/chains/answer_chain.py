from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from simba.core.factories.llm_factory import get_llm


# Data model
class GradeAnswer(BaseModel):
    """Binary score to assess answer addresses question."""

    binary_score: str = Field(description="Answer addresses the question, 'yes' or 'no'")


# LLM with function call
llm = get_llm()
structured_llm_grader = llm.with_structured_output(GradeAnswer)

# Prompt
system = """You are a grader assessing whether an answer addresses / resolves a question \n
     Give a binary score 'yes' or 'no'. Yes' means that the answer resolves the question."""
answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        (
            "human",
            "User question: \n\n {question} \n\n LLM generation: {generation}",
        ),
    ]
)

answer_chain = answer_prompt | structured_llm_grader
