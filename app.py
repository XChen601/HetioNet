from flask import Flask, jsonify, request
from flask_cors import CORS
from mongodb import MongoDB

app = Flask(__name__)
CORS(app)

mongo_db = MongoDB()

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


if __name__ == '__main__':
    app.run(debug=True)
