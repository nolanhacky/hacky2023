from binance import Client

import numpy as np
import pandas as pd
import ta 
import time

api_key = 's20c6FhOSUORTSgkjROWRCekmWoyMtMnV3BEbistCKvX3OUckd4vkL1WCNF6iZ5x'
secret_key = 'vBmwXWkWTM5hfLbury8sMAfgI6Zfnw3ZLkq524Cve0KHwUpWNdeYcz21VdzTW69E'

client = Client(api_key, secret_key, {"timeout": 20})

class Signals:
    def __init__(self, df, lags):
        self.df = df
        self.lags = lags
    
    def get_trigger(self):
        dfx = pd.DataFrame()
        for i in range(self.lags + 1):
            mask = (self.df['%K'].shift(i) < 20) & (self.df['%D'].shift(i) < 20)
            dfx = pd.concat([dfx,mask.to_frame().T], axis = 0, ignore_index = True)
        return dfx.sum(axis=0)
    
    def decide(self):
        self.df['triggered'] = np.where(self.get_trigger(), 1, 0)
        self.df['buy'] = np.where((self.df.triggered) &
                                   (self.df['%K'].between(20,80)) &
                                   (self.df['%D'].between(20,80)) &
                                   (self.df['rsi'] > 50) &
                                   (self.df['macd']> 0), 1, 0)
#(self.df['macd'].iloc[-2] > 0) &

def get_data(symbol, interval, lookback):
    df = pd.DataFrame(client.get_historical_klines(symbol,
                                      interval,
                                      str(lookback) + ' hour ago UTC'))
    df = df.iloc[:,:6]
    df.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    df.insert(loc=0, column='Name', value=symbol)
    df.iloc[:,1:] = df.iloc[:,1:].astype(float)
    df.Time = pd.to_datetime(df.Time, unit = 'ms')
    # df.set_index('Time', inplace = True)
    
    return df

def get_ta(df):
    df['rsi'] = ta.momentum.rsi(df.Close, window = 14)
    df['%K'] = ta.momentum.stoch(df.High, df.Low, df.Close, window = 14, smooth_window = 3)
    df['%D'] = df['%K'].rolling(3).mean()
    df['macd'] = ta.trend.macd_diff(df.Close)
    df.dropna(inplace = True)
    return df


pairs = []
exchange_info = client.get_exchange_info()
for s in exchange_info['symbols']:
     if (s['symbol'][-4:] == 'USDT') & (s['status'] == 'TRADING') & ((s['symbol'][-6:-4] != 'UP') & (s['symbol'][-8:-4] != 'DOWN')):
        pairs.append(s['symbol'])

stream = pd.DataFrame(columns=['Name', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
# stream.set_index('Time', inplace = True)

for pair in pairs:
    pair_data = get_ta(get_data(pair, Client.KLINE_INTERVAL_1HOUR, '300'))
    Signals(pair_data, 5).decide()
    if pair_data['buy'].iloc[-1]:
        print('Target: {}'.format(pair_data['Name'].to_string().split()[1]))

    

# print(stream)
# chess = get_ta(get_data('CHESSUSDT', Client.KLINE_INTERVAL_1HOUR, '300'))
# instance = Signals(chess,10)
# instance.decide()
# print(chess.iloc[-10::])  