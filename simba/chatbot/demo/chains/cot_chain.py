from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from simba.core.factories.llm_factory import get_llm
from typing import List
class DocumentSelectorChain(BaseModel):
    id: List[str] = Field(description="The id of the document")   
    page_content: List[str] = Field(description="The page content of the document")       


prompt = ChatPromptTemplate.from_template(
    """
    # Prompt « Sélection Top 5 »
    *(RAG – Documents Atlanta Sanad, liste de glossaires structurés)*

    ## Contexte
    Tu reçois :
    1. **Question principale** de l'utilisateur ;
    2. **Liste Q** : variantes reformulées (Q1…Qn) ;
    3. **Corpus** : N documents déjà résumés sous forme de glossaires hiérarchiques Markdown (cf. prompt d'extraction).

    ## Rôle
    Agir comme moteur de recherche expert : identifier **jusqu'à 5 documents** les plus pertinents pour répondre à la question, en tenant compte des variantes Q1…Qn.

    ## Critères de Pertinence (par ordre décroissant)
    1. **Correspondance sémantique** avec concepts, garanties, exclusions, montants, dates, acteurs cités dans la question ou ses reformulations ;
    2. **Chevauchement lexical** (mots exacts, synonymes, acronyms) ;
    3. **Spécificité** : un document ciblant précisément le sujet > un document généraliste ;
    4. **Hiérarchie interne** : si la section *Garanties Couvertures* ou *Conditions* traite directement d'un terme clé, bonus ;
    5. **Actualité** : privilégier les versions ou avenants les plus récents si date disponible ;
    6. **Type de doc** : Police avenant > Guide sinistre > FAQ > CGV > Note interne, sauf si la question appelle explicitement un autre type.

    ## Directives d'Extraction
    - **Ne lis que les glossaires fournis** ; n'invente rien.
    - Lorsque plusieurs docs semblent équivalents, choisis celui qui couvre **le plus grand nombre d'entités** mentionnées dans Q & Qn.
    - Si < 5 documents atteignent un seuil de pertinence raisonnable, retourne-en moins, jamais plus de 5.

    ## Format de Sortie
    Renvoie l'ID du document et le contenu du document.

    Here is the question:
    {question}
    Here are sub queries:
    {sub_queries}
    Here is the context:
    {summaries}
    """
)

llm = get_llm()
cot_chain = prompt | llm.with_structured_output(DocumentSelectorChain)

