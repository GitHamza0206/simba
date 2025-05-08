
from simba.core.factories.llm_factory import get_llm
from langchain_core.prompts import ChatPromptTemplate
from simba.models.simbadoc import SimbaDoc

llm = get_llm() 

prompt = ChatPromptTemplate.from_template(
    """
    # Extraction Prompt — Mode « Guideflexible »

            *(Generic Documents — Any Type of Document)*

            ## Role  
            Analyst tasked with condensing any document into a guide for use by an LLM for research purposes.  

            ## Objective  
            Extract **all** key points: concepts, amounts, clauses, actors, dates, relationships, and conditions; provide the LLM with a "map" to find any information, even from vague questions.  

            ## Content Guidelines  
            - Review the entire text; no relevant information should be omitted, even if it doesn't fit a predefined template.  
            - Summarize without personal interpretation; retain specific terminology and use quotation marks for significant clauses.  
            - When necessary, create your **own subheadings** to categorize atypical information.  
            - Mention every named entity (product, coverage, exclusion, stakeholder, instance, law, decree, amount, date, phone number, procedure).  
            - Briefly describe relationships or conditions (e.g., triggers, thresholds, dependencies between coverages).  
            - If information doesn't fit any category, place it under **"Other Key Points"**.  

            ## Style & Format  
            - **Flexible hierarchical Markdown**: you can add, rename, or remove sections according to the document.  
            - Each element: short sentence or bullet point ending with ";" or ".".  
            - No nested numbered lists > 2 levels to maintain readability.  
            - No JSON, no tables.  
            - Start with the short title of the document in **bold**, followed by a colon.  

            ## Skeleton (freely adaptable)  

            text  
            **Short Title**:  

            ### Overview  
            Brief summary of the purpose and scope of the document;  

            ### Key Concepts & Entities  
            - … ;  

            ### Coverages / Guarantees  
            - … ;  

            ### Conditions, Limits & Thresholds  
            - … ;  

            ### Procedures (Subscription, Claims, Cancellation, etc.)  
            - … ;  

            ### Legal Bases & References  
            - … ;  

            ### Other Key Points  
            - … ;  

            Here is the document:  
            {document}

    """
)

summary_chain = prompt | llm

def summarize_document(simbadoc : SimbaDoc) -> str: 
    docs_content = "\n\n".join(doc.page_content for doc in simbadoc.documents)
    response= summary_chain.invoke({"document": docs_content}) 
    return response.content