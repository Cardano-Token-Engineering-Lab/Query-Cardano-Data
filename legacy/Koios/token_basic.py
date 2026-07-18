import koios_api as koi
import json
import itertools
import pandas as pd
import openpyxl

# print(koi.get_tip())
# LQ policy_id = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
# qADA = "a04ce7a52545e5e33c2867e148898d9e667a69602285f6a1298f9d68"

policy_id = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
asset_name = '4c51'

# Generate token metadata dataframe from asset policy info
def policy_info(pol_id):
    asset_policy_info = koi.get_policy_asset_info(pol_id)
    df_policy_info = pd.DataFrame.from_dict(asset_policy_info)
    return df_policy_info


def metadata(df_policy_info):
    df_reg_metadata = df_policy_info["token_registry_metadata"].to_frame()
    df_metadata = df_reg_metadata.explode("token_registry_metadata").reset_index(
        drop=True
    )
    df_metadata = df_metadata.join(
        pd.json_normalize(df_reg_metadata.pop("token_registry_metadata"))
    )
    df_metadata = df_metadata.iloc[0]
    return df_metadata


# Extract metadata key info
def metadata_pull(pol_id, df_metadata):
    df = policy_info(pol_id)
    total_supply = pd.to_numeric(df["total_supply"])
    token_name = df_metadata["name"]
    token_ticker = df_metadata["ticker"]
    token_decimals = df_metadata["decimals"]
    return total_supply, token_name, token_ticker, token_decimals


# Generate Token holder addresses and quantities from policy ID
def holders(df_policy_info, pol_id, name, decimals):
    asset_address_list = koi.get_asset_address_list(pol_id)
    df_holders = pd.DataFrame.from_dict(asset_address_list)
    df_holders["Name"] = name
    print(df_holders.head(50))
    df_holders["quantity"] = pd.to_numeric(df_holders["quantity"])
    df_holders["quantity"] = df_holders["quantity"]/ (10**decimals)
    df_holders = df_holders.sort_values(by="quantity", ascending=False)
    total_circ_supply = df_holders["quantity"].sum()
    total_supply = pd.to_numeric(df_policy_info["total_supply"]) / (
        10**decimals
    )
    print("Total Circulating Supply = ", total_circ_supply)
    pct_circ = total_circ_supply / total_supply
    print("Pct of Tokens in circulation = ", pct_circ)
    print(df_holders.head(20))
    return df_holders


def xls_writer(df, token_name):
    filename = token_name + " token holders data.xlsx"
    df.to_excel("token holders data.xlsx")


df_policy_info = policy_info(policy_id)
print(df_policy_info)

df_metadata = metadata(df_policy_info)
print(df_metadata)

total_supply, token_name, token_ticker, token_decimals = metadata_pull(
    policy_id, df_metadata
)

df_holders = holders(df_policy_info, policy_id, token_name, token_decimals)

xls_writer(df_holders)

#with pd.ExcelWriter('output.xlsx') as writer:  
#    df_policy_info.to_excel(writer, sheet_name='Policy_Info')
#    df_summary.to_excel(writer, sheet_name='Asset_Summary')
#    df_address.to_excel(writer, sheet_name='Address_List')
#    df_tx.to_excel(writer, sheet_name='Asset_txs')