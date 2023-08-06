import pandas as pd
import matplotlib.pyplot as plt
from helper_functions import read_csv, write_csv, get_api_token

# Load Blockfrost API key
api = get_api_token()

# Token information to be queried analyzed
policy_id = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d24"
asset_name = "4c51"
token_name = bytearray.fromhex(asset_name).decode()

def unix_to_time(df):
    df['time'] = pd.to_datetime(df['block_time'], unit='s')
    return df

def get_asset_tx(policy_id, asset_name, page):
    df = pd.DataFrame()
    while True:
        data = api.asset_transactions(asset=policy_id + asset_name, page=page, return_type="pandas")
        df = pd.concat([data,df])
        if len(data) < 100:
            break
        page += 1
    
    df = unix_to_time(df)
    write_csv(df_tx_data, token_name+"_tx_data.csv")
    return df

# Use one of the following lines to get data
df_tx_data = get_asset_tx(policy_id, asset_name, 1)
# df_tx_data = read_csv(token_name+"_tx_data.csv")

def histogram(df, token_name):
    df['year_month'] = df['time'].dt.to_period('M')
    monthly_events = df.groupby('year_month').size()
    plt.figure(figsize=(10, 6))
    monthly_events.plot(kind='bar', color='skyblue')
    plt.xlabel('Time')
    plt.ylabel('Token Tx per month')
    plt.title(token_name+' Monthly Tx counts since launch')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def process_tx_data(data, token_name):
    if type(data) == str:
        df = read_csv(data)
    else:
        df = data
    df = unix_to_time(df)
    df.sort_values(by=['time'])
    histogram(df, token_name)

process_tx_data(token_name+"_tx_data.csv", token_name)





