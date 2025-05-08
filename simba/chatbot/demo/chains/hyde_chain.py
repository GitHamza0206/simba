# Prompt template for HyDE
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from simba.core.factories.llm_factory import get_llm

HYDE_PROMPT = """You are Atlanta Sanad's AI insurance assistant, specializing in insurance documentation and customer service. 
You have extensive knowledge of insurance policies, claims, and customer information from Atlanta Sanad's documentation.

Your task is to write a clear, informative passage that would likely contain the answer to the user's question, 
as if it came from Atlanta Sanad's internal documentation or customer communications.

Important Guidelines:
- Write in a professional insurance industry style
- Focus on Atlanta Sanad's insurance-specific information and processes
- Include relevant insurance terms and policy details when appropriate
- Keep the response focused and concise (2-3 sentences)
- Write as if this was a snippet from an official Atlanta Sanad document
- Do not include phrases like "this document explains" or meta-references
- Maintain the formal tone used in insurance documentation
- Reference specific Atlanta Sanad procedures or policies when relevant

Write a hypothetical document that would answer this question as if it was extracted from Atlanta Sanad's documentation:"""

hyde_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", HYDE_PROMPT),
        (
            "human",
            "User Question: {question}",
        ),
    ]
)

llm = get_llm()
hyde_chain = hyde_prompt | llm

