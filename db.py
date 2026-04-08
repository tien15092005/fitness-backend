import os
from arango import ArangoClient
from dotenv import load_dotenv

load_dotenv()

def get_db():
    try:
        client = ArangoClient(
            hosts=os.environ.get("ARANGO_HOST", "https://qrywlgjahp.us14.qoddiapp.com:443")
        )
        db = client.db(
            os.environ.get("ARANGO_DB", "fitness_app"),
            username=os.environ.get("ARANGO_USER", "root"),
            password=os.environ.get("ARANGO_PASSWORD", "")
        )
        return db
    except Exception as e:
        print(f"[DB ERROR] Cannot connect to ArangoDB: {e}")
        return None

db = get_db()