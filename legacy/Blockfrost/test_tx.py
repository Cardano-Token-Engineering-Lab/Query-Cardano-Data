import pandas as pd
from helper_functions import read_csv, write_csv, get_api_token

# Load Blockfrost API key
api = get_api_token()

# Token information to be queried and analyzed
policy_id = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
asset_name = "4c51"
token_name = bytearray.fromhex(asset_name).decode()

df_tx = read_csv(token_name+"_tx_data.csv")

tx_hash = df_tx.loc[0, 'tx_hash']
df = api.transaction(tx_hash, return_type="pandas")
df_exploded = df.explode('output_amount')
df_unnested = pd.json_normalize(df['output_amount'])
print(df_unnested)
df_combined = pd.concat([df.drop(columns='output_amount'), df_unnested], axis=1)
# print(df_combined)

write_csv(df_unnested, token_name+"_tx_data_detail.csv")