import pandas as pd
import numpy as np
import copy


def normalize(a):
    m = (a/max(a)).reset_index(drop=True)
    return m


def min_max_distance(val, min_column_name, max_column_name):
    val = float(val)
    min_max_db = db.filter(items=[min_column_name, max_column_name])
    min_max_db = min_max_db.dropna(axis=0, how='any')
    min_column = min_max_db[min_column_name].astype('float')
    max_column = min_max_db[max_column_name].astype('float')
    abs_distance = (abs(val - min_column) + abs(max_column - val) - abs(max_column - min_column)) / 2.0
    min_max_db['Distance'] = normalize(abs_distance)
    temp = pd.merge(db, min_max_db, how='left', left_index=True, right_index=True)
    temp['Distance'] = temp['Distance'].fillna(1)
    return temp['Distance']


def exact_distance(val, column_name):
    distance = np.where(db[column_name] == val, 0, 1)
    return distance


def price_distance(val):
    return min_max_distance(val, 'MinTotalPrice', 'MaxTotalPrice')


def ppsm_distance(val):
    return min_max_distance(val, 'MinPPSM', 'MaxPPSM')


def area_distance(val):
    return min_max_distance(val, 'MinTotalArea', 'MaxTotalArea')


def rooms_distance(val):
    rooms_col = copy.copy(db['Rooms'])
    rooms_col[rooms_col == '-1'] = '10'
    rooms_col = rooms_col.apply(lambda x: x.split()[0])
    rooms_col[(rooms_col < '0') | (rooms_col > '9')] = '10'
    rooms_col = rooms_col.astype('int')
    abs_distance = abs(rooms_col - int(val.split()[0]))
    return normalize(abs_distance)


def name_distance(val):
    return exact_distance(val, 'Name')


def loc_distance(val):
    locs = db['Location']
    locs_x = locs.apply(lambda x: float(x.split(', ')[0])) * 0.6
    locs_y = locs.apply(lambda x: float(x.split(', ')[1]))
    val_x = float(val.split(',')[0]) * 0.6
    val_y = float(val.split(',')[1])
    abs_distance = ((locs_x - val_x)**2 + (locs_y - val_y)**2)**0.5
    return normalize(abs_distance)


def date_distance(val):
    dates = db['Date'][:]
    dates[dates == '-1'] = '10000.10000'
    dates[dates == 'введений'] = '0.0'
    val_year = int(val.split('.')[1])
    val_month = int(val.split('.')[0])
    dates_year = dates.apply(lambda x: int(x.split('.')[1]))
    dates_month = dates.apply(lambda x: int(x.split('.')[0]))
    abs_distance = np.maximum(np.zeros_like(dates_year), (dates_year - val_year) * 12 + dates_month - val_month)
    return normalize(abs_distance)


def type_distance(val):
    return exact_distance(val, 'Type')


db = pd.DataFrame()
func_dict = {'TotalPrice': price_distance, 'PPSM': ppsm_distance, 'TotalArea': area_distance, 'Name': name_distance,
             'Rooms': rooms_distance, 'Location': loc_distance, 'Date': date_distance, 'Type': type_distance}


def process(val, parameter, d):
    global db
    db = copy.copy(d)
    if parameter in func_dict:
        return func_dict[parameter](val)

