import os
import pandas as pd
from llama_index.readers.web import SimpleWebPageReader
from llama_index.core import KnowledgeGraphIndex, SimpleDirectoryReader
from llama_index.core import StorageContext
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.core import download_loader
from llama_index.core import SummaryIndex

BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")
loader = BeautifulSoupWebReader()


from llama_index.llms.openai import OpenAI
from IPython.display import Markdown, display


username = os.environ.get("NEO4J_USER")
password = os.environ.get("NEO4J_PWD")
url = "bolt://localhost:7687"
embed_dim = 1536

articles = pd.read_csv("data/articles.csv")


graph_store = Neo4jGraphStore(username=username, password=password, url=url)


storage_context = StorageContext.from_defaults(graph_store=graph_store)
url = articles.loc[11]["url"]
title = articles.loc[11]["title"]
doc = loader.load_data(urls=[url])
# NOTE: can take a while!
documents = SimpleWebPageReader(html_to_text=True).load_data([url])
index = SummaryIndex.from_documents(documents)
# set Logging to DEBUG for more detailed outputs
query_engine = index.as_query_engine()
response = query_engine.query("Is there any mention of human trafficking?")
index = KnowledgeGraphIndex.from_documents(
    doc,
    storage_context=storage_context,
    max_triplets_per_chunk=100,
    embed_dim=embed_dim,
    llm=OpenAI(),
    chunk_sizes=[2048, 512, 128],
)
index.as_query_engine()
for n, row in articles.iterrows():
    print(f"Title: {row['title']}, URL: {row['url']}")
    doc = loader.load_data(urls=[row["url"]])
    index = KnowledgeGraphIndex.from_documents(
        doc,
        storage_context=storage_context,
        max_triplets_per_chunk=100,
        embed_dim=embed_dim,
        llm=OpenAI(),
        chunk_sizes=[2048, 512, 128],
    )

    if not os.path.exists(persist_dir):
        index = build_storage(doc, persist_dir)
        query_engine = index.as_query_engine()
