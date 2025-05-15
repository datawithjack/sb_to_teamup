import pandas as pd

# 1. Read the JSON file
df = pd.read_json("converted.json")

# 2. (Optional) inspect the first few rows
print(df.head())

# 3. Save to CSV
output_path = "converted_events.csv"
df.to_csv(output_path, index=False)

print(f"Saved {len(df)} rows → {output_path}")