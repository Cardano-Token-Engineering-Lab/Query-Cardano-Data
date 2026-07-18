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


def get_wallet_transactions(wallet_address, start_block, end_epoch):
    emissions_tx = kp_mainnet.get_address_txs(wallet_address, start_block)
    print(f"Retrieved {len(emissions_tx)} transactions.")
    filtered_emissions_tx = filter_data_by_end_epoch(emissions_tx, end_epoch)
    filtered_emissions_tx = filter_data_by_start_epoch(filtered_emissions_tx, start_epoch)
    print(f"Filtered list to {len(filtered_emissions_tx)} transactions.")

    return filtered_emissions_tx

def filter_data_by_end_epoch(data, end_epoch):
    return [item for item in data if item["epoch_no"] <= end_epoch]

def filter_data_by_start_epoch(data, start_epoch):
    return [item for item in data if item["epoch_no"] >= start_epoch]


def get_transaction_details(tx_hash):
    # Use get_tx_utxos instead of get_tx_info to get complete UTXO information
    tx_details = kp_mainnet.get_tx_utxos(tx_hash)
    return tx_details


def check_token_emissions(transactions, start_epoch, end_epoch):
    all_emissions = []
    tx_counter = 0

    for tx in transactions:
        tx_details = get_transaction_details(tx["tx_hash"])
        if not tx_details:  # Skip if no details returned
            continue
            
        tx_counter += 1
        
        # Debug first transaction
        if tx_counter == 1:
            print("\nFirst transaction details:")
            print(f"Transaction hash: {tx['tx_hash']}")
            print(json.dumps(tx_details[0], indent=2))

        if tx_counter % 100 == 0:
            print(f"{tx_counter} tx processed in Epoch {tx['epoch_no']}")

        try:
            # Process outputs (tokens being sent)
            for output in tx_details[0].get("outputs", []):
                if "assets" in output:  # Check if there are any assets in the output
                    for asset_id, quantity in output["assets"].items():
                        policy_id, asset_name = asset_id.split(".")
                        
                        if tx_counter == 1:
                            print(f"\nChecking asset: {policy_id} - {asset_name}")
                            
                        if (
                            policy_id == TOKEN_POLICY_ID
                            and asset_name == TOKEN_ASSET_NAME
                        ):
                            print(f"\nFound matching token in transaction {tx['tx_hash']}")
                            
                            datetime_format = datetime.fromtimestamp(
                                tx["block_time"]
                            ).strftime("%Y-%m-%d %H:%M:%S")

                            all_emissions.append({
                                "epoch": tx["epoch_no"],
                                "timestamp": datetime_format,
                                "wallet": output["address"],
                                "tx_hash": tx["tx_hash"],
                                "amount": int(quantity),
                                "utxo_index": output.get("output_index", 0)
                            })

        except Exception as e:
            print(f"Error processing transaction {tx['tx_hash']}: {str(e)}")
            if tx_counter == 1:
                print("Transaction structure:")
                print(json.dumps(tx_details, indent=2))

    print(f"\nTotal transactions processed: {tx_counter}")
    print(f"Total emissions found: {len(all_emissions)}")
    
    if len(all_emissions) > 0:
        print("\nFirst emission found:")
        print(json.dumps(all_emissions[0], indent=2))
    
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

    parser.add_argument(
        "--end_epoch",
        type=int,
        required=False,
        help="The starting epoch to check from",
    )

    args = parser.parse_args()
    start_epoch = args.start_epoch
    end_epoch = args.end_epoch

    current_epoch, current_block = get_current_epoch()

    # Determine start block for the given start epoch
    # For simplicity, let's assume 432000 slots per epoch (5 days epoch with 1 second per slot)
    # This assumption should be replaced with a precise calculation or API call to get accurate block height for the epoch.
    slots_per_epoch = 432000
    start_block = (start_epoch - 1) * slots_per_epoch
    print(start_block)

    print(f"\nChecking for token:")
    print(f"Policy ID: {TOKEN_POLICY_ID}")
    print(f"Asset Name: {TOKEN_ASSET_NAME}")
    
    transactions = get_wallet_transactions(SUNDAE_LQ_REWARD_WALLET, start_block, end_epoch)
    
    # Add debug info for a sample transaction
    if transactions:
        print("\nSample transaction before processing:")
        print(json.dumps(transactions[0], indent=2))

        # Print full details of first transaction
        first_tx_details = get_transaction_details(transactions[0]["tx_hash"])
        print("\nFull details of first transaction:")
        print(json.dumps(first_tx_details, indent=2))


    # Pre-fetch transaction details for all transactions
    # tx_details_dict = {tx["tx_hash"]: get_transaction_details(tx["tx_hash"]) for tx in transactions}

    # Filter out transactions outputted to the same wallet address
    # filtered_transactions = [
    #     tx for tx in transactions
    #     if all(output["payment_addr"]["bech32"] != SUNDAE_LQ_REWARD_WALLET
    #            for output in tx_details_dict[tx["tx_hash"]][0]["outputs"])
    # ]

    # Check emissions within the epoch range
    all_emissions = check_token_emissions(transactions, start_epoch, end_epoch)

    # Convert to DataFrame
    df_emissions = pd.DataFrame(all_emissions)

    # Print the DataFrame
    print(df_emissions)

    make_csv = args.make_csv
    if make_csv == True:
        csv_name = args.csv_name
        convert_to_csv(df_emissions, "./output/" + csv_name + ".csv")
