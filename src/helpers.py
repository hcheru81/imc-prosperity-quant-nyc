import matplotlib.pyplot as plt


def print_attributes(obj, indent=0):
    print(
        "\n".join(
            [
                " " * indent
                + f"{attr}: {getattr(obj, attr) if not hasattr(getattr(obj, attr), '__dict__') else print_attributes(getattr(obj, attr), indent + 2)}"
                for attr in dir(obj)
                if not attr.startswith("__")
            ]
        )
    )


def plot_order_depths(order_depths):
    for product, depth in order_depths.items():
        # Extracting buy and sell orders into separate lists
        buy_prices, buy_volumes = zip(*sorted(depth.buy_orders.items()))
        sell_prices, sell_volumes = zip(*sorted(depth.sell_orders.items()))

        # Negate sell volumes for plotting
        sell_volumes = [-vol for vol in sell_volumes]

        # Plotting
        plt.figure(figsize=(10, 6))
        plt.bar(buy_prices, buy_volumes, color="green", width=0.5, label="Buy Orders")
        plt.bar(sell_prices, sell_volumes, color="red", width=0.5, label="Sell Orders")
        plt.xlabel("Price")
        plt.ylabel("Volume")
        plt.title(f"Order Depth for {product}")
        plt.legend()
        plt.grid(True)
        plt.show()
