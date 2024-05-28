import pandas as pd
import numpy as np
import math
import itertools
import timeit

# Helper functions
def truncate(number, digits):
    stepper = 10.0 ** digits
    return int(number * stepper) / stepper

def get_diff_count_units(diff):
    _count_1 = _count_0 = _units_traded_1 = _units_traded_0 = 0
    _price_1 = _price_0 = 0

    if len(diff) == 1:
        row = diff.iloc[0]
        if row['type'] == 1:
            _count_1 = row['count']
            _units_traded_1 = row['units_traded']
            _price_1 = row['price']
        else:
            _count_0 = row['count']
            _units_traded_0 = row['units_traded']
            _price_0 = row['price']
    elif len(diff) == 2:
        row_1 = diff.iloc[1]
        row_0 = diff.iloc[0]
        _count_1 = row_1['count']
        _count_0 = row_0['count']
        _units_traded_1 = row_1['units_traded']
        _units_traded_0 = row_0['units_traded']
        _price_1 = row_1['price']
        _price_0 = row_0['price']

    return (_count_1, _count_0, _units_traded_1, _units_traded_0, _price_1, _price_0)

def cal_mid_price(gr_bid_level, gr_ask_level, group_t, mid_type='simple', level=5):
    if len(gr_bid_level) > 0 and len(gr_ask_level) > 0:
        bid_top_price = gr_bid_level.iloc[0].price
        bid_top_level_qty = gr_bid_level.iloc[0].quantity
        ask_top_price = gr_ask_level.iloc[0].price
        ask_top_level_qty = gr_ask_level.iloc[0].quantity
        
        if mid_type == 'wt':
            mid_price = ((gr_bid_level.head(level)['price'].mean() + gr_ask_level.head(level)['price'].mean()) * 0.5)
        elif mid_type == 'mkt':
            mid_price = ((bid_top_price * ask_top_level_qty) + (ask_top_price * bid_top_level_qty)) / (bid_top_level_qty + ask_top_level_qty)
            mid_price = truncate(mid_price, 1)
        elif mid_type == 'vwap':
            mid_price = (group_t['total'].sum()) / (group_t['units_traded'].sum())
            mid_price = truncate(mid_price, 1)
        else:
            mid_price = (bid_top_price + ask_top_price) * 0.5

        return (mid_price, bid_top_price, ask_top_price, bid_top_level_qty, ask_top_level_qty)
    else:
        print('Error: serious cal_mid_price')
        return (-1, -1, -2, -1, -1)

def live_cal_trade_indicator(param, gr_bid_level, gr_ask_level, diff, var, mid):
    ratio, level, interval, normal_fn = param
    normal_fn_dict = {'power': power_fn, 'log': log_fn, 'sqrt': sqrt_fn, 'raw': raw_fn}
    
    if normal_fn not in normal_fn_dict:
        raise ValueError(f"Error: normal_fn '{normal_fn}' does not exist")
    
    decay = np.exp(-1.0 / interval)
    
    if var.get('_flag', True):
        var['_flag'] = False
        var['tradeIndicator'] = 0.0
        return 0.0

    _count_1, _count_0, _units_traded_1, _units_traded_0, _price_1, _price_0 = diff
    
    BSideTrade = normal_fn_dict[normal_fn](ratio, _units_traded_1) * _price_1
    ASideTrade = normal_fn_dict[normal_fn](ratio, _units_traded_0) * _price_0

    tradeIndicator = var.get('tradeIndicator', 0.0)
    tradeIndicator += (-1 * BSideTrade + ASideTrade)
    
    var['tradeIndicator'] = tradeIndicator * decay

    return var['tradeIndicator']

def live_cal_book_d_v1(param, gr_bid_level, gr_ask_level, diff, var, mid):
    ratio, level, interval = param
    decay = math.exp(-1.0 / interval)
    
    if var.get('_flag', True):
        var.update({
            '_flag': False,
            'prevBidQty': gr_bid_level['quantity'].sum(),
            'prevAskQty': gr_ask_level['quantity'].sum(),
            'prevBidTop': gr_bid_level.iloc[0].price,
            'prevAskTop': gr_ask_level.iloc[0].price,
            'bidSideAdd': 0,
            'bidSideDelete': 0,
            'askSideAdd': 0,
            'askSideDelete': 0,
            'bidSideTrade': 0,
            'askSideTrade': 0,
            'bidSideFlip': 0,
            'askSideFlip': 0,
            'bidSideCount': 0,
            'askSideCount': 0,
        })
        return 0.0

    curBidQty = gr_bid_level['quantity'].sum()
    curAskQty = gr_ask_level['quantity'].sum()
    curBidTop = gr_bid_level.iloc[0].price
    curAskTop = gr_ask_level.iloc[0].price

    if curBidQty > var['prevBidQty']:
        var['bidSideAdd'] += 1
        var['bidSideCount'] += 1
    elif curBidQty < var['prevBidQty']:
        var['bidSideDelete'] += 1
        var['bidSideCount'] += 1

    if curAskQty > var['prevAskQty']:
        var['askSideAdd'] += 1
        var['askSideCount'] += 1
    elif curAskQty < var['prevAskQty']:
        var['askSideDelete'] += 1
        var['askSideCount'] += 1
        
    if curBidTop < var['prevBidTop']:
        var['bidSideFlip'] += 1
        var['bidSideCount'] += 1
    if curAskTop > var['prevAskTop']:
        var['askSideFlip'] += 1
        var['askSideCount'] += 1

    _count_1, _count_0, _units_traded_1, _units_traded_0, _price_1, _price_0 = get_diff_count_units(diff)

    var['bidSideTrade'] += _count_1
    var['bidSideCount'] += _count_1
    
    var['askSideTrade'] += _count_0
    var['askSideCount'] += _count_0

    bidSideCount = var['bidSideCount'] if var['bidSideCount'] != 0 else 1
    askSideCount = var['askSideCount'] if var['askSideCount'] != 0 else 1

    bidBookV = (-var['bidSideDelete'] + var['bidSideAdd'] - var['bidSideFlip']) / (bidSideCount ** ratio)
    askBookV = (var['askSideDelete'] - var['askSideAdd'] + var['askSideFlip']) / (askSideCount ** ratio)
    tradeV = (var['askSideTrade'] / (askSideCount ** ratio)) - (var['bidSideTrade'] / (bidSideCount ** ratio))
    bookDIndicator = askBookV + bidBookV + tradeV
        
    for key in ['bidSideCount', 'askSideCount', 'bidSideAdd', 'bidSideDelete', 'askSideAdd', 'askSideDelete', 'bidSideTrade', 'askSideTrade', 'bidSideFlip', 'askSideFlip']:
        var[key] *= decay

    var['prevBidQty'] = curBidQty
    var['prevAskQty'] = curAskQty
    var['prevBidTop'] = curBidTop
    var['prevAskTop'] = curAskTop

    return bookDIndicator

def live_cal_book_i_v1(param, gr_bid_level, gr_ask_level, diff, var, mid):
    mid_price = mid
    ratio, level, interval = param
    
    if var.get('_flag', True):
        var['_flag'] = False
        return 0.0

    quant_v_bid = gr_bid_level['quantity'] ** ratio
    price_v_bid = gr_bid_level['price'] * quant_v_bid

    quant_v_ask = gr_ask_level['quantity'] ** ratio
    price_v_ask = gr_ask_level['price'] * quant_v_ask

    askQty = quant_v_ask.sum()
    bidPx = price_v_bid.sum()
    bidQty = quant_v_bid.sum()
    askPx = price_v_ask.sum()
    bid_ask_spread = interval
        
    book_price = 0
    if bidQty > 0 and askQty > 0:
        book_price = (((askQty * bidPx) / bidQty) + ((bidQty * askPx) / askQty)) / (bidQty + askQty)

    indicator_value = (book_price - mid_price) / bid_ask_spread
    
    return indicator_value

# Indicator calculation functions
def power_fn(ratio, units):
    return ratio * units ** 2

def log_fn(ratio, units):
    return ratio * np.log1p(units)

def sqrt_fn(ratio, units):
    return ratio * np.sqrt(units)

def raw_fn(ratio, units):
    return ratio * units

def init_indicator_var(indicator, p):
    return {'_flag': True, 'tradeIndicator': 0.0}  # 예시로 단순화된 초기화 함수

def add_norm_fn(params):
    norm_fns = ['power', 'log', 'sqrt', 'raw']
    return [(p[0], p[1], p[2], fn) for p in params for fn in norm_fns]

# Main function to calculate indicators and save to CSV
def faster_calc_indicators(order_book_fn, trade_fn, output_fn):
    start_time = timeit.default_timer()

    group_o = get_sim_df(order_book_fn)
    group_t = get_sim_df_trade(trade_fn)

    delay = timeit.default_timer() - start_time
    print(f'df loading delay: {delay:.2f}s')

    level_1, level_2 = 2, 5
    print('param levels', level_1, level_2)

    book_imbalance_params = [(0.2, level_1, 1), (0.2, level_2, 1)]
    book_delta_params = [(0.2, level_1, 1), (0.2, level_1, 5), (0.2, level_1, 15), (0.2, level_2, 1), (0.2, level_2, 5), (0.2, level_2, 15)]
    trade_indicator_params = [(0.2, level_1, 1), (0.2, level_1, 5), (0.2, level_1, 15)]

    variables = {}
    _dict = {}
    _dict_indicators = {}

    for p in book_imbalance_params:
        indicator = 'BI'
        _dict[(indicator, p)] = []
        variables[(indicator, p)] = init_indicator_var(indicator, p)

    for p in book_delta_params:
        for indicator in ['BDv1', 'BDv2', 'BDv3']:
            _dict[(indicator, p)] = []
            variables[(indicator, p)] = init_indicator_var(indicator, p)

    for p in add_norm_fn(trade_indicator_params):
        for indicator in ['TIv1', 'TIv2']:
            _dict[(indicator, p)] = []
            variables[(indicator, p)] = init_indicator_var(indicator, p)

    _timestamp, _mid_price = [], []

    seq = 0
    print('total groups:', len(group_o), len(group_t))

    for (timestamp_o, data_o), (timestamp_t, data_t) in zip(group_o, group_t):

        if data_o is None or data_t is None:
            print('Warning: group is empty')
            continue

        timestamp = data_o.iloc[0]['timestamp']
        
        gr_bid_level = data_o[data_o.type == 0]
        gr_ask_level = data_o[data_o.type == 1]
        diff = get_diff_count_units(data_t)

        mid_price, bid, ask, bid_qty, ask_qty = cal_mid_price(gr_bid_level, gr_ask_level, data_t)

        if bid >= ask:
            seq += 1
            continue

        _timestamp.append(timestamp)
        _mid_price.append(mid_price)
        
        _dict_group = {}
        for (indicator, p) in _dict.keys():
            level = p[1]
            if level not in _dict_group:
                level = min(level, len(gr_bid_level), len(gr_ask_level))
                _dict_group[level] = (gr_bid_level.head(level), gr_ask_level.head(level))
            
            p1 = (p[0], level, p[2]) if len(p) == 3 else (p[0], level, p[2], p[3])
            _i = _l_indicator_fn[indicator](p1, _dict_group[level][0], _dict_group[level][1], diff, variables[(indicator, p)], mid_price)
            _dict[(indicator, p)].append(_i)
        
        for (indicator, p) in _dict.keys():
            col_name = f'{_l_indicator_name[indicator].replace("_", "-")}-{p[0]}-{p[1]}-{p[2]}'
            if indicator in ['TIv1', 'TIv2']:
                col_name = f'{_l_indicator_name[indicator].replace("_", "-")}-{p[0]}-{p[1]}-{p[2]}-{p[3]}'
            
            _dict_indicators[col_name] = _dict[(indicator, p)]

        _dict_indicators['timestamp'] = _timestamp
        _dict_indicators['mid_price'] = _mid_price

        seq += 1

    df_dict_to_csv(_dict_indicators, output_fn)

# Functions for loading data
def get_sim_df(fn):
    print(f'loading... {fn}')
    df = pd.read_csv(fn).apply(pd.to_numeric, errors='ignore')
    return df.groupby('timestamp')

def get_sim_df_trade(fn):
    print(f'loading... {fn}')
    df = pd.read_csv(fn).apply(pd.to_numeric, errors='ignore')
    return df.groupby('timestamp')

def df_dict_to_csv(dict_data, fn):
    df = pd.DataFrame(dict_data)
    df.to_csv(fn, index=False)

# Indicator function mappings
_l_indicator_fn = {
    'TIv1': live_cal_trade_indicator,
    'TIv2': live_cal_trade_indicator,
    'BDv1': live_cal_book_d_v1,
    'BDv2': live_cal_book_d_v1,
    'BDv3': live_cal_book_d_v1,
    'BI': live_cal_book_i_v1
}

_l_indicator_name = {
    'TIv1': 'trade_indicator_v1',
    'TIv2': 'trade_indicator_v2',
    'BDv1': 'book_delta_v1',
    'BDv2': 'book_delta_v2',
    'BDv3': 'book_delta_v3',
    'BI': 'book_imbalance'
}

# Usage
order_book_fn = '2024-05-01-upbit-BTC-book.csv'  # Replace with your order book CSV filename
trade_fn = '2024-05-01-upbit-BTC-trade.csv'  # Replace with your trade CSV filename
output_fn = '2024-05-01-upbit-btc-feature.csv'  # Replace with your desired output CSV filename

faster_calc_indicators(order_book_fn, trade_fn, output_fn)
