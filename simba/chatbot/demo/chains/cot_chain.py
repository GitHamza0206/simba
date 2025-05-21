from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from simba.core.factories.llm_factory import get_llm
from typing import List
class DocumentSelectorChain(BaseModel):
    is_summary_enough: bool = Field(description="True if the summary is enough to answer the question, False otherwise")
    id: List[str] = Field(description="The id of the document")   
    page_content: List[str] = Field(description="The page content of the document")       


prompt = ChatPromptTemplate.from_template(
    """
    # Document Selection Expert Prompt

    ## Context
    You receive:
    1. A **Primary Question** from the user;
    2. **Query List**: Reformulated variations (Q1...Qn) of the primary question;
    3. **Corpus**: N documents already summarized in hierarchical Markdown format.

    ## Role
    Act as an expert search engine: identify **up to 5 documents** most relevant to answering the question, considering all query variations Q1...Qn.

    ## Relevance Criteria (in decreasing order of importance)
    1. **Semantic Correspondence** with key concepts, terms, entities, figures, dates, or actors mentioned in the question or its reformulations;
    2. **Lexical Overlap** (exact words, synonyms, acronyms, technical terms);
    3. **Specificity**: documents directly addressing the topic > general documents;
    4. **Internal Structure**: documents with sections specifically covering key terms receive higher priority;
    5. **Recency**: prefer more recent versions or updates if date information is available;
    6. **Document Type**: prioritize authoritative primary sources over secondary references, unless the question explicitly requires otherwise.

    ## Extraction Guidelines
    - **Only read the provided summaries**; do not invent information.
    - When multiple documents appear equally relevant, choose those covering the **greatest number of entities** mentioned in the primary question and variations.
    - Return fewer than 5 documents if only those meet a reasonable relevance threshold, never more than 5.

    ## Output Format
    Return the document ID and document content for each selected document.
    If the context provided is sufficient to answer the question, set is_summary_enough to True, otherwise False.

    Here is the question:
    {question}
    Here are sub queries:
    {sub_queries}
    Here is the context:
    {summaries}

    
    YOUR MUST SPEAK IN CHINESE 
    """
)

llm = get_llm()
cot_chain = prompt | llm.with_structured_output(DocumentSelectorChain)

