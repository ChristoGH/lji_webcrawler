import os
import streamlit as st
from googlesearch import search
from datetime import datetime, timedelta
import pandas as pd
import tldextract
from libraries.neo4j_lib import Neo4jConnection
import requests
import bs4
import openai
import wikipedia
import wikipediaapi
import os
import json
from typing import Optional
from IPython.display import display, Markdown
from tenacity import retry, wait_random_exponential, stop_after_attempt
import logging

logging.basicConfig(
    level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s"
)

OPENAI_MODEL = "gpt-3.5-turbo-0613"

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

labels = [
    "person",  # people, including fictional characters
    "victim",  # people who have been harmed, injured, or killed as a result of a crime, accident, or other event or action
    "criminal",  # a person who has committed a crime
    "crime",  # an action or omission that constitutes an offense that may be prosecuted by the state and is punishable by law
    # "trafficker",  # a person who engages in the illicit activity of trading in something illegal or stolen
    # "broker",      # a person who buys and sells goods or assets for others
    # "host",        # a person who receives or entertains other people as guests
    # "transporter",  # a person or thing that transports something
    "fac",  # buildings, airports, highways, bridges
    # "org",         # organizations, companies, agencies, institutions
    "gpe",  # geopolitical entities like countries, cities, states
    "loc",  # non-gpe locations
    # # "employment",  # the condition of having paid work
    # # "event",       # named sports, scientific milestones, historical events
    "date",  # absolute or relative dates or periods
    # "money",       # monetary values, including unit
]


def system_message(labels):
    return f"""
You are an expert in Natural Language Processing. Your task is to identify common Named Entities (NER) in a given text.
The possible common Named Entities (NER) types are exclusively: ({", ".join(labels)})."""


def assisstant_message():
    return f"""
EXAMPLE:
    Text: By 12th January 2015 thirteen-year-old Sunmaya Ayamnus had been missing from her home in Pokhara in Nepal for nearly a month when our team intercepted her. \n"
    "The suspect, Okesh Kitesh, promised to marry her shortly after they met each other on TikTok.  Okesh Kitesh was arrested and charged with human trafficking.
    {{
        "gpe": ["Nepal", "Pokhara"],
        "date": ["12th January 2015"],
        "person": ["Sunmaya Ayamnus", "Okesh Kitesh"],
        "criminal": ["Okesh Kitesh"],
        "victim": ["Sunmaya Ayamnus"],
    }}
--"""


def user_message(text):
    return f"""
TASK:
    Text: {text}
"""


@retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(5))
def find_link(entity: str) -> Optional[str]:
    """
    Finds a Wikipedia link for a given entity.
    """
    try:
        titles = wikipedia.search(entity)
        if titles:
            # naively consider the first result as the best
            page = wikipedia.page(titles[0])
            return page.url
    except wikipedia.exceptions.WikipediaException as ex:
        logging.error(
            f"Error occurred while searching for Wikipedia link for entity {entity}: {str(ex)}"
        )

    return None


def generate_functions(labels: dict) -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": "enrich_entities",
                "description": "Enrich Text with Knowledge Base Links",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "r'^(?:' + '|'.join({labels}) + ')$'": {
                            "type": "array",
                            "items": {"type": "string"},
                        }
                    },
                    "additionalProperties": False,
                },
            },
        }
    ]


def find_all_links(label_entities: dict) -> dict:
    """
    Finds all Wikipedia links for the dictionary entities in the whitelist label list.
    """
    whitelist = [
        "event",
        "gpe",
        "loc",
        "person",
        "fac",
        "crime",
        "victim",
        "suspect",
        "trafficker",
        "broker",
        "host",
        "transporter",
        "employment",
        "org",
        "product",
        "law",
        "language",
        "date",
        "time",
        "percent",
        "money",
        "quantity",
    ]

    return {
        e: find_link(e)
        for label, entities in label_entities.items()
        for e in entities
        if label in whitelist
    }


def enrich_entities(text: str, label_entities: dict) -> str:
    """
    Enriches text with knowledge base links.
    """
    entity_link_dict = find_all_links(label_entities)
    logging.info(f"entity_link_dict: {entity_link_dict}")

    for entity, link in entity_link_dict.items():
        text = text.replace(entity, f"[{entity}]({link})")

    return text


@retry(wait=wait_random_exponential(min=1, max=10), stop=stop_after_attempt(5))
def run_openai_task(labels, text):
    messages = [
        {"role": "system", "content": system_message(labels=labels)},
        {"role": "assistant", "content": assisstant_message()},
        {"role": "user", "content": user_message(text=text)},
    ]

    # TODO: functions and function_call are deprecated, need to be updated
    # See: https://platform.openai.com/docs/api-reference/chat/create#chat-create-tools
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        # model="gpt-3.5-turbo-0613",
        messages=messages,
        tools=generate_functions(labels),
        tool_choice={"type": "function", "function": {"name": "enrich_entities"}},
        temperature=0,
        frequency_penalty=0,
        presence_penalty=0,
    )

    response_message = response.choices[0].message

    available_functions = {"enrich_entities": enrich_entities}
    function_name = response_message.tool_calls[0].function.name

    function_to_call = available_functions[function_name]
    logging.info(f"function_to_call: {function_to_call}")

    function_args = json.loads(response_message.tool_calls[0].function.arguments)
    logging.info(f"function_args: {function_args}")

    function_response = function_to_call(text, function_args)

    return {"model_response": response, "function_response": function_response}


text = """The PVs below were through a phone call promised jobs of domestic work by one Kutosi Jackson(host) on 27/01/2023. Host who is a Ugandan but based in Bungoma, Kenya promised them USh 450,000 each per month. He also covered all travel costs through mobile money means.  Field monitors intercepted them and sent them back home.

*Narrative*

The monitoring team (LJU) that was monitoring along Mutukula porous border intercepted the above PVs before crossing to Kenya. PVs who are related narrated in an interview that they were on 27th/01/2023 through a phone call contacted by one Kutosi Jackson (host) a Ugandan but based in Kenya. He promised them jobs of domestic work at his home in Bungoma Kenya at a promised monthly pay of 450,000 Ugx each that is more than double the normal pay. The host, who covered all travel costs for the PVs through mobile money means, planned for this trip with the PVs without the consent of the uncle as the LJU team confirmed this through a phone call. The host who was to pick the PVs from the porous border and proceed with them denied promising the PVs any job but when contacted he insisted that they were his nieces who were only visiting him. PVs who opted to go back home were educated about human trafficking and were offered with safe transport back home.
The PVs did not have travel documents
They were also intercepted at a porous border an illegalentry into another country"""


result = run_openai_task(labels, text)
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

url = "https://www.inkl.com/news/chinese-triad-s-sophisticated-human-trafficking-operations-exposed-in-kansas"
url = "https://timesofindia.indiatimes.com/india/bjp-releases-documentary-on-sandeshkhali-highlighting-womens-plight/articleshow/107905561.cms"
url = "https://www.justice.gov/usao-edtn/pr/bristol-resident-sentenced-serve-235-months-federal-prison-child-pornography-production"
response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = bs4.BeautifulSoup(response.text, "lxml")
text = soup.body.get_text(" ", strip=True)
result = run_openai_task(labels, text)
display(
    Markdown(
        f"""**Text:** {text}
                     **Enriched_Text:** {result['function_response']}"""
    )
)

text = (
    "By 12th January 2015 thirteen-year-old Sunmaya Ayamnus had been missing from her home in Pokhara in Nepal for nearly a month when our team intercepted her. \n"
    "The suspect, Okesh Kitesh, promised to marry her shortly after they met each other on TikTok.  Okesh Kitesh was arrested and charged with human trafficking. "
)
