import math
import string
from typing import List

import jsonpickle

from datamodel import Order, OrderDepth, TradingState, UserId

POSITION_LIMITS = {"AMETHYSTS": 20, "STARFRUIT": 20}


class Trader:

    def __init__(self):
        self.previous_starfruit_prices = []

    def vwap(self, orders: dict) -> float:
        total_volume = sum(orders.values())
        if total_volume == 0:
            return 0
        return sum(price * volume for price, volume in orders.items()) / total_volume

    def update_starfruit_price_history(
        self, previousTradingState, tradingState: TradingState
    ):
        if "previous_starfruit_prices" in previousTradingState:
            self.previous_starfruit_prices = previousTradingState[
                "previous_starfruit_prices"
            ]
        else:
            self.previous_starfruit_prices = []

        # Use VWAP for both buy and sell orders
        sell_orders = tradingState.order_depths["STARFRUIT"].sell_orders
        buy_orders = tradingState.order_depths["STARFRUIT"].buy_orders
        sell_vwap = self.get_vwap(sell_orders)
        buy_vwap = self.get_vwap(buy_orders)

        # Calculate average of buy and sell VWAP
        current_vwap = (sell_vwap + buy_vwap) / 2

        self.previous_starfruit_prices.append(current_vwap)

        if len(self.previous_starfruit_prices) > 4:
            self.previous_starfruit_prices.pop(0)

    def calculate_acceptable_price(
        self, buy_orders: dict, sell_orders: dict, product
    ) -> int:

        if product == "AMETHYSTS":
            return 10000

        if buy_orders and sell_orders:
            buy_vwap = self.vwap(buy_orders)
            sell_vwap = self.vwap(sell_orders)
            midpoint_vwap = (buy_vwap + sell_vwap) / 2
            return midpoint_vwap - 1

        elif buy_orders:
            return max(buy_orders.keys())  # Max buy price if no sell orders
        elif sell_orders:
            return min(sell_orders.keys())  # Min sell price if no buy orders
        else:
            return 0  # Fallback

    def generate_orders(
        self,
        product: str,
        current_position: int,
        acceptable_price: int,
        order_depth: OrderDepth,
    ) -> List[Order]:
        """
        OUTPUTS:
        List[Order]: A list of Order objects, where each Order is initialized with the product name,
        the price, and the modified volume (taking into account the fudge factor).
        """
        orders: List[Order] = []

        position_limit = POSITION_LIMITS.get(product, 20)
        current_position = current_position

        sorted_sell_orders = sorted(
            list(order_depth.sell_orders.items()), key=lambda x: x[0]
        )

        sorted_buy_orders = sorted(
            list(order_depth.buy_orders.items()),
            key=lambda x: x[0],
            reverse=True,
        )

        mid_price_floor = math.floor(acceptable_price)
        mid_price_ceil = math.ceil(acceptable_price)

        # Buying
        for ask, volume in sorted_sell_orders:
            if current_position >= position_limit:
                break
            if (
                ask < acceptable_price
            ):  # if someone wants to sell for less than a fair price we buy
                buy_quantity = min(abs(volume), position_limit - current_position)
                current_position += buy_quantity
                orders.append(Order(product, ask, buy_quantity))
                # print(f"placed trade - prod: {product}, ask: {ask}, bq: {buy_quantity}")

            # if were still short we can settle for a suboptimal price to netralize
            if ask == mid_price_floor and current_position < 0:
                buy_quantity = min(abs(volume), current_position)
                current_position += buy_quantity
                orders.append(Order(product, ask, buy_quantity))

        if current_position < position_limit:
            if current_position < 0:  # we are overleveraged short
                # TODO: split conditions based on how leveraged current pos is
                target = min(mid_price_floor, sorted_buy_orders[0][0])
                neutralzing_quantity = abs(current_position)
                current_position += neutralzing_quantity
                orders.append(Order(product, target, neutralzing_quantity))  # limit buy

        # Selling
        for bid, volume in sorted_buy_orders:
            if current_position <= -position_limit:
                break
            if bid > acceptable_price:
                sell_quantity = max(-(abs(volume)), -position_limit - current_position)
                orders.append(Order(product, bid, sell_quantity))
                current_position += sell_quantity
            if bid == mid_price_ceil and current_position > 0:  # overleveraged long
                sell_quantity = max(-volume, -current_position)
                current_position += sell_quantity
                orders.append(Order(product, bid, sell_quantity))

        if current_position > -position_limit:  # room to sell more
            if current_position > 0:  # we are long
                target = max(mid_price_ceil, sorted_sell_orders[0][0])
                neutralzing_quantity = -current_position
                current_position += neutralzing_quantity
                orders.append(Order(product, target, neutralzing_quantity))

        return orders

    def run(self, state: TradingState):
        try:
            previousStateData = jsonpickle.decode(state.traderData)
        except:
            previousStateData = {}

        self.update_starfruit_price_history(previousStateData, state)

        result = {}
        for product, order_depth in state.order_depths.items():
            acceptable_price = self.calculate_acceptable_price(
                order_depth.buy_orders, order_depth.sell_orders, product
            )
            orders = self.generate_orders(
                product,
                state.position.get(product, 0),
                acceptable_price,
                order_depth,
            )
            result[product] = orders

        serialisedTraderData = jsonpickle.encode(serialisedTraderData)
        conversions = 1

        return result, conversions, serialisedTraderData
