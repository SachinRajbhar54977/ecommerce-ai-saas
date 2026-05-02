import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

from imblearn.over_sampling import SMOTE

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv("customers.csv")

print("Shape:", df.shape)

# -----------------------------
# TARGET VARIABLE
# -----------------------------
target = "churned"

# -----------------------------
# DROP USELESS COLUMNS
# -----------------------------
drop_cols = ["customer_id", "registration_date"]
df = df.drop(columns=[col for col in drop_cols if col in df.columns])

# -----------------------------
# HANDLE CATEGORICAL FEATURES
# -----------------------------
label_encoders = {}

cat_cols = df.select_dtypes(include="object").columns

for col in cat_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    label_encoders[col] = le

# -----------------------------
# SPLIT FEATURES AND TARGET
# -----------------------------
X = df.drop(target, axis=1)
y = df[target]

feature_names = X.columns.tolist()

# -----------------------------
# TRAIN TEST SPLIT
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# -----------------------------
# HANDLE IMBALANCED DATA WITH SMOTE
# -----------------------------
smote = SMOTE(random_state=42)

X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)

print("Before SMOTE:")
print(y_train.value_counts())

print("\nAfter SMOTE:")
print(y_train_resampled.value_counts())

# -----------------------------
# TRAIN MODEL
# -----------------------------
model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    class_weight="balanced",
    random_state=42
)

model.fit(X_train_resampled, y_train_resampled)

# -----------------------------
# EVALUATION
# -----------------------------
y_proba = model.predict_proba(X_test)[:, 1]

threshold = 0.30
y_pred = (y_proba >= threshold).astype(int)
y_proba = model.predict_proba(X_test)[:, 1]

def risk_category(p):
    if p < 0.3:
        return "Low Risk"
    elif p < 0.7:
        return "Medium Risk"
    else:
        return "High Risk"

risk_levels = pd.Series(y_proba).apply(risk_category)

print("\nThreshold:", threshold)
print("\nAccuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nAccuracy:", accuracy_score(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# -----------------------------
# FEATURE IMPORTANCE
# -----------------------------
feature_importance = pd.Series(
    model.feature_importances_,
    index=feature_names
).sort_values(ascending=False)

print("\nTop Important Features:")
print(feature_importance.head(10))

plt.figure(figsize=(10, 6))
feature_importance.head(10).sort_values().plot(kind="barh")
plt.title("Top Features for Churn Prediction")
plt.xlabel("Importance Score")
plt.tight_layout()
plt.savefig("feature_importance.png")
print("\nFeature importance chart saved as feature_importance.png")

# -----------------------------
# SAVE MODEL FILES
# -----------------------------
joblib.dump(model, "churn_model.pkl")
joblib.dump(label_encoders, "label_encoders.pkl")
joblib.dump(feature_names, "feature_names.pkl")

print("\nModel saved successfully!")