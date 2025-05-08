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
    # Prompt « Sélection Top 5 »
        *(RAG – General Documents, structured glossary list)*

        ## Context
        You receive:
        1. **Main question** from the user;
        2. **Q List**: reformulated variants (Q1…Qn);
        3. **Corpus**: N documents already summarized in hierarchical Markdown glossaries (see extraction prompt).

        ## Role
        Act as an expert search engine: identify **up to 5 documents** most relevant to answer the question, considering variants Q1…Qn.

        ## Relevance Criteria (in descending order)
        1. **Semantic match** with concepts, guarantees, exclusions, amounts, dates, actors mentioned in the question or its reformulations;
        2. **Lexical overlap** (exact words, synonyms, acronyms);
        3. **Specificity**: a document specifically targeting the subject > a generalist document;
        4. **Internal hierarchy**: if the *Coverage Guarantees* or *Conditions* section directly addresses a key term, bonus points;
        5. **Freshness**: prioritize newer versions or amendments if date available;
        6. **Document type**: Endorsement Policy > Claims Guide > FAQ > Terms of Service > Internal Memo, unless the question explicitly calls for another type.

        ## Extraction Guidelines
        - **Only read the provided glossaries**; do not invent any information.
        - When multiple documents seem equivalent, choose the one covering **the most entities** mentioned in Q & Qn.
        - If fewer than 5 documents meet a reasonable relevance threshold, return fewer, never more than 5.

        ## Output Format
        Return the document ID and its content.

        Here is the question:
        {question}
        Here are sub queries:
        {sub_queries}
        Here is the context:
        {summaries}
        If the context is enough to answer the question, is_summary_enough is True else False.

    """
)

llm = get_llm()
cot_chain = prompt | llm.with_structured_output(DocumentSelectorChain)

