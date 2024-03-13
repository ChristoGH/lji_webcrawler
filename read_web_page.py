from dotenv import load_dotenv
from llama_index.core import download_loader
from llama_index.core import VectorStoreIndex, ServiceContext
from llama_index.core import (
    GPTVectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)

from openai import OpenAI
import os

from llama_index.core.llms import LLM

# from llama_index.llms.openai import OpenAI
load_dotenv()
URL = "https://timesofindia.indiatimes.com/city/bengaluru/nia-charges-13-bangla-men-with-human-trafficking/articleshow/107473428.cms"

BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")
loader = BeautifulSoupWebReader()
documents = loader.load_data(urls=[URL])

llm = OpenAI()


def build_storage(data_dir, persist_dir):
    documents = SimpleDirectoryReader(data_dir).load_data()
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir)
    return index


def read_from_storage(persist_dir):
    storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
    return load_index_from_storage(storage_context)


# service_context = ServiceContext.from_defaults(llm=llm)
persist_dir = "./storage"
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
index.storage_context.persist(persist_dir)
persist_dir = "./storage"
data_dir = "./data"
index = None
if os.path.exists(persist_dir):
    index = read_from_storage(persist_dir)
else:
    index = build_storage(data_dir, persist_dir)
    query_engine = index.as_query_engine()


for doc in documents:
    print(doc.text)


import bs4, requests

response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
soup = bs4.BeautifulSoup(response.text, "lxml")

text = soup.body.get_text(" ", strip=True)

from llama_index.core.memory import ChatMemoryBuffer

memory = ChatMemoryBuffer.from_defaults(token_limit=3000)

chat_engine = index.as_chat_engine(
    chat_mode="context",
    memory=memory,
    system_prompt=(
        "You are a chatbot, but also have deep insight into crime and criminal activity especially human trafficking."
    ),
)


response = chat_engine.chat(
    "Assistant, Is there mention of crime in this article?  If yes, provide the crime(s) by name."
)
response = chat_engine.chat(
    "Assistant, Is there mention of victims in this article?  If yes, provide their names in a list."
)
response = chat_engine.chat(
    "Assistant, Is there mention of suspects in this article?  If yes, provide their names in a list."
)
response = chat_engine.chat(
    "Assistant, Is there mention of the date and time of the crime mentioned in this article?  If yes, provide only the date and time."
)
response = chat_engine.chat(
    "Assistant, Is there mention of the location of the crime, such as address, town and country mentioned in this article?  If yes, provide only that detail."
)

prompt = """Assistant, please carefully analyze the article and provide the following details  in this EXAMPLE json format:
{
  "crimes": ["human trafficking", "slavery"],
  "victims": ["victim1", "victim2"],
  "suspects": ["suspect1", "suspect2"],
  "date": "yyyy-mm-dd",
  "address": "address",
   "town": "town",
   "country: "country"
}
"""

response = chat_engine.chat(prompt)
print(response)
