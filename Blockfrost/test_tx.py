import pandas as pd
from helper_functions import read_csv, write_csv, get_api_token

# Load Blockfrost API key
api = get_api_token()

# Token information to be queried and analyzed
policy_id = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
asset_name = "4c51"
token_name = bytearray.fromhex(asset_name).decode()

staking_addr = "addr1w8arvq7j9qlrmt0wpdvpp7h4jr4fmfk8l653p9t907v2nsss7w7r4"

def query_staking_info(staking_addr, policy_id, asset_name):
    # Query staking information using the Blockfrost API
    staking_info = api.address_utxos_asset(staking_addr, policy_id, asset_name, return_type="pandas")
    return staking_info

print(query_staking_info(staking_addr, policy_id, asset_name))
