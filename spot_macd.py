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
    df = pd.DataFrame(client.get_historical_klines(symbol,
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
    df['ema'] = ta.trend.ema_indicator(df.Close, window = 200)
    df['macd_line'] = ta.trend.macd(df.Close)
    df['macd_signal'] = ta.trend.macd_signal(df.Close)
    df['macd_diff'] = ta.trend.macd_diff(df.Close)
    df['prev_macd'] = df['macd_diff'].shift(1)
    return df

# Start trading (example)
count = 0
correct = 0
sale_cost = 0
total_profit = 0
balance = float(client.get_asset_balance(asset='BUSD')['free'])
bought = float(client.get_asset_balance(asset='BTC')['free'])
buy_money = round(balance / 5, 6)

while True:
    tracking_data = get_ta(get_data('BTCBUSD', Client.KLINE_INTERVAL_1MINUTE, '500'))
    print("Current price is {} and macd 1min is {}, prev macd 1min is {}".format(tracking_data.iloc[-1, 5], tracking_data.iloc[-2,10], tracking_data.iloc[-2,11]))

    buy_cond_1 = (tracking_data.iloc[-2,10] > 0) & (tracking_data.iloc[-2,11] < 0) 
    buy_cond_2 = (tracking_data.iloc[-2,8] < 0) & (tracking_data.iloc[-2,9] < 0)

    if buy_cond_1 & buy_cond_2:
        price = tracking_data.iloc[-1, 5]
        if balance >= buy_money:
            # quantity = round(buy_money/price, 5)
            order = client.create_order(symbol = "BTCBUSD",
                                        side = 'BUY',
                                        type = 'MARKET', 
                                        quoteOrderQty = buy_money)
            sale_cost += buy_money
            balance = float(client.get_asset_balance(asset='BUSD')['free'])
            bought = float(client.get_asset_balance(asset='BTC')['free'])
        elif (balance > 10) & (balance < buy_money):
            # quantity = round(balance/price,5)
            order = client.create_order(symbol = "BTCBUSD",
                                        side = 'BUY',
                                        type = 'MARKET', 
                                        quoteOrderQty = balance)
            sale_cost += balance
            balance = float(client.get_asset_balance(asset='BUSD')['free'])
            bought = float(client.get_asset_balance(asset='BTC')['free'])
        print("Bought {} at an average of {}".format(bought, sale_cost/bought))
        print("Remaining balance :{}".format(balance))
    
    sell_cond_1 = (tracking_data.iloc[-2,10] < 0) & (tracking_data.iloc[-2,11] > 0)
    sell_cond_2 = (tracking_data.iloc[-2,8] > 0) & (tracking_data.iloc[-2,9] > 0)

    if sell_cond_1 & sell_cond_2:
        if bought != 0:
            count += 1
            client.order_market_sell(symbol="BTCBUSD", quantity = bought)
            print("Sold {} for a total of {}".format(bought, bought*tracking_data.iloc[-1, 5]))
            balance = float(client.get_asset_balance(asset='BUSD')['free'])
            bought = float(client.get_asset_balance(asset='BTC')['free'])
            buy_money = round(balance / 5, 6)
            if tracking_data.iloc[-1, 5] * bought > sale_cost:
                correct += 1
                print("{}/{}".format(correct, count))
            print(balance)
    time.sleep(60)