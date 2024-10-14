from mongodb import MongoDB
from neo4j_hetio import Neo4jDB

mongo_db = MongoDB()
neo4j_query = Neo4jDB()


def run_query_one():
    disease_id = input('Enter disease for query 1: ')
    res = mongo_db.query_one(disease_id)
    print(res)

def run_query_two():
    input('Press enter to run query two')
    res = neo4j_query.query_two()
    print(res)

def create_databases():
    mongo_db.create_database()
    neo4j_query.create_database()

create_bool = input('Create databases? (y/n): ')
if create_bool == 'y':
    create_databases()

query_num = input("Enter 1 or 2 to run query 1 or 2: ")
if query_num == '1':
    run_query_one()
else:
    run_query_two()