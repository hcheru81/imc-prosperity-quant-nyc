import collections
import json
import math
import string
from typing import Any, List

import jsonpickle

from datamodel import (
    Listing,
    Observation,
    Order,
    OrderDepth,
    ProsperityEncoder,
    Symbol,
    Trade,
    TradingState,
    UserId,
)


class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(
        self,
        state: TradingState,
        orders: dict[Symbol, list[Order]],
        conversions: int,
        trader_data: str,
    ) -> None:
        base_length = len(
            self.to_json(
                [
                    self.compress_state(state, ""),
                    self.compress_orders(orders),
                    conversions,
                    "",
                    "",
                ]
            )
        )

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
        max_item_length = (self.max_log_length - base_length) // 3

        print(
            self.to_json(
                [
                    self.compress_state(
                        state, self.truncate(state.traderData, max_item_length)
                    ),
                    self.compress_orders(orders),
                    conversions,
                    self.truncate(trader_data, max_item_length),
                    self.truncate(self.logs, max_item_length),
                ]
            )
        )

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append(
                [listing["symbol"], listing["product"], listing["denomination"]]
            )

        return compressed

    def compress_order_depths(
        self, order_depths: dict[Symbol, OrderDepth]
    ) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append(
                    [
                        trade.symbol,
                        trade.price,
                        trade.quantity,
                        trade.buyer,
                        trade.seller,
                        trade.timestamp,
                    ]
                )

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sunlight,
                observation.humidity,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value

        return value[: max_length - 3] + "..."


logger = Logger()

POSITION_LIMITS = {"AMETHYSTS": 20, "STARFRUIT": 20, "ORCHIDS": 100}
STARFRUIT_COEFFICIENTS = [5.24986188, 0.70354115, 0.23410216, 0.04909509, 0.01222407]


class Trader:
    def __init__(self):
        self.previous_starfruit_prices = []
        self.previous_orchids_prices = []

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
        try:
            return (
                sum(price * volume for price, volume in orders.items()) / total_volume
            )
        except:
            return 0

    def update_price_history(
        self,
        previous_trading_state,
        state: TradingState,
        product: str,
        memory: int = 4,
    ):
        previous_prices_key = f"previous_{product.lower()}_prices"
        previous_prices = previous_trading_state.get(previous_prices_key, [])

        orders = state.order_depths.get(product, OrderDepth())
        sell_orders = orders.sell_orders
        buy_orders = orders.buy_orders

        if sell_orders and buy_orders:
            sell_vwap = self.vwap(sell_orders)
            buy_vwap = self.vwap(buy_orders)
            current_vwap = (sell_vwap + buy_vwap) / 2
            previous_prices.append(current_vwap)
            previous_prices = previous_prices[-memory:]  # Only cache last 4 ticks

        # Update the state with the new price history
        setattr(self, previous_prices_key, previous_prices)

    def calculate_acceptable_price(self, product) -> int:
        if product == "AMETHYSTS":
            return 10000

        if product == "STARFRUIT":
            if len(self.previous_starfruit_prices) >= len(STARFRUIT_COEFFICIENTS) - 1:
                expected_price = STARFRUIT_COEFFICIENTS[0] + sum(
                    STARFRUIT_COEFFICIENTS[i + 1] * self.previous_starfruit_prices[i]
                    for i in range(len(STARFRUIT_COEFFICIENTS) - 1)
                )
                return int(expected_price)
            else:
                return 0  # Not enough data to calculate price

        if product == "ORCHIDS":
            if len(self.previous_orchids_prices) >= 1:
                return int(self.previous_orchids_prices[-1])

        return 0

    # def orchid_trading_decision(self, state: TradingState) -> float:
    #     if not self.previous_orchids_prices:
    #         return 0
    #     prev_orchids = self.previous_orchids_prices[-1]
    #     sunlight = state.observations.conversionObservations["ORCHIDS"].sunlight
    #     humidity = state.observations.conversionObservations["ORCHIDS"].humidity
    #     transport_fees = state.observations.conversionObservations[
    #         "ORCHIDS"
    #     ].transportFees
    #     export_tariff = state.observations.conversionObservations[
    #         "ORCHIDS"
    #     ].exportTariff

    #     # print(
    #     #     f"prev o: {prev_orchids}, sunlight: {sunlight}, humidity: {humidity}, export_tariff: {export_tariff}"
    #     # )

    #     if sunlight <= 2481.92:
    #         if humidity <= 92.12:
    #             return 0  # class: 0
    #         else:
    #             return 0  # class: 0
    #     else:
    #         if humidity <= 68.17:
    #             return 1  # class: 1
    #         else:
    #             return 0  # class: 0

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

        best_bid = sorted_buy_orders[0][0]
        best_ask = sorted_sell_orders[0][0]

        mid_price_floor = math.floor(acceptable_price)
        mid_price_ceil = math.ceil(acceptable_price)

        position_limit = POSITION_LIMITS.get(product, 20)
        buy_pos = position

        HALF_LIMIT = POSITION_LIMITS.get(product) // 2

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
                s1, s2 = 0, 0
                # try to get back to neutral at a good price
                target = min(mid_price_floor + s1, best_bid + s2)
                neutralzing_quantity = abs(buy_pos)
                buy_pos += neutralzing_quantity
                orders.append(Order(product, target, neutralzing_quantity))  # limit buy
            if 0 <= buy_pos and buy_pos <= HALF_LIMIT:
                s1, s2 = -2, 1
                target = min(mid_price_floor + s1, best_bid + s2)
                neutralzing_quantity = (
                    -buy_pos + HALF_LIMIT
                )  # get holding up to half shares
                buy_pos += neutralzing_quantity
                orders.append(Order(product, target, neutralzing_quantity))  # limit buy
            if buy_pos >= HALF_LIMIT:
                s1, s2 = -1, 1
                target = min(mid_price_floor + s1, best_bid + s2)
                neutralzing_quantity = position_limit - buy_pos
                buy_pos += neutralzing_quantity
                orders.append(Order(product, target, neutralzing_quantity))  # limit buy

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
                s1, s2 = 0, 0
                target = max(mid_price_ceil + s1, best_ask + s2)
                neutralzing_quantity = -sell_pos
                sell_pos += neutralzing_quantity
                orders.append(Order(product, target, neutralzing_quantity))
            if sell_pos <= 0 and sell_pos >= -HALF_LIMIT:  # SAFE
                s1, s2 = 2, -1
                target = max(mid_price_ceil + s1, best_ask + s2)
                neutralzing_quantity = -sell_pos - HALF_LIMIT
                sell_pos += neutralzing_quantity
                orders.append(Order(product, target, neutralzing_quantity))
            if sell_pos <= -HALF_LIMIT:
                s1, s2 = 2, -2
                target = max(mid_price_ceil + s1, best_ask + s2)
                neutralzing_quantity = -position_limit - sell_pos
                sell_pos += neutralzing_quantity
                orders.append(Order(product, target, neutralzing_quantity))
        return orders

    def generate_orchid_orders(
        self, state: TradingState, orchid_signal, acceptable_price
    ):

        orders: List[Order] = []
        orchid_depth = state.order_depths.get("ORCHIDS", OrderDepth())

        sorted_sell_orders = sorted(
            list(orchid_depth.sell_orders.items()), key=lambda x: x[0]
        )

        sorted_buy_orders = sorted(
            list(orchid_depth.buy_orders.items()),
            key=lambda x: x[0],
            reverse=True,
        )

        best_bid = sorted_buy_orders[0][0]
        best_ask = sorted_sell_orders[0][0]

        mid_price_floor = math.floor(acceptable_price)
        mid_price_ceil = math.ceil(acceptable_price)

        position_limit = POSITION_LIMITS.get("ORCHIDS", 100)
        buy_pos = state.position.get("ORCHIDS", 0)

    def run(self, state: TradingState):
        previous_state_data = self.deserialize_trader_data(state.traderData)
        self.update_price_history(
            previous_state_data,
            state,
            "STARFRUIT",
            memory=4,
        )
        self.update_price_history(previous_state_data, state, "ORCHIDS", 4)

        result = {}

        for product, order_depth in state.order_depths.items():
            acceptable_price = self.calculate_acceptable_price(product)
            if product in ["AMETHYSTS", "STARFRUIT"]:
                orders = self.generate_orders(
                    product,
                    state.position.get(product, 0),
                    acceptable_price,
                    order_depth,
                )
                result[product] = orders
            elif product == "ORCHIDS":
                orchid_signal = self.orchid_trading_decision(state)
                logger.print(
                    f"product: {product}, acceptable_price, {acceptable_price}, orchid_signal: {orchid_signal}"
                )
                orchid_bid = state.observations.conversionObservations[
                    "ORCHIDS"
                ].bidPrice
                orchid_ask = state.observations.conversionObservations[
                    "ORCHIDS"
                ].askPrice
                logger.print(f"orchid_bid: {orchid_bid}, orchid_ask: {orchid_ask}")
                orders = self.generate_orchid_orders(
                    state, orchid_signal, acceptable_price
                )
                result[product] = orders

        trader_data = {
            "previous_starfruit_prices": self.previous_starfruit_prices,
            "previous_orchids_prices": self.previous_orchids_prices,
        }
        conversions = 0

        serialized_trader_data = self.serialize_trader_data(trader_data)

        logger.flush(state, result, conversions, serialized_trader_data)

        return result, conversions, serialized_trader_data
