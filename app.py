from flask import Flask, jsonify, request
from flask_cors import CORS
from mongodb import MongoDB
from neo4j_hetio import Neo4jDB
app = Flask(__name__)
CORS(app)

mongo_db = MongoDB()
neo4j_query = Neo4jDB()

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/query_one', methods=['GET'])
def query_one():
    print('running query one')
    disease_id = request.args.get('disease_id')

    if not disease_id:
        return jsonify({"error": "Please provide a disease_id"}), 400

    try:
        result = mongo_db.query_one(disease_id)
        print(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/query_two', methods=['GET'])
def query_two():
    print('running query two')
    disease_id = request.args.get('disease_id')
    try:
        result = neo4j_query.query_two(disease_id)
        print(result)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
