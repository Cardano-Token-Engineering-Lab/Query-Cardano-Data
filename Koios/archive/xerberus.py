import koios_python

kp_mainnet = koios_python.URLs(url="http://10.0.0.89:8053/api/v1/")

TOKEN_POLICY_ID = "6d06570ddd778ec7c0cca09d381eca194e90c8cffa7582879735dbde"  # Replace with actual policy ID
TOKEN_ASSET_NAME = "584552"  # Replace with actual asset name


def get_asset_info(policy_id=TOKEN_POLICY_ID, asset_name=TOKEN_ASSET_NAME):
    asset_info = kp_mainnet.get_asset_info(policy_id, asset_name)
    return asset_info


asset_info = get_asset_info()
print(asset_info)
