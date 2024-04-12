import string
from typing import List

import numpy as np
import pandas as pd

from datamodel import Order, OrderDepth, TradingState, UserId


class Trader:

    def __init__(self) -> None:
        self.position_limits = {"STARFRUIT": 20, "AMETHYSTS": 20}

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

    def run(self, state: TradingState):
        result = {}
        positions = {"STARFRUIT": 0, "AMETHYSTS": 0}
        for k, v in state.position.items():
            positions[k] += v

        for product, order_depth in state.order_depths.items():
            acceptable_price = self.calculate_acceptable_price(
                order_depth.buy_orders, order_depth.sell_orders, product
            )

            orders: List[Order] = []
            sorted_sell_orders = sorted(order_depth.sell_orders.items())

            for price, volume in sorted_sell_orders:
                if price <= acceptable_price:
                    if (
                        positions[product] + abs(volume)
                        >= self.position_limits[product]
                    ):
                        result[product] = orders
                        return result, "SAMPLE", 1
                    orders.append(Order(product, price, abs(volume)))
                    positions[product] += volume

            sorted_buy_orders = sorted(order_depth.buy_orders.items(), reverse=True)
            for price, volume in sorted_buy_orders:
                if price >= acceptable_price:
                    if (
                        positions[product] + abs(volume)
                        >= self.position_limits[product]
                    ):
                        result[product] = orders
                        return result, "SAMPLE", 1
                    orders.append(Order(product, price, -abs(volume)))
                    positions[product] += volume

            result[product] = orders

        return result, "SAMPLE", 1
