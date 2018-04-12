import pandas as pd
import numpy as np


def normalize(a):
    return a/max(a)


def price_distance(val):
    val = float(val)
    min_price = db['MinTotalPrice'].astype('float')
    max_price = db['MaxTotalPrice'].astype('float')
    abs_distance = np.minimum(abs(val - min_price), abs(max_price - val))
    return normalize(abs_distance)


def ppsm_distance(val):
    val = float(val)
    min_ppsm = db['MinPPSM'].astype('float')
    max_ppsm = db['MaxPPSM'].astype('float')
    abs_distance = np.minimum(abs(val - min_ppsm), abs(max_ppsm - val))
    return normalize(abs_distance)


def area_distance(val):
    val = float(val)
    min_area = db['MinTotalArea'].astype('float')
    max_area = db['MaxTotalArea'].astype('float')
    abs_distance = np.minimum(abs(val - min_area), abs(max_area - val))
    return normalize(abs_distance)


def rooms_distance(val):
    val = int(val)
    rooms = db['Rooms'].astype('int')
    abs_distance = abs(rooms - val)
    return normalize(abs_distance)


def loc_distance(val):
    locs = db['Location']
    locs_x = locs.apply(lambda x: float(x.split(',')[0]))
    locs_y = locs.apply(lambda x: float(x.split(',')[1]))
    val_x = float(val.split(',')[0])
    val_y = float(val.split(',')[1])
    abs_distance = (locs_x - val_x)**2 + (locs_y - val_y)**2
    return normalize(abs_distance)


def date_distance(val):
    dates = db['Date']
    val_year = int(val.split('.')[1])
    val_month = int(val.split('.')[0])
    dates_year = dates.apply(lambda x: int(x.split('.')[1]))
    dates_month = dates.apply(lambda x: int(x.split('.')[1]))
    abs_distance = np.maximum(np.zeros_like(dates_year), (dates_year - val_year) * 12 + dates_month - val_month)
    return normalize(abs_distance)


def type_distance(val):
    types = db['Type']
    abs_distance = np.where(types==val, 0, 1)
    return abs_distance


db = pd.read_csv('FullDB.csv')
func_dict = {'TotalPrice': price_distance, 'PPSM': ppsm_distance, 'TotalArea': area_distance,
             'Rooms': rooms_distance, 'Location': loc_distance, 'Date': date_distance, 'Type': type_distance}


def process(val, parameter):
    if parameter in func_dict:
        return func_dict[parameter](val)

