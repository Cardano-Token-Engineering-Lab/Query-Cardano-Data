import koios_python
import requests
import pandas as pd
from datetime import datetime
from collections import defaultdict

kp_mainnet = koios_python.URLs(url="http://10.0.0.89:8053/api/v1/")

TOKEN_POLICY_ID = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
TOKEN_ASSET_NAME = "4c51"
LQ_USER_DIST_WALLET = "addr1xxawr298yy36qrqw6yqc9v2qvgfddwjpqkgnfkt2rvq3u3f74zdzpgetwrygga9mlz44dc5tfrd82m0vxpfjmkpsf9ts06jfwd"
LQ_STAKING_WALLET_1 = "addr1xx0cj23c0mhfht6uj74x6ytr6c3jr3gnxd3tthdemcxdulrw7xjpplgp0lahw2u869nn77avyd3vw96p4jhtdrykyt4safjps8"
LQ_STAKING_WALLET_2 = "addr1x8q76ctyve23u8h5sux3npxwwlnedpxlz3ft89vlshhs5val9ytme40nlqwch8gxnrsk3cvt69qn8xuqsd2fuv7fgghqjct4kw"
SUNDAE_LQ_REWARD_WALLET = "addr1q9clfpceddhyejpxkr0jllp04spldxpsucge5nwk6pjx4z7hy3954pmhklwxjz05vsx0qt4yw4a9275eldyrkp0c0hlqtpqx6e"
LQ_STAKING_CONTRACT = "addr1w8arvq7j9qlrmt0wpdvpp7h4jr4fmfk8l653p9t907v2nsss7w7r4"

staking_wallets = [LQ_STAKING_WALLET_1, LQ_STAKING_WALLET_2]


def get_claimed_emissions(file_path, emissions_wallet):
    try:
        df = pd.read_csv(file_path)
        filtered_df = df[df["wallet"] != emissions_wallet]
        filtered_df['tx_hash_utxo'] = df.apply(lambda row: f"{row['tx_hash']}#{row['utxo_index']}", axis=1)
        return filtered_df
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return None
    except pd.errors.EmptyDataError:
        print("Error: The file is empty.")
        return None
    except pd.errors.ParserError:
        print("Error: There was a parsing error.")
        return None


df = get_claimed_emissions("./output/emissions_488-449.csv", SUNDAE_LQ_REWARD_WALLET)
print(df)

def get_utxos_by_tx_hash(utxo_hash):
    utxos = kp_mainnet.get_utxo_info(utxo_hash)
    return utxos


def get_transaction_details(tx_hash):
    tx_details = kp_mainnet.get_tx_info(tx_hash)
    return tx_details


def check_subsequent_transactions(token_emissions):
    print(token_emissions)
    results = []
    processed_txs = set()  # Cache to avoid redundant processing

    for index, row in token_emissions.iterrows():
        tx_hash = row['tx_hash']
        utxo_index = row['utxo_index']
        utxo_hash = f"{tx_hash}#{utxo_index}"
        print(f"Row {index}: tx_hash = {tx_hash}, utxo_index = {utxo_index}")

        # Check if the transaction has already been processed
        if utxo_hash in processed_txs:
            continue

        processed_txs.add(utxo_hash)

        # Get UTXO details for the transaction hash
        utxos = get_utxos_by_tx_hash(utxo_hash)
        print(utxos)

        for utxo in utxos:
            if utxo["tx_hash"] == tx_hash and utxo["tx_index"] == utxo_index:
                spent_in_tx = utxo["is_spent"]

                if spent_in_tx:
                    subsequent_tx_details = get_transaction_details(tx_hash)
                    # print(subsequent_tx_details)
                    interacted_with_smart_contract = False

                    for output in subsequent_tx_details[0]["outputs"]:
                        if output.get("inline_datum") or output.get("reference_script_hash"):
                            interacted_with_smart_contract = True
                            break
                else:
                    interacted_with_smart_contract = False

                results.append(
                    {
                        "epoch_no": utxo['epoch_no'],
                        "utxo": f"{tx_hash}#{utxo_index}",
                        "spent_in_tx": spent_in_tx,
                        "interacted_with_smart_contract": interacted_with_smart_contract,
                    }
                )
                print(results)
                break

    return results


if __name__ == "__main__":
    # Example token emissions data (from previous script output)
    token_emissions = get_claimed_emissions("./output/emissions_488-449.csv", SUNDAE_LQ_REWARD_WALLET)

    # Check subsequent transactions for the token emissions
    results = check_subsequent_transactions(token_emissions)
    print(results)

    # Create a DataFrame for the results
    df_results = pd.DataFrame(results)

    # Classify the results
    df_results["classification"] = df_results.apply(
        lambda row: (
            "c) tokens spent in a subsequent transaction and interacted with a smart contract"
            if row["interacted_with_smart_contract"]
            else (
                "b) tokens spent in a subsequent transaction but did not interact with a smart contract"
                if row["spent_in_tx"]
                else "a) tokens not spent in a subsequent transaction"
            )
        ),
        axis=1,
    )

    # Print the DataFrame
    print(df_results)
