from newsapi import NewsApiClient
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from libraries.neo4j_lib import Neo4jConnection
import os

neo4j_config = {
    "username": os.environ.get("NEO4J_USER"),
    "password": os.environ.get("NEO4J_PWD"),
    "uri": "bolt://localhost:7687",
}
# Initialize News API client
newsapikey = st.secrets["newsapikey"]
newsapi = NewsApiClient(api_key=newsapikey["key"])
style = """
<style>
.stDataFrame {
    color: #000;
}
.stDataFrame > div > div > div > div {
    background-color: white;
}
.stDataFrame > div > div > div:nth-of-type(odd) > div {
    background-color: #add8e6;
}
</style>
"""
topics = (
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


def get_new_articles():
    url = f"https://newsapi.org/v2/everything?q={topics}&from={start_date_str}&to={end_date_str}&sortBy=publishedAt&apiKey={newsapikey['key']}"
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json().get("articles", [])
        if articles:
            for article in articles:
                st.write(article["title"], article["url"])
        else:
            st.write("No articles found.")
    else:
        st.error(f"Failed to fetch articles. Error code: {response.status_code}")
    return articles
    # This function does not need to return articles since it writes directly to Streamlit


def get_existing_articles():
    query = """MATCH (article:Article) RETURN article.url as url, article.title AS title,  ID(article) as id_
    ORDER BY article.title ASC;"""
    parameters = {}
    with Neo4jConnection(
        neo4j_config["uri"], neo4j_config["username"], neo4j_config["password"]
    ) as conn:
        result = conn.execute_query(query, parameters)
    return result


if st.session_state.get("existing_articles") is None:
    st.session_state["existing_articles"] = get_existing_articles()


# Define topic options with their corresponding query segments
topic_options = {
    "Human, Sex, or Child Exploitation/Trafficking": "((human OR sex OR child) AND (exploitation OR trafficking))",
    "Forced Labour, Prostitution, Marriage, Servitude, or Recruitment": "(forced AND (labour OR prostitution OR marriage OR servitude OR recruitment))",
    "Modern Slavery": "(modern slavery)",
    "Debt Bondage": '("debt bondage")',
    "Sexual Exploitation": '("sexual exploitation")',
    "Child Soldiers": '("child soldiers")',
    "Organ Trafficking": '("organ trafficking")',
    "Forced Begging": '("forced begging")',
    "Domestic Servitude": '("domestic servitude")',
    "Coerced Criminality": '("coerced criminality")',
    "Exploitative Sham Marriages": '("exploitative sham marriages")',
    "Cyber Trafficking": '("cyber trafficking")',
    "Trafficking for Biomedical Research": '("trafficking for biomedical research")',
}

# Create checkboxes for each topic in the sidebar
# selected_topics = []
# for topic, query in topic_options.items():
#     if st.sidebar.checkbox(topic, key=topic):
#         selected_topics.append(query)
#
# # Construct the final topic query string
# if selected_topics:
#     topic_query = "(" + " OR ".join(selected_topics) + ")"
# else:
#     topic_query = ""
#
# # Display the constructed topic query
# st.write("Your constructed topic query is:")
# st.text(topic_query)


# Calculate yesterday's date for the 'from' parameter
yesterday = datetime.now() - timedelta(days=1)
yesterday_str = yesterday.strftime("%Y-%m-%d")
today = datetime.now() - timedelta(days=0)
today_str = yesterday.strftime("%Y-%m-%d")
start_date = st.sidebar.date_input("Search start date", yesterday)
end_date = st.sidebar.date_input("Search end date", today)
start_date_str = start_date.strftime("%Y-%m-%d")
end_date_str = end_date.strftime("%Y-%m-%d")

if st.button("get existing articles"):
    existing_articles = get_existing_articles()

with st.expander("See current list of articles..."):
    # Display the custom CSS
    # st.markdown(style, unsafe_allow_html=True)
    # Display the DataFrame with the custom styling applied
    # st.dataframe(st.session_state['articles'])
    articles_dict = st.session_state["existing_articles"]
    if articles_dict:
        for article in st.session_state["existing_articles"]:
            st.write(article["title"], article["url"])

if st.button("Fetch new articles"):
    st.session_state["new_articles"] = get_new_articles()
    st.write(
        f"Retrieved {len(st.session_state['new_articles'])} articles; existing articles {len(st.session_state['existing_articles'])}."
    )
    # st.write(st.session_state['new_articles'])
    articles_table = pd.DataFrame(st.session_state["new_articles"])

if st.button("Upload new articles"):
    query = """MERGE (source:Source {name: $sourceName})
WITH source
MERGE (article:Article {
    title: $title,
    description: $description,
    url: $url,
    urlToImage: $urlToImage,
    publishedAt: $publishedAt,
    content: $content
})
MERGE (article)-[:HAS_SOURCE]->(source)
WITH article
OPTIONAL MATCH (author:Author {name: $authorName})
WITH author, article
FOREACH(_ IN CASE WHEN author IS NOT NULL THEN [1] ELSE [] END |
    MERGE (author)-[:AUTHORED]->(article)
)

    """
    if st.session_state["new_articles"]:
        for data in st.session_state["new_articles"]:
            parameters = {
                "sourceName": data["source"]["name"],
                "authorName": data["author"],
                "title": data["title"],
                "description": data["description"],
                "url": data["url"],
                "urlToImage": data["urlToImage"],
                "publishedAt": data["publishedAt"],
                "content": data["content"],
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
