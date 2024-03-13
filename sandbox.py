# https://python.langchain.com/docs/use_cases/web_scraping

from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
import os

# Load HTML
loader = AsyncChromiumLoader(["https://www.facebook.com"])
html = loader.load()

# Transform
bs_transformer = BeautifulSoupTransformer()
docs_transformed = bs_transformer.transform_documents(html, tags_to_extract=["span"])
# Result
docs_transformed[0].page_content[0:500]

from playwright.sync_api import sync_playwright
import re
import asyncio


with sync_playwright() as p:
    browser = p.webkit.launch()
    page = browser.new_page()
    page.goto("https://www.facebook.com/login/")
    page.get_by_label("email").fill(os.environ.get("LJI_FB_USER"))
    page.get_by_label("Password").fill(os.environ.get("LJI_FB_PWD"))
    login = page.get_by_role("button", name=re.compile("Log in", re.IGNORECASE))
    login.click()
    # page.screenshot(path="img/example_logged_in.png")
    page.wait_for_load_state()
    print(page.title())
    page.screenshot(path="img/example_logged_in.png")
    browser.close()

page.get_by_label("email").fill(os.environ.get("LJI_FB_USER"))
page.get_by_label("Password").fill(os.environ.get("LJI_FB_PWD"))
# page.screenshot(path="img/example_credentials.png")
page.get_by_role("button", name=re.compile("Log in", re.IGNORECASE)).click()
# await page.get_by_role("button", name=re.compile("submit", re.IGNORECASE)).click()


from playwright.async_api import async_playwright


async def login_to_website(page):
    await page.get_by_label("email").fill(os.environ.get("LJI_FB_USER"))
    await page.get_by_label("Password").fill(os.environ.get("LJI_FB_PWD"))
    await page.click(
        "role=button[name=/Log in/i]"
    )  # Using regex directly in the selector


async def main():
    async with async_playwright() as p:
        browser = await p.webkit.launch()
        page = await browser.new_page()
        await page.goto("https://www.facebook.com/login/")
        await page.screenshot(path="img/example_login.png")
        await login_to_website(page)
        await page.screenshot(path="img/example_logged_in.png")
        await browser.close()


# Running the async main function
asyncio.run(main())


# =========================================================
from llama_index.core.memory import ChatMemoryBuffer
from googlesearch import search
import bs4, requests
from llama_index.core import download_loader
from llama_index.core import VectorStoreIndex, ServiceContext
from llama_index.core import (
    GPTVectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)

BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")
loader = BeautifulSoupWebReader()


memory = ChatMemoryBuffer.from_defaults(token_limit=3000)

query = "'human trafficking' Uganda"
results = search(query, tld="co.in", num=10, stop=None, tbs="qdr:d", pause=10)
prompt = """Assistant, please carefully analyze the article and provide the following details  in this EXAMPLE json layout:
{
  "crimes": ["human trafficking", "slavery", "cyber trafficking"],
  "date": "yyyy-mm-dd",
  "address": "address",
  "place": ["business", "location", "land mark"],
   "town": ["town"],
   "country: ["country"],
   "persons: [{"name": "firstname surname",
              "role": "unknown",
              "gender": "male"},
              {"name": "firstname surname",
              "role": "victim",
              "gender": "female"},
              {"name": "firstname surname",
              "role": "suspect",
              "gender": "male"}],
}
"""

for url in results:
    print(url)
    documents = loader.load_data(urls=[url])
    index = VectorStoreIndex.from_documents(documents)
    chat_engine = index.as_chat_engine(
        chat_mode="context",
        memory=memory,
        system_prompt=(
            "You are a chatbot, but also have deep insight into crime and criminal activity especially human trafficking.  "
            "You will be tasked to extract pertinent factual data and always be precise."
        ),
    )
    response = chat_engine.chat(prompt)
    print(response)


# =========================================================
import requests

SERVER = "localhost"
PORT = "8001"

HEALTH_URL = f"http://{SERVER}:{PORT}/health"
INGEST_FILE_URL = f"http://{SERVER}:{PORT}/v1/ingest/file"
DELETE_FILE_URL = f"http://{SERVER}:{PORT}/v1/ingest/file"
INGESTED_LIST_URL = f"http://{SERVER}:{PORT}/v1/ingest/list"
CHAT_COMPLETION_URL = f"http://{SERVER}:{PORT}/v1/chat/completions"

prompt = "Please return a summary of this article."
response = requests.get(INGESTED_LIST_URL)


messages = [
    {
        "role": "system",
        "content": "You are the worlds best analyst of crime events and publications.  Always be precise and answer truthfully",
    },
    {"role": "user", "content": prompt},
]
requestBody = {
    "include_sources": True,
    "messages": messages,
    "stream": True,
    "use_context": True,
    "context_filter": {"docs_ids": []},
}

with requests.post(CHAT_COMPLETION_URL, json=requestBody, stream=True) as r:
    for line in r.iter_lines():
        # print(line)
        print(line.text)


import openai
import os

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

data = SimpleDirectoryReader(input_dir="./data/example/").load_data()
index = VectorStoreIndex.from_documents(data)

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
    "Assistant, Is there mention of crime in this article?  Please answer only with a yes or no."
)
response = chat_engine.chat(
    "Name the crime or crimes wtaht were commited?  Please answer only with a list of crime lables."
)
