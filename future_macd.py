from binance import Client

import numpy as np
import pandas as pd
import ta 
import time

api_key = 's20c6FhOSUORTSgkjROWRCekmWoyMtMnV3BEbistCKvX3OUckd4vkL1WCNF6iZ5x'
secret_key = 'vBmwXWkWTM5hfLbury8sMAfgI6Zfnw3ZLkq524Cve0KHwUpWNdeYcz21VdzTW69E'

# Create connection to Binance
client = Client(api_key, secret_key)

# Pull price data from Binance
def get_data(symbol, interval, lookback):
    df = pd.DataFrame(client.futures_historical_klines(symbol,
                                      interval,
                                      str(lookback) + ' minute ago UTC'))
    df = df.iloc[:,:6]
    df.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    df.insert(loc=0, column='Name', value=symbol)
    df.iloc[:,1:] = df.iloc[:,1:].astype(float)
    df.Time = pd.to_datetime(df.Time, unit = 'ms')
    # df.set_index('Time', inplace = True)
    
    return df

# Calculate indicators
def get_ta(df):
    df['ema'] = ta.trend.ema_indicator(df.Close, window=200)
    df['macd_line'] = ta.trend.macd(df.Close)
    df['macd_signal'] = ta.trend.macd_signal(df.Close)
    df['macd_diff'] = ta.trend.macd_diff(df.Close)
    df['prev_macd'] = df['macd_diff'].shift(1)
    df['+di'] = ta.trend.adx_pos(df.High, df.Low, df.Close)
    df['-di'] = ta.trend.adx_neg(df.High, df.Low, df.Close)
    return df

# Start trading (example)
# count = 0
# correct = 0
# sale_cost = 0
# total_profit = 0
def trade_future(leverage = 5):
    long_pos = False
    short_pos = False
    btc_amount = float(client.futures_account_balance()[1]['balance'])
    usdt_balance = float(client.futures_account_balance()[6]['balance'])
    buy_money = round(usdt_balance / 5, 6)
    client.futures_change_leverage(symbol='BTCUSDT', leverage=leverage)

    while True:
        data = get_ta(get_data('BTCUSDT', Client.KLINE_INTERVAL_5MINUTE, '2500'))
        print("Current price is {} and macd 1min is {}, prev macd 1min is {}".format(data.iloc[-1, 5], data.iloc[-2,10], data.iloc[-2,11]))
        long_cond_1 = (data.iloc[-2,10] > 0) & (data.iloc[-2,11] < 0) 
        long_cond_2 = (data.iloc[-2,8] < 0) & (data.iloc[-2,9] < 0)
        long_cond_3 = (data.iloc[-2,12] > data.iloc[-2,13])

        if long_cond_1 & long_cond_2 & long_cond_3:
            if short_pos == True:
                print(client.futures_position_information(symbol=("BTCUSDT"))[0])
                quant = abs(float(client.futures_position_information(symbol=("BTCUSDT"))[0]['positionAmt']))
                close_short = client.futures_create_order(symbol = "BTCUSDT",
                                                        side = 'BUY',
                                                        type = 'LIMIT',
                                                        timeInForce = 'GTX',
                                                        price = float(client.futures_ticker(symbol = "BTCUSDT")['lastPrice']), 
                                                        quantity = quant)
                short_pos = False
                usdt_balance = float(client.futures_account_balance()[6]['balance'])
                print(usdt_balance)

            if usdt_balance >= buy_money:
                order = client.futures_create_order(symbol = "BTCUSDT",
                                                    side = 'BUY',
                                                    type = 'LIMIT',
                                                    timeInForce = 'GTX',
                                                    price = float(client.futures_ticker(symbol = "BTCUSDT")['lastPrice']),
                                                    quantity = round(buy_money*leverage/data.iloc[-1,5],3))
                usdt_balance = float(client.futures_account_balance()[6]['balance'])
                btc_amount = float(client.futures_account_balance()[1]['balance'])

            elif (usdt_balance > 10) & (usdt_balance < buy_money):
                order = client.futures_create_order(symbol = "BTCUSDT", 
                                                    side = 'BUY',
                                                    type = 'LIMIT',
                                                    timeInForce = 'GTX',
                                                    price = float(client.futures_ticker(symbol = "BTCUSDT")['lastPrice']), 
                                                    quantity = round(buy_money*leverage/data.iloc[-1,5],3))
                usdt_balance = float(client.get_asset_balance(asset='USDT')['free'])
                bought = float(client.get_asset_balance(asset='BTC')['free'])
            long_pos = True
            print("Opened a long position")
            print("Remaining balance :{}".format(usdt_balance))

        short_cond_1 = (data.iloc[-2,10] < 0) & (data.iloc[-2,11] > 0)
        short_cond_2 = (data.iloc[-2,8] > 0) & (data.iloc[-2,9] > 0)
        short_cond_3 = (data.iloc[-2,12] < data.iloc[-2,13])

        if short_cond_1 & short_cond_2 & short_cond_3:
            if long_pos == True:
                print(client.futures_position_information(symbol=("BTCUSDT"))[0])
                quant = abs(float(client.futures_position_information(symbol=("BTCUSDT"))[0]['positionAmt']))
                close_long = client.futures_create_order(symbol = "BTCUSDT",
                                                        side = 'SELL',
                                                        type = 'LIMIT',
                                                        timeInForce = 'GTX',
                                                        price = float(client.futures_ticker(symbol = "BTCUSDT")['lastPrice']), 
                                                        quantity = quant)
                long_pos = False
                usdt_balance = float(client.futures_account_balance()[6]['balance'])
                print(usdt_balance)

            if usdt_balance >= buy_money:
                order = client.futures_create_order(symbol = "BTCUSDT",
                                                    side = 'SELL',
                                                    type = 'LIMIT',
                                                    price = float(client.futures_ticker(symbol = "BTCUSDT")['lastPrice']), 
                                                    timeInForce = 'GTX',
                                                    quantity = round(buy_money*leverage/data.iloc[-1,5],3))
                usdt_balance = float(client.futures_account_balance()[6]['balance'])
                btc_amount = float(client.futures_account_balance()[1]['balance'])

            elif (usdt_balance > 10) & (usdt_balance < buy_money):
                # quantity = round(balance/price,5)
                order = client.futures_create_order(symbol = "BTCUSDT",
                                                    side = 'SELL',
                                                    type = 'LIMIT',
                                                    price = float(client.futures_ticker(symbol = "BTCUSDT")['lastPrice']),
                                                    timeInForce = 'GTX',
                                                    quantity = round(buy_money*leverage/data.iloc[-1,5],3))
                usdt_balance = float(client.get_asset_balance(asset='USDT')['free'])
                btc_amount = float(client.get_asset_balance(asset='BTC')['free'])
            short_pos = True
            print("Opened a short position")
            print("Remaining balance :{}".format(usdt_balance))
            
        time.sleep(300)

trade_future()
# tickers = float(client.futures_ticker(symbol = "BTCUSDT")['lastPrice'])
# print(tickers, type(tickers))
# print(client.futures_get_all_orders(symbol='BTCUSDT')[-1])
