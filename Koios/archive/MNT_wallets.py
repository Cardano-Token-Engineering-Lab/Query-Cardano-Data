import koios_python
import pandas as pd
import argparse
from collections import defaultdict
from datetime import datetime
import json

kp_mainnet = koios_python.URLs(url="http://10.0.0.89:8053/api/v1/")

# Information for MNT Mynth Token 
TOKEN_POLICY_ID = "43b07d4037f0d75ee10f9863097463fc02ff3c0b8b705ae61d9c75bf"
TOKEN_ASSET_NAME = "4d796e746820546f6b656e"

def get_asset_info(policy_id=TOKEN_POLICY_ID, asset_name=TOKEN_ASSET_NAME):
    asset_info = kp_mainnet.get_asset_info(policy_id, asset_name)
    return asset_info

def get_asset_summary(policy_id=TOKEN_POLICY_ID, asset_name=TOKEN_ASSET_NAME):
    asset_summary = kp_mainnet.get_asset_summary(policy_id, asset_name)
    return asset_summary

def get_asset_tx(policy_id=TOKEN_POLICY_ID, asset_name=TOKEN_ASSET_NAME, block_height=0, history=False):
    asset_tx = kp_mainnet.get_asset_txs(policy_id, asset_name)
    return asset_tx

asset_info = get_asset_info()
print(asset_info)

asset_summary = get_asset_summary()
print(asset_summary)

asset_txs = get_asset_tx()
print(asset_txs)