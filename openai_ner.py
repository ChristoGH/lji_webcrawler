# https://jorgepit-14189.medium.com/ner-with-openai-and-langchain-687814196a26
from typing import List
from pydantic import BaseModel, Field
import requests
import bs4
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
import os
import langchain_core.utils.function_calling
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from libraries.neo4j_lib import Neo4jConnection

neo4j_config = {
    "username": os.environ.get("NEO4J_USER"),
    "password": os.environ.get("NEO4J_PWD"),
    "uri": "bolt://localhost:7687",
}
model = ChatOpenAI(temperature=0)

trafficking_terms = [
    '"human trafficking"',
    '"cyber trafficking"',
    '"child trafficking"',
]
legal_action_terms = ["suspect", "victim", "arrest", "prosecute"]

# Construct the parts of the query
trafficking_query_part = f"({' OR '.join(trafficking_terms)})"
legal_action_query_part = f"({' OR '.join(legal_action_terms)})"

# Combine parts into the final query
query = f"{trafficking_query_part} {legal_action_query_part} after:{start_date_str} before:{end_date_str}"


class NER(BaseModel):
    """We want to extract the 'name', 'age', 'date', 'address', 'phone' and 'bank account' entities"""

    ner: List[str] = Field(
        description="the detected entity in the document such as author, victim, suspect, age, date, address, phone, city, country"
    )
    type: List[str] = Field(
        description="the type of the detected entity with possible values: 'author', 'victim', 'suspect', 'age', 'date', 'address', 'phone', 'city', 'country'. For every entity detected in ner this should be the corresponding type"
    )


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Extract the relevant information, if not explicitly provided do not guess. Extract partial info",
        ),
        ("human", "{input}"),
    ]
)
extraction_functions = [convert_pydantic_to_openai_function(NER)]
# extraction_functions = [convert_to_openai_function(NER)]
extraction_model = model.bind(
    functions=extraction_functions, function_call={"name": "NER"}
)

extraction_chain = prompt | extraction_model | JsonOutputFunctionsParser()
url = "https://www.withinnigeria.com/news/2024/03/03/suspected-human-trafficker-arrested-in-kaduna/"
response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = bs4.BeautifulSoup(response.text, "lxml")
text = soup.body.get_text(" ", strip=True)
ner_types = extraction_chain.invoke({"input": text})

for entity, entity_type in zip(ner_types["ner"], ner_types["type"]):
    print(entity, entity_type)
    parameters = {"name": entity, "entity_type": entity_type, "url": url}

    query = f"""MATCH (search_result:SearchResult {{url: $url}})
    WITH search_result
    MERGE (entity:{entity_type.title()} {{name: $name}})
    MERGE (search_result)-[:HAS_ENTITY]->(entity)
        """
    print(parameters)
    with Neo4jConnection(
        neo4j_config["uri"], neo4j_config["username"], neo4j_config["password"]
    ) as conn:
        result = conn.execute_query(query, parameters)
        print(result)

import spacy
import requests
from bs4 import BeautifulSoup

# Load the pre-trained English language model
nlp = spacy.load("en_core_web_sm")
doc = nlp(text)

# Print the named entities and their labels
for ent in doc.ents:
    print(f"{ent.text}: {ent.label_}")
