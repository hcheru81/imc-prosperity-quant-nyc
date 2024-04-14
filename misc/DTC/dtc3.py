import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor, export_text

# Load and prepare the data
data = pd.read_csv("round2-data-bottle/prices_round_2_day_-1.csv", delimiter=";")

# Generating lagged features
lags = 4
for col in [
    "ORCHIDS",
    "SUNLIGHT",
    "HUMIDITY",
    "TRANSPORT_FEES",
    "EXPORT_TARIFF",
    "IMPORT_TARIFF",
]:
    for lag in range(1, lags + 1):
        data[f"{col}_lag_{lag}"] = data[col].shift(lag)

# Calculate the PriceChange as the target variable
data["NextDayOrchids"] = data["ORCHIDS"].shift(-1)
data["PriceChange"] = data["NextDayOrchids"] - data["ORCHIDS"]

# Drop rows with NaN values resulting from shifts
data.dropna(inplace=True)

# Define features and target
features = [
    f"{col}_lag_{lag}"
    for col in [
        "ORCHIDS",
        "SUNLIGHT",
        "HUMIDITY",
        "TRANSPORT_FEES",
        "EXPORT_TARIFF",
        "IMPORT_TARIFF",
    ]
    for lag in range(1, lags + 1)
]
X = data[features]
y = data["PriceChange"]

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Initialize and train the Decision Tree Regressor
model = DecisionTreeRegressor(max_depth=5)
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Mean Squared Error (MSE): {mse:.2f}")
print(f"Mean Absolute Error (MAE): {mae:.2f}")
print(f"R-squared (R2): {r2:.2f}")

# Extract rules
rule_text = export_text(model, feature_names=features)
print("Decision Rules from Decision Tree:")
print(rule_text)


# Simulate trading
capital = 1000
current_holdings = 0
transaction_costs = 0

for index, row in data.iterrows():
    row_df = pd.DataFrame([row[features]], columns=features)
    predicted_change = model.predict(row_df)[0]

    target_holdings = 100 if predicted_change > 0 else -100
    change_in_holdings = target_holdings - current_holdings
    capital -= abs(change_in_holdings) * transaction_costs
    current_holdings = target_holdings

    if index < len(data) - 1:
        capital += current_holdings * (
            data.iloc[index + 1]["ORCHIDS"] - data.iloc[index]["ORCHIDS"]
        )

print(f"Final capital after trading: {capital:.2f}")
