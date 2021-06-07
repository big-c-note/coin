## Practice BlockChain

Simple blockchain basics written in python. Loosely based off [this typescript
version](https://github.com/lhartikk/naivecoin).

Super rough at this point, so be careful!

### Dependencies

- You'll need openssl for wallet creation (see `coin/wallet`).
- You'll a `wallet` directory in your top level. Else change the globals in `coin/wallet`

``` {python}
pip3 install -r requirements.txt
pip3 install -e .
```

### Examples

You can find simple examples of an API build with coin.block and connections to
a peer using websockets python package. I haven't included transactions yet in the
examples.

#### Transactions

``` {python}
from coin.transaction import get_coinbase_transaction, process_transactions
from coin.wallet import init_wallet, get_public_from_wallet, create_transaction,\
	get_private_from_wallet

# Initialize wallet (uses open ssl and wallet directory (see above))
init_wallet()
# Create initial transaction.
pubkey = get_public_from_wallet()
tx = get_coinbase_transaction(pubkey, 0) 
unspent_tx_outs = process_transactions([tx], [])
# See address and amount of coinbase transaction.
unspent_tx_outs[0].amount
unspent_tx_outs[0].address
# Send some of that coin to another address.
priv = get_private_from_wallet()
tx2 = create_transaction("cat", 45., priv, unspent_tx_outs)
# See signature.
tx2.tx_outs[0].signature
```

### Future Development Needs:

- Tests!!!. CI/CD
- Generally confusing organization of code base.
- Transaction Relaying.
- Better peer to peer deployment and dockerization.
- Wallet.
- Blockhain Explorer.
