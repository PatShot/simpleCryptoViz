#!/usr/bin/env python3

import requests
import os
import pandas as pd
from datetime import datetime, timedelta

#Constants
API_BASE = 'https://api.coingecko.com/api/v3/'
ASSET_PLAT = '/asset_platforms'
COIN_LIST = '/coins/list'

def make_data_dir():
    new_dir = os.path.join(os.getcwd(), 'data')
    try:
        os.mkdir(new_dir)
        dir_flag = True
    except FileExistsError:
        dir_flag = False
    return dir_flag

def update_data_folder():
    try:
        res_coin = requests.get(API_BASE+COIN_LIST)
        res_plat = requests.get(API_BASE+ASSET_PLAT)
    except:
        raise NameError("Something Unexpected in connection")

    data_1 = res_coin.json()
    data_2 = res_plat.json()

    coin_df= pd.DataFrame(data_1)
    plat_df= pd.DataFrame(data_2)

    coin_df.to_csv(os.path.join('data', 'coin_list.csv'))
    plat_df.to_csv(os.path.join('data', 'asset_platforms.csv'))

    with open(os.path.join('data', 'metadata_f.txt'), 'a') as metafile:
        date = datetime.now().strftime("%Y_%m_%d, %H:%M:%S")
        metafile.write(date)

def check_metafile():
    """Returns the last date of updation of metafile"""
    try:
        with open(os.path.join('data', 'metadata_f.txt'), 'r') as file:
            data = file.readlines()
            print(data[-1])
            return data[-1]
    except FileNotFoundError:
        raise "metadata_f.txt is not present in the Data folder."

def auto_update_data(Interval=3):
    """
    Auto Updates Data at a Given Interval of Days.
    :param Interval: interval of updates in days.
    :return : Last line of the Metadata file.
    """
    latest_meta_line = check_metafile()
    if datetime.today() > latest_meta_line + timedelta(Interval):
        update_data_folder()
    else:
        return 0
    

if __name__ == "__main__":
    if make_data_dir():
        update_data_folder()
    else:
        auto_update_data(Interval=0)