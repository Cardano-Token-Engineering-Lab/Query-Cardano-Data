import koios_python
import pandas as pd
from collections import defaultdict
import argparse

kp_mainnet = koios_python.URLs(url="http://10.0.0.89:8053/api/v1/")

TOKEN_POLICY_ID = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
TOKEN_ASSET_NAME = "4c51"
LQ_USER_DIST_WALLET = "addr1xxawr298yy36qrqw6yqc9v2qvgfddwjpqkgnfkt2rvq3u3f74zdzpgetwrygga9mlz44dc5tfrd82m0vxpfjmkpsf9ts06jfwd"
LQ_STAKING_WALLET_1 = "addr1xx0cj23c0mhfht6uj74x6ytr6c3jr3gnxd3tthdemcxdulrw7xjpplgp0lahw2u869nn77avyd3vw96p4jhtdrykyt4safjps8"
LQ_STAKING_WALLET_2 = "addr1x8q76ctyve23u8h5sux3npxwwlnedpxlz3ft89vlshhs5val9ytme40nlqwch8gxnrsk3cvt69qn8xuqsd2fuv7fgghqjct4kw"
SUNDAE_LQ_REWARD_WALLET = "addr1q9clfpceddhyejpxkr0jllp04spldxpsucge5nwk6pjx4z7hy3954pmhklwxjz05vsx0qt4yw4a9275eldyrkp0c0hlqtpqx6e"

staking_wallets = [LQ_STAKING_WALLET_1, LQ_STAKING_WALLET_2]

# print(kp_mainnet.get_asset_addresses(policy_id, asset_name, content_range="0-1000"))

print(koios_python.__file__)

def get_emissions_transactions(wallet_address):
    emissions_tx = kp_mainnet.get_address_txs(wallet_address)
    # emissions_df = pd.DataFrame(emissions_tx)
    # print(emissions_df)
    # print(len(emissions_df))
    return emissions_tx


def get_transaction_details(tx_hash):
    tx_details = kp_mainnet.get_tx_info(tx_hash)
    # tx_details_df = pd.DataFrame(tx_details)
    # print(tx_details_df[0])
    return tx_details


def check_token_emissions(wallet_address, start_epoch, end_epoch):
    transactions = get_emissions_transactions(wallet_address)
    all_emissions = []

    for tx in transactions:
        epoch_no = tx["epoch_no"]
        if tx["epoch_no"] >= start_epoch and tx["epoch_no"] <= end_epoch:
            tx_details = get_transaction_details(tx["tx_hash"])
            for output in tx_details[0]["outputs"]:
                for asset in output["asset_list"]:
                    if (
                        asset["policy_id"] == TOKEN_POLICY_ID
                        and asset["asset_name"] == TOKEN_ASSET_NAME
                    ):
                        all_emissions.append(
                            {
                                "epoch": epoch_no,
                                "wallet": output["payment_addr"]["bech32"],
                                "tx_hash": tx["tx_hash"],
                                "amount": int(asset["quantity"])                                
                            }
                        )
    return all_emissions


def get_current_epoch():
    tip_info = kp_mainnet.get_tip()
    return tip_info[0]["epoch_no"]

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
        raise ValueError("Input data must be a dictionary (JSON object) or a pandas DataFrame.")
    
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

    args = parser.parse_args()
    start_epoch = args.start_epoch

    current_epoch = get_current_epoch()

    all_emissions = []

    for epoch in range(start_epoch, current_epoch + 1):
        emissions = check_token_emissions(SUNDAE_LQ_REWARD_WALLET, epoch, epoch)
        all_emissions.extend(emissions)

    # Convert to DataFrame
    df_emissions = pd.DataFrame(all_emissions)

    # Print the DataFrame
    print(df_emissions)

    # Create csv file of outputs
    convert_to_csv(df_emissions, "./output/emissions_sundae.csv")

# emission_tx = get_emissions_transactions(staking_wallets)
# print(emission_tx)
# print(get_transaction_details("6dcefc2ca4c946ccf41737f10ce2642e8e96ec419c01391b4dc83347b9848791"))
# print(check_token_emissions(SUNDAE_LQ_REWARD_WALLET, 420, 422))
