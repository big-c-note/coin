import os
from typing import List, Tuple

from coin.transaction import UnspentTxOut, TxOut, Transaction, TxIn, sign_tx_in


# TODO: Currently user creates this directory.
# Should use pathlib.
PRIVATE_FILE_LOCATION = 'wallet/'
PRIVATE_KEY_NAME = "keyo.pem"
PUBLIC_KEY_NAME = "pubkeyo.pem"


def create_private_public_key():
    """
    Generate private and public key using openssl.
    https://medium.com/@skloesch/openssl-and-ecdsa-signatures-db60c005b1f4
    """
    secp = PRIVATE_FILE_LOCATION + "secp256k1.pem"
    os.system(f"openssl ecparam -name secp256k1 -out {secp}")
    priv_key = PRIVATE_FILE_LOCATION + PRIVATE_KEY_NAME
    os.system(f"openssl ecparam -in {secp} -genkey -noout -out {priv_key}")
    pub_key = PRIVATE_FILE_LOCATION + PUBLIC_KEY_NAME
    os.system(f"openssl ec -in {priv_key} -pubout > {pub_key}")


def get_private_from_wallet():
    """
    Retrieve private from file.
    """
    priv_key = PRIVATE_FILE_LOCATION + PRIVATE_KEY_NAME
    with open(priv_key) as f:
        content = f.read().splitlines()
    private = ''
    for line in content:
        if not (line[0] == '-' and line[-1] == '-'):
            private += line
    return private


def get_public_from_wallet():
    """
    Retrieve public from file.
    """
    pub_key = PRIVATE_FILE_LOCATION + PUBLIC_KEY_NAME
    with open(pub_key) as f:
        content = f.read().splitlines()
    public = ''
    for line in content:
        if not (line[0] == '-' and line[-1] == '-'):
            public += line
    return public


def get_signature(data: str):
    """Produces signature from private key."""
    data_loc = PRIVATE_FILE_LOCATION + "data"
    os.system(f"echo -n {data} > {data_loc}")
    priv_key = PRIVATE_FILE_LOCATION + PRIVATE_KEY_NAME
    sig_file = PRIVATE_FILE_LOCATION + "sig.b64"
    os.system(f"openssl dgst -sha1 -sign {priv_key} {data_loc} | base64 > {sig_file}")
    with open(f"{sig_file}") as f:
        content = f.read().splitlines()
    signature = ''.join(content)
    return signature


def init_wallet():
    """
    Create Wallet.
    """
    priv_key = PRIVATE_FILE_LOCATION + PRIVATE_KEY_NAME
    if os.path.isfile(priv_key):
        return
    create_private_public_key()


#
def get_balance(address: str, unspent_tx_outs: List[UnspentTxOut]) -> float:
    amount = 0.
    for u_tx_out in unspent_tx_outs:
        if u_tx_out.address == address:
            amount += u_tx_out.amount
    return amount


#
def find_tx_outs_for_amount(
    amount: float,
    my_unspent_tx_outs: List[UnspentTxOut]
) -> Tuple[List[UnspentTxOut], float]:
    current_amount = 0.
    included_unspent_tx_outs: List[UnspentTxOut] = []
    for my_unspent_tx_out in my_unspent_tx_outs:
        included_unspent_tx_outs.append(my_unspent_tx_out)
        current_amount += my_unspent_tx_out.amount
        if current_amount >= amount:
            left_over_amount = current_amount - amount
            return included_unspent_tx_outs, left_over_amount
    raise ValueError("Insufficeint funds")


#
# TODO: Am I only allowing for 1 transaction to have two tx_ins/outs?
def create_tx_outs(
    receiver_address: str,
    my_address: str,
    amount: float,
    left_over_amount: float
) -> List[TxOut]:
    tx_out_1: TxOut = TxOut(receiver_address, amount)
    if left_over_amount == 0:
        return [tx_out_1]
    else:
        left_over_tx: TxOut = TxOut(my_address, left_over_amount)
        return [tx_out_1, left_over_tx]


def create_transaction(
    receiver_address: str,
    amount: float,
    private_key: str,
    unspent_tx_outs: List[UnspentTxOut]
) -> Transaction:
    """Helper function for creating transaction."""
    my_address: str = get_public_from_wallet()
    my_unspent_tx_outs: List[UnspentTxOut] = [
        u_tx_out for u_tx_out in unspent_tx_outs if u_tx_out.address == my_address
    ]
    included_unspent_tx_outs, left_over_amount = find_tx_outs_for_amount(
        amount,
        my_unspent_tx_outs
    )

    def to_unsigned_tx_in(u_tx_out: UnspentTxOut):
        tx_in = TxIn(u_tx_out.tx_out_id, u_tx_out.tx_out_index, None)
        return tx_in

    # Wat?
    unsigned_tx_ins: List[TxIn] = [
        to_unsigned_tx_in(u_tx_out) for u_tx_out in included_unspent_tx_outs
    ]
    # TODO: Is it a problem that I make the tx id before signing?
    tx = Transaction(
        unsigned_tx_ins,
        create_tx_outs(receiver_address, my_address, amount, left_over_amount)
    )
    for i, tx_in in enumerate(tx.tx_ins):
        tx_in.signature = sign_tx_in(tx, i, private_key, unspent_tx_outs)
    return tx
