import koios_python
import pandas as pd
import argparse
from collections import defaultdict
from datetime import datetime
import json

kp_mainnet = koios_python.URLs(url="http://10.0.0.89:8053/api/v1/")

TOKEN_POLICY_ID = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
TOKEN_ASSET_NAME = "4c51"
LQ_USER_DIST_WALLET = "addr1xxawr298yy36qrqw6yqc9v2qvgfddwjpqkgnfkt2rvq3u3f74zdzpgetwrygga9mlz44dc5tfrd82m0vxpfjmkpsf9ts06jfwd"
LQ_STAKING_WALLET_1 = "addr1xx0cj23c0mhfht6uj74x6ytr6c3jr3gnxd3tthdemcxdulrw7xjpplgp0lahw2u869nn77avyd3vw96p4jhtdrykyt4safjps8"
LQ_STAKING_WALLET_2 = "addr1x8q76ctyve23u8h5sux3npxwwlnedpxlz3ft89vlshhs5val9ytme40nlqwch8gxnrsk3cvt69qn8xuqsd2fuv7fgghqjct4kw"
SUNDAE_LQ_REWARD_WALLET = "addr1q9clfpceddhyejpxkr0jllp04spldxpsucge5nwk6pjx4z7hy3954pmhklwxjz05vsx0qt4yw4a9275eldyrkp0c0hlqtpqx6e"

staking_wallets = [LQ_STAKING_WALLET_1, LQ_STAKING_WALLET_2]


def read_csv_to_df(file_path):
    df = pd.read_csv(file_path)
    print(f"Successfully read {file_path} into a DataFrame.")
    return df

def get_transaction_details(df):

    all_tx_details = {}

    for tx in df['tx_hash']:
        tx_data = kp_mainnet.get_tx_info(tx)
        tx_details = {
            "inputs": [],
            "outputs": []
        }
        # Extract inputs
        for inp in tx_data["inputs"]:
            tx_details["inputs"].append({
                "tx_hash": inp["tx_hash"],
                "utxo_index": inp["tx_index"],
                "address": inp["address"],
                "is_contract": inp.get("is_contract", False),
                "contract_address": inp.get("contract_address", None)
            })
        # Extract outputs
        for out in tx_data["outputs"]:
            tx_details["outputs"].append({
                "tx_hash": out["tx_hash"],
                "utxo_index": out["tx_index"],
                "address": out["address"],
                "is_contract": out.get("is_contract", False),
                "contract_address": out.get("contract_address", None)
            })
        all_tx_details[tx] = tx_details
    else:
        # print(f"Failed to fetch transaction details for {tx}: {response.status_code}")
        all_tx_details[tx] = None

    return all_tx_details


def determine_utxo_status(df, specific_contract):
    # Initialize status column
    df["status"] = 1  # Assume not consumed as default

    # Create a set of UTXOs for quick lookup
    utxo_set = set((row.tx_hash, row.utxo_index) for idx, row in df.iterrows())

    # Iterate over the dataframe to determine the status
    for idx, row in df.iterrows():
        utxo = (row.tx_hash, row.utxo_index)
        consumed = False
        interacts_specific_contract = False
        interacts_other_contract = False

        # Check subsequent transactions for this UTXO
        for other_idx, other_row in df.iterrows():
            if other_idx <= idx:
                continue  # Skip checking the current or previous transactions

            tx_details = get_transaction_details(other_row.tx_hash)
            for inp in tx_details["inputs"]:
                if (inp["tx_hash"], inp["utxo_index"]) == utxo:
                    consumed = True
                    if inp["is_contract"]:
                        if inp["contract_address"] == specific_contract:
                            interacts_specific_contract = True
                        else:
                            interacts_other_contract = True
                    break  # No need to check further if this UTXO is consumed

            if consumed:
                break

        if consumed:
            if interacts_specific_contract:
                df.at[idx, "status"] = 3
            elif interacts_other_contract:
                df.at[idx, "status"] = 4
            else:
                df.at[idx, "status"] = 2

    return df


# specific_contract = "addr1w8arvq7j9qlrmt0wpdvpp7h4jr4fmfk8l653p9t907v2nsss7w7r4"
# tx_data = read_csv_to_df("./output/lq_emissions.csv")
# df = determine_utxo_status(tx_data, specific_contract)
# print(df)

data = read_csv_to_df("./Cardano-Token-Engineering-Lab/Query-Cardano-Data/Koios/output/emissionsv2.csv")
data_details = get_transaction_details(data)
print(data_details)
