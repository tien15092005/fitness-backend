from arango import ArangoClient

client = ArangoClient(hosts="http://localhost:8529")

db = client.db(
    "fitness_app",
    username="root",
    password="test"
)
