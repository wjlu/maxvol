import os,re
from gateway import BinanceFutureHttp, OrderStatus, OrderType, OrderSide
from utils import config
from utils import round_to
import logging
from datetime import datetime
from utils.config import signal_data
from utils.positions import Positions
from utils.dingmessage import DingTalk_Disaster

class BinanceFutureTrader_ema(object):
# from utils.dingmessage import DingTalk_Disaster
    def __init__(self):
        """
        免责声明:
        the binance future trader, 币安合约马丁格尔策略.
        the Martingle strategy in Future will endure a lot of risk， use it before you understand the risk and martingle strategy, and the code may have bugs,
        Use it at your own risk. We won't ensure you will earn money from this code.
        马丁策略在合约上会有很大的风险，请注意风险, 使用前请熟知该代码，可能会有bugs或者其他未知的风险。
        """

        self.http_client = BinanceFutureHttp(api_key=config.api_key, secret=config.api_secret,
                                             proxy_host=config.proxy_host, proxy_port=config.proxy_port)

        self.symbols_dict = {}  # 全市场的交易对. all symbols dicts {'BTCUSDT': value}
        self.tickers_dict = {}  # 全市场的tickers数据.

        self.buy_orders_dict = {}  # 买单字典 buy orders {'symbol': [], 'symbol1': []}
        self.sell_orders_dict = {}  # 卖单字典. sell orders  {'symbol': [], 'symbol1': []}
        self.positions = Positions('future_positions.json')
        self.initial_id = 0
        self.ding = DingTalk_Disaster()

    def get_exchange_info(self):
        data = self.http_client.exchangeInfo()

        if isinstance(data, dict):
            items = data.get('symbols', [])
            for item in items:
                if item.get('quoteAsset') == 'USDT' and item.get('status') == "TRADING":

                    symbol = item['symbol']
                    symbol_data = {"symbol": symbol}

                    for filters in item['filters']:
                        if filters['filterType'] == 'PRICE_FILTER':
                            symbol_data['min_price'] = float(filters['tickSize'])
                        elif filters['filterType'] == 'LOT_SIZE':
                            symbol_data['min_qty'] = float(filters['stepSize'])
                        elif filters['filterType'] == 'MIN_NOTIONAL':
                            symbol_data['min_notional'] = float(filters['notional'])

                    self.symbols_dict[symbol] = symbol_data

        # print(len(self.symbols),self.symbols)  # 129 个交易对.

    def get_klines(self, symbol: str, interval, limit):
        return self.http_client.get_kline(symbol=symbol, interval=interval, limit=limit)

    def get_all_tickers(self):

        tickers = self.http_client.get_all_tickers()
        if isinstance(tickers, list):
            for tick in tickers:
                symbol = tick['symbol']
                ticker = {"bid_price": float(tick['bidPrice']), "ask_price": float(tick["askPrice"])}
                self.tickers_dict[symbol] = ticker
        else:
            self.tickers_dict = {}

    def start(self):
        """
        执行核心逻辑，网格交易的逻辑.

        the grid trading logic
        :return:
        """

        delete_buy_orders = []  # the buy orders need to remove from buy_orders[] list
        delete_sell_orders = []  # the sell orders need to remove from sell_orders[] list

        # 买单逻辑,检查成交的情况.

        for key in self.buy_orders_dict.keys():
            for buy_order in self.buy_orders_dict.get(key, []):
                check_order = self.http_client.get_order(buy_order.get('symbol'),
                                                         client_order_id=buy_order.get('clientOrderId'))

                if check_order:
                    if check_order.get('status') == OrderStatus.CANCELED.value:
                        delete_buy_orders.append(buy_order)

                        symbol = buy_order.get('symbol')
                        print(f"{symbol}: buy order was canceled, time: {datetime.now()}")

                        price = float(check_order.get('price'))
                        qty = float(check_order.get('executedQty', 0))
                        min_qty = self.symbols_dict.get(symbol).get('min_qty', 0)

                        if qty > 0:
                            self.positions.update(symbol=symbol, trade_price=price, trade_amount=qty, min_qty=min_qty,
                                                  is_buy=True)

                            logging.info(
                                f"{symbol}: buy order was partially filled, price: {price}, qty: {qty}, time: {datetime.now()}")

                    elif check_order.get('status') == OrderStatus.FILLED.value:
                        delete_buy_orders.append(buy_order)
                        # 买单成交.
                        symbol = buy_order.get('symbol')
                        price = float(check_order.get('price'))
                        qty = float(check_order.get('origQty'))
                        min_qty = self.symbols_dict.get(symbol).get('min_qty', 0)

                        self.positions.update(symbol=symbol, trade_price=price, trade_amount=qty, min_qty=min_qty,
                                              is_buy=True)

                        logging.info(
                            f"{symbol}: buy order was filled, price: {price}, qty: {qty}, time: {datetime.now()}")


                    elif check_order.get('status') == OrderStatus.NEW.value:
                        print(f"{buy_order.get('symbol')}: buy order is new, time: {datetime.now()}")

                    else:
                        print(
                            f"{buy_order.get('symbol')} buy order's status is not in above options, status: {check_order.get('status')}, time: {datetime.now()}")

        # the expired\canceled\delete orders
        for delete_order in delete_buy_orders:
            for key in self.buy_orders_dict.keys():
                orders = self.buy_orders_dict.get(key, [])
                if delete_order in orders:
                    orders.remove(delete_order)

        # 卖单逻辑, 检查卖单成交情况.
        for key in self.sell_orders_dict.keys():
            for sell_order in self.sell_orders_dict.get(key, []):
                check_order = self.http_client.get_order(sell_order.get('symbol'),
                                                         client_order_id=sell_order.get('clientOrderId'))
                if check_order:
                    if check_order.get('status') == OrderStatus.CANCELED.value:
                        delete_sell_orders.append(sell_order)

                        symbol = sell_order.get('symbol')
                        print(f"{symbol}: sell order was canceled, time: {datetime.now()}")

                        price = float(check_order.get('price'))
                        qty = float(check_order.get('executedQty', 0))
                        min_qty = self.symbols_dict.get(symbol).get('min_qty', 0)

                        if qty > 0:
                            self.positions.update(symbol=symbol, trade_price=price, trade_amount=qty, min_qty=min_qty,
                                                  is_buy=False)

                            logging.info(
                                f"{symbol}: sell order was partially filled, price: {price}, qty: {qty}, total_profit: {self.positions.total_profit}, time: {datetime.now()}")

                    elif check_order.get('status') == OrderStatus.FILLED.value:
                        delete_sell_orders.append(sell_order)

                        symbol = check_order.get('symbol')
                        price = float(check_order.get('price'))
                        qty = float(check_order.get('origQty'))

                        min_qty = self.symbols_dict.get(symbol).get('min_qty', 0)
                        self.positions.update(symbol=symbol, trade_price=price, trade_amount=qty, min_qty=min_qty,
                                              is_buy=False)

                        logging.info(
                            f"{symbol}: sell order was filled, price: {price}, qty: {qty}, total_profit: {self.positions.total_profit}, time: {datetime.now()}")


                    elif check_order.get('status') == OrderStatus.NEW.value:
                        print(f"sell order status is: New, time: {datetime.now()}")
                    else:
                        print(
                            f"sell order status is not in above options: {check_order.get('status')}, time: {datetime.now()}")
        self.positions.save_data()

        # the expired\canceled\delete orders
        for delete_order in delete_sell_orders:
            for key in self.sell_orders_dict.keys():
                orders = self.sell_orders_dict.get(key, [])
                if delete_order in orders:
                    orders.remove(delete_order)

        ####################################
        """
        check about the current position and order status.
        """

        self.get_all_tickers()
        if len(self.tickers_dict.keys()) == 0:
            return

        symbols = self.positions.positions.keys()
        # symbols = [s for s in symbols if '_' not in s]
        # print(symbols)
        for s in symbols:
            pos_data = self.positions.positions.get(s)  # 拿到json中所有仓位信息 以及加仓逻辑在这里
            pos = pos_data.get('pos')  # 张数
            bid_price = self.tickers_dict.get(s, {}).get('bid_price', 0)  # bid price
            ask_price = self.tickers_dict.get(s, {}).get('ask_price', 0)  # ask price

            min_qty = self.symbols_dict.get(s, {}).get('min_qty')

            if bid_price > 0 and ask_price > 0:
                value = pos * bid_price
                if value < self.symbols_dict.get(s, {}).get('min_notional', 0):
                    print(f"{s} notional value is small, delete the position data.")
                    del self.positions.positions[s]  # delete the position data if the position notional is very small.
                else:
                    avg_price = pos_data.get('avg_price')
                    self.positions.update_profit_max_price(s, bid_price)
                    # calculate the profit here.
                    profit_pct = bid_price / avg_price - 1
                    pull_back_pct = self.positions.positions.get(s, {}).get('profit_max_price', 0) / bid_price - 1

                    dump_pct = self.positions.positions.get(s, {}).get('last_entry_price', 0) / bid_price - 1
                    current_increase_pos_count = self.positions.positions.get(s, {}).get('current_increase_pos_count',
                                                                                         1)


                    if dump_pct >= config.increase_pos_when_drop_down and len(self.buy_orders_dict.get(s,
                                                                                                         [])) <= 0 and current_increase_pos_count <= config.max_increase_pos_count:

                        # cancel the sell orders, when we want to place buy orders, we need to cancel the sell orders.
                        sell_orders = self.sell_orders_dict.get(s, [])
                        for sell_order in sell_orders:
                            print(
                                "cancel the sell orders, when we want to place buy orders, we need to cancel the sell orders")
                            self.http_client.cancel_order(s, sell_order.get('clientOrderId'))

                        buy_value = config.initial_trade_value * config.trade_value_multiplier ** current_increase_pos_count

                        qty = round_to(buy_value / bid_price, min_qty)

                        buy_order = self.http_client.place_order(symbol=s, order_side=OrderSide.BUY,
                                                                 order_type=OrderType.LIMIT, quantity=qty,
                                                                 price=bid_price)

                        if buy_order:
                            # resolve buy orders
                            orders = self.buy_orders_dict.get(s, [])
                            orders.append(buy_order)

                            self.buy_orders_dict[s] = orders

            else:
                print(f"{s}: bid_price: {bid_price}, ask_price: {bid_price}")

        pos_symbols = self.positions.positions.keys()  # the position's symbols, if there is {"symbol": postiondata}, you get the symbols here.
        pos_count = len(pos_symbols)  # position count

        left_times = config.max_pairs - pos_count

        # for signal in signal_data.get('signals', []):
        #     s = signal['symbol']
        #     if s in pos_symbols:
        #         bid_price = self.tickers_dict.get(s, {}).get('bid_price', 0)  # bid price
        #         if self.positions.positions.get(s)['minus_count'] == 0:
        #             pos_data = self.positions.positions.get(s)  # 拿到json所所有仓位信息
        #
        #             if bid_price >= signal['zhiying_price']:
        #                 # 第一次止盈是 只能拿到实时布林，此时仓位止盈是none 下单以后仓位会更新止盈信息，所以后面是下一个判断
        #                 self.ding.send_msg('进入止盈 准备检查')
        #                 pos = pos_data.get('pos')  # 张数
        #                 # min_qty = self.symbols_dict.get(s).get('min_qty', 0)
        #                 pos_puls =(pos / 5) if (pos / 5) >= min_qty else min_qty
        #                 if float(str(min_qty).split(".")[0]) >= 0.99:
        #                     pos_puls = int(pos_puls)
        #                 else:
        #                     print(len(str(min_qty).split(".")[1]))
        #                     print(round(pos_puls, len(str(min_qty).split(".")[1])))
        #                     pos_puls = (round(pos_puls, len(str(min_qty).split(".")[1])))
        #                 self.place_sell_order(s, pos_puls, order_type=OrderType.MARKET, message="boll止盈20%，第一次止盈，注意检查")
        #
        #         elif config.max_minus_count > self.positions.positions.get(s)['minus_count'] > 0 :
        #             pos_data = self.positions.positions.get(s)  # 拿到json所所有仓位信息
        #             if bid_price >= pos_data['zhiying_price']:
        #                 self.ding.send_msg('进入止盈 准备检查')
        #                 pos = pos_data.get('pos')  # 张数
        #                 pos_puls =(pos / 5) if (pos / 5) >= min_qty else min_qty
        #                 if float(str(min_qty).split(".")[0]) >= 0.99:
        #                     pos_puls = int(pos_puls)
        #                 else:
        #                     print(len(str(min_qty).split(".")[1]))
        #                     print(round(pos_puls, len(str(min_qty).split(".")[1])))
        #                     pos_puls = (round(pos_puls, len(str(min_qty).split(".")[1])))
        #                 self.place_sell_order(s, pos_puls, order_type=OrderType.MARKET, message="boll止盈20%，第一次止盈，注意检查")
        #
        #
        #     # 更新仓位信息,毕竟少了5分之一的仓位
        # self.positions.save_data()


        # if self.initial_id == signal_data.get('id', self.initial_id):
        #     # the id is not updated, indicates that the data is not updated.
        #     # print("the current initial_id is the same, we do nothing.")
        #     return
        #
        # self.initial_id = signal_data.get('id', self.initial_id)

        index = 0
        for signal in signal_data.get('signals', []):
            s = signal['symbol']
            bid_price = self.tickers_dict.get(s, {}).get('bid_price', 0)  # bid price


            # 趋势做多，并且 index < left_times（设置的最大仓位还能买 ）  并且 没有买过 并且 交易量判断通过
            if signal['signal'] == 1 and index < left_times and signal['symbol'] not in pos_symbols  and '_' not in s:

                # the last one hour's the symbol jump over some percent.
                if len(config.allowed_lists) > 0 and s in config.allowed_lists and index < left_times:

                    index += 1
                    # the last one hour's the symbol jump over some percent.
                    self.place_order(s, order_type=OrderType.MARKET)
                    signal['minus_count'] = 0

                if s not in config.blocked_lists and len(config.allowed_lists) == 0 and index < left_times:
                    index += 1
                    self.place_order(s, order_type=OrderType.MARKET)
                    signal['minus_count'] = 0

                if len(config.allowed_lists) == 0 and config.blocked_lists == 0 and index < left_times:
                    index += 1
                    self.place_order(s, order_type=OrderType.MARKET)
                    signal['minus_count'] = 0

            # if signal['signal'] == -1 and signal['symbol'] in pos_symbols:
            #     # 死叉 市场价强制出场
            #
            #     pos_data = self.positions.positions.get(s)  # 拿到json所所有仓位信息
            #     pos = pos_data.get('pos')  # 张数
            #     self.place_sell_order(s,pos, order_type=OrderType.MARKET)

            # # 其他情况的强制出场 ,要么想办法提前止损出场，要么止损位置不变，拿一半仓位boll止盈出场。这里选择第二种  并且要判断过之前没有减过仓位
            # if signal.get('minus_count',0) == 0 and signal['symbol'] in pos_symbols:
            #     if bid_price >= signal['zhiying_price']:
            #         # 第一次止盈是 只能拿到实时布林，此时仓位止盈是none 下单以后仓位会更新止盈信息，所以后面是下一个判断
            #         pos_data = self.positions.positions.get(s)  # 拿到json所所有仓位信息
            #         pos = pos_data.get('pos')  # 张数
            #         self.place_sell_order(s,int(pos/5), order_type=OrderType.MARKET,message="boll止盈20%，第一次止盈，注意检查")
            #         signal['minus_count'] = 1
            # elif config.max_minus_count > signal.get('minus_count',0) > 0 and signal['symbol'] in pos_symbols:
            #     if  bid_price >= pos_data['zhiying_price']:
            #         pos_data = self.positions.positions.get(s)  # 拿到json所所有仓位信息
            #         pos = pos_data.get('pos')  # 张数
            #         self.place_sell_order(s,int(pos/5), order_type=OrderType.MARKET,message=f"boll止盈20%，第{signal.get('minus_count')}次止盈,注意检查")
            #         signal['minus_count'] += 1
        # print(self.positions.positions)
        # logging.info(self.positions.positions)
        self.positions.save_data()

    def place_order(self, symbol: str ,order_type=OrderType.LIMIT):

        buy_value = config.initial_trade_value
        min_qty = self.symbols_dict.get(symbol, {}).get('min_qty')
        bid_price = self.tickers_dict.get(symbol, {}).get('bid_price', 0)  # bid price
        if bid_price <= 0:
            print(f"error -> future {symbol} bid_price is :{bid_price}")
            return

        qty = round_to(buy_value / bid_price, min_qty)

        # buy_order = self.http_client.place_order(symbol=symbol, order_side=OrderSide.BUY,
        #                                          order_type=OrderType.LIMIT, quantity=qty,
        #                                          price=bid_price)
        # print(
        #     f"{symbol}  place buy order: {buy_order}")
        # if buy_order:
        #     # resolve buy orders
        #     orders = self.buy_orders_dict.get(symbol, [])
        #     orders.append(buy_order)
        #     self.buy_orders_dict[symbol] = orders
        #     self.ding.send_msg(f'{symbol} 买入:{qty} ，价格:{bid_price}')
        self.ding.send_msg(f'{symbol} 买入:{qty} ，价格:{bid_price}')

    def place_sell_order(self, symbol: str,pos, order_type=OrderType.LIMIT,message="死叉出场"):

        pass
        # bid_price = self.tickers_dict.get(symbol, {}).get('bid_price', 0)  # bid price
        # if bid_price <= 0:
        #     print(f"error -> future {symbol} bid_price is :{bid_price}")
        #     return
        #
        #
        # sell_order = self.http_client.place_order(symbol=symbol, order_side=OrderSide.SELL, order_type=OrderType.LIMIT ,quantity=pos,price=bid_price)
        # print(f"{symbol}  place sell order: {sell_order}")
        # if sell_order:
        #     # resolve buy orders
        #     orders = self.sell_orders_dict.get(symbol, [])
        #     orders.append(sell_order)
        #     self.sell_orders_dict[symbol] = orders
        #     self.ding.send_msg(f'{symbol} 卖出 ，价格:{bid_price} ，类型:{message}')
