import os
import pandas as pd
from llama_index.readers.web import SimpleWebPageReader
from llama_index.core import SummaryIndex
from libraries.neo4j_lib import Neo4jConnection
from time import sleep

username = os.environ.get("NEO4J_USER")
password = os.environ.get("NEO4J_PWD")
uri = "bolt://localhost:7687"

neo4j_query = (
    "MATCH (article:Article) RETURN article.url as url, ID(article) as id_ LIMIT 1;"
)
parameters = {}
with Neo4jConnection(uri, username, password) as conn:
    result = conn.execute_query(neo4j_query, parameters)
    print(result)
url = result[0]["url"]
id = result[0]["id_"]
documents = SimpleWebPageReader(html_to_text=True).load_data([url])
index = SummaryIndex.from_documents(documents)
# set Logging to DEBUG for more detailed outputs
query_engine = index.as_query_engine()

topic_test = (
    "'human trafficking '"
    "' OR sex trafficking '"
    "' OR modern slavery '"
    "' OR debt bondage '"
    "' OR sexual exploitation '"
    "' OR child trafficking '"
    "' OR organ trafficking '"
    "' OR forced begging '"
    "' OR domestic servitude '"
    "' OR coerced criminality '"
    "' OR exploitative sham marriages '"
    "' OR cyber trafficking '"
    "' OR trafficking for biomedical research '"
)
query1 = (
    "As a world renowned expert in analyzing reports related to human trafficking and exploitation, your task is to meticulously examine the content of the text"
    f" you are presented with for any of the following criminal activities: {topic_test}"
    " for factual evidence without relying on pre-existing knowledge. "
    "Firstly, determine if the article discusses any of the above criminal behaviours. Provide either exactly 'yes' or 'no'."
)

query2 = (
    "As a world renowned expert in analyzing reports related to human trafficking and exploitation, your task is to meticulously examine the content of the text you are presented with."
    "Identify if there are any suspects or accused individuals mentioned. If named, list their names; if not, indicate 'not named'."
    "Check for the presence of victims and whether their names are disclosed. If named, list their names; if not, state 'not named'."
    "Ascertain if the location of the incident is specified. If so, provide the location as accurately as possible mention any detail of interest."
    "Verify if the date and time of the incident is provided. If mentioned, provide it; otherwise, state 'no date mentioned'."
    "Carefully extract the nature of the incident if described. If detailed, describe the nature; otherwise, note 'the nature of the incident is unknown'."
    "Note if there are any other details of interest and provide them if available. If not, state 'no other details mentioned'."
    "Present the extracted information in a structured JSON format for clarity and ease of analysis."
)


query_engine = index.as_query_engine()
response = query_engine.query(query1)

parameters = {"id": result[0]["id_"], "evidence": response.response}
neo4j_update_query = "MATCH (article:Article) WHERE ID(article) = $id SET article.trafficking = $evidence;"

with Neo4jConnection(uri, username, password) as conn:
    result = conn.execute_query(neo4j_update_query, parameters)
    print(result)

neo4j_query = (
    "MATCH (article:Article) RETURN article.url as url, ID(article) as id_ LIMIT 1;"
)
parameters = {}

neo4j_query = """MATCH (article:Article)
WHERE article.trafficking IS NULL
RETURN article.url AS url, ID(article) AS id_"""
with Neo4jConnection(uri, username, password) as conn:
    result = conn.execute_query(neo4j_query, parameters)

for entry in result:
    url = entry["url"]
    # print(url)
    documents = SimpleWebPageReader(html_to_text=True).load_data([url])
    sleep(5)
    index = SummaryIndex.from_documents(documents)
    # set Logging to DEBUG for more detailed outputs
    query_engine = index.as_query_engine()
    response = query_engine.query(query1)
    parameters = {"id": entry["id_"], "evidence": response.response}
    neo4j_update_query = "MATCH (article:Article) WHERE ID(article) = $id SET article.trafficking = $evidence;"
    with Neo4jConnection(uri, username, password) as conn:
        result = conn.execute_query(neo4j_update_query, parameters)
        # print(result)
    print("response.response: ", response.response, "; url: ", url)

url = result[0]["url"]
id = result[0]["id_"]

neo4j_query = """MATCH (article:Article)
WHERE article.trafficking  =~ '(?i).*yes.*'
RETURN article.url AS url, ID(article) AS id_"""
with Neo4jConnection(uri, username, password) as conn:
    result = conn.execute_query(neo4j_query, parameters)

url = "https://bnnbreaking.com/breaking-news/crime/digital-lures-a-close-encounter-with-human-trafficking-on-the-indo-nepal-border"
for entry in result:
    url = entry["url"]
    # print(url)
    documents = SimpleWebPageReader(html_to_text=True).load_data([url])
    sleep(5)
    index = SummaryIndex.from_documents(documents)
    # set Logging to DEBUG for more detailed outputs
    query_engine = index.as_query_engine()
    response = query_engine.query(query2)
    parameters = {"id": entry["id_"], "narrative": response.response}
    neo4j_update_query = "MATCH (article:Article) WHERE ID(article) = $id SET article.narrative = $narrative;"
    with Neo4jConnection(uri, username, password) as conn:
        conn.execute_query(neo4j_update_query, parameters)
        # print(result)
    print("response.response: ", response.response, "; url: ", url)
