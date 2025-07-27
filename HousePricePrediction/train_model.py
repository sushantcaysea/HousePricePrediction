import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

import joblib
from matplotlib.ticker import FuncFormatter

# 1. Load and Prepare the Dataset
def load_and_prepare_data(filepath):
    # Check file extension to determine how to read it
    if filepath.endswith('.csv'):
        data = pd.read_csv(filepath)
    elif filepath.endswith('.xlsx'):
        data = pd.read_excel(filepath)
    else:
        raise ValueError("Unsupported file format. Please provide a .csv or .xlsx file.")

    # Strip whitespace from column names to avoid KeyError
    data.columns = data.columns.str.strip()

    # Ensure prices and features are non-negative integers
    data['Price'] = data['Price'].fillna(0).round().astype(int)

    features = [
        'Avg. Area Income', 'Avg. Area House Age',
        'Avg. Area Number of Rooms',
        'Avg. Area Number of Bedrooms',
        'Area Population',
        'Build-up Area',
        'Land Area',
        'Floor'                # <-- Add this line
    ]
    # Fill missing values in features with 0 before rounding/converting
    data[features] = data[features].fillna(0).round().astype(int)

    # Drop rows with negative values (if any)
    data = data[(data[features] >= 0).all(axis=1)]
    data = data[data['Price'] >= 0]

    return data, features
# Update the file path to use forward slashes or raw string
filepath = r'C:\Users\Asus\OneDrive\Desktop\kathmandu\HousePricePrediction\HousePricePrediction\kathmandudataset.xlsx'
data, features = load_and_prepare_data(filepath)

# Rest of your code remains the same...
# 2. Split Features and Target
X = data[features]
y = data['Price']

# 3. Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

# Print min and max for each feature in training data
print("\nFeature min/max values in training data:")
for col in X_train.columns:
    print(f"{col}: min={X_train[col].min()}, max={X_train[col].max()}")

# 4. Train the Model with Non-Negative Constraints
model = LinearRegression(positive=True)  # Critical: Force coefficients ≥ 0
model.fit(X_train, y_train)

# Save model
joblib.dump(model, 'my_new_model.pkl')
print("✅ Model trained and saved successfully!")

# 5. Predict with Safeguards
def predict_price(model, input_data):
    """Ensure predictions are non-negative and handle edge cases."""
    if isinstance(input_data, (list, np.ndarray)):
        input_data = pd.DataFrame([input_data], columns=features)

    # Clamp inputs to training min/max
    for i, col in enumerate([
        'Avg. Area Income', 'Avg. Area House Age',
        'Avg. Area Number of Rooms', 'Avg. Area Number of Bedrooms',
        'Area Population', 'Build-up Area', 'Land Area', 'Floor'
    ]):
        min_val = X_train[col].min()
        max_val = X_train[col].max()
        if input_data[col] < min_val:
            input_data[col] = min_val
        elif input_data[col] > max_val:
            input_data[col] = max_val

    # Validate input ranges (warn if outside training data)
    for col in features:
        if (input_data[col].min() < X_train[col].min() or 
            input_data[col].max() > X_train[col].max()):
            print(f"⚠️ Warning: Input '{col}' is outside training range!")

    y_pred = model.predict(input_data)
    y_pred = np.round(np.maximum(y_pred, 0)).astype(int)  # Force ≥ 0 and integer
    return y_pred

# 6. Evaluate on Test Set
y_pred = predict_price(model, X_test)

# Sample predictions
preview = pd.DataFrame({
    'Actual Price (NPR)': y_test.values,
    'Predicted Price (NPR)': y_pred,
    'Error (NPR)': abs(y_test.values - y_pred)
})
print("\n🔍 Sample Predictions:")
print(preview.head())

# 7. Evaluation Metrics
r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)

print("\n📊 Evaluation Metrics:")
print(f"R² Score: {r2:.4f}")
print(f"Mean Absolute Error: NPR {mae:,.0f}")
print(f"Mean Squared Error: NPR {mse:,.0f}")
print(f"Root Mean Squared Error: NPR {rmse:,.0f}")

# 8. Visualization
plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, alpha=0.6, color='green', label='Predictions')
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 
         'r--', label='Perfect Prediction')
plt.xlabel('Actual Price (NPR)')
plt.ylabel('Predicted Price (NPR)')
plt.title('Actual vs Predicted House Prices (NPR)')
plt.legend()
plt.grid(True)

# Format axes as NPR
plt.ticklabel_format(style='plain', axis='both')
plt.gca().get_xaxis().set_major_formatter(
    FuncFormatter(lambda x, _: f'NPR {x:,.0f}'))
plt.gca().get_yaxis().set_major_formatter(
    FuncFormatter(lambda y, _: f'NPR {y:,.0f}'))

plt.tight_layout()
plt.show()