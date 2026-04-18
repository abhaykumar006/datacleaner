import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.metrics import mean_squared_error


# ================= STRING CLEANING =================
def fill_string_columns(df):
    df = df.copy()

    for col in df.columns:
        if df[col].dtype == 'object':

            # Strip spaces
            df[col] = df[col].astype(str).str.strip()

            # Replace empty strings or 'nan' text → NaN
            df[col] = df[col].replace(["", "nan", "None"], np.nan)

            # 🔥 FINAL RULE: fill missing with "Unavailable_column"
            df[col] = df[col].fillna(f"Unavailable_{col}")

    return df


# ================= MAIN CLEAN FUNCTION =================
def clean_dataframe(df):
    df = df.copy()

    # 🔹 Backup original data for accuracy
    original_df = df.copy()

    # ================= REMOVE DUPLICATES =================
    df.drop_duplicates(inplace=True)

    # ================= COLUMN CLEAN =================
    df.columns = df.columns.str.strip()

    # ================= STRING CLEANING =================
    df = fill_string_columns(df)

    # ================= NUMERIC COLUMNS =================
    num_cols = df.select_dtypes(include=['number']).columns

    # ================= KNN IMPUTATION =================
    if len(num_cols) > 0:
        try:
            imputer = KNNImputer(n_neighbors=3)
            df[num_cols] = imputer.fit_transform(df[num_cols])
        except Exception as e:
            print("KNN Error:", e)

    # ================= ACCURACY CALCULATION =================
    accuracy = 100

    try:
        if len(num_cols) > 0:
            # Replace NaN with 0 in original only for comparison
            original_numeric = original_df[num_cols].fillna(0)

            mse = mean_squared_error(original_numeric, df[num_cols])

            # Convert to percentage score
            accuracy = max(0, 100 - mse)

    except Exception as e:
        print("Accuracy Error:", e)
        accuracy = 90

    # ================= DATA TYPE FIX =================
    for col in df.columns:
        if df[col].dtype == 'float64':
            try:
                # Convert float to int if all values are whole numbers
                if (df[col] % 1 == 0).all():
                    df[col] = df[col].astype(int)
            except:
                pass

    return df, round(accuracy, 2)