import string
from typing import List

from datamodel import Order, OrderDepth, TradingState, UserId

FUDGE = {
    "STARFRUIT": {"b_obg": 0, "s_obg": 0},
    "AMETHYSTS": {"b_obg": 0, "s_obg": 0},
}

POSITION_LIMITS = {"AMETHYSTS": 20, "STARFRUIT": 20}


class Trader:

    def vwap(self, orders: dict) -> float:
        total_volume = sum(orders.values())
        if total_volume == 0:
            return 0
        return sum(price * volume for price, volume in orders.items()) / total_volume

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
        current_position_in_product: int,
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
        current_position_in_product = current_position_in_product

        sorted_sell_orders = sorted(
            list(order_depth.sell_orders.items()), key=lambda x: x[0]
        )

        sorted_buy_orders = sorted(
            list(order_depth.buy_orders.items()),
            key=lambda x: x[0],
            reverse=True,
        )

        if current_position_in_product == position_limit:  # we're at capacity
            pass

        else:  # were not at capacity
            buy_quantity = 0
            # Buying
            for ask, volume in sorted_sell_orders:
                # Place buy orders to match the most attractive sellers
                if ask < acceptable_price:
                    buy_quantity = abs(volume) + FUDGE[product]["s_obg"]
                    while current_position_in_product + buy_quantity >= position_limit:
                        buy_quantity -= 1
                    orders.append(Order(product, ask, buy_quantity))
                    current_position_in_product += buy_quantity

            sell_quantity = 0

            # Selling
            for bid, volume in sorted_buy_orders:
                # place sell orders to match the most attractive buyers
                if bid > acceptable_price:
                    sell_quantity = -(abs(volume + FUDGE[product]["b_obg"]))
                    while (
                        current_position_in_product + sell_quantity <= -position_limit
                    ):
                        sell_quantity += 1
                    orders.append(Order(product, bid, sell_quantity))
                    current_position_in_product += sell_quantity

            return orders

    def run(self, state: TradingState):
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

        traderData = "SAMPLE"
        conversions = 1

        return result, conversions, traderData
