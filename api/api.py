from flask import Flask, request, abort

from coin.block import BlockChain

app = Flask(__name__)
app.config["DEBUG"] = True


block_chain: BlockChain = BlockChain()


@app.route("/", methods=["GET"])
def home():
    return """ <h1>Crypto API</h1>"""


@app.route("/blocks", methods=["GET"])
def blocks():
    return block_chain.get_json()


@app.route("/make_blocks", methods=["POST"])
def make_blocks():
    if not request.json or "data" not in request.json:
        abort(400)
    block_data: str = request.json['data']
    block_chain.generate_new_block(block_data)
    return "success", 201

# To send a request: r = requests.post("http://127.0.0.1:5000/mine_blocks",
# json={"data": "llama"})


@app.route("/replace_chain", methods=["POST"])
def replace_blocks():
    global block_chain
    if not request.json or "chain" not in request.json:
        abort(400)
    block_chain = BlockChain(json=request.json)
    return "Success", 201


if __name__ == "__main__":
    app.run()
