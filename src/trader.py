import string
from typing import List

from datamodel import Order, OrderDepth, TradingState, UserId


class Trader:

    # def __init__(self) -> None:
    #     self.position_limits = {"STARFRUIT": 20, "AMETHYSTS": 20}

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
            return 0  # Fallback

    def run(self, state: TradingState):
        result = {}
        fudge_factors = {
            "STARFRUIT": {
                "b_obg": 5,
                "s_obg": 6,
                "b_odc": 1,
                "s_odc": 1,
            },
            "AMETHYSTS": {
                "b_obg": 6,
                "s_obg": 6,
                "b_odc": 1,
                "s_odc": 1,
            },
        }

        for product, order_depth in state.order_depths.items():
            acceptable_price = self.calculate_acceptable_price(
                order_depth.buy_orders, order_depth.sell_orders, product
            )

            # print(state.position)

            orders: List[Order] = []
            if len(order_depth.sell_orders) != 0:
                sorted_sell_orders = sorted(order_depth.sell_orders.items())
                for price, volume in sorted_sell_orders[
                    0 : fudge_factors[product]["s_odc"]
                ]:
                    # print(
                    #     f"product: {product}, price: {price}, vol: {volume}, acceptable_price: {acceptable_price}"
                    # )
                    if (
                        price <= acceptable_price
                    ):  # place a buy order to fill sell order
                        orders.append(
                            Order(
                                product,
                                price,
                                abs(volume) + fudge_factors[product]["s_obg"],
                            )
                        )

            if len(order_depth.buy_orders) != 0:
                sorted_buy_orders = sorted(order_depth.buy_orders.items(), reverse=True)
                for price, volume in sorted_buy_orders[
                    0 : fudge_factors[product]["b_odc"]
                ]:
                    # print(
                    #     f"product: {product}, price: {price}, vol: {volume}, acceptable_price: {acceptable_price}"
                    # )
                    if price > acceptable_price:
                        orders.append(
                            Order(
                                product,
                                price,
                                -(abs(volume) + fudge_factors[product]["b_obg"]),
                            )
                        )

            result[product] = orders

        traderData = "SAMPLE"
        conversions = 1

        return result, traderData, conversions
