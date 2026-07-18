import pandas as pd
from helper_functions import create_info_xlsx, get_api_token

# Load Blockfrost API key
api = get_api_token()

# Token information to be queried and analyzed
policy_id = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
asset_name = "4c51"
token_name = bytearray.fromhex(asset_name).decode()


def asset_info(policy_id, asset_name):
    df = api.asset(asset=policy_id + asset_name, return_type="pandas")
    return df

def tokens_in_policy(policy_id):
    df = api.assets_policy(policy_id, return_type="pandas")
    policy_token_count = len(df.index)
    print(
        f"The total number of tokens under the selected policy is/are: {policy_token_count}"
    )
    return df

# Query Asset information
df_info = asset_info(policy_id,asset_name)
df_tokens_in_policy = tokens_in_policy(policy_id)

# Get xlsx sheet info prepared
dataframes_dict = {'Asset Info': df_info, 'Tokens In Policy': df_tokens_in_policy}

# create_info_xlsx(dataframes_dict, token_name+".xlsx")
