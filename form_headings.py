from libraries.google_lib import DB_Conn

query = "SELECT * FROM dataentry_irfcommon LIMIT 10"
with DB_Conn() as conn:
    df = conn.ex_query(query)
