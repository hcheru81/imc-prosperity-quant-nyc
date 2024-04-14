Harshil & Armaan: WTF are conversions?
    1. We are the NORTH island.
    2. ORCHIDS can be traded with the SOUTH island.
    3. OrderDepth shows us spread for ORCHIDS in the NORTH.
    4. orchid_ask = conversionObservations["ORCHIDS"].[ask/bid]Price shows us the bid/ask in the SOUTH!
    5. Humzah adjusts the BID and ASK like so:
        south_adjusted_bid = south_bid - obs.exportTariff - obs.transportFees
        south_adjusted_ask = south_ask + obs.importTariff + obs.transportFees (BUYER pays import/export tarrifs)
    6. 


Summarizing trading microstructure of ORCHIDs:
1.	ConversionObservation (https://imc-prosperity.notion.site/Writing-an-Algorithm-in-Python-658e233a26e24510bfccf0b1df647858#44efb36257b94733887ae00f46a805f1) shows quotes of ORCHID offered by the ducks from South Archipelago
2.	If you want to purchase 1 unit of ORCHID from the south, you will purchase at the askPrice, pay the TRANSPORT_FEES, IMPORT_TARIFF 
3.	If you want to sell 1 unit of ORCHID to the south, you will sell at the bidPrice, pay the TRANSPORT_FEES, EXPORT_TARIFF
4.	You can ONLY trade with the south via the conversion request with applicable conditions as mentioned in the wiki
5.	For every 1 unit of ORCHID net long position you hold, you will pay 0.1 Seashells per timestamp you hold that position. No storage cost applicable to net short position
6.	Negative ImportTariff would mean you would receive premium for importing ORCHIDs to your island
7.	Each Day in ORCHID trading is equivalent to 12 hours on the island. You can assume the ORCHID quality doesn’t deteriorate overnight
8.	Sunlight unit: Average sunlight per hour is 2500 units. The data/plot shows instantaneous rate of sunlight on any moment of the day