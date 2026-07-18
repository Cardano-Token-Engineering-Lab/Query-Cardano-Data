import koios_api as koi
import pandas as pd

policy_id = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
asset_name = '4c51'
block_height = 5406748
# Liqwid Smart Contract for LQ Staking
sc_address = 'addr1w8arvq7j9qlrmt0wpdvpp7h4jr4fmfk8l653p9t907v2nsss7w7r4'
token_name = bytearray.fromhex(asset_name).decode()

data = koi.get_address_info(sc_address)
#print(address_info)
data_dict = {
    'policy_id': [obj.policy_id for obj in data],
    'asset_name': [obj.asset_name for obj in data],
    'asset_name_ascii': [obj.asset_name_ascii for obj in data],
    'fingerprint': [obj.asset_name for obj in data],
    'asset_name': [obj.asset_name for obj in data],
    'asset_name': [obj.asset_name for obj in data],
    'asset_name': [obj.asset_name for obj in data],
    'asset_name': [obj.asset_name for obj in data],
    'asset_name': [obj.asset_name for obj in data],
}
search_key = 'utxo_set'
address_utxo_set = [data[search_key] for data in address_info if search_key in data]
#print(address_utxo_set)
df_utxo_set = pd.DataFrame.from_dict(address_utxo_set)
print(df_utxo_set)

def xls_writer(df, token_name):
    filename = token_name + " token holders data.xlsx"
    df.to_excel("token holders data.xlsx")

xls_writer(df_utxo_set, token_name)

#df_stacked = df_utxo_set.apply(pd.Series).stack().reset_index(level=0)
#df_stacked.columns = ['value', 'tx_hash', 'tx_index', 'asset_list']
#df_utxo_set_pivot = df_stacked.pivot(columns='keys', values='value')
#print(df_utxo_set_pivot)