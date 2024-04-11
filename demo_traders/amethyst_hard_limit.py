import string
from typing import List

from datamodel import Order, OrderDepth, TradingState, UserId


class Trader:
    def calculate_acceptable_price(self, buy_orders: dict, sell_orders: dict) -> int:
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
            return int(
                (buy_vwap + sell_vwap) / 2
            )  # Midpoint of VWAPs as acceptable price
        elif buy_orders:
            return int(max(buy_orders))  # Max buy price if no sell orders
        elif sell_orders:
            return int(min(sell_orders))  # Min sell price if no buy orders
        else:
            return 0  # Fallback if no orders

    def process_market_trades(self, market_trades: dict):
        for product, trades in market_trades.items():
            print(f"Market trades for {product}:")
            for trade in trades:
                print(f"Price: {trade.price}, Volume: {trade.quantity}")

    def run(self, state: TradingState):
        # print("traderData: " + state.traderData)
        # print("Observations: " + str(state.observations))

        result = {}
        for product, order_depth in state.order_depths.items():
            if product == "STARFRUIT":
                acceptable_price = self.calculate_acceptable_price(
                    order_depth.buy_orders, order_depth.sell_orders
                )
                print(f"Acceptable price for {product}: {acceptable_price}")

                orders: List[Order] = []
                # Sort sell orders to prioritize lower prices
                sorted_sell_orders = sorted(order_depth.sell_orders.items())
                for price, volume in sorted_sell_orders:
                    if price <= acceptable_price:
                        orders.append(Order(product, price, abs(volume)))

                # Sort buy orders to prioritize higher prices
                sorted_buy_orders = sorted(order_depth.buy_orders.items(), reverse=True)
                for price, volume in sorted_buy_orders:
                    if price >= acceptable_price:
                        orders.append(Order(product, price, -volume))

                result[product] = orders
            elif product == "AMETHYSTS":
                # self.process_market_trades(state.market_trades)
                sorted_sell_orders = sorted(order_depth.sell_orders.items())
                for price, volume in sorted_sell_orders:
                    if price <= 9996:
                        orders.append(Order(product, price, abs(volume)))

                sorted_buy_orders = sorted(order_depth.buy_orders.items(), reverse=True)
                for price, volume in sorted_buy_orders:
                    if price >= 10004:
                        orders.append(Order(product, price, -volume))

        traderData = "SAMPLE"
        conversions = 1
        return result, conversions, traderData
