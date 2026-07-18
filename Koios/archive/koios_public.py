import koios_api
import pandas as pd

api = koios_api

def fetch_transactions(start_block, end_block):
    """
    Fetch transactions in a specific epoch range from the public Koios API.
    """
    transactions = []
    for block in range(start_block, end_block + 1):
        # Fetch transactions for each epoch
        epoch_transactions = api.epoch_txs(block)
        transactions.extend(epoch_transactions)
    
    return transactions

txs = fetch_transactions()