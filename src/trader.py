import string
from typing import List

from datamodel import Order, OrderDepth, TradingState, UserId


class Trader:
    def __init__(self):
        self.price_history: dict[str, List[float]] = {}

    def update_price_history(self, market_trades: dict[str, List]):
        for product, trades in market_trades.items():
            if product not in self.price_history:
                self.price_history[product] = []

            for trade in trades:
                self.price_history[product].append((trade.timestamp, trade.price))

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
                return midpoint_vwap + 1
        elif buy_orders:
            return int(max(buy_orders.keys()))  # Max buy price if no sell orders
        elif sell_orders:
            return int(min(sell_orders.keys()))  # Min sell price if no buy orders
        else:
            return 0  # Fallback if no orders

    def run(self, state: TradingState):
        self.update_price_history(state.market_trades)
        print("Price history: " + str(self.price_history))

        result = {}
        for product, order_depth in state.order_depths.items():
            acceptable_price = self.calculate_acceptable_price(
                order_depth.buy_orders, order_depth.sell_orders, product
            )
            print(f"Acceptable price for {product}: {acceptable_price}")

            orders: List[Order] = []
            sorted_sell_orders = sorted(order_depth.sell_orders.items())
            for price, volume in sorted_sell_orders:
                if price <= acceptable_price:
                    orders.append(Order(product, price, abs(volume)))

            sorted_buy_orders = sorted(order_depth.buy_orders.items(), reverse=True)
            for price, volume in sorted_buy_orders:
                if price >= acceptable_price:
                    orders.append(Order(product, price, -volume))

            result[product] = orders

        traderData = "SAMPLE"
        conversions = 1
        return result, conversions, traderData
