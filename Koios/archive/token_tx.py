import koios_api as kp
import pandas as pd
import json
import openpyxl

# qADA token for ADA supplied to Liqwid Protocol
policy_id = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
asset_name = "4c51"

# Limit tx search past the below block height
block_height = 9000000

# asset_txs = koios.get_asset_txs(policy_id, asset_name, block_height, False)

#print(asset_txs)

data = kp.get_asset_txs(policy_id, asset_name, block_height, False)
asset_txs = pd.json_normalize(data)

print(asset_txs)
