import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib

# -------------------------------
# 1. Load and Prepare the Dataset
# -------------------------------
data = pd.read_csv(r'C:\Users\Asus\Downloads\USA_Housing.csv')

# Convert price to float (no need for clean_price if data is already numeric)
data['Price'] = data['Price'].astype(float)

# -------------------------------
# 2. Prepare Features and Target
# -------------------------------
X = data[['Avg. Area Income', 'Avg. Area House Age',
          'Avg. Area Number of Rooms', 'Avg. Area Number of Bedrooms',
          'Area Population']]

Y = data['Price']                 # Target

# -------------------------------
# 3. Split the Data
# -------------------------------
X_train, X_test, Y_train, Y_test = train_test_split(
    X, Y, test_size=0.3, random_state=42
)

# -------------------------------
# 4. Train the Model
# -------------------------------
model = LinearRegression()
model.fit(X_train, Y_train)

# Save model
joblib.dump(model, 'house_price_model.pkl')
print("✅ Model trained and saved successfully!")

# -------------------------------
# 5. Predict on Test Data
# -------------------------------
predictions = model.predict(X_test)

# Create a preview DataFrame
preview = pd.DataFrame({
    'Actual Price': Y_test.values,
    'Predicted Price': predictions
})
preview['Error'] = abs(preview['Actual Price'] - preview['Predicted Price'])

print("\n🔍 Sample Predictions:")
print(preview.head())

# -------------------------------
# 6. Evaluation Metrics
# -------------------------------
r2 = r2_score(Y_test, predictions)
mae = mean_absolute_error(Y_test, predictions)
mse = mean_squared_error(Y_test, predictions)
rmse = np.sqrt(mse)

print(f"\n📊 Model Evaluation Metrics:")
print(f"R² Score: {r2:.4f}")
print(f"Mean Absolute Error: Nrs{mae:,.2f}")
print(f"Mean Squared Error: Nrs{mse:,.2f}")
print(f"Root Mean Squared Error: Nrs{rmse:,.2f}")

# -------------------------------
# 7. Visualization
# -------------------------------
plt.figure(figsize=(8, 6))
plt.scatter(Y_test, predictions, alpha=0.6, color='teal')
plt.plot([Y_test.min(), Y_test.max()], [Y_test.min(), Y_test.max()], 'r--')
plt.xlabel('Actual Price')
plt.ylabel('Predicted Price')
plt.title('Actual vs Predicted Prices')
plt.grid(True)
plt.tight_layout()
plt.show()