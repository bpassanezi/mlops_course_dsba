# EDA functions have been merged into data_cleaning.py
# Use: from model.data_cleaning import run_eda, run_all_eda
from model.data_cleaning import run_all_eda, run_eda  # noqa: F401

if __name__ == "__main__":
    run_all_eda()

