from libraries.ner import run_openai_task
import os
from llama_index.core import VectorStoreIndex, ServiceContext
from llama_index.core import download_loader
from llama_index.core import (
    GPTVectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
from IPython.display import display, Markdown

OPENAI_MODEL = "gpt-3.5-turbo-0613"

labels = [
    "person",  # people, including fictional characters
    "fac",  # buildings, airports, highways, bridges
    "org",  # organizations, companies, agencies, institutions
    "gpe",  # geopolitical entities like countries, cities, states
    "loc",  # non-gpe locations
    "product",  # vehicles, foods, appareal, appliances, software, toys
    "event",  # named sports, scientific milestones, historical events
    "work_of_art",  # titles of books, songs, movies
    "law",  # named laws, acts, or legislations
    "language",  # any named language
    "date",  # absolute or relative dates or periods
    "time",  # time units smaller than a day
    "percent",  # percentage (e.g., "twenty percent", "18%")
    "money",  # monetary values, including unit
    "quantity",  # measurements, e.g., weight or distance
]


def build_storage(documents, persist_dir):
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir)
    return index


def read_from_storage(persist_dir):
    storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
    return load_index_from_storage(storage_context)


persist_dir = "./storage"
data_dir = "./data"

URL = "https://timesofindia.indiatimes.com/city/bengaluru/nia-charges-13-bangla-men-with-human-trafficking/articleshow/107473428.cms"
BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")
loader = BeautifulSoupWebReader()
documents = loader.load_data(urls=[URL])
# index = VectorStoreIndex.from_documents(documents)
persist_dir = "./storage01"
data_dir = "./data01"
index = None
if os.path.exists(persist_dir):
    index = read_from_storage(persist_dir)
else:
    index = build_storage(documents, persist_dir)
    query_engine = index.as_query_engine()

# storage_context = StorageContext.from_defaults(persist_dir=persist_dir)

response = query_engine.query("When were the people arrested?")
print(response)

import bs4, requests

response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
soup = bs4.BeautifulSoup(response.text, "lxml")

text = soup.body.get_text(" ", strip=True)
result = run_openai_task(labels, OPENAI_MODEL, text)

display(
    Markdown(
        f"""**Text:** {text}
                     **Enriched_Text:** {result['function_response']}"""
    )
)

i_tokens = result["model_response"].usage.prompt_tokens
o_tokens = result["model_response"].usage.completion_tokens

i_cost = (i_tokens / 1000) * 0.0015
o_cost = (o_tokens / 1000) * 0.002

print(
    f"""Token Usage
    Prompt: {i_tokens} tokens
    Completion: {o_tokens} tokens
    Cost estimation: ${round(i_cost + o_cost, 5)}"""
)

# Assuming articles_table is your DataFrame
