from typing import List

import jsonpickle

from datamodel import Order, OrderDepth, Trade, TradingState


class Trader:
    def __init__(self):
        self.history = {}

    def update_history(self, trades: List[Trade], product: str):
        if product not in self.history:
            self.history[product] = []
        self.history[product].extend(trades)

    def get_average_price(self, trades: List[Trade]):
        if not trades:
            return None
        total = sum(trade.price * trade.quantity for trade in trades)
        quantity = sum(trade.quantity for trade in trades)
        return total / quantity if quantity else None

    def run(self, state: TradingState):
        result = {}
        conversions = 0  # Assuming no conversion logic for simplicity

        for product, order_depth in state.order_depths.items():
            self.update_history(state.market_trades.get(product, []), product)

            average_price = self.get_average_price(self.history.get(product, []))
            if average_price is None:
                continue

            best_ask = min(order_depth.sell_orders) if order_depth.sell_orders else None
            best_bid = max(order_depth.buy_orders) if order_depth.buy_orders else None

            orders = []
            position = state.position.get(product, 0)
            position_limit = 20  # Assume a position limit; replace with actual limit

            # Buy logic
            if (
                best_ask
                and best_ask < average_price * 0.95
                and position < position_limit
            ):
                quantity_to_buy = min(
                    order_depth.sell_orders[best_ask], position_limit - position
                )
                orders.append(Order(product, best_ask, quantity_to_buy))

            # Sell logic
            if (
                best_bid
                and best_bid > average_price * 1.05
                and position > -position_limit
            ):
                quantity_to_sell = min(
                    order_depth.buy_orders[best_bid], position_limit + position
                )
                orders.append(Order(product, best_bid, -quantity_to_sell))

            result[product] = orders

        traderData = jsonpickle.encode(
            self.history
        )  # Serialize history for next iteration

        return result, conversions, traderData
