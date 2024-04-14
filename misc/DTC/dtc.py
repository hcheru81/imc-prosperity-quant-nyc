import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor, export_text

# Load your data
data = pd.read_csv("round2-data-bottle/prices_round_2_day_-1.csv", delimiter=";")

# Calculate the change in Orchids price and set up the target variable
data["PriceChange"] = data["ORCHIDS"].diff().shift(-1)  # Predict next day's change

# Drop rows with NaN values immediately after creating 'PriceChange' to ensure alignment
data.dropna(subset=["PriceChange", "SUNLIGHT", "HUMIDITY", "ORCHIDS"], inplace=True)

# Prepare data (ensure 'ORCHIDS' lags to avoid look-ahead bias)
data["ORCHIDS_lag"] = data["ORCHIDS"].shift(1)
X = data[["SUNLIGHT", "HUMIDITY", "ORCHIDS_lag"]]  # Using lagged Orchids price
y = data["PriceChange"]

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Initialize and train the decision tree regressor
tree = DecisionTreeRegressor(max_depth=3)  # Limit depth for simpler rules
tree.fit(X_train, y_train)

# Extract rules from the trained decision tree
tree_rules = export_text(tree, feature_names=["SUNLIGHT", "HUMIDITY", "ORCHIDS_lag"])
print(tree_rules)

# Make predictions
y_pred = tree.predict(X_test)

# Calculate metrics
mse = mean_squared_error(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

# Print evaluation results
print(f"Mean Squared Error (MSE): {mse:.2f}")
print(f"Mean Absolute Error (MAE): {mae:.2f}")
print(f"R-squared (R2): {r2:.2f}")
