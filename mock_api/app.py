import os

from flask import Flask, jsonify, request

app = Flask(__name__)

POST = {
    "userId": 1,
    "id": 1,
    "title": "sunt aut facere repellat provident occaecati excepturi optio reprehenderit",
    "body": "quia et suscipit suscipit recusandae consequuntur expedita et cum\n"
    "reprehenderit molestiae ut ut quas totam nostrum rerum est autem sunt rem",
}


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/posts/1")
def get_post():
    return jsonify(POST), 200


@app.route("/posts", methods=["POST"])
def create_post():
    payload = request.get_json(silent=True) or {}
    created = dict(POST)
    created.update({k: v for k, v in payload.items() if v is not None})
    created["id"] = int(os.getenv("MOCK_NEXT_ID", "101"))
    return jsonify(created), 201


@app.route("/posts/500", methods=["POST"])
def create_post_error():
    return jsonify({"error": "internal"}), 500


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
