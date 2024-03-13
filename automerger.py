from libraries.engines import build_automerging_index
import os
import pandas as pd
from llama_index.core import download_loader
from llama_index.core import ServiceContext
from openai import OpenAI
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex
from llama_index.core import StorageContext
from llama_index.core.settings import Settings
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes

llm = OpenAI(model="gpt-3.5-turbo")
BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")
loader = BeautifulSoupWebReader()


articles = pd.read_csv("data/articles.csv")

n = 3
url = articles.loc[n]["url"]
doc = loader.load_data(urls=[url])
index = build_automerging_index(
    documents=doc,
    llm=llm,
    embed_model="local:BAAI/bge-small-en-v1.5",
    save_dir=f"merging_index_{n}",
)
merging_context = ServiceContext.from_defaults(
    embed_model="local:BAAI/bge-small-en-v1.5",
)

node_parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[2048, 512, 128])
nodes = node_parser.get_nodes_from_documents(doc)
Settings.embed_model = "local:BAAI/bge-small-en-v1.5"

dir(Settings.llm)

storage_context = StorageContext.from_defaults()
storage_context.docstore.add_documents(nodes)
leaf_nodes = get_leaf_nodes(nodes)
automerging_index = VectorStoreIndex(
    leaf_nodes, storage_context=storage_context, service_context=Settings
)
automerging_index.storage_context.persist(persist_dir=f"data/merging_index_{n}")
automerging_index.as_query_engine()
