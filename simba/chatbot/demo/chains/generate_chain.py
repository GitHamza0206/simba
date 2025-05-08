# Chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from simba.core.factories.llm_factory import get_llm

# prompt = hub.pull("rlm/rag-prompt")
prompt_template = ChatPromptTemplate.from_template(
    """
    You are a helpful assistant
    Your name is Simba.
    You are able to answer questions about the documents in the context.
    You are also able to reason and provide general answers
    You always respond in the user's language.
    Here are the summaries of the documents that are well fromated to help you answer the question:
    {summaries}
    Here is the question:
    {question}
    Here is the context:
    {context}
    Here is the chat history:
    {chat_history}
    Answer:
"""
)

llm = get_llm()
generate_chain = prompt_template | llm | StrOutputParser()
