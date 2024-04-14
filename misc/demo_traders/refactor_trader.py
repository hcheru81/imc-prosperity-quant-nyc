import math
import string
from collections import deque
from typing import List

import jsonpickle

from datamodel import Order, OrderDepth, TradingState, UserId

POSITION_LIMITS = {"AMETHYSTS": 20, "STARFRUIT": 20}
STARFRUIT_COEFFICIENTS = [5.24986188, 0.70354115, 0.23410216, 0.04909509, 0.01222407]


class Trader:

    def __init__(self):
        self.previous_starfruit_prices = deque(
            maxlen=max(len(STARFRUIT_COEFFICIENTS), 20)
        )

    def deserialize_trader_data(self, state_data):
        try:
            return jsonpickle.decode(state_data)
        except:
            return {}

    def serialize_trader_data(self, data):
        try:
            return jsonpickle.encode(data)
        except:
            return None

    def vwap(self, orders: dict) -> float:
        total_volume = sum(orders.values())
        return (
            sum(price * volume for price, volume in orders.items()) / total_volume
            if total_volume > 0
            else 0
        )

    def update_starfruit_price_history(
        self, previous_trading_state, trading_state: TradingState
    ):
        self.previous_starfruit_prices.extend(
            previous_trading_state.get("previous_starfruit_prices", [])
        )
        starfruit_orders = trading_state.order_depths.get("STARFRUIT", OrderDepth())
        if starfruit_orders.sell_orders and starfruit_orders.buy_orders:
            sell_vwap = self.vwap(starfruit_orders.sell_orders)
            buy_vwap = self.vwap(starfruit_orders.buy_orders)
            self.previous_starfruit_prices.append((sell_vwap + buy_vwap) / 2)

    def calculate_acceptable_price(self, product) -> int:
        if product == "AMETHYSTS":
            return 10000
        elif (
            product == "STARFRUIT"
            and len(self.previous_starfruit_prices) >= len(STARFRUIT_COEFFICIENTS) - 1
        ):
            return int(
                sum(
                    coef * price
                    for coef, price in zip(
                        STARFRUIT_COEFFICIENTS, self.previous_starfruit_prices
                    )
                )
            )
        return 0

    def add_buy_order(
        self,
        orders,
        product,
        buy_pos,
        mid_price_floor,
        sorted_buy_orders,
        delta_pos,
        s1,
        s2,
    ) -> int:
        target = min(mid_price_floor + s1, sorted_buy_orders[0][0] + s2)
        neutralizing_quantity = delta_pos
        buy_pos += neutralizing_quantity
        orders.append(Order(product, target, neutralizing_quantity))
        return buy_pos

    def add_sell_order(
        self,
        orders,
        product,
        sell_pos,
        mid_price_ceil,
        sorted_sell_orders,
        delta_pos,
        s1,
        s2,
    ) -> int:
        target = max(mid_price_ceil + s1, sorted_sell_orders[0][0] + s2)
        neutralizing_quantity = delta_pos
        sell_pos += neutralizing_quantity
        orders.append(Order(product, target, neutralizing_quantity))
        return sell_pos

    def generate_orders(
        self,
        product: str,
        position: int,
        acceptable_price: int,
        order_depth: OrderDepth,
    ) -> List[Order]:
        """
        OUTPUTS:
        List[Order]: A list of Order objects, where each Order is initialized with the product name,
        the price, and the modified volume (taking into account the fudge factor).
        """
        orders: List[Order] = []

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

        position_limit = POSITION_LIMITS.get(product, 20)
        buy_pos = position

        # BUYING
        for ask, volume in sorted_sell_orders:
            if buy_pos >= position_limit:
                break
            if (
                ask < acceptable_price
            ):  # if someone wants to sell for less than a fair price we buy
                buy_quantity = min(abs(volume), position_limit - buy_pos)
                buy_pos += buy_quantity
                orders.append(Order(product, ask, buy_quantity))

            # if were still short we can settle for a suboptimal price to netralize
            if ask == mid_price_floor and buy_pos < 0:
                buy_quantity = min(abs(volume), -buy_pos)
                buy_pos += buy_quantity
                orders.append(Order(product, ask, buy_quantity))

        if buy_pos < position_limit:  # maximize market exposure
            if buy_pos < 0:
                # Try to get back to neutral at a good price
                buy_pos = self.add_buy_order(
                    orders,
                    product,
                    buy_pos,
                    mid_price_floor,
                    sorted_buy_orders,
                    abs(buy_pos),
                    0,
                    0,
                )

            if 0 <= buy_pos <= 10:
                # Get up to 10 shares
                buy_pos = self.add_buy_order(
                    orders,
                    product,
                    buy_pos,
                    mid_price_floor,
                    sorted_buy_orders,
                    10 - buy_pos,
                    -1,
                    1,
                )

            if buy_pos >= 10:
                # Adjust to match the position limit
                buy_pos = self.add_buy_order(
                    orders,
                    product,
                    buy_pos,
                    mid_price_floor,
                    sorted_buy_orders,
                    position_limit - buy_pos,
                    -1,
                    1,
                )

        sell_pos = position  # NOTE: set sell_pos to state.position

        # SELLING
        for bid, volume in sorted_buy_orders:
            if sell_pos <= -position_limit:
                break
            if bid > acceptable_price:
                sell_quantity = max(-(abs(volume)), -position_limit - sell_pos)
                orders.append(Order(product, bid, sell_quantity))
                sell_pos += sell_quantity
            if bid == mid_price_ceil and sell_pos > 0:  # overleveraged long
                sell_quantity = max(-volume, -sell_pos)
                sell_pos += sell_quantity
                orders.append(Order(product, bid, sell_quantity))

        if sell_pos > -position_limit:  # room to sell more
            if sell_pos > 0:  # we are long
                sell_pos = self.add_sell_order(
                    orders,
                    product,
                    sell_pos,
                    mid_price_ceil,
                    sorted_sell_orders,
                    -sell_pos,
                    0,
                    0,
                )
            if 0 >= sell_pos >= -10:  # SAFE
                sell_pos = self.add_sell_order(
                    orders,
                    product,
                    sell_pos,
                    mid_price_ceil,
                    sorted_sell_orders,
                    -10 - sell_pos,
                    1,
                    -1,
                )
            if sell_pos < -10:
                sell_pos = self.add_sell_order(
                    orders,
                    product,
                    sell_pos,
                    mid_price_ceil,
                    sorted_sell_orders,
                    -position_limit - sell_pos,
                    2,
                    -1,
                )

        return orders

    def run(self, state: TradingState):
        previous_state_data = self.deserialize_trader_data(state.traderData)
        self.update_starfruit_price_history(previous_state_data, state)
        result = {
            product: self.generate_orders(
                product,
                state.position.get(product, 0),
                self.calculate_acceptable_price(product),
                order_depth,
            )
            for product, order_depth in state.order_depths.items()
        }
        serialized_trader_data = self.serialize_trader_data(
            {"previous_starfruit_prices": list(self.previous_starfruit_prices)}
        )
        return result, serialized_trader_data
