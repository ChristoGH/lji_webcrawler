# https://truera.com/ai-quality-education/generative-ai-rags/evals-build-better-rags-trulens-milvus/

from llama_index import download_loader
from libraries.sl_data import get_irf
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

WikipediaReader = download_loader("WikipediaReader")
cities = [
    "Kampala",
    "Nairobi",
    "Kaabong",
    "Kigali",
    "Khartoum",
    "Kano, Nigeria",
    "Adjumani",
    "Kanungu",
    "Kasese",
    "Ibanda",
    "Kasese",
]

wiki_docs = []
for city in cities:
    try:
        doc = WikipediaReader().load_data(pages=[city])
        wiki_docs.extend(doc)
    except Exception as e:
        print(f"Error loading page for city {city}: {e}")
doc = WikipediaReader().load_data(pages=["Kano, Nigeria"])
doc = WikipediaReader().load_data(pages=["VOLTA LAKE"])
doc = WikipediaReader().load_data(pages=["JHB, CBD"])
irfs = get_irf()

irfs["where_going_destination"]

split_columns = irfs["where_going_destination"].str.split(";", expand=True)

# Now, you can name these new columns as needed
split_columns.columns = [
    "Destination1",
    "Destination2",
    "Destination3",
    "Destination4",
]  # and so on, depending on how many splits you have

# Join these new columns back to the original DataFrame
irfs = irfs.join(split_columns)
irfs["destination0"] = irfs["Destination1"] + ", " + irfs["country"]
len(irfs.loc[irfs["country"] == "Uganda", "Destination1"].unique())

len(irfs["destination0"].unique())

destinations = irfs["Destination1"].unique()
destinations = irfs.loc[irfs["country"] == "Uganda", "Destination1"].unique()
destinations.sort()
destinations_dict = {}
counter = 0
for destination in destinations:
    try:
        counter += 1
        doc = WikipediaReader().load_data(pages=[destination])
        destinations_dict[destination] = doc
        print(f"Loaded page for {destination}: {counter} of {len(destinations)}")
    except Exception as e:
        print(f"Error loading page for city {destination}: {e}")
        destinations_dict[destination] = e

df = pd.DataFrame.from_dict(destinations_dict, orient="index").reset_index()
df.columns = ["city", "description"]
df.to_csv("data/destination_descriptions_uganda.csv", index=False)
description = df.iloc[2]["description"]
from llama_index.schema import Document

documents = []
for entry in df["description"]:
    # Check if 'entry' is a list-like object and has at least one element
    if isinstance(entry, list) and len(entry) > 0:
        # Check if the first element of 'entry' is an instance of Document
        if isinstance(entry[0], Document):
            # If 'entry[0]' is a Document, safely call 'get_text()' or equivalent method
            print(entry[0].get_text())  # Assuming 'get_text()' is a method of Document
            documents.append(entry[0])
        else:
            print(entry[0])  # Assuming 'entry[0]' is a string

len(documents)

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    SentenceTransformersTokenTextSplitter,
)
from llama_index import VectorStoreIndex
from libraries.helper_utils import word_wrap

embedding_function = SentenceTransformerEmbeddingFunction()
token_splitter = SentenceTransformersTokenTextSplitter(
    chunk_overlap=0, tokens_per_chunk=256
)
character_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ". ", " ", ""], chunk_size=1000, chunk_overlap=0
)
documents[0].get_text()
description = [df.iloc[2]["description"][0].get_text()]
all_texts = [document.get_text() for document in documents]
character_split_texts = character_splitter.split_text("\n\n".join(all_texts))
print(word_wrap(description))
print(f"\nTotal chunks: {len(character_split_texts)}")

token_split_texts = []
for text in character_split_texts:
    token_split_texts += token_splitter.split_text(text)

print(word_wrap(token_split_texts[10]))
print(f"\nTotal chunks: {len(token_split_texts)}")

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


print(embedding_function([token_split_texts[10]]))


chroma_client = chromadb.Client()
chroma_collection = chroma_client.create_collection(
    "destinations_uganda", embedding_function=embedding_function
)

ids = [str(i) for i in range(len(token_split_texts))]

chroma_collection.add(ids=ids, documents=token_split_texts)
chroma_collection.count()
query = "Where is abu dhabi located?"

results = chroma_collection.query(query_texts=[query], n_results=5)
retrieved_documents = results["documents"][0]
for document in retrieved_documents:
    print(word_wrap(document))
    print("\n")


import umap
import numpy as np
from tqdm import tqdm

embeddings = chroma_collection.get(include=["embeddings"])["embeddings"]
umap_transform = umap.UMAP(random_state=0, transform_seed=0).fit(embeddings)


# In[3]:


def project_embeddings(embeddings, umap_transform):
    umap_embeddings = np.empty((len(embeddings), 2))
    for i, embedding in enumerate(tqdm(embeddings)):
        umap_embeddings[i] = umap_transform.transform([embedding])
    return umap_embeddings


# In[4]:


projected_dataset_embeddings = project_embeddings(embeddings, umap_transform)


# In[5]:


import matplotlib.pyplot as plt

plt.figure()
plt.scatter(
    projected_dataset_embeddings[:, 0], projected_dataset_embeddings[:, 1], s=10
)
plt.gca().set_aspect("equal", "datalim")
plt.title("Projected Embeddings")
plt.axis("off")

# =Demo1===========================================================
query = "Tell me more about Mutukula?"

results = chroma_collection.query(
    query_texts=query, n_results=5, include=["documents", "embeddings"]
)

retrieved_documents = results["documents"][0]

for document in results["documents"][0]:
    print(word_wrap(document))
    print("")


# In[7]:


query_embedding = embedding_function([query])[0]
retrieved_embeddings = results["embeddings"][0]

projected_query_embedding = project_embeddings([query_embedding], umap_transform)
projected_retrieved_embeddings = project_embeddings(
    retrieved_embeddings, umap_transform
)


# In[8]:


# Plot the projected query and retrieved documents in the embedding space
plt.figure()
plt.scatter(
    projected_dataset_embeddings[:, 0],
    projected_dataset_embeddings[:, 1],
    s=10,
    color="gray",
)
plt.scatter(
    projected_query_embedding[:, 0],
    projected_query_embedding[:, 1],
    s=150,
    marker="X",
    color="r",
)
plt.scatter(
    projected_retrieved_embeddings[:, 0],
    projected_retrieved_embeddings[:, 1],
    s=100,
    facecolors="none",
    edgecolors="g",
)

plt.gca().set_aspect("equal", "datalim")
plt.title(f"{query}")
plt.axis("off")


# =Demo 2===========================================================
query = "Where is Abu Dhabi?"
results = chroma_collection.query(
    query_texts=query, n_results=5, include=["documents", "embeddings"]
)

retrieved_documents = results["documents"][0]

for document in results["documents"][0]:
    print(word_wrap(document))
    print("")


# In[10]:


query_embedding = embedding_function([query])[0]
retrieved_embeddings = results["embeddings"][0]

projected_query_embedding = project_embeddings([query_embedding], umap_transform)
projected_retrieved_embeddings = project_embeddings(
    retrieved_embeddings, umap_transform
)


# In[11]:


# Plot the projected query and retrieved documents in the embedding space
plt.figure()
plt.scatter(
    projected_dataset_embeddings[:, 0],
    projected_dataset_embeddings[:, 1],
    s=10,
    color="gray",
)
plt.scatter(
    projected_query_embedding[:, 0],
    projected_query_embedding[:, 1],
    s=150,
    marker="X",
    color="r",
)
plt.scatter(
    projected_retrieved_embeddings[:, 0],
    projected_retrieved_embeddings[:, 1],
    s=100,
    facecolors="none",
    edgecolors="g",
)

plt.gca().set_aspect("equal", "datalim")
plt.title(f"{query}")
plt.axis("off")
