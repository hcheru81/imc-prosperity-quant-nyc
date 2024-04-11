import string
from typing import List

import numpy as np
import pandas as pd

from datamodel import Order, OrderDepth, TradingState, UserId


class Trader:
    def __init__(self):
        self.price_history = {}

    def update_price_history(self, product: str, price: float):
        if product not in self.price_history:
            self.price_history[product] = []
        self.price_history[product].append(price)

    def calculate_ema(self, product: str, window: int = 5):
        prices = self.price_history.get(product, [])
        if len(prices) >= window:
            return pd.Series(prices).ewm(span=window, adjust=False).mean().iloc[-1]
        return None

    def calculate_vwap(self, order_depth: OrderDepth):
        total_volume = sum(order_depth.buy_orders.values()) - sum(
            order_depth.sell_orders.values()
        )
        total_price_volume = sum(
            price * volume for price, volume in order_depth.buy_orders.items()
        ) - sum(price * volume for price, volume in order_depth.sell_orders.items())
        if total_volume != 0:
            return total_price_volume / total_volume
        return None

    def run(self, state: TradingState):
        result = {}
        for product, order_depth in state.order_depths.items():
            current_price = (
                max(order_depth.buy_orders, default=0)
                + min(order_depth.sell_orders, default=0)
            ) / 2
            self.update_price_history(product, current_price)

            ema = self.calculate_ema(product)
            vwap = self.calculate_vwap(order_depth)
            if ema is None or vwap is None:
                continue

            if current_price > ema and current_price < vwap:
                # Market is below VWAP but above EMA, indicating potential upward momentum
                best_ask_price = min(order_depth.sell_orders)
                quantity = abs(order_depth.sell_orders[best_ask_price])
                result[product] = [Order(product, best_ask_price, quantity)]
            elif current_price < ema and current_price > vwap:
                # Market is above VWAP but below EMA, indicating potential downward momentum
                best_bid_price = max(order_depth.buy_orders)
                quantity = order_depth.buy_orders[best_bid_price]
                result[product] = [Order(product, best_bid_price, -quantity)]

        return result, 0, "SAMPLE"
