from blockfrost import BlockFrostApi
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import os
from dotenv import load_dotenv


def read_csv(filepath):
    df = pd.read_csv(filepath)
    return df

def write_csv(df, file_path):
    df.to_csv(file_path, index=False)

def create_info_xlsx(dataframes_dict, output_filename):
    workbook = Workbook()
    for sheet_name, df in dataframes_dict.items():
        sheet = workbook.create_sheet(title=sheet_name)
        for row in dataframe_to_rows(df, index=False, header=True):
            sheet.append(row)
    workbook.remove(workbook['Sheet'])
    workbook.save(output_filename)

def get_api_token():
    load_dotenv()
    api_key = os.getenv("BLOCKFROST_API_TOKEN")
    api = BlockFrostApi(project_id=api_key)
    return api

def unix_to_time(df):
    df['time'] = df['time'].astype(int)
    df['time'] = pd.to_datetime(df['block_time'], unit='s')
    return df