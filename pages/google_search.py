import os
import streamlit as st
from googlesearch import search
from datetime import datetime, timedelta
import pandas as pd
import tldextract
from libraries.neo4j_lib import Neo4jConnection

url = "https://www.inkl.com/news/chinese-triad-s-sophisticated-human-trafficking-operations-exposed-in-kansas"
neo4j_config = {
    "username": os.environ.get("NEO4J_USER"),
    "password": os.environ.get("NEO4J_PWD"),
    "uri": "bolt://localhost:7687",
}
topics = (
    "'human trafficking'"
    " OR 'sex trafficking'"
    " OR 'modern slavery'"
    " OR 'debt bondage'"
    " OR 'sexual exploitation'"
    " OR 'child trafficking'"
    " OR 'organ trafficking'"
    " OR 'forced begging'"
    " OR 'domestic servitude'"
    " OR 'coerced criminality'"
    " OR 'exploitative sham marriages'"
    " OR 'cyber trafficking'"
    " OR 'trafficking for biomedical research '"
)
# Calculate yesterday's date for the 'from' parameter
yesterday = datetime.now() - timedelta(days=1)
yesterday_str = yesterday.strftime("%Y-%m-%d")
today = datetime.now() - timedelta(days=0)
today_str = yesterday.strftime("%Y-%m-%d")
start_date = st.sidebar.date_input("Search start date", yesterday)
end_date = st.sidebar.date_input("Search end date", today)
start_date_str = start_date.strftime("%Y-%m-%d")
end_date_str = end_date.strftime("%Y-%m-%d")

# Using the sidebar for the sliders
num = st.sidebar.slider("num", 1, 1000, 10, key="narticles")  # Start value is 25
stop = st.sidebar.slider("stop", 1, 1000, 10, key="nstop")  # Start value is 50
pause = st.sidebar.slider(
    "pause", 1, 10, 2, key="npause"
)  # Start value is 2, assuming a reasonable default
# Define the base terms for trafficking and legal action
trafficking_terms = [
    '"human trafficking"',
    '"cyber trafficking"',
    '"child trafficking"',
]
legal_action_terms = ["suspect", "victim", "arrest", "prosecute"]

# Construct the parts of the query
trafficking_query_part = f"({' OR '.join(trafficking_terms)})"
legal_action_query_part = f"({' OR '.join(legal_action_terms)})"

# Combine parts into the final query
query = f"{trafficking_query_part} {legal_action_query_part} after:{start_date_str} before:{end_date_str}"


# to search
# query = f"suspect victim arrest prosecute 'human trafficking' 'cyber trafficking' 'child trafficking' after:{start_date_str} before:{end_date_str}"


def get_new_articles():
    new_articles = []
    for j in search(
        query,
        tld="co.in",
        num=10,
        stop=st.session_state["nstop"],
        pause=st.session_state["npause"],
    ):
        st.write(j)
        new_articles.append(j)
    return new_articles


if st.button("Fetch new google search articles"):
    st.session_state["new_articles"] = get_new_articles()
    st.write(
        f"Retrieved {len(st.session_state['new_articles'])} articles; existing articles {len(st.session_state['existing_articles'])}."
    )
    # st.write(st.session_state['new_articles'])
    articles_table = pd.DataFrame(st.session_state["new_articles"])

if st.button("Fetch and upload google search articles"):
    st.session_state["new_articles"] = get_new_articles()
    st.write(
        f"Retrieved {len(st.session_state['new_articles'])} articles; existing articles {len(st.session_state['existing_articles'])}."
    )
    # st.write(st.session_state['new_articles'])
    articles_table = pd.DataFrame(st.session_state["new_articles"])
    query = """MERGE (searchresult:SearchResult {url: $url})
    WITH searchresult
    MERGE (domain:Domain {
        name: $domain_name
    })
    MERGE (searchresult)-[:HAS_DOMAIN]->(domain)
        """
    if st.session_state["new_articles"]:
        for url in st.session_state["new_articles"]:
            extracted = tldextract.extract(url)
            domain_name = extracted.domain
            subdomain_name = extracted.subdomain
            suffix = extracted.suffix
            is_private = extracted.is_private
            parameters = {
                "domain_name": domain_name,
                "url": url,
            }
            print(parameters)
            with Neo4jConnection(
                neo4j_config["uri"], neo4j_config["username"], neo4j_config["password"]
            ) as conn:
                result = conn.execute_query(query, parameters)
                print(result)
    st.session_state[
        "new_articles"
    ] = None  # Convert the 'source' column from dictionaries to separate columns
else:
    st.write("No new articles to upload.")

# url = 'https://www.lovejustice.ngo/blog/breaking-13-year-old-girl-lured-via-tiktok-suspect-arrested'
# articles =get_new_articles()
# for url in articles:
#     response = requests.get(url)
#     soup = bs4.BeautifulSoup(response.text, 'html.parser')
#
#     # Extract text from the BeautifulSoup object
#     text = soup.get_text(separator=' ', strip=True)
#
#     # Print or process the extracted text
#     print(text)
#
# response = requests.get(url)
#
# # Use BeautifulSoup to parse the HTML content
# soup = BeautifulSoup(response.text, 'html.parser')
#
# # Extract text from the BeautifulSoup object
# text = soup.get_text(separator=' ', strip=True)
#
# # Print or process the extracted text
# print(text)
