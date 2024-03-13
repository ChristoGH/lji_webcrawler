from llama_index.core import VectorStoreIndex
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
import openai
import wikipedia
import wikipediaapi
import os
import json
from typing import Optional
from tenacity import retry, wait_random_exponential, stop_after_attempt
import logging

logging.basicConfig(
    level=logging.INFO, format=" %(asctime)s - %(levelname)s - %(message)s"
)


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


def system_message(labels):
    return f"""
You are an expert in Natural Language Processing. Your task is to identify common Named Entities (NER) in a given text.
The possible common Named Entities (NER) types are exclusively: ({", ".join(labels)})."""


def assisstant_message():
    return f"""
EXAMPLE:
    Text: 'In Germany, in 1440, goldsmith Johannes Gutenberg invented the movable-type printing press. His work led to an information revolution and the unprecedented mass-spread /
    of literature throughout Europe. Modelled on the design of the existing screw presses, a single Renaissance movable-type printing press could produce up to 3,600 pages per workday.'
    {{
        "gpe": ["Germany", "Europe"],
        "date": ["1440"],
        "person": ["Johannes Gutenberg"],
        "product": ["movable-type printing press"],
        "event": ["Renaissance"],
        "quantity": ["3,600 pages"],
        "time": ["workday"]
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
    whitelist = ["event", "gpe", "org", "person", "product", "work_of_art"]

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
def run_openai_task(labels, model, text):
    messages = [
        {"role": "system", "content": system_message(labels=labels)},
        {"role": "assistant", "content": assisstant_message()},
        {"role": "user", "content": user_message(text=text)},
    ]

    # TODO: functions and function_call are deprecated, need to be updated
    # See: https://platform.openai.com/docs/api-reference/chat/create#chat-create-tools
    response = openai.chat.completions.create(
        model=model,
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
