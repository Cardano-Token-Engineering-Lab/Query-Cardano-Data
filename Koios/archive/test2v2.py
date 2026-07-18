import koios_python
import pandas as pd
import argparse
from collections import defaultdict
from datetime import datetime

kp_mainnet = koios_python.URLs(url="http://10.0.0.89:8053/api/v1/")

TOKEN_POLICY_ID = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
TOKEN_ASSET_NAME = "4c51"
LQ_USER_DIST_WALLET = "addr1xxawr298yy36qrqw6yqc9v2qvgfddwjpqkgnfkt2rvq3u3f74zdzpgetwrygga9mlz44dc5tfrd82m0vxpfjmkpsf9ts06jfwd"
LQ_STAKING_WALLET_1 = "addr1xx0cj23c0mhfht6uj74x6ytr6c3jr3gnxd3tthdemcxdulrw7xjpplgp0lahw2u869nn77avyd3vw96p4jhtdrykyt4safjps8"
LQ_STAKING_WALLET_2 = "addr1x8q76ctyve23u8h5sux3npxwwlnedpxlz3ft89vlshhs5val9ytme40nlqwch8gxnrsk3cvt69qn8xuqsd2fuv7fgghqjct4kw"
SUNDAE_LQ_REWARD_WALLET = "addr1q9clfpceddhyejpxkr0jllp04spldxpsucge5nwk6pjx4z7hy3954pmhklwxjz05vsx0qt4yw4a9275eldyrkp0c0hlqtpqx6e"

staking_wallets = [LQ_STAKING_WALLET_1, LQ_STAKING_WALLET_2]


def get_wallet_transactions(wallet_address, start_block):
    emissions_tx = kp_mainnet.get_address_txs(wallet_address, start_block)
    return emissions_tx


def get_transaction_details(tx_hash):
    tx_details = kp_mainnet.get_tx_info(tx_hash)
    return tx_details


def check_token_emissions(transactions, start_epoch, end_epoch):
    all_emissions = []
    tx_counter = 0

    # Filter transactions by epoch range
    filtered_transactions = [
        tx for tx in transactions if start_epoch <= tx["epoch_no"] <= end_epoch
    ]

    for tx in filtered_transactions:
        epoch_no = tx["epoch_no"]
        tx_details = get_transaction_details(tx["tx_hash"])
        tx_counter += 1
        if tx_counter % 100 == 0:
            print(f"{tx_counter} tx processed in Epoch {epoch_no}")

        for output in tx_details[0]["outputs"]:
            for asset in output["asset_list"]:
                if (
                    asset["policy_id"] == TOKEN_POLICY_ID
                    and asset["asset_name"] == TOKEN_ASSET_NAME
                ):
                    # Convert Unix timestamp to standard datetime format
                    datetime_format = datetime.fromtimestamp(
                        tx_details[0]["tx_timestamp"]
                    ).strftime("%Y-%m-%d %H:%M:%S")

                    all_emissions.append(
                        {
                            "epoch": epoch_no,
                            "timestamp": datetime_format,
                            "wallet": output["payment_addr"]["bech32"],
                            "tx_hash": tx["tx_hash"],
                            "amount": int(asset["quantity"]),
                            "utxo_index": output["tx_index"],
                        }
                    )

    return all_emissions


def get_current_epoch():
    tip_info = kp_mainnet.get_tip()
    return tip_info[0]["epoch_no"], tip_info[0]["abs_slot"]


def convert_to_csv(data, output_file):
    """
    Converts a JSON object or a pandas DataFrame to a CSV file.

    Parameters:
    data (dict or pandas.DataFrame): The JSON object (as a Python dict) or DataFrame to convert.
    output_file (str): The path to the output CSV file.
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
    df.to_csv(output_file, index=False)
    print(f"Data successfully written to {output_file}")


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Check Cardano native token emissions from a specific wallet."
    )
    parser.add_argument(
        "--start_epoch",
        type=int,
        required=True,
        help="The starting epoch to check from.",
    )

    parser.add_argument(
        "--make_csv",
        type=bool,
        required=False,
        help="Create a .csv output file",
    )

    parser.add_argument(
        "--csv_name",
        type=str,
        required=False,
        help="Name the .csv output file",
    )

    args = parser.parse_args()
    start_epoch = args.start_epoch

    current_epoch, current_block = get_current_epoch()

    # Determine start block for the given start epoch
    # For simplicity, let's assume 432000 slots per epoch (5 days epoch with 1 second per slot)
    # This assumption should be replaced with a precise calculation or API call to get accurate block height for the epoch.
    slots_per_epoch = 432000
    start_block = (start_epoch - 1) * slots_per_epoch

    # Get all transactions once
    transactions = get_wallet_transactions(SUNDAE_LQ_REWARD_WALLET, start_block)

    # Pre-fetch transaction details for all transactions
    tx_details_dict = {tx["tx_hash"]: get_transaction_details(tx["tx_hash"]) for tx in transactions}

    # Filter out transactions outputted to the same wallet address
    filtered_transactions = [
        tx for tx in transactions 
        if all(output["payment_addr"]["bech32"] != SUNDAE_LQ_REWARD_WALLET 
               for output in tx_details_dict[tx["tx_hash"]][0]["outputs"])
    ]

    # Check emissions within the epoch range
    all_emissions = check_token_emissions(transactions, start_epoch, current_epoch)

    # Convert to DataFrame
    df_emissions = pd.DataFrame(all_emissions)

    # Print the DataFrame
    print(df_emissions)

    make_csv = args.make_csv
    if make_csv == True:
        csv_name = args.csv_name
        convert_to_csv(df_emissions, "./output/" + csv_name + ".csv")
