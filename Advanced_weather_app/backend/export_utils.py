import io
import pandas as pd

def records_to_dataframe(records):
    rows = [r.to_dict() for r in records]
    return pd.DataFrame(rows)

def to_csv_bytes(records):
    df = records_to_dataframe(records)
    return df.to_csv(index=False).encode("utf-8")

def to_json_bytes(records):
    df = records_to_dataframe(records)
    return df.to_json(orient="records", indent=2).encode("utf-8")

def to_md_bytes(records):
    df = records_to_dataframe(records)
    return df.to_markdown(index=False).encode("utf-8")
