import math
import string
from typing import List

import jsonpickle

from datamodel import Order, OrderDepth, TradingState, UserId

POSITION_LIMITS = {"AMETHYSTS": 20, "STARFRUIT": 20}
STARFRUIT_COEFFICIENTS = [5.24986188, 0.70354115, 0.23410216, 0.04909509, 0.01222407]


class Trader:

    def __init__(self):
        self.previous_starfruit_prices = []

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
        if total_volume == 0:
            return 0
        return sum(price * volume for price, volume in orders.items()) / total_volume

    def update_starfruit_price_history(
        self, previousTradingState, tradingState: TradingState, memory: int
    ):
        self.previous_starfruit_prices = previousTradingState.get(
            "previous_starfruit_prices", []
        )

        starfruit_orders = tradingState.order_depths.get(
            "STARFRUIT", OrderDepth()
        )  # Provide default as OrderDepth()
        sell_orders = starfruit_orders.sell_orders
        buy_orders = starfruit_orders.buy_orders

        # Calculate VWAP only if there are both buy and sell orders
        if sell_orders and buy_orders:
            sell_vwap = self.vwap(sell_orders)
            buy_vwap = self.vwap(buy_orders)
            current_vwap = (sell_vwap + buy_vwap) / 2
            self.previous_starfruit_prices.append(current_vwap)
            self.previous_starfruit_prices = self.previous_starfruit_prices[-memory:]

    def calculate_acceptable_price(self, product) -> int:
        if product == "AMETHYSTS":
            return 10000  # Static price for AMETHYSTS

        if product == "STARFRUIT":
            # Ensure we have enough historical data to apply the regression model
            if len(self.previous_starfruit_prices) >= len(STARFRUIT_COEFFICIENTS) - 1:
                # Calculate the expected price using linear regression weights
                expected_price = STARFRUIT_COEFFICIENTS[0] + sum(
                    STARFRUIT_COEFFICIENTS[i + 1] * self.previous_starfruit_prices[i]
                    for i in range(len(STARFRUIT_COEFFICIENTS) - 1)
                )
                return int(expected_price)
            else:
                return 0  # Not enough data to calculate price
        return 0

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
            if ask == mid_price_floor and current_position < 5:
                buy_quantity = min(abs(volume), -current_position)
                current_position += buy_quantity
                orders.append(Order(product, ask, buy_quantity))

        assert abs(current_position) <= position_limit

        if current_position < position_limit:
            if current_position < 0:  # we are overleveraged short
                s1, s2 = 0, 0
                target = min(mid_price_floor + s1, sorted_buy_orders[0][0] + s2)
                neutralzing_quantity = abs(current_position)
                current_position += neutralzing_quantity
                orders.append(Order(product, target, neutralzing_quantity))  # limit buy
            # if 0 <= current_position <= 10:
            #     s1, s2 = -1, 1
            #     target = min(mid_price_floor + s1, sorted_buy_orders[0][0] + s2)
            #     neutralzing_quantity = abs(current_position)
            #     current_position += neutralzing_quantity
            #     orders.append(Order(product, target, neutralzing_quantity))  # limit buy
            # if current_position >= 10:
            #     s1, s2 = -3, 1
            #     target = min(mid_price_floor + s1, sorted_buy_orders[0][0] + s2)
            #     neutralzing_quantity = abs(current_position)
            #     current_position += neutralzing_quantity
            #     orders.append(Order(product, target, neutralzing_quantity))  # limit buy

        assert abs(current_position) <= position_limit

        # Selling
        for bid, volume in sorted_buy_orders:
            if current_position <= -position_limit:
                break
            if bid > acceptable_price:
                sell_quantity = max(-(abs(volume)), -position_limit - current_position)
                orders.append(Order(product, bid, sell_quantity))
                current_position += sell_quantity
            if bid == mid_price_ceil and current_position > 5:  # overleveraged long
                sell_quantity = max(-volume, -current_position)
                current_position += sell_quantity
                orders.append(Order(product, bid, sell_quantity))

        assert abs(current_position) <= position_limit

        if current_position > -position_limit:  # room to sell more
            if current_position > 0:  # we are long
                s1, s2 = 0, 0
                target = max(mid_price_ceil + s1, sorted_sell_orders[0][0] + s2)
                neutralzing_quantity = -current_position
                current_position += neutralzing_quantity
                orders.append(Order(product, target, neutralzing_quantity))
            # if 0 >= current_position >= -10:  # we are long
            #     s1, s2 = 1, -1
            #     target = max(mid_price_ceil + s1, sorted_sell_orders[0][0] + s2)
            #     neutralzing_quantity = -current_position
            #     current_position += neutralzing_quantity
            #     orders.append(Order(product, target, neutralzing_quantity))
            # if -10 >= current_position:  # we are long
            #     s1, s2 = 2, -1
            #     target = max(mid_price_ceil + s1, sorted_sell_orders[0][0] + s2)
            #     neutralzing_quantity = -current_position
            #     current_position += neutralzing_quantity
            #     orders.append(Order(product, target, neutralzing_quantity))
        assert abs(current_position) <= position_limit
        return orders

    def run(self, state: TradingState):
        previous_state_data = self.deserialize_trader_data(state.traderData)
        self.update_starfruit_price_history(
            previous_state_data, state, memory=len(STARFRUIT_COEFFICIENTS) - 1
        )

        result = {}
        for product, order_depth in state.order_depths.items():
            acceptable_price = self.calculate_acceptable_price(product)
            orders = self.generate_orders(
                product,
                state.position.get(product, 0),
                acceptable_price,
                order_depth,
            )
            result[product] = orders

        trader_data = {"previous_starfruit_prices": self.previous_starfruit_prices}
        serialized_trader_data = self.serialize_trader_data(trader_data)
        conversions = 1

        return result, conversions, serialized_trader_data
