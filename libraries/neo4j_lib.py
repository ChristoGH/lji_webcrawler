from neo4j import GraphDatabase


class Neo4jConnection:
    def __init__(self, uri, user, pwd):
        self.__uri = uri
        self.__user = user
        self.__pwd = pwd
        self.__driver = None
        try:
            self.__driver = GraphDatabase.driver(
                self.__uri, auth=(self.__user, self.__pwd)
            )
        except Exception as e:
            print("Failed to create the driver:", e)

    def __enter__(self):
        self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__user, self.__pwd))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__driver is not None:
            self.__driver.close()

    def close(self):
        if self.__driver is not None:
            self.__driver.close()

    def execute_query(self, query, parameters=None):
        if self.__driver is not None:
            try:
                with self.__driver.session() as session:
                    result = session.execute_write(
                        lambda tx: tx.run(query, parameters).data()
                    )
                    return result
            except Exception as e:
                print("Query failed:", e)
                return None
