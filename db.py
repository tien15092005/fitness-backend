import os
from arango import ArangoClient
from dotenv import load_dotenv

# Load biến môi trường từ file .env (chỉ dùng local)
load_dotenv()

client = ArangoClient(
    hosts=os.environ.get("ARANGO_HOST")
)

db = client.db(
    os.environ.get("ARANGO_DB"),
    username=os.environ.get("ARANGO_USER"),
    password=os.environ.get("ARANGO_PASSWORD")
)
