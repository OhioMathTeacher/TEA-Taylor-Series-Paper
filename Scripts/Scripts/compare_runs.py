import pandas as pd

# Load both runs
run1 = pd.read_csv("out_rows-run1/rows.csv")
run2 = pd.read_csv("out_rows/rows.csv")

def split_row(df):
    """Split LaTeX row into individual columns."""
    parts = df["row"].str.rstrip("\\").str.split("&")
    for i, name in enumerate(["Student", "AI Words", "Student Words", "Total", "% AI", "% Student"]):
        df[name] = parts.str[i].str.strip()
    # Convert numeric cols where possible
    for col in ["AI Words", "Student Words", "Total", "% AI", "% Student"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

run1 = split_row(run1.copy())
run2 = split_row(run2.copy())

# Merge on filename
merged = run1.merge(run2, on="filename", suffixes=("_run1", "_run2"), how="outer")

# Calculate deltas for numeric columns
for col in ["AI Words", "Student Words", "Total", "% AI", "% Student"]:
    merged[f"Δ {col}"] = merged[f"{col}_run2"] - merged[f"{col}_run1"]

# Sort by absolute % Student difference
merged = merged.sort_values(by="Δ % Student", key=lambda s: s.abs(), ascending=False)

# Save full comparison
out_file = "compare_report.csv"
merged.to_csv(out_file, index=False)
print(f"Comparison written to {out_file}")

# Show top 10 biggest % Student differences in console
print("\nTop 10 biggest % Student differences:")
print(merged[["filename", "% Student_run1", "% Student_run2", "Δ % Student"]].head(10))
