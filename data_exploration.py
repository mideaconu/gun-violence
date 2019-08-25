import pandas as pd
import numpy as np
import re
from functools import reduce

# Lookup dictionary of common address abbreviations found in the dataset
lookup_dict = {"Pkwy": "Parkway", "Blvd": " Boulevard", "Rd": "Road", "Dr ": "Drive ",
               "Dr$": "Drive", "Ave ": "Avenue ", "Ave$": "Avenue", "avenues": "Avenues",
               "Block": "block", "Expwy": "Expressway", "Pl ": "Place ", "Pl$": "Place", 
               "Ln": "Lane", "Northwest": "NW", "Southwest": "SW", "Northeast": "NE",
               "Southeast": "SE", "North-west": "NW", "South-west": "SW", "North-east": "NE",
               "South-east": "SE", "NorthWest": "NW", "SouthWest": "SW", "NorthEast": "NE",
               "SouthEast": "SE", "North-West": "NW", "South-West": "SW", "North-East": "NE",
               "South-East": "SE", "North ": "N ", "South ": "S ", "East ": "E ", "West ": "W ",
               "North$": "N", "South$": "S", "East$": "E", "West$": "W", "Av ": "Avenue ", 
               "Av$": "Avenue", "St$": "Street"}

def missing_values_table(df):
    total = df.isnull().sum().sort_values(ascending=False)
    percent = (round(df.isnull().sum() / df.isnull().count() * 100, 2)).sort_values(ascending=False)
    missing_data = pd.concat([total, percent], axis=1, keys=['Missing', 'Percentage'])
    missing_data['Missing'] = missing_data['Missing'].map('{:,.0f}'.format)
    return missing_data.T

def unique_values_table(df):
    total = df.nunique().sort_values(ascending=False)
    percent = (round(df.nunique() / df.count() * 100, 2)).sort_values(ascending=False)
    unique_data = pd.concat([total, percent], axis=1, keys=['Unique', 'Percentage'])
    unique_data['Unique'] = unique_data['Unique'].map('{:,.0f}'.format)
    return unique_data.T

def split_into_dict(string):
    if pd.isnull(string):
        return np.nan
    str_dict = dict()
    # The dataset contains instances deparated by | or ||, and : or :: respectively
    # Thus we have to consider both cases when working on those strings
    str_list = '#$%'.join('#$%'.join(string.split('||')).split('|')).split('#$%')
    for index in str_list:
        # If indices and values are split by '::'
        i, sep, v = index.partition('::')
        if sep and v:
            str_dict[int(i)] = v
        # If indices and values are split by ':'
        else:
            i, _, v = index.partition(':')
            str_dict[int(i)] = v
    return str_dict

def convert_vals_to_int(str_dict):
    if pd.isnull(str_dict):
        return np.nan
    for key in str_dict:
        str_dict[key] = int(str_dict[key])
    return str_dict

def split_into_list(string):
    if pd.isnull(string):
        return np.nan
    # Split the string by '|' or '||', depending on the format
    return '#$%'.join('#$%'.join(string.split('||')).split('|')).split('#$%')

def transfer_suspect(key, row, df):
    offset = df.columns.get_loc("suspect_name") - df.columns.get_loc("participant_name")
    for col in range(df.columns.get_loc("participant_name"), df.columns.get_loc("participant_status")+1):
        if pd.notnull(row[col]):
            if key in row[col].keys():
                if pd.isnull(row[col+offset]):
                    row[col+offset] = dict()
                row[col+offset][key] = row[col][key]
                del row[col][key]
            if len(row[col]) == 0:
                row[col] = np.nan

def find_suspect(row, df):
    nr_suspects = 0
    if pd.notnull(row[df.columns.get_loc("participant_type")]):
        for k, v in row[df.columns.get_loc("participant_type")].items():
            if v == "Subject-Suspect":
                nr_suspects += 1
                transfer_suspect(k, row, df)
    row[df.columns.get_loc("n_suspects")] = nr_suspects
    return row

def populate_suspect_columns(df):
    data = df.values
    return pd.DataFrame([find_suspect(data[i], df) for i in range(data.shape[0])], index=df.index, columns=df.columns)

def replace_dict(dictionary):
    if pd.notnull(dictionary):
        return len(dictionary)
    else:
        return np.nan

def clean_whitespaces(address):
    new_address = re.sub(' +', ' ', address)
    new_address = re.sub(' ,', ',', new_address)
    new_address = re.sub(r'^\s+', '', new_address, flags=re.UNICODE)
    new_address = re.sub(r"\s+$", "", new_address, flags=re.UNICODE)
    return new_address

def clean_special_characters(address):
    new_address = re.sub("\.", "", address)
    new_address = re.sub(",|\-|\/", " ", new_address)
    return new_address

def clean_address_string(address):
    if pd.isnull(address):
        return np.nan
    else:
        new_address = clean_special_characters(address)
        new_address = reduce(lambda x, y: re.sub(y, lookup_dict[y], x), lookup_dict, new_address)
        new_address = clean_whitespaces(new_address)
        return new_address

def get_victims_by_year(row, df):
    return max(row[df.columns.get_loc("n_killed")] + row[df.columns.get_loc("n_injured")] - row[df.columns.get_loc("n_suspects")], 0)

def victims_by_year(df, year):
    data = df.values
    return [get_victims_by_year(data[i], df) for i in range(data.shape[0]) if data[i][0].year == 2013]

    