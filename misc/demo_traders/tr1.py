import collections
import math
from typing import Any, Dict, List

import jsonpickle

from datamodel import Order, OrderDepth, TradingState, UserId

POSITION_LIMIT = 20

POSITION_LIMITS = {"AMETHYSTS": 20, "STARFRUIT": 20, "PRODUCT1": 10, "PRODUCT2": 20}

PRICE_AGGRESSION = 0

THRESHOLDS = {"over": 2, "mid": 5}

STARFRUIT_COEFFICIENTS = [5.24986188, 0.70354115, 0.23410216, 0.04909509, 0.01222407]


class Trader:
    previous_starfruit_prices = []

    def get_vwap(self, orders: dict) -> float:
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

    def get_starfruit_price(self) -> float | None:
        # if we don't have enough data, return None
        if len(self.previous_starfruit_prices) < 4:
            return None

        # calculate the average of the last four prices

        print(STARFRUIT_COEFFICIENTS)
        print(self.previous_starfruit_prices)
        print(
            sum(
                [
                    STARFRUIT_COEFFICIENTS[i] * self.previous_starfruit_prices[i]
                    for i in range(4)
                ]
            )
        )

        expected_price = STARFRUIT_COEFFICIENTS[0] + sum(
            [
                STARFRUIT_COEFFICIENTS[i + 1] * self.previous_starfruit_prices[i]
                for i in range(4)
            ]
        )

        return expected_price

    def get_orders(
        self, state: TradingState, acceptable_price: int | float, product: str
    ) -> List[Order]:
        # market taking + making based on Stanford's 2023 entry
        product_order_depth = state.order_depths[product]
        product_position_limit = POSITION_LIMITS[product]
        acceptable_buy_price = math.floor(acceptable_price)
        acceptable_sell_price = math.ceil(acceptable_price)  # TODO: use this logic
        orders = []

        # sort the order books by price (will sort by the key by default)
        orders_sell = sorted(
            list(product_order_depth.sell_orders.items()), key=lambda x: x[0]
        )
        orders_buy = sorted(
            list(product_order_depth.buy_orders.items()),
            key=lambda x: x[0],
            reverse=True,
        )

        lowest_sell_price = orders_sell[0][0]
        lowest_buy_price = orders_buy[0][0]

        # we start with buying - using our current position to determine how much and how aggressively we buy from the market

        current_position = state.position.get(product, 0)
        print(f"{product} current buying position: {current_position}")

        for ask, vol in orders_sell:
            vol = abs(vol)
            # skip if there is no quota left
            if product_position_limit - current_position <= 0:
                break

            if ask < acceptable_price - PRICE_AGGRESSION:
                # we want to buy
                most_we_can_buy = product_position_limit - current_position
                buy_amount = min(vol, most_we_can_buy)
                current_position += buy_amount
                assert buy_amount > 0
                orders.append(Order(product, ask, buy_amount))
                print(f"{product} buy order 1: {-vol} at {ask}")

            # if overleveraged, buy up until we are no longer leveraged
            if ask == acceptable_buy_price and current_position < 0:
                buy_amount = min(vol, -current_position)
                current_position += buy_amount
                assert buy_amount > 0
                orders.append(Order(product, ask, buy_amount))
                print(f"{product} buy order 2: {-vol} at {ask}")

        # once we exhaust all profitable sell orders, we place additional buy orders
        # at a price acceptable to us
        # what that price looks like will depend on our position

        if product_position_limit != current_position:
            if (
                current_position < THRESHOLDS["over"]
            ):  # if we are overleveraged to sell, buy at parity for price up to neutral position
                target_buy_price = min(acceptable_buy_price, lowest_buy_price + 1)
                vol = -current_position + THRESHOLDS["over"]
                orders.append(Order(product, target_buy_price, vol))
                print(f"{product} buy order 3: {vol} at {target_buy_price}")
                current_position += vol
            if THRESHOLDS["over"] <= current_position <= THRESHOLDS["mid"]:
                target_buy_price = min(acceptable_buy_price - 1, lowest_buy_price + 1)
                vol = (
                    -current_position + THRESHOLDS["mid"]
                )  # if we are close to neutral
                orders.append(Order(product, target_buy_price, vol))
                print(f"{product} buy order 4: {vol} at {target_buy_price}")
                current_position += vol
            if current_position >= THRESHOLDS["mid"]:
                target_buy_price = min(acceptable_buy_price - 3, lowest_buy_price + 1)
                vol = product_position_limit - current_position
                orders.append(Order(product, target_buy_price, vol))
                print(f"{product} buy order 5: {vol} at {target_buy_price}")
                current_position += vol

        # now we sell - we reset our position
        selling_pos = state.position.get(product, 0)

        print(f"{product} current selling position: {selling_pos}")

        for bid, vol in orders_buy:
            # positive orders in the list
            # but we are sending negative sell orders, so we negate it
            # max we can sell is -product_position_limit - current position
            # if current position is negative we can sell less - if positive we can sell more

            if -selling_pos >= product_position_limit:
                break

            if bid > acceptable_price + PRICE_AGGRESSION:
                sell_amount = min(
                    max(-vol, -product_position_limit - selling_pos), -1
                )  # added min
                selling_pos += sell_amount
                assert sell_amount < 0
                orders.append(Order(product, bid, sell_amount))
                print("{product} sell order 1: ", sell_amount, bid)

            # if at parity, sell up until we are no longer leveraged
            if bid == acceptable_sell_price and selling_pos > 0:
                sell_amount = max(-vol, -selling_pos)
                selling_pos += sell_amount
                assert sell_amount < 0
                orders.append(Order(product, bid, sell_amount))
                print("{product} sell order 2: ", sell_amount, bid)

        # start market making with remaining quota
        # if selling_pos
        if -product_position_limit - selling_pos < 0:
            if selling_pos > -THRESHOLDS["over"]:
                target_sell_price = max(acceptable_sell_price, lowest_sell_price - 1)
                vol = -selling_pos - THRESHOLDS["over"]
                orders.append(Order(product, target_sell_price, vol))
                selling_pos += vol
                print(f"{product} sell order 3: selling {vol} at {target_sell_price}")
            if -THRESHOLDS["over"] >= selling_pos >= -THRESHOLDS["mid"]:
                target_sell_price = max(
                    acceptable_sell_price + 1, lowest_sell_price - 1
                )
                vol = -selling_pos - THRESHOLDS["mid"]
                orders.append(Order(product, target_sell_price, vol))
                selling_pos += vol
                print(f"{product} sell order 4: selling {vol} at {target_sell_price}")
            if -THRESHOLDS["mid"] >= selling_pos:
                target_sell_price = max(
                    acceptable_sell_price + 2, lowest_sell_price - 1
                )
                vol = -product_position_limit - selling_pos
                orders.append(Order(product, target_sell_price, vol))
                selling_pos += vol
                print(f"{product} sell order 5: selling {vol} at {target_sell_price}")

        return orders

    def get_acceptable_price(
        self, state: TradingState, product: str
    ) -> int | float | None:
        if product == "AMETHYSTS":
            return 10000
        if product == "STARFRUIT":
            return self.get_starfruit_price()
        return None

    def run(self, state: TradingState):
        try:
            previousStateData = jsonpickle.decode(state.traderData)
        except:
            previousStateData = {}
        self.update_starfruit_price_history(previousStateData, state)

        result = {}

        for product in state.order_depths:
            product_acceptable_price = self.get_acceptable_price(state, product)
            if product_acceptable_price is None:
                continue
            else:
                orders = self.get_orders(state, product_acceptable_price, product)
                result[product] = orders

        traderData = {"previous_starfruit_prices": self.previous_starfruit_prices}

        print(result)

        serialisedTraderData = jsonpickle.encode(traderData)

        conversions = 0  # will be activated in later rounds

        return result, conversions, serialisedTraderData
