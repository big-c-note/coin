import os

import requests
import asyncio
import websockets


HOST_IP = os.environ.get("HOST_IP")
CLIENT_IP = os.environ.get("CLIENT_IP")


def make_block(data):
    r = requests.post(f"http://{HOST_IP}:5000/make_blocks", json={"data": data})
    return r


def get_chain():
    block_data = requests.get("http://{HOST_IP}:5000/blocks")
    return block_data


async def hello():
    uri = f"ws://{CLIENT_IP}:8000"
    async with websockets.connect(uri) as websocket:
        data = "cat"
        make_block(data)
        block_data = get_chain()

        await websocket.send(block_data)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(hello())
