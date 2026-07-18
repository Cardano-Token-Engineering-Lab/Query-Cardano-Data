import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from helper_functions import read_csv, write_csv, get_api_token
from token_info import asset_info
from project_data import asset_name, policy_id, token_name, project_wallets

# Load Blockfrost API key
api = get_api_token()

asset_name = asset_name
policy_id = policy_id
project_wallets = [
    "addr1xxawr298yy36qrqw6yqc9v2qvgfddwjpqkgnfkt2rvq3u3f74zdzpgetwrygga9mlz44dc5tfrd82m0vxpfjmkpsf9ts06jfwd",
    "addr1x85etkeguzkemwfxtjtnl3ysp8fdmrjcdhsyp645y8ghwt4fp42lutam2alc7dzukvxgkxq0wd4aphv4zwczey39dysqy6rd7d",
    "addr1xxhrfw3fxavu9mzvh9ag8aja7uvhz70zqpf8m24gxash02s84wdjchweuj84lmg028rqft97snacuhs4cmvu9ywyhzcs3rxckm",
    "addr1x8q76ctyve23u8h5sux3npxwwlnedpxlz3ft89vlshhs5val9ytme40nlqwch8gxnrsk3cvt69qn8xuqsd2fuv7fgghqjct4kw",
    "addr1w8arvq7j9qlrmt0wpdvpp7h4jr4fmfk8l653p9t907v2nsss7w7r4"
]

# Pull in data if needing to query use first statement or if available locally use second line
# df_asset_addy = query_holders(policy_id, asset_name, 1)
df_asset_addy = read_csv(token_name + "_holders.csv")

# df_script = script_address(df_asset_addy)
df_script = read_csv(token_name + "_address_detail.csv")

# Filter contracts that rolled over on the csv due to too many tokens
df_script = df_script[df_script['address'].str.startswith('addr1')]

# Query only contract rows
df_script = df_script[df_script['script'] ==True]
df_script = df_script.query("address not in @project_wallets")

df_script = df_script.merge(df_asset_addy, on='address')
print(df_script)

df_script = df_script.sort_values(by='quantity', ascending=False).reset_index(drop=True)
df_script['cumulative_sum'] = df_script['quantity'].cumsum()
contract_total = df_script['cumulative_sum'].max()
df_script.drop(columns=['amount', 'stake_address', 'script'], inplace=True)

print(df_script)