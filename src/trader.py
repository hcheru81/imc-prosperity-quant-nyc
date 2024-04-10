import string
from typing import List

from datamodel import Order, OrderDepth, TradingState, UserId


class Trader:

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        # Orders to be placed on exchange matching engine
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []

            # Calculate weighted average (VWAP) for sell and buy orders
            def vwap(orders):
                total_volume = sum(volume for price, volume in orders)
                if total_volume == 0:
                    return 0
                return sum(price * volume for price, volume in orders) / total_volume

            if order_depth.sell_orders:
                sell_orders = order_depth.sell_orders.items()
                sell_vwap = vwap(sell_orders)
            else:
                sell_vwap = float("inf")  # No sell orders

            if order_depth.buy_orders:
                buy_orders = order_depth.buy_orders.items()
                buy_vwap = vwap(buy_orders)
            else:
                buy_vwap = 0  # No buy orders

            # Set acceptable price as the average of sell and buy VWAP
            ACCEPTABLE_PRICE = int((sell_vwap + buy_vwap) / 2)

            # print(f"Acceptable price for {product}: {ACCEPTABLE_PRICE}")

            if len(order_depth.sell_orders) != 0:  # sellers are selling
                best_ask, best_ask_amount = sorted(
                    list(order_depth.sell_orders.items())
                )[0]
                if int(best_ask) < ACCEPTABLE_PRICE:
                    # print("-" * 50)
                    # print(
                    #     f"BUYING {-best_ask_amount} shares of {product} @ $ {best_ask}"
                    # )
                    # print("-" * 50)
                    orders.append(Order(product, best_ask, -best_ask_amount))

            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = sorted(
                    list(order_depth.buy_orders.items())
                )[0]
                if int(best_bid) > ACCEPTABLE_PRICE:
                    # print("-" * 50)
                    # print(
                    #     f"SELLING {best_bid_amount} shares of {product} @ $ {best_bid}"
                    # )
                    # print("-" * 50)
                    orders.append(Order(product, best_bid, -best_bid_amount))

            result[product] = orders

        # String value holding Trader state data required.
        # It will be delivered as TradingState.traderData on next execution.
        traderData = "SAMPLE"

        # Sample conversion request. Check more details below.
        conversions = 1
        return result, conversions, traderData
