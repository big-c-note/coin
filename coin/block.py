from hashlib import sha256
import math
from typing import List, Optional
import json

from datetime import datetime


class Block:
    def __init__(
            self,
            index: int,
            data: str,
            previous_hash: Optional[str],
            difficulty: int,
            nonce: int
    ):
        assert type(index) == int
        self.index: int = index
        # TODO: how to validate type of hash
        if previous_hash:
            self.previous_hash: str = previous_hash
        else:
            self.previous_hash = ''
        if data == "genesis block":
            self.time: int = 0
        else:
            self.time = self._unix_milli()
        assert type(data) == str
        self.data: str = data
        self.difficulty: int = difficulty
        self.nonce: int = nonce
        self.hashed_data: str = self._calculate_sha()

    def calculate_sha(self):
        return self._calculate_sha()

    def _calculate_sha(self):
        body = (
            str(self.nonce)
            + str(self.index)
            + self.previous_hash
            + str(self.time)
            + self.data
            + str(self.difficulty)
        )
        return sha256(body.encode()).hexdigest()

    @staticmethod
    def _unix_milli():
        time = datetime.now()
        epoch = datetime.utcfromtimestamp(0)
        return (time - epoch).total_seconds() * 1000.0

    def get_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)


class BlockChain:
    def __init__(self, json=None):
        if json:
            for k, v in json.items():
                if k == "chain":
                    blocks: List[Block] = ([
                        Block(
                            b["index"],
                            b["data"],
                            b["previous_hash"],
                            b["difficulty"],
                            b["nonce"]
                        ) for b in v
                    ])
                    v = blocks
                setattr(self, k, v)
        else:
            self.chain: List[Block] = [Block(0, "genesis block", None, 5, 0)]
            self.difficulty_adjustment_interval = 10
            self.block_generation_interval = 10
            self._cummulative_difficulty = 0

    def generate_new_block(self, block_data: str):
        index: int = self.latest_block.index + 1
        previous_hash = self.latest_block.hashed_data
        difficulty = self.get_difficulty()
        nonce = 0
        done = False
        while not done:
            # TODO: Makes sense to calculate the has outside of the class, in
            # the case here, I wouldn't have to initiate a new object every
            # time.
            new_block: Block = Block(index, block_data, previous_hash, difficulty, nonce)
            if self.hash_matches_difficulty(new_block.hashed_data, difficulty):
                done = True
            else:
                nonce += 1
        assert self._block_is_valid(new_block, self.latest_block)
        self.chain.append(new_block)
        self._cummulative_difficulty += 2**difficulty

    def _block_is_valid(self, new_block: Block, old_block: Block):
        assert new_block.index == old_block.index + 1
        assert new_block.previous_hash == old_block.hashed_data
        assert new_block.hashed_data == new_block.calculate_sha()
        return True

    def chain_is_valid(self, chain: List[Block]):
        prev_block: Optional[Block] = None
        for block in chain:
            if prev_block:
                assert self._block_is_valid(block, prev_block)
            else:
                assert block.hashed_data == self.chain[0].hashed_data
            prev_block = block
        return True

    @staticmethod
    def hash_matches_difficulty(hashed_data: str, difficulty: int):
        num_bits = int(len(hashed_data) * math.log2(16))
        hash_in_binary = bin(int(hashed_data, 16))[2:].zfill(num_bits)
        return hash_in_binary[:difficulty] == "0" * difficulty

    def get_difficulty(self):
        get_difficulty = self.latest_block.index % self.difficulty_adjustment_interval == 0
        if get_difficulty and self.latest_block.index != 0:
            return self.get_adjusted_difficulty()
        else:
            return self.latest_block.difficulty

    def get_adjusted_difficulty(self):
        # TODO: Possible bug for when this fires.
        prev_adjustment_block = self.chain[self.length - self.difficulty_adjustment_interval]
        time_expected = self.difficulty_adjustment_interval * self.block_generation_interval
        time_taken = self.latest_block.time - prev_adjustment_block.time
        if time_taken < time_expected / 2:
            return prev_adjustment_block.difficulty + 1
        elif time_taken > time_expected * 2:
            return prev_adjustment_block.difficulty - 1
        else:
            return prev_adjustment_block.difficulty

    @property
    def cummulative_difficulty(self):
        return self._cummulative_difficulty

    def is_valid_timestamp(self, new_block: Block, previous_block: Block):
        assert previous_block.time - 6000 < new_block.time
        assert new_block.time - 6000 < self._unix_milli()

    def get_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    @staticmethod
    def _unix_milli():
        time = datetime.now()
        epoch = datetime.utcfromtimestamp(0)
        return (time - epoch).total_seconds() * 1000.0

    @property
    def latest_block(self):
        return self.chain[-1]

    @property
    def length(self):
        return len(self.chain)
