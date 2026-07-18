import koios_api as kp
import pandas as pd

# for LQ Token
policy_id = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
asset_name = '4c51'
token_name = bytearray.fromhex(asset_name).decode()

def asset_policy_info(policy_id):
    data = kp.get_policy_asset_info(policy_id)
    df = pd.json_normalize(data)
    return df

#data = kp.get_asset_addresses(policy_id, asset_name)
#df = pd.json_normalize(data)
#print(df)

data = kp.get_asset_summary(policy_id, asset_name)
df = pd.json_normalize(data)
print(df)

df_asset_info = asset_policy_info(policy_id)

def xls_writer(df, token_name):
    filename = token_name + " asset data.xlsx"
    df.to_excel(filename)

xls_writer(df_asset_info, token_name)

