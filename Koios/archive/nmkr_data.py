import koios_python
import pandas as pd
import argparse
from collections import defaultdict
from datetime import datetime
import json

kp_mainnet = koios_python.URLs(url="http://10.0.0.89:8053/api/v1/")

# Information for NMKR Token 
TOKEN_POLICY_ID = "5dac8536653edc12f6f5e1045d8164b9f59998d3bdc300fc92843489"
TOKEN_ASSET_NAME = "4e4d4b52"

def get_asset_info(policy_id=TOKEN_POLICY_ID, asset_name=TOKEN_ASSET_NAME):
    asset_info = kp_mainnet.get_asset_info(policy_id, asset_name)
    return asset_info

asset_info = get_asset_info()

def fetch_token_holders(policy_id):
    """
    Fetch all token holders for a given policy ID.
    :param policy_id: The policy ID of the token.
    :return: A dictionary of addresses and quantities.
    """
    try:
        # Retrieve asset list under the policy
        assets = kp_mainnet.get_policy_asset_info(TOKEN_POLICY_ID)

        if not assets:
            print("No assets found for the given policy ID.")
            return
        
        # For each asset under the policy, get the holders
        for asset in assets:
            asset_name = asset['asset_name']
            print(f"Fetching holders for Asset: {asset_name}")
            
            # Get asset info to find holders
            asset_holders = kp_mainnet.get_asset_addresses(TOKEN_POLICY_ID, TOKEN_ASSET_NAME)
            print(asset_holders)
            
            # Display the results
            for holder in asset_holders:
                # Updated to use 'payment_address' and 'quantity'
                payment_address = holder.get('payment_address', 'Unknown Payment Address')
                stake_address = holder.get('stake_address', 'Unknown Stake Address')
                quantity = holder.get('quantity', '0')
                print(f"Payment Address: {payment_address}, Stake Address: {stake_address}, Quantity: {quantity}")
    
    except Exception as e:
        print(f"An error occurred: {e}")

# Fetch and display token holders
fetch_token_holders(TOKEN_POLICY_ID)