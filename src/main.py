from datamodel import Listing, OrderDepth, Trade, TradingState
from helpers import print_attributes, plot_order_depths
from trader import Trader

timestamp = 1000

listings = {
    "STARFRUIT": Listing(
        symbol="STARFRUIT", product="STARFRUIT", denomination="SEASHELLS"
    ),
    "AMETHYSTS": Listing(
        symbol="AMETHYSTS", product="AMETHYSTS", denomination="SEASHELLS"
    ),
}

order_depths = {"STARFRUIT": OrderDepth(), "AMETHYSTS": OrderDepth()}

# Set the buy_orders and sell_orders explicitly

order_depths["STARFRUIT"].buy_orders = {20: 7, 9: 5}
order_depths["STARFRUIT"].sell_orders = {13: -8, 12: -4, 30: -10}
order_depths["AMETHYSTS"].buy_orders = {10004: 5, 10003: 3}
order_depths["AMETHYSTS"].sell_orders = {10000: -10, 10001: -3, 9995: -1}

# plot_order_depths(order_depths)

own_trades = {"STARFRUIT": [], "AMETHYSTS": []}

market_trades = {
    "STARFRUIT": [
        Trade(
            symbol="STARFRUIT",
            price=11,
            quantity=4,
            buyer="",
            seller="",
            timestamp=900,
        )
    ],
    "AMETHYSTS": [],
}

position = {"STARFRUIT": 0, "AMETHYSTS": 0}

observations = {}
traderData = ""

state = TradingState(
    traderData,
    timestamp,
    listings,
    order_depths,
    own_trades,
    market_trades,
    position,
    observations,
)
# print_attributes(state)

trader = Trader()
result, conversion, traderData = trader.run(state)

print("Result:")
print(result)
