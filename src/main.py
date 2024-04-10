from typing import List

from datamodel import Listing, Order, OrderDepth, Trade, TradingState


class Trader:

    def run(self, state: TradingState):
        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            acceptable_price = 10
            # Participant should calculate this value
            print("Acceptable price : " + str(acceptable_price))
            print(
                "Buy Order depth : "
                + str(len(order_depth.buy_orders))
                + ", Sell order depth : "
                + str(len(order_depth.sell_orders))
            )

            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                if int(best_ask) < acceptable_price:
                    print("BUY", str(-best_ask_amount) + "x", best_ask)
                    orders.append(Order(product, best_ask, -best_ask_amount))

            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                if int(best_bid) > acceptable_price:
                    print("SELL", str(best_bid_amount) + "x", best_bid)
                    orders.append(Order(product, best_bid, -best_bid_amount))

            result[product] = orders

        traderData = "SAMPLE"  # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.

        conversions = 1
        return result, conversions, traderData


def main():

    state = TradingState(
        traderData="",
        timestamp=1000,
        listings={
            "PRODUCT1": Listing(
                symbol="PRODUCT1", product="PRODUCT1", denomination="SEASHELLS"
            ),
            "PRODUCT2": Listing(
                symbol="PRODUCT2", product="PRODUCT2", denomination="SEASHELLS"
            ),
        },
        order_depths={
            "PRODUCT1": OrderDepth(
                buy_orders={10: 7, 9: 5}, sell_orders={11: -4, 12: -8}
            ),
            "PRODUCT2": OrderDepth(
                buy_orders={142: 3, 141: 5}, sell_orders={144: -5, 145: -8}
            ),
        },
        own_trades={"PRODUCT1": [], "PRODUCT2": []},
        market_trades={
            "PRODUCT1": [
                Trade(
                    symbol="PRODUCT1",
                    price=11,
                    quantity=4,
                    buyer="",
                    seller="",
                    timestamp=900,
                )
            ],
            "PRODUCT2": [],
        },
        position={"PRODUCT1": 3, "PRODUCT2": -5},
        observations={},
    )

    trader = Trader()
    trader.run(state)


if __name__ == "__main__":
    main()
