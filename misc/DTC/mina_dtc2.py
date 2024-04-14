import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text

data = pd.read_csv("round2-data-bottle/prices_round_2_day_1.csv", delimiter=";")

# Define a binary target: 1 if the price increased, 0 if it decreased or stayed the same
data["NextDayOrchids"] = data["ORCHIDS"].shift(-1)
data["PriceChange"] = (data["NextDayOrchids"] > data["ORCHIDS"]).astype(int)
data["Prev_ORCHIDS"] = data["ORCHIDS"].shift(1)  # Lagged feature

data.dropna(inplace=True)

features = [
    "Prev_ORCHIDS",
    "SUNLIGHT",
    "HUMIDITY",
    "TRANSPORT_FEES",
    "EXPORT_TARIFF",
    "IMPORT_TARIFF",
]
X = data[features]
y = data["PriceChange"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = DecisionTreeClassifier(max_depth=2)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"Accuracy: {accuracy:.2f}")
print("Classification Report:")
print(classification_report(y_test, y_pred))

# Extract and print rules
rule_text = export_text(model, feature_names=features)
print("Decision Rules from Decision Tree:")
print(rule_text)

# Simulate trading using the model's predictions
capital = 1000  # Initial capital
current_holdings = 0  # Initial holdings in Orchids
transaction_costs = 0  # Cost of buying/selling Orchids

for index, row in data.iterrows():
    row_df = pd.DataFrame([row[features]], columns=features)
    predicted_increase = model.predict(row_df)[0]  # Predict if price will increase

    # Decision logic for trading based on predicted price movement
    target_holdings = 100 if predicted_increase else -100

    change_in_holdings = target_holdings - current_holdings
    capital -= abs(change_in_holdings) * transaction_costs  # Subtract transaction costs
    current_holdings = target_holdings  # Update holdings

    # Update capital based on the next day's actual price change
    if index < len(data) - 1:
        capital += current_holdings * (
            data.iloc[index + 1]["ORCHIDS"] - row["ORCHIDS"]
        )  # Calculate PNL

print(f"Final capital after trading: {capital:.2f}")


# Simulate trading
capital = 1000  # Initial capital
current_holdings = 0  # Initial holdings in Orchids
transaction_costs = 0  # Cost of buying/selling Orchids

for index, row in data.iterrows():

    # Decision logic for trading based on predicted price change
    coin = np.random.randint(0, 2)
    if coin == 0:
        target_holdings = 100  # Buy more if price expected to rise
    else:
        target_holdings = -100  # Sell if price expected to fall

    change_in_holdings = target_holdings - current_holdings
    capital -= abs(change_in_holdings) * transaction_costs  # Subtract transaction costs
    current_holdings = target_holdings  # Update holdings

    # Update capital based on the next day's actual price change
    if index < len(data) - 1:
        capital += (
            current_holdings * row["PriceChange"]
        )  # Calculate PNL based on the change in price


print(f"Final capital after RANDOM trading: {capital:.2f}")


# Calculate the price change for trading simulation
data["PriceChange"] = data["ORCHIDS"].diff()  # Daily price change
data["TwoDayChange"] = data["ORCHIDS"].diff(periods=2)  # Two-day price change

# Drop any rows with NaN values resulting from the diff calculation
data.dropna(inplace=True)

# Initialize trading variables
capital = 1000  # Initial capital
current_holdings = 100  # Start with an initial holding of 100 ORCHIDS

for index, row in data.iterrows():
    # Decision logic for trading based on the trend over the last two days
    if row["TwoDayChange"] > 0:
        target_holdings = 100  # Maintain or increase holdings if the price has risen over the last two days
    else:
        target_holdings = -100  # Sell or go short if the price has fallen

    # Calculate the change in holdings and update capital
    change_in_holdings = target_holdings - current_holdings
    capital -= (
        abs(change_in_holdings) * 0
    )  # Assuming no transaction costs for simplicity

    # Update holdings
    current_holdings = target_holdings

    # Update capital based on the next day's actual price change
    if index < len(data) - 1:
        capital += current_holdings * data.iloc[index + 1]["PriceChange"]

print(f"Final capital after 2 day up down trading: {capital:.2f}")
