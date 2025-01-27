# Chain
from langchain import hub
from core.factories.llm_factory import get_llm
from langchain_core.output_parsers import StrOutputParser

prompt = hub.pull("rlm/rag-prompt")
llm = get_llm()
generate_chain = prompt | llm | StrOutputParser()