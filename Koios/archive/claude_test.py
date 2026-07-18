import argparse
from datetime import datetime

# kp_mainnet = koios_python.URLs(url="http://10.0.0.89:8053/api/v1/")

# TOKEN_POLICY_ID = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
# TOKEN_ASSET_NAME = "4c51"
# LQ_USER_DIST_WALLET = "addr1xxawr298yy36qrqw6yqc9v2qvgfddwjpqkgnfkt2rvq3u3f74zdzpgetwrygga9mlz44dc5tfrd82m0vxpfjmkpsf9ts06jfwd"
# LQ_STAKING_WALLET_1 = "addr1xx0cj23c0mhfht6uj74x6ytr6c3jr3gnxd3tthdemcxdulrw7xjpplgp0lahw2u869nn77avyd3vw96p4jhtdrykyt4safjps8"
# LQ_STAKING_WALLET_2 = "addr1x8q76ctyve23u8h5sux3npxwwlnedpxlz3ft89vlshhs5val9ytme40nlqwch8gxnrsk3cvt69qn8xuqsd2fuv7fgghqjct4kw"
# SUNDAE_LQ_REWARD_WALLET = "addr1q9clfpceddhyejpxkr0jllp04spldxpsucge5nwk6pjx4z7hy3954pmhklwxjz05vsx0qt4yw4a9275eldyrkp0c0hlqtpqx6e"

import requests
import json
from collections import defaultdict
from typing import List, Dict, Any

# Constants
API_BASE_URL = "http://10.0.0.89:8053/api/v1"

def get_api_data(endpoint: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    response = requests.get(f"{API_BASE_URL}/{endpoint}", params=params)
    response.raise_for_status()
    return response.json()

def get_asset_utxos(policy_id: str, asset_name: str, address: str) -> List[Dict[str, Any]]:
    params = {
        "asset": f"{policy_id}.{asset_name}",
        "_address": address
    }
    return get_api_data("asset_utxos", params)

def get_tx_info(tx_hash: str) -> Dict[str, Any]:
    return get_api_data(f"tx_info/{tx_hash}")[0]

def categorize_utxo(tx_info: Dict[str, Any], staking_contract: str) -> str:
    if not tx_info["output_amount"]:
        return "Unspent"
    
    for output in tx_info["outputs"]:
        if output["payment_addr"]["script_hash"]:
            if output["payment_addr"]["script_hash"] == staking_contract:
                return "Staked Rewards"
            return "Swapped Rewards"
    
    return "Basic Transaction"

def analyze_token_emissions(
    token_policy_id: str,
    token_asset_name: str,
    rewards_wallet_address: str,
    staking_contract_address: str,
    starting_epoch: int,
    ending_epoch: int
) -> Dict[str, int]:
    
    utxos = get_asset_utxos(token_policy_id, token_asset_name, rewards_wallet_address)
    
    results = defaultdict(int)
    
    for utxo in utxos:
        tx_hash = utxo["tx_hash"]
        tx_info = get_tx_info(tx_hash)
        
        if starting_epoch <= tx_info["block"]["epoch"] <= ending_epoch:
            category = categorize_utxo(tx_info, staking_contract_address)
            results[category] += 1
    
    return dict(results)

def main():
    # User inputs
    token_policy_id = input("Enter token policy ID: ")
    token_asset_name = input("Enter token asset name: ")
    rewards_wallet_address = input("Enter rewards wallet address: ")
    staking_contract_address = input("Enter staking contract address: ")
    starting_epoch = int(input("Enter starting epoch: "))
    ending_epoch = int(input("Enter ending epoch: "))
    
    results = analyze_token_emissions(
        token_policy_id,
        token_asset_name,
        rewards_wallet_address,
        staking_contract_address,
        starting_epoch,
        ending_epoch
    )
    
    print("\nResults:")
    for category, count in results.items():
        print(f"{category}: {count}")

if __name__ == "__main__":
    main()