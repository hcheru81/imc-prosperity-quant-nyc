trader(state, t) -> action @ time=t

state.order_depths["STARFRUIT"].buy_orders = {20: 9, 21: 2}
state.order_depths["STARFRUIT"].sell_orders = {22: -5, 21: -2}


t=0: trader(state, 0), state.position = {}
t=1: trader(state, 1), state.position = {{"STARFRUIT": 1, "AMETHYSTS": -1}}
>> self.orders = []
>> self.position_limits = {"STARFRUIT": 20, "AMETHYSTS": 20}
>> self.current_position = {"STARFRUIT": 1, "AMETHYSTS": -1}

for product in products:
    for price, volume in floating_sell_orders:
        if price is good:
            if self.current_position[product] + volume <= self.position_limits[product]:
                orders.append(product, price, abs(volume)) # BUY ORDER
                self.current_positions[product] += volume
            else:
                break # go to next product because this one is saturated

    for price, volume in floating_buy_orders:
        if price is good:
            orders.append(product, price, -abs(volume)) # BUY ORDER



