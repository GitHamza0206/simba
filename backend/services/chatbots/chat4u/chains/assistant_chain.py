
from core.factories.llm_factory import get_llm
from ..tools.retrieve_tool import retrieve
from langchain_core.output_parsers import StrOutputParser

llm  = get_llm()
tools = [retrieve]
# we bind tools to assistant
assistant_chain =  llm.bind_tools(tools) 
