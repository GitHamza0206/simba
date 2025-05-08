
from simba.core.factories.llm_factory import get_llm
from langchain_core.prompts import ChatPromptTemplate
from simba.models.simbadoc import SimbaDoc

llm = get_llm() 

prompt = ChatPromptTemplate.from_template(
    """
    # Extraction Prompt — Mode « Guideflexible »  
        *(Documents Atlanta Sanad – Assurances, Maroc)*  

        ## Rôle  
        Analyste assurance/juridique devant condenser tout document Atlanta Sanad (police, avenant, CGV, guide sinistre, FAQ, note interne, etc.) en un guide destiné à un LLM de recherche.

        ## Objectif  
        Restituer **tous** les points saillants : notions, montants, clauses, acteurs, dates, relations et conditions ; offrir au LLM une « carte » permettant de retrouver n’importe quelle information, même issue d’une question vague.

        ## Directives de Contenu  
        - Parcourir l’intégralité du texte ; aucune info pertinente ne doit être omise même si elle ne correspond pas à un gabarit pré‑défini.  
        - Synthétiser sans interprétation personnelle ; conserver le vocabulaire juridique, les guillemets pour les clauses importantes.  
        - Lorsque nécessaire, créer vos **propres sous-rubriques** pour ranger des informations atypiques.  
        - Mentionner chaque entité nommée (produit, garantie, exclusion, partie prenante, instance, loi, décret, montant, date, téléphone, procédure).  
        - Décrire brièvement les relations ou conditions (ex. déclencheurs, seuils, dépendances entre garanties).  
        - Si une information ne « rentre » nulle part, placer-la sous **« Autres points saillants »**.

        ## Style & Format  
        - Markdown hiérarchique **flexible** : vous pouvez ajouter, renommer ou supprimer des sections selon le document.  
        - Chaque élément : phrase courte ou puce terminée par « ; » ou « . ».  
        - Pas de listes numérotées imbriquées > 2 niveaux pour garder la lisibilité.  
        - Pas de JSON, pas de tableau.  
        - Commencer par le titre court du document en **gras**, suivi d’un « : ».

        ## Squelette (à adapter librement)  

        text
        **Titre Court** :

        ### Vue d’ensemble
        Bref résumé du but et de la portée du document ;

        ### Concepts & Entités clés
        - … ;

        ### Garanties / Couvertures
        - … ;

        ### Conditions, Plafonds & Seuils
        - … ;

        ### Procédures (Souscription, Sinistre, résiliation, etc.)
        - … ;

        ### Bases légales & Références
        - … ;

        ### Autres points saillants
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