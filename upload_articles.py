from neo4j import GraphDatabase
import os
from datetime import datetime, timedelta
import requests
import urllib.parse
import streamlit as st
from libraries.neo4j_lib import Neo4jConnection

neo4j_config = {
    "username": os.environ.get("NEO4J_USER"),
    "password": os.environ.get("NEO4J_PWD"),
    "uri": "bolt://localhost:7687",
}

topic_test = (
    '("human trafficking") '
    'OR ("sex trafficking") '
    'OR ("modern slavery") '
    'OR ("debt bondage") '
    'OR ("sexual exploitation") '
    'OR ("child trafficking") '
    'OR ("organ trafficking") '
    'OR ("forced begging") '
    'OR ("domestic servitude") '
    'OR ("coerced criminality") '
    'OR ("exploitative sham marriages") '
    'OR ("cyber trafficking") '
    'OR ("trafficking biomedical research") '
)

username = os.environ.get("NEO4J_USER")
password = os.environ.get("NEO4J_PWD")
uri = "bolt://localhost:7687"
embed_dim = 1536

# Assuming you have these credentials (replace them with your actual credentials)


get_articles_query = """"""


# Prepare your query
query = """
MERGE (source:Source {name: $sourceName})
WITH source
OPTIONAL MATCH (author:Author {name: $authorName})
FOREACH(ignoreMe IN CASE WHEN $authorName IS NOT NULL THEN [1] ELSE [] END |
    MERGE (author)-[:AUTHORED]->(article)
)
MERGE (article:Article {
    title: $title,
    description: $description,
    url: $url,
    urlToImage: $urlToImage,
    publishedAt: $publishedAt,
    content: $content
})
MERGE (article)-[:HAS_SOURCE]->(source)
"""


# Don't forget to close the connection when done


newsapikey = {"key": st.secrets["newsapikey"]}

# Properly encoding the topic for URL
encoded_topic = urllib.parse.quote(topic_test)

for delta in range(0, 30):
    # print(delta)
    yesterday = datetime.now() - timedelta(days=delta + 1)
    start_date = yesterday.strftime("%Y-%m-%d")
    today = datetime.now() - timedelta(days=delta)
    end_date = yesterday.strftime("%Y-%m-%d")

    # Constructing the URL
    url = f"https://newsapi.org/v2/everything?q={topic_test}&from={start_date}&to={end_date}&sortBy=publishedAt&apiKey={newsapikey['key']['key']}"

    # Make the HTTP request to the API
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # Access the articles list
        articles = data.get("articles", [])

        # Example: print each article's title and url
        for article in articles:
            print(f"Title: {article['title']}, URL: {article['url']}")
    else:
        print(f"Failed to fetch articles, status code: {response.status_code}")

    for data in articles:
        parameters = {
            "sourceName": data["source"]["name"],
            "authorName": data["author"],
            "title": data["title"],
            "description": data["description"],
            "url": data["url"],
            "urlToImage": data["urlToImage"],
            "publishedAt": data["publishedAt"],
            "content": data["content"],
        }
        print(parameters)
        with Neo4jConnection(uri, username, password) as conn:
            result = conn.execute_query(query, parameters)
            print(result)
