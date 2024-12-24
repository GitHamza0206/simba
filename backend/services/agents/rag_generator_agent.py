from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
import os
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables from .env file
load_dotenv()
# Pydantic model for input data validation
class GenerationInput(BaseModel):
    context: List[str] = Field(..., description="The list of documents' content for the context")
    question: str = Field(..., description="The question that needs to be answered based on the context")




# Class implementation
class RAGGenerator:
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0):


        # Define the prompt template with the correct variables
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Use the following context to answer questions:\n\n{context}"),
            ("human", "{question}"),
            ("system", "The following are the previous messages from the user, you can use them to answer the question:\n\n{messages}"),
            
        ])

        
        # Pull the prompt from the hub
        self.prompt = prompt

        # Initialize the language model
        self.llm = ChatOpenAI(
                            model_name="gpt-4o",
                            temperature=0, 
                            openai_api_key=os.getenv('OPENAI_API_KEY'),
                            streaming=True
                            )

        
        # Output parser
        self.output_parser = StrOutputParser()
        
        # Chain the prompt, LLM, and output parser together
        # self.rag_chain = self.prompt | self.llm | self.output_parser
        # Initialize the conversation chain with correct configuration
        
        

    @staticmethod
    def format_docs(docs: List[str]) -> str:
        """
        Format the list of document contents into a single string.
        """
        return "\n\n".join(docs)

    def invoke(self, input_data: dict):
        """
        Run the RAG generation process.
        """
        context = input_data.get('context', [])
        question = input_data.get('question', '')
        messages = input_data.get('messages', [])[:-1] # Exclude the last message
        
        if hasattr(context, 'page_content'):
            page_contents = [context.page_content]
        else:
            page_contents = [doc.page_content for doc in context]
            
        formatted_content = self.format_docs(page_contents)

        chain = self.prompt | self.llm

        inputs = {
            "context": formatted_content,
            "question": question,
            "messages": messages
        }
        
        return chain.invoke(inputs)
    
    async def astream(self, input_data: dict):
        """
        Stream the RAG generation process asynchronously.
        """
        context = input_data.get('context', [])
        question = input_data.get('question', '')
        
        if hasattr(context, 'page_content'):
            page_contents = [context.page_content]
        else:
            page_contents = [doc.page_content for doc in context]
            
        formatted_content = self.format_docs(page_contents)

        chain = self.prompt | self.llm

        inputs = {
            "context": formatted_content,
            "question": question
        }
        
        async for chunk in chain.astream(inputs):
            response_data = {
                "generation": chunk
            }
            yield response_data
    
    
   
# Example usage
if __name__ == "__main__":
    # Example documents and question
    docs = [
        "This is the content of document 1.",
        "Here is the content of document 2.",
        "The content of document 3 goes here."
    ]
    question = "What information is contained in these documents?"

    # Create an instance of GenerationInput
    input_data = GenerationInput(context=docs, question=question)

    # Create an instance of RAGGenerator
    rag_generator = RAGGenerator()
    
    # Generate the answer
    result = rag_generator.invoke(input_data)
    
    # Print the generated result
    print(f"Generated Answer: {result}")
