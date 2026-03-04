from arango import ArangoClient

client = ArangoClient(hosts="https://b716a5707e97.arangodb.cloud:8529")

db = client.db(
    "Gym_db",
    username="root",
    password="O7Tk0Kt152xNkJ9SQ6fy"
)
