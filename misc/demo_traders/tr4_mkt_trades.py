import string
from typing import List

import numpy as np
import pandas as pd

from datamodel import Order, OrderDepth, TradingState, UserId


class Trader:

    def __init__(self):
        self.price_history: dict[str, List[float]] = {}
        self.position_limits = {"STARFRUIT": 20, "AMETHYSTS": 20}
        self.product_dfs = {}  # Dictionary to store dataframes for each product

    def update_trade_history(self, market_trades: dict[str, List]):
        for product, trades in market_trades.items():
            if product not in self.product_dfs:
                self.product_dfs[product] = pd.DataFrame(
                    columns=["timestamp", "price", "quantity"]
                )

            # Convert trade objects to a list of dictionaries
            trades_data = [
                {
                    "timestamp": trade.timestamp,
                    "price": trade.price,
                    "quantity": trade.quantity,
                }
                for trade in trades
            ]

            # Append new trades to the dataframe
            if trades_data:
                self.product_dfs[product] = pd.concat(
                    [self.product_dfs[product], pd.DataFrame(trades_data)],
                    ignore_index=True,
                )

    def calculate_acceptable_price(
        self, buy_orders: dict, sell_orders: dict, product
    ) -> int:
        def vwap(orders: dict) -> float:
            total_volume = sum(orders.values())
            if total_volume == 0:
                return 0
            return (
                sum(price * volume for price, volume in orders.items()) / total_volume
            )

        if buy_orders and sell_orders:
            buy_vwap = vwap(buy_orders)
            sell_vwap = vwap(sell_orders)
            midpoint_vwap = int((buy_vwap + sell_vwap) / 2)
            if product == "STARFRUIT":
                return midpoint_vwap - 1
            else:
                return midpoint_vwap
        elif buy_orders:
            return int(max(buy_orders.keys()))  # Max buy price if no sell orders
        elif sell_orders:
            return int(min(sell_orders.keys()))  # Min sell price if no buy orders
        else:
            return 0  # Fallback if no orders

    def calculate_price_trend(self, product: str, lookback_periods: int = 10) -> float:
        df = self.product_dfs.get(product, pd.DataFrame())
        if df.empty or len(df) < lookback_periods:
            return 0  # Not enough data to establish a trend

        # Take the last 'lookback_periods' data points
        recent_data = df.tail(lookback_periods).copy()

        # Convert 'price' column to numeric type, using 'coerce' to handle any conversion errors
        recent_data["price"] = pd.to_numeric(recent_data["price"], errors="coerce")
        X = np.arange(len(recent_data))  # Independent variable (time)
        y = recent_data["price"].values  # Dependent variable (price)

        try:
            slope, _ = np.polyfit(X, y, 1)
        except TypeError as e:
            print(f"Error in polyfit: {e}")
            return 0

        return slope

    def run(self, state: TradingState):
        self.update_trade_history(state.market_trades)
        # print(self.product_dfs)

        print(f"t={state.timestamp}, trade_ledger={self.product_dfs}")
        print(f"t={state.timestamp}, observations={state.market_trades}")

        result = {}

        # print(f"Current positions: {current_positions}")

        for product, order_depth in state.order_depths.items():
            trend = self.calculate_price_trend(product, lookback_periods=80)
            acceptable_price = self.calculate_acceptable_price(
                order_depth.buy_orders, order_depth.sell_orders, product
            )

            if trend < 0.8:
                cp = state.position.get(product, 0)
                if cp > 0:  # currently long
                    orders: List[Order] = []
                    sorted_sell_orders = sorted(order_depth.sell_orders.items())
                    for price, volume in sorted_sell_orders:  # sell!
                        if price <= acceptable_price:
                            orders.append(Order(product, price, abs(volume)))
                    result[product] = orders
                    return result, "SAMPLE", 1
            if trend > 0.8:
                cp = state.position.get(product, 0)
                if cp < 0:  # currently short
                    orders: List[Order] = []
                    sorted_buy_orders = sorted(
                        order_depth.buy_orders.items(), reverse=True
                    )
                    for price, volume in sorted_buy_orders:
                        if price > acceptable_price:
                            orders.append(Order(product, price, -volume))
                    result[product] = orders
                return result, "SAMPLE", 1
            # print(
            #     f"Product {product} - acceptable_price: {acceptable_price} - trend: {trend}"
            # )

            orders: List[Order] = []
            sorted_sell_orders = sorted(order_depth.sell_orders.items())
            print(f"sorted_sell: {sorted_sell_orders}")
            for price, volume in sorted_sell_orders:
                if price <= acceptable_price:
                    orders.append(Order(product, price, abs(volume)))

            sorted_buy_orders = sorted(order_depth.buy_orders.items(), reverse=True)
            print(f"sorted_buy: {sorted_buy_orders}")
            for price, volume in sorted_buy_orders:
                if price > acceptable_price:
                    orders.append(Order(product, price, -volume))

            result[product] = orders

        traderData, conversions = "SAMPLE", 1
        # print(state.position)
        return result, conversions, traderData
