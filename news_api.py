from newsapi import NewsApiClient
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from llama_index.core import download_loader
from llama_index.core import VectorStoreIndex, ServiceContext
from llama_index.core import (
    GPTVectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
from libraries.ner import build_storage, read_from_storage
import urllib.parse
import os
import requests
import json
from datetime import datetime, timedelta

# Init
newsapikey = st.secrets["newsapikey"]
newsapi = NewsApiClient(api_key=newsapikey["key"])
newsapi.get_sources()

# /v2/top-headlines
top_headlines = newsapi.get_top_headlines(
    q="cyber trafficking",
    sources="bbc-news,the-verge, abc-news, cnn, fox-news, google-news, nbc-news, the-wall-street-journal, the-washington-post, time, usa-today, the-new-york-times, the-huffington-post, the-guardian-uk, the-telegraph, the-times-of-india, the-hindu, the-economist, the-financial-times, the-globe-and-mail",
    # category='business',
    language="en",
)

# /v2/everything
all_articles = newsapi.get_everything(
    q="social media",  # sources='bbc-news,wsj',
    domains="bbc.co.uk,techcrunch.com,engadget.com,nytimes.com,wsj.com,theguardian.com,thetimes.co.uk,telegraph.co.uk,thetelegraph.co.uk,thetimes.co.uk,theguardian.co.uk,theguardian.com",
    from_param="2024-01-24",
    to="2024-02-23",
    # language='en',
    sort_by="relevancy",
    page=5,
)
all_articles.get("articles")
# /v2/top-headlines/sources
sources = newsapi.get_sources()


# topic='((human OR sex OR child) + (exploitation OR trafficking)) OR (forced + (labour OR prostitution OR marriage)) OR (modern slavery)'
# topic='Baglung Municipality, Baglung'
# Your API URL
yesterday = datetime.now() - timedelta(days=1)
yesterday_str = yesterday.strftime("%Y-%m-%d")
today = datetime.now() - timedelta(days=0)
today_str = yesterday.strftime("%Y-%m-%d")
start_date = yesterday_str
end_date = today_str
start_date_str = start_date
end_date_str = today_str


# Your complex topic string
topic = (
    "((human OR sex OR child) AND (exploitation OR trafficking)) "
    "OR (forced AND (labour OR prostitution OR marriage OR servitude OR recruitment)) "
    'OR ("modern slavery") '
    'OR ("debt bondage") '
    'OR ("sexual exploitation") '
    'OR ("child soldiers") '
    'OR ("organ trafficking") '
    'OR ("forced begging") '
    'OR ("domestic servitude") '
    'OR ("coerced criminality") '
    'OR ("exploitative sham marriages") '
    'OR ("cyber trafficking") '
    'OR ("trafficking biomedical research") '
)

topic_test1 = (
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

topic_test2 = (
    '"human exploitation"'
    'OR "child exploitation"'
    'OR "sex trafficking"'
    'OR "child trafficking"'
    'OR "forced labor"'
    'OR "forced marriage"'
    'OR "forced prostitution"'
    'OR "forced servitude"'
    'OR "forced recruitment"'
    'OR "modern slavery"'
    'OR "debt bondage"'
    'OR "sexual exploitation"'
    'OR "organ trafficking"'
)
# Assuming start_date_str and end_date_str are defined, for example:


# Your API key (placeholder)
newsapikey = {"key": st.secrets["newsapikey"]}

# Properly encoding the topic for URL
encoded_topic = urllib.parse.quote(topic_test1)

# Constructing the URL
url = f"https://newsapi.org/v2/everything?q={topic_test1}&from={start_date_str}&to={end_date_str}&sortBy=publishedAt&apiKey={newsapikey['key']['key']}"

print(url)

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

# Note: Handle the API key securely and avoid exposing it in shared code

articles

BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")
articles_table = pd.DataFrame(articles)
loader = BeautifulSoupWebReader()

# Assuming articles_table is your DataFrame
# Convert the 'source' column from dictionaries to separate columns
articles_table["source_id"] = articles_table["source"].apply(lambda d: d.get("id"))

articles_table["source_name"] = articles_table["source"].apply(lambda d: d.get("name"))
articles_table["start_date"] = start_date_str
articles_table["end_date"] = end_date_str
# Drop the original 'source' column as it's now redundant
articles_table.drop("source", axis=1, inplace=True)
articles_table_list = list(articles_table)
articles_table_list.sort()
articles_table_list = [
    "start_date",
    "end_date",
    "title",
    "url",
    "author",
    "content",
    "description",
    "publishedAt",
    "source_id",
    "source_name",
    "urlToImage",
]
articles_table[articles_table_list].to_csv("data/articles.csv", index=False)
articles_table.columns
query = (
    "As a world renowned expert in analyzing reports related to human trafficking and exploitation, your task is to meticulously examine the content"
    " for factual evidence without relying on pre-existing knowledge. Your focus should be on identifying instances of human trafficking or exploitation,"
    " defined as any form of coercion or manipulation for monetary, financial, sexual, or other benefits."
    "Firstly, determine if the article discusses any of the above criminal behaviours. Provide a yes or no answer."
    "If the article does discuss human trafficking or exploitation, proceed to answer the following questions:"
    "Identify if there are any suspects or accused individuals mentioned. If named, list their names; if not, indicate 'not named'."
    "Check for the presence of victims and whether their names are disclosed. If named, list their names; if not, state 'not named'."
    "Ascertain if the location of the incident is specified. If so, provide the location as accurately as possible mention any detail of interest."
    "Verify if the date and time of the incident is provided. If mentioned, provide it; otherwise, state 'no date mentioned'."
    "Carefully extract the nature of the incident if described. If detailed, describe the nature; otherwise, note 'the nature of the incident is unknown'."
    "Present the extracted information in a structured JSON format for clarity and ease of analysis."
)


from llama_index.core.node_parser import SimpleNodeParser

parser = SimpleNodeParser()
articles_table = pd.read_csv("data/articles.csv")
articles_table[articles_table_list].to_csv("data/articles.csv", index=False)


persist_dir = "./main_storage"
index = read_from_storage(persist_dir)

url0 = articles_table.loc[0]["url"]
doc0 = loader.load_data(urls=[url0])
index.insert(doc0[0])
new_nodes0 = parser.get_nodes_from_documents(doc0)
index.insert_nodes(new_nodes0)


url1 = articles_table.loc[1]["url"]
doc1 = loader.load_data(urls=[url1])
index.insert(doc1[0])
new_nodes1 = parser.get_nodes_from_documents(doc1)
index.insert_nodes(new_nodes1)
index.storage_context.persist(persist_dir)

url2 = articles_table.loc[2]["url"]
doc2 = loader.load_data(urls=[url2])
index.insert(doc2[0])
new_nodes2 = parser.get_nodes_from_documents(doc2)
index.insert_nodes(new_nodes2)
index.storage_context.persist(persist_dir)
index.ref_doc_info
index.ref_doc_info
url3 = articles_table.loc[3]["url"]
doc3 = loader.load_data(urls=[url3])
index.insert(doc3[0])

url4 = articles_table.loc[4]["url"]
doc4 = loader.load_data(urls=[url4])
index.insert(doc4[0])

# index.storage_context.persist(persist_dir)
index = read_from_storage(persist_dir)
query_engine = index.as_query_engine()
query = "What is discussed in these articles?"
response = query_engine.query(query)

query = """Given the context of you documents, your task is to meticulously analyze each document for instances and markers of human abuse, including but not limited to human trafficking, sexual exploitation, forced labor, child exploitation, and other forms of mistreatment and exploitation.

For each document in the library, you are to:

1. Identify and list any instances or markers of human abuse. This includes descriptions of exploitation, trafficking, coercion, and any other forms of abuse against individuals or groups.

2. For each instance identified, note the specific type of abuse (e.g., human trafficking, sexual exploitation, forced labor), providing a brief description of the context in which it was mentioned.

3. Clearly indicate the location within the document where each instance was found, such as the section title, page number, or paragraph, to facilitate direct reference.

4. Summarize the overall theme or focus of each document regarding human abuse, highlighting any recurring patterns, specific regions, populations affected, or interventions discussed.

5. Compile your findings into a structured format, with each document's analysis clearly separated and organized for easy review. Include document titles or identifiers for reference.

Your analysis will contribute to a deeper understanding of the prevalence and portrayal of human abuse across these documents, aiding in further research, policy formulation, and advocacy efforts. Please ensure your review is thorough and considerate of the sensitivity of the topics discussed.
"""

for n, row in articles_table.iterrows():
    print(f"Title: {row['title']}, URL: {row['url']}")
    doc = loader.load_data(urls=[row["url"]])
    index = None
    persist_dir = f"./storage_{n}"
    if not os.path.exists(persist_dir):
        index = build_storage(doc, persist_dir)
        query_engine = index.as_query_engine()

persist_dir = "./storage_35"
index = read_from_storage(persist_dir)
query_engine = index.as_query_engine()
response = query_engine.query(query)
query = "Please provide the author, title, date and url of this article?"
reponse = query_engine.query(query)
print(response)
response_string = response.json()
response_dict = json.loads(response_string)
articles_table.loc[14]
