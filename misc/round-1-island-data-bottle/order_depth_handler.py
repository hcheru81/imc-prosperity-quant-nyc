import csv


def parse_order_depths(csv_file):
    order_depths = {}
    with open(csv_file, "r") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            product = row["product"]
            if product not in order_depths:
                order_depths[product] = {"buy_orders": {}, "sell_orders": {}}

            for i in range(1, 4):
                bid_price = row.get(f"bid_price_{i}")
                ask_price = row.get(f"ask_price_{i}")
                bid_volume = row.get(f"bid_volume_{i}")
                ask_volume = row.get(f"ask_volume_{i}")

                if bid_price and bid_volume:
                    order_depths[product]["buy_orders"][float(bid_price)] = int(
                        bid_volume
                    )
                if ask_price and ask_volume:
                    order_depths[product]["sell_orders"][float(ask_price)] = -int(
                        ask_volume
                    )

    return order_depths


# order_depths = parse_order_depths(
#     "round-1-island-data-bottle/prices_round_1_day_-1.csv"
# )
# print(order_depths)
