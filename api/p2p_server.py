import ast
import json
import os

import requests
import asyncio
import websockets

from coin.block import BlockChain


HOST_IP = os.environ.get("HOST_IP")
CLIENT_IP = os.environ.get("CLIENT_IP")


def get_chain():
    block_data = requests.get(f"http://{HOST_IP}:5000/blocks")
    return block_data


def replace_chain(data):
    r = requests.post("http://{HOST_IP}:5000/replace_chain", json=data)
    return r


async def hello(websocket, path):
    block_data = await websocket.recv()
    our_block_data = get_chain()
    print("Received Broadcast")

    new_chain = BlockChain(json=ast.literal_eval(block_data.decode("UTF-8")))
    block_chain = BlockChain(json=our_block_data.json())
    if block_chain.chain_is_valid(new_chain.chain):
        replace_chain(ast.literal_eval(block_data.decode("UTF-8")))


if __name__ == "__main__":
    start_server = websockets.serve(hello, "0.0.0.0", 8000)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
