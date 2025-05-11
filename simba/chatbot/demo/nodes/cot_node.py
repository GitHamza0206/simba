from simba.chatbot.demo.state import State
from simba.core.factories.database_factory import get_database
from simba.chatbot.demo.chains.cot_chain import cot_chain
db =get_database() 
all_docs = db.get_all_documents()
all_summaries = "\n\n".join( f"**{doc.id}**\n{doc.metadata.summary}" for doc in all_docs)



def cot(state: State):
    question = state["messages"][-1].content
    sub_queries = state["sub_queries"] 
    response = cot_chain.invoke({"question": question, "sub_queries": sub_queries, "summaries": all_summaries})
    is_summary_enough = response.is_summary_enough
    ids, summaries = response.id, response.page_content
    if is_summary_enough:
        return {
            "summaries": summaries,
            "sub_queries": sub_queries,
            "question": question,
            "documents": [],
            "is_summary_enough": response.is_summary_enough
        }
    else:
        
        context = db.get_document(ids)
        return {

            "summaries": summaries,
            "sub_queries": sub_queries,
            "question": question,
            "documents": context,
            "is_summary_enough": response.is_summary_enough
        }