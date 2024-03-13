from libraries.google_lib import DB_Conn
import numpy as np
import logging

logger = logging.getLogger(__name__)
create_sql = """
CREATE TABLE articles (
    source_id VARCHAR(255),
    source_name VARCHAR(255),
    author VARCHAR(255),
    title TEXT,
    description TEXT,
    url TEXT,
    urlToImage TEXT,
    publishedAt TIMESTAMP,
    content TEXT
);
"""
insert_sql = """INSERT INTO articles (source_id, source_name, author, title, description, url, urlToImage, publishedAt, content) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
encodings_batch = []
for person_id, encoding, outcome in zip(encodings_batch):
    try:
        if isinstance(encoding, np.ndarray):
            encoding_list = encoding.tolist()
        else:
            encoding_list = []

        parameters = (
            int(person_id),
            encoding_list,
            outcome,
        )

        # Logging the SQL statement and parameters for debugging
        logger.debug(f"Executing SQL: {insert_sql} with parameters: {parameters}")
        with DB_Conn() as dbc:
            dbc.insert_query(insert_sql, parameters)
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise e
