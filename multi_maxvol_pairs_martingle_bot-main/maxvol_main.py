import os
# os.environ["http_proxy"] = "http://127.0.0.1:7890"
# os.environ["https_proxy"] = "http://127.0.0.1:7890"
import time
import talib
import logging
from trader.binance_future_trader_ema import BinanceFutureTrader_ema
from utils import config
from utils.utility import *
from utils.dingmessage import DingTalk_Disaster
from apscheduler.schedulers.background import BackgroundScheduler

format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=format, filename='log.txt')
logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)
logger = logging.getLogger('binance')
from typing import Union
from gateway.binance_future import Interval
import numpy as np
import pandas as pd
from datetime import datetime

pd.set_option('expand_frame_repr', False)
ding = DingTalk_Disaster()
from utils.config import signal_data



def get_data(trader: BinanceFutureTrader_ema):
    # traders.symbols is a dict data structure.
    symbols = trader.symbols_dict.keys()

    signals = []

    # we calculate the signal here.
    dingding_tixing_list ={}
    for symbol in symbols:
        # klines = trader.get_klines(symbol=symbol, interval=Interval.MINUTE_5, limit=100)
        klines = trader.get_klines(symbol=symbol, interval=Interval.HOUR_1, limit=100)
        if len(klines) > 0:
            df = pd.DataFrame(klines, dtype=np.float64,
                              columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'turnover', 'a2',
                                       'a3', 'a4', 'a5'])
            df = df[['open_time', 'open', 'high', 'low', 'close', 'volume', 'turnover','close_time']]
            # df['open_time'] = pd.to_datetime(df['open_time'], unit='ms') + pd.Timedelta(hours=8)
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms') + pd.Timedelta(hours=8)

            df.set_index('open_time', inplace=True)
            df.index = pd.to_datetime(df.index, unit='ms') + pd.Timedelta(hours=8)


            # current_bar = df.iloc[-1]  # 最后一行.
            now = datetime.now()
            # if current_bar['close_time'] > now:  # 防止时间提前了, 收盘价的时候还没有到整点.
            #     # df.drop(len(df) - 1, inplace=True)  # 删除最后一行.
            #     df = df[:-1]
                # print(df)
            # df['fast_ema'] = talib.EMA(df['close'], timeperiod=fast_ema_window)
            # df['slow_ema'] = talib.EMA(df['close'], timeperiod=slow_ema_window)
            #
            # df['boll_up'], df['boll_mid'], df['boll_dn'] = talib.BBANDS(df['close'],
            #                                                             timeperiod=58,
            #                                                             nbdevup=2.4,
            #                                                             nbdevdn=2.4
            #                                                             )
            # 获得最后两个Bar, 看看他们的数据, 比较金叉和死叉.
            current_bar = df.iloc[-1]
            last_bar = df.iloc[-2]

            # # 计算开仓的数量
            # self.trade_size = round_to(trade_money / float(current_bar['close']), min_volume)
            # if self.trade_size < self.min_volume:
            #     self.trade_size = self.min_volume

            # k = current_bar['fast_ema']
            # s = current_bar['slow_ema']
            # lk = last_bar['fast_ema']
            # ls = last_bar['slow_ema']
            #print(df.shape[0])  # 有多少列
            # print(df)
            # ss=df.sort_values(by="turnover", axis=1, ascending=True, inplace=True)
            # print(ss)
            dingding_tixing_list[symbol] = df[df['turnover'] > current_bar['turnover'] ].shape[0]
            # calculate your signal here.
            value = {'symbol': symbol,'hour_turnover': df['turnover'][-1],'max_hour_turnover': df['turnover'].max(), 'mean_turnover':df['turnover'].mean(), 'bili':float(df['turnover'][-1]/df['turnover'].mean())}
            # print(df['turnover'].max())   # 求前100列的最大值
            # print(current_bar)
            # 金叉的时候.  慢线价格大于0.2刀防止布林计算错误并且防止垃圾币， 当前价格要小于布林上轨避免接盘
            if current_bar['turnover'] >= df['turnover'].max() and current_bar['close'] >= df['high'].max():
                value['signal'] = 1
                # print(f"{symbol}趋势做多，4小时快线，慢线：{k}.{s}")

                # logging.log(msg = f"{symbol}趋势做多，1小时快线，慢线：{k}.{s}" ,level = "info")
                # ding.send_msg(f'趋势做多，1小时快线，慢线：{k}.{s}')
            # 死叉的时候.
            elif  current_bar['close'] <= df['low'].min():
                value['signal'] = -1
                # logging.log(msg = f"{symbol}趋势做空，1小时快线，慢线：{k}.{s}")
                # print(f"{symbol}趋势做空，4小时快线，慢线：{k}.{s}")

                # ding.send_msg(f'趋势做空，1小时快线，慢线：{k}.{s}')
            else:
                value['signal'] = 0
                # logging.log(msg = f"{symbol}无趋势，1小时快线，慢线：{k}.{s}")
                # print(f"{symbol}无趋势，4快线，慢线：{k}.{s}")
                # ding.send_msg(f'无趋势，1小时快线，慢线：{k}.{s}')

            # print(f'当前4时差值，{k - s},上一个4小时差值，{lk - ls}')
            # print(f'4小时变动，{k - s - lk + ls}')
            # value['hour_diff'] = k-s
            # value['hour_change'] = k - s - lk + ls
            # value['zhiying_price'] = current_bar['boll_up']
            # calculate the pair's price change is one hour. you can modify the code below. 等会儿在说
            # pct = df['close'] / df['open'] - 1
            # pct_4h = df_4hour['close']/df_4hour['open'] - 1
            #
            # value = {'pct': pct[-1], 'pct_4h':pct_4h[-1] , 'symbol': symbol, 'hour_turnover': df['turnover'][-1]}


            # calculate your signal here.
            # if value['pct'] >= config.pump_pct or value['pct_4h'] >= config.pump_pct_4h:
            #     # the signal 1 mean buy signal.
            #     value['signal'] = 1
            # elif value['pct'] <= -config.pump_pct or value['pct_4h'] <= -config.pump_pct_4h:
            #     value['signal'] = -1
            # else:
            #     value['signal'] = 0

            signals.append(value)
    # print(dingding_tixing_list)
    a = sorted(dingding_tixing_list.items(), key=lambda x: x[1], reverse=False)
    print(a)

    signals.sort(key=lambda x: x['bili'], reverse=True)
    signal_data['id'] = signal_data['id'] + 1
    signal_data['time'] = datetime.now()
    signal_data['signals'] = signals
    print(signal_data)
    ding.send_msg(f'vol still alive, 交易量变动前三名是:{a[0:3]}')

if __name__ == '__main__':

    config.loads('./config.json')
    # print(config.blocked_lists)


    trader = BinanceFutureTrader_ema()


    trader.get_exchange_info()
    get_data(trader)  # for testing

    scheduler = BackgroundScheduler()
    scheduler.add_job(get_data, trigger='cron', minute='*/13', args=(trader,))

    # scheduler.add_job(get_data, trigger='cron', hour='*/1', args=(trader,))
    scheduler.start()

    while True:
        time.sleep(30)
        trader.start()

