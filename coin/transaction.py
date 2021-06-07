from typing import List, Optional, Union
from hashlib import sha256


COINBASE_AMOUNT = 50.


class UnspentTxOut:
    """Class for unspent transactions."""
    def __init__(
        self,
        tx_out_id: str,
        tx_out_index: int,
        address: str,
        amount: float
    ):
        assert type(tx_out_id) == str
        assert type(tx_out_index) == int
        assert type(address) == str
        assert type(amount) == float
        self.tx_out_id = tx_out_id
        self.tx_out_index = tx_out_index
        self.address = address
        self.amount = amount

    # TODO: Avoid setting attributes after creation.

    def __delattr__(self, key, value):
        raise AttributeError("Cannot delete attributes.")


class TxIn:
    """
    The transaction input. Usually there will be more than one. This is because
    the protocol ammasess as inputs several previous unspent outputs,
    including, if there is more more money available in total for the unspent
    transactions that cover the transaction amount, the remaining unneeded
    coins go back to the sender as a transaction output.
    """
    def __init__(self, tx_out_id: str, tx_out_index: int, signature: Optional[str]):
        assert type(tx_out_id) == str
        assert type(tx_out_index) == int
        assert type(signature) == str or signature is None
        # This is the traansaction id and index of the tx out.
        self.tx_out_id: str = tx_out_id
        self.tx_out_index: int = tx_out_index
        self.signature: Optional[str] = signature  # Not the private key itself


class TxOut:
    """Transaction output."""
    def __init__(self, address: str, amount: float):
        assert type(address) == str
        assert type(amount) == float
        self.address: str = address
        self.amount: float = amount


class Transaction:
    def __init__(self, tx_ins: List[TxIn], tx_outs: List[TxOut]):
        for tx_in, tx_out in zip(tx_ins, tx_outs):
            assert isinstance(tx_in, TxIn) and isinstance(tx_out, TxOut)
        self.tx_ins: List[TxIn] = tx_ins
        self.tx_outs: List[TxOut] = tx_outs
        self.transaction_id = self._get_transaction_id()

    def _get_transaction_id(self):
        tx_in_str: str = [
            tx_in.tx_out_id + str(tx_in.tx_out_index) for tx_in in self.tx_ins
        ]
        tx_out_str: str = [
            tx_out.address + str(tx_out.amount) for tx_out in self.tx_outs
        ]
        unhashed_id: str = ''.join(tx_out_str) + ''.join(tx_in_str)
        return sha256(unhashed_id.encode()).hexdigest()


# TODO: Validations
def get_tx_in_amount(tx_in: TxIn, a_unspent_tx_outs: List[UnspentTxOut]) -> float:
    """Get amounts from unspent transactions."""
    u_tx_out = find_unspent_tx_out(
        tx_in.tx_out_id,
        tx_in.tx_out_index,
        a_unspent_tx_outs
    )
    if u_tx_out:
        return u_tx_out.amount
    return 0.


def find_unspent_tx_out(
    transaction_id: str,
    index: int,
    a_unspent_tx_outs: List[UnspentTxOut]
) -> Union[bool, UnspentTxOut]:
    """Lookup unspent transaction."""
    # TODO: Would be good to do with sets/numpy.
    # Generally awkward to return Union[bool, UnspentTxOut]
    for u_tx_out in a_unspent_tx_outs:
        if transaction_id == u_tx_out.tx_out_id and index == u_tx_out.tx_out_index:
            return u_tx_out
    return False


def get_coinbase_transaction(address: str, block_index: int) -> Transaction:
    """Usually the first transaction, in order to start outputs."""
    tx_ins: List[TxIn] = [TxIn("", block_index, "")]
    tx_outs: List[TxOut] = [TxOut(address, COINBASE_AMOUNT)]
    return Transaction(tx_ins, tx_outs)


def sign_tx_in(
    transaction: Transaction,
    tx_in_index: int,
    private_key: str,
    a_unspent_tx_outs: List[UnspentTxOut]
):
    """
    As the owner of unspent transactions, in order to spend the coins, you must
    prove that you own the coins by providing a signature. The signature shows
    that you have the private key that produced that public key (address).
    """
    tx_in: TxIn = transaction.tx_ins[tx_in_index]
    data_to_sign: str = transaction.transaction_id
    referenced_unspent_tx_out: Union[bool, UnspentTxOut] = find_unspent_tx_out(
        tx_in.tx_out_id, tx_in.tx_out_index, a_unspent_tx_outs
    )
    # TODO: Hack to avoid circular dependency.
    from coin.wallet import get_public_from_wallet, get_signature
    # TODO: Bit of a hack for now.
    assert isinstance(referenced_unspent_tx_out, UnspentTxOut)
    referenced_address: str = referenced_unspent_tx_out.address
    pubkey = get_public_from_wallet()
    # Making sure that we are signing for a transaction (ie; trying to spend
    # an unspent transaction) whoe funds belong to our public key.
    assert referenced_address == pubkey
    sig = get_signature(data_to_sign)
    return sig


def process_transactions(
    a_transactions: List[Transaction],
    a_unspent_transactions: List[UnspentTxOut]
):
    """Helper function for this."""
    # TODO Validate on the receivers end. Rn I'm assuming they are benevolent
    # and using this software to create transactions, which doesn't have to be
    # the case.
    return update_unspent_tx_outs(a_transactions, a_unspent_transactions)


def update_unspent_tx_outs(
    new_transactions: List[Transaction],
    a_unspent_tx_outs: List[UnspentTxOut]
):
    """
    After new_transactions come in, this function is used to update the list of
    unspent transactions. That list is important to maintain to be able to
    iterate through and see who has unspent transactions.
    """
    # TODO: Hack to avoid circular dependency.
    from coin.wallet import get_public_from_wallet
    # In particular these would be the new ones from a new block
    # After that block had been validated.
    # TODO: Not efficeint
    # TODO: Wrap in UpdateUnspentTxOut
    new_unspent_tx_outs: List[UnspentTxOut] = [
        UnspentTxOut(
            t.transaction_id,
            i,
            tx_out.address,
            tx_out.amount
        ) for t in new_transactions for i, tx_out in enumerate(t.tx_outs)
    ]
    consumed_tx_outs: List[UnspentTxOut] = [
        UnspentTxOut(
            tx_in.tx_out_id,
            tx_in.tx_out_index,
            "",
            0.
        ) for t in new_transactions for tx_in in t.tx_ins
    ]
    resulting_unspent_tx_outs: List[UnspentTxOut] = []
    for u_tx_out in a_unspent_tx_outs:
        found_tx_out: UnspentTxOut = find_unspent_tx_out(
            u_tx_out.tx_out_id,
            u_tx_out.tx_out_index,
            consumed_tx_outs
        )
        if found_tx_out is False:
            resulting_unspent_tx_outs.append(u_tx_out)
    resulting_unspent_tx_outs += new_unspent_tx_outs
    return resulting_unspent_tx_outs
