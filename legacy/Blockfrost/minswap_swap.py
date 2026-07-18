import pandas as pd
from helper_functions import read_csv, write_csv, get_api_token, asciitoken_name
from token_info import policy_id, asset_name

# Load Blockfrost API key
api = get_api_token()

# Token info
policy_id = policy_id
asset_name = asset_name
token_name = asciitoken_name(asset_name)

# Minswap swap address
minswap_addy = "addr1zxn9efv2f6w82hagxqtn62ju4m293tqvw0uhmdl64ch8uw6j2c79gy9l76sdg0xwhd7r0c0kna0tycz4y5s6mlenh8pq6s3z70"


def swap_info(swap_addy, policy_id, asset_name, max_page):
    df = pd.DataFrame()
    while True:
        data = api.address_utxos_asset(
            address=swap_addy, asset=policy_id + asset_name, return_type="pandas")
        df = pd.concat([data, df])
        return df

swap_df = swap_info(minswap_addy, policy_id, asset_name, 5)
print(swap_df)

write_csv(swap_df, token_name + "_swap_info.csv")
