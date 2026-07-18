import koios_python
import pandas as pd
from collections import defaultdict
import argparse

kp_mainnet = koios_python.URLs(url="http://10.0.0.89:8053/api/v1/")

TOKEN_POLICY_ID = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
TOKEN_ASSET_NAME = "4c51"
WALLET_ADDRESS = "addr1q9clfpceddhyejpxkr0jllp04spldxpsucge5nwk6pjx4z7hy3954pmhklwxjz05vsx0qt4yw4a9275eldyrkp0c0hlqtpqx6e"
START_EPOCH = 485
END_EPOCH = 486
SPECIFIED_SMART_CONTRACT_HASH = (
    "b2893731a362af8c58b15a5a3b4d115bdab65920b6c41aa22bd2a197423f60c6"
)


def convert_to_csv(data, file_name):
    """
    Converts a JSON object or a pandas DataFrame to a CSV file.

    Parameters:
    data (dict or pandas.DataFrame): The JSON object (as a Python dict) or DataFrame to convert.
    file_name (str): The path to the output CSV file.
    """
    if isinstance(data, dict):
        # Convert JSON object to DataFrame
        df = pd.json_normalize(data)
    elif isinstance(data, pd.DataFrame):
        # Use the DataFrame directly
        df = data
    else:
        raise ValueError(
            "Input data must be a dictionary (JSON object) or a pandas DataFrame."
        )

    # Save DataFrame to CSV
    output = "./output/" + file_name + ".csv"
    df.to_csv(output, index=False)
    print(f"Data successfully written to {output}")


def get_current_epoch():
    tip_info = kp_mainnet.get_tip()
    return tip_info[0]["epoch_no"]


def fetch_epoch_blocks():
    # Fetch all blocks to build epoch block dictionary
    blocks = []
    block_no = 1
    current_epoch = get_current_epoch()
    while True:
        if block_no > current_epoch:
            break
        block_info = kp_mainnet.get_epoch_info(block_no)
        blocks.append(block_info)
        block_no += 1

    flat_epoch_data = [item[0] for item in blocks]
    df = pd.DataFrame(flat_epoch_data)

    # Initialize first block
    df.loc[0, "first_block"] = 1
    df.loc[0, "last_block"] = df.loc[0, "blk_count"]

    # Calculate first block and last block for each epoch
    for i in range(1, len(df)):
        df.loc[i, "first_block"] = df.loc[i - 1, "last_block"] + 1
        df.loc[i, "last_block"] = df.loc[i, "first_block"] + df.loc[i, "blk_count"] - 1

    df = df.drop(
        columns=[
            "out_sum",
            "fees",
            "start_time",
            "end_time",
            "active_stake",
            "total_rewards",
            "avg_blk_reward",
        ]
    )

    return df


epoch_data = fetch_epoch_blocks()

print(epoch_data)


def get_asset_utxo(TOKEN_POLICY_ID, TOKEN_ASSET_NAME):
    asset_utxo = kp_mainnet.get_asset_utxos([TOKEN_POLICY_ID, TOKEN_ASSET_NAME])
    # flat_asset_data = [item[0] for item in asset_utxo]
    df = pd.DataFrame(asset_utxo)
    return df


asset_utxo = get_asset_utxo(TOKEN_POLICY_ID, TOKEN_ASSET_NAME)
convert_to_csv(asset_utxo, "asset_UTXO_v1")
print(asset_utxo)
