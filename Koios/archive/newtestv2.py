import koios_python
import pandas as pd
from collections import defaultdict
import argparse

kp_mainnet = koios_python.URLs(url="http://10.0.0.89:8053/api/v1/")


def fetch_token_info(policy_id, asset_name):
    token_info = kp_mainnet.get_asset_info(policy_id, asset_name)
    return token_info


def fetch_block_info(block_no):
    block_info = kp_mainnet.get_block_info(block_no)
    return block_info


def fetch_block_transactions(block_hash):
    block_tx = kp_mainnet.get_block_txs(block_hash)
    return block_tx


def fetch_tx_info(tx_hash):
    tx_info = kp_mainnet.get_tx_info(tx_hash)
    return tx_info[
        0
    ]  # Assuming the API returns a list with a single transaction info object


def fetch_address_utxos(address):
    address_utxo = kp_mainnet.get_address_utxos(address)
    return address_utxo


def fetch_epoch_blocks():
    # Fetch all blocks to build epoch block dictionary
    blocks = []
    block_no = 1
    while True:
        block_info = fetch_block_info(block_no)
        if not block_info:
            break
        blocks.append(block_info)
        block_no += 1

    # Build epoch block dictionary
    epoch_blocks = {}
    current_epoch = blocks[0]["epoch_no"]
    first_block = blocks[0]["hash"]
    for block in blocks[1:]:
        if block["epoch_no"] != current_epoch:
            epoch_blocks[current_epoch] = {
                "first_block": first_block,
                "last_block": blocks[blocks.index(block) - 1]["hash"],
            }
            current_epoch = block["epoch_no"]
            first_block = block["hash"]
    epoch_blocks[current_epoch] = {
        "first_block": first_block,
        "last_block": blocks[-1]["hash"],
    }

    return epoch_blocks


def fetch_epoch_transactions(epoch_no, wallet_address, policy_id):
    epoch_blocks = fetch_epoch_blocks()
    if epoch_no not in epoch_blocks:
        return []

    transactions = []
    first_block = epoch_blocks[epoch_no]["first_block"]
    last_block = epoch_blocks[epoch_no]["last_block"]

    block_hash = first_block
    while block_hash != last_block:
        block_info = fetch_block_info(block_hash)
        if block_info["epoch_no"] != epoch_no:
            break

        tx_hashes = fetch_block_transactions(block_hash)

        for tx_hash in tx_hashes:
            tx_info = fetch_tx_info(tx_hash)
            sender_addresses = [
                input["payment_addr"]["bech32"] for input in tx_info["inputs"]
            ]

            if wallet_address in sender_addresses:
                if any(
                    output
                    for output in tx_info["outputs"]
                    if any(
                        asset["asset_policy"] == policy_id for asset in output["value"]
                    )
                ):
                    transactions.append(tx_info)

        block_hash = block_info["next_block_hash"]

    return transactions


def analyze_utxos(
    transactions, wallet_address, policy_id, specified_smart_contract_hash
):
    utxo_status = []

    processed_count = 0
    for tx in transactions:
        tx_hash = tx["tx_hash"]
        for output in tx["outputs"]:
            if any(asset["asset_policy"] == policy_id for asset in output["value"]):
                address = output["payment_addr"]["bech32"]
                addr_info = fetch_address_utxos(address)
                if any(utxo["tx_hash"] == tx_hash for utxo in addr_info["utxos"]):
                    status = "unspent"
                else:
                    status = "spent"
                    tx_utxos = fetch_block_transactions(
                        tx_hash
                    )  # Assuming this endpoint provides inputs info
                    for utxo in tx_utxos["inputs"]:
                        if "datum_hash" in utxo:
                            if utxo["datum_hash"] == specified_smart_contract_hash:
                                status = "spent in specified smart contract"
                            else:
                                status = "spent in other smart contract"
                        else:
                            status = "spent in simple transaction"
                utxo_status.append(
                    {"tx_hash": tx_hash, "address": address, "status": status}
                )

        # Print progress for every 100 transactions processed
        processed_count += 1
        if processed_count % 100 == 0:
            print(
                f"Processed {processed_count} transactions from wallet {wallet_address}"
            )

    return utxo_status


def main(
    policy_id,
    asset_name,
    wallet_address,
    start_epoch,
    end_epoch,
    specified_smart_contract_hash,
):
    token_info = fetch_token_info(policy_id, asset_name)
    print("Token Info:", token_info)

    for epoch in range(start_epoch, end_epoch + 1):
        transactions = fetch_epoch_transactions(epoch, wallet_address, policy_id)
        utxo_status = analyze_utxos(
            transactions, wallet_address, policy_id, specified_smart_contract_hash
        )

        total_emissions = sum(
            asset["quantity"]
            for tx in transactions
            for output in tx["outputs"]
            for asset in output["value"]
            if asset["asset_policy"] == policy_id
        )
        total_addresses = len(set(utxo["address"] for utxo in utxo_status))
        utxos_status_counts = {
            status: len([utxo for utxo in utxo_status if utxo["status"] == status])
            for status in set(utxo["status"] for utxo in utxo_status)
        }

        print(f"Epoch {epoch}:")
        print(f"Total Emissions: {total_emissions}")
        print(f"Total Addresses: {total_addresses}")
        print(f"UTXO Status Counts: {utxos_status_counts}")


if __name__ == "__main__":
    TOKEN_POLICY_ID = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
    TOKEN_ASSET_NAME = "4c51"
    WALLET_ADDRESS = "addr1q9clfpceddhyejpxkr0jllp04spldxpsucge5nwk6pjx4z7hy3954pmhklwxjz05vsx0qt4yw4a9275eldyrkp0c0hlqtpqx6e"
    START_EPOCH = 485
    END_EPOCH = 486
    SPECIFIED_SMART_CONTRACT_HASH = (
        "b2893731a362af8c58b15a5a3b4d115bdab65920b6c41aa22bd2a197423f60c6"
    )

    # LQ_USER_DIST_WALLET = "addr1xxawr298yy36qrqw6yqc9v2qvgfddwjpqkgnfkt2rvq3u3f74zdzpgetwrygga9mlz44dc5tfrd82m0vxpfjmkpsf9ts06jfwd"
    # LQ_STAKING_WALLET_1 = "addr1xx0cj23c0mhfht6uj74x6ytr6c3jr3gnxd3tthdemcxdulrw7xjpplgp0lahw2u869nn77avyd3vw96p4jhtdrykyt4safjps8"
    # LQ_STAKING_WALLET_2 = "addr1x8q76ctyve23u8h5sux3npxwwlnedpxlz3ft89vlshhs5val9ytme40nlqwch8gxnrsk3cvt69qn8xuqsd2fuv7fgghqjct4kw"
    # SUNDAE_LQ_REWARD_WALLET = "addr1q9clfpceddhyejpxkr0jllp04spldxpsucge5nwk6pjx4z7hy3954pmhklwxjz05vsx0qt4yw4a9275eldyrkp0c0hlqtpqx6e"
    # staking_wallets = [LQ_STAKING_WALLET_1, LQ_STAKING_WALLET_2]

    main(
        TOKEN_POLICY_ID,
        TOKEN_ASSET_NAME,
        WALLET_ADDRESS,
        START_EPOCH,
        END_EPOCH,
        SPECIFIED_SMART_CONTRACT_HASH,
    )
