from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from simba.core.factories.llm_factory import get_llm
from typing import List
# LLM
llm = get_llm()

class Questions(BaseModel):
    sub_queries: List[str] = Field(description="the 3 sub queries to be used for retrieval")


# Prompt
system = """
    **Role**    
    You are an assistant that helps information‑retrieval systems.  
    Your job is to:  

    1. **Reformulate the user’s original question** so it becomes clear, unambiguous, and search‑friendly.  
    2. **Propose 3 concise sub‑queries** that explore complementary angles (who, what, where, when, why, how, constraints, synonyms, connected entities, background context, edge cases).  
    3. Keep everything **short, specific, and self‑contained** so each line can be used verbatim in a search engine or vector index.  

    think step by step knowing that you're in context of insurance 
    """
re_write_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        (
            "human",
            "Here is the initial question: \n\n {question} \n",
        ),
    ]
)

question_rewrite_chain = re_write_prompt | llm.with_structured_output(Questions)
