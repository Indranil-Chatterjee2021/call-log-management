# Helper Function to convert records to DataFrame
from attrs import asdict, has as is_attrs
import dataclasses
import pandas as pd


def df_from_records(records: list, keep_uid: bool = False, is_master: bool = False) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    
    # 1. Improved Conversion (Handles attrs, dataclasses, and custom objects)
    processed_records = []
    for r in records:
        if is_attrs(r.__class__):
            processed_records.append(asdict(r))
        elif dataclasses.is_dataclass(r):
            processed_records.append(dataclasses.asdict(r))
        elif hasattr(r, 'to_dict'):
            processed_records.append(r.to_dict())
        elif hasattr(r, '__dict__'):
            processed_records.append(r.__dict__)
        else:
            processed_records.append(r) # Assume it's already a dict
    
    df = pd.DataFrame.from_records(processed_records)
    
    # 2. Setup exclusion list
    cols_to_drop = ['id', '_id', 'created_at']
    if is_master:
        cols_to_drop.extend(['created_by', 'updated_at', 'updated_by'])
        
    if not keep_uid:
        cols_to_drop.append('uid')

    df = df.drop(columns=cols_to_drop, errors='ignore')
    
    # 3. Format Date columns
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

    # 4. Capitalize Column Names
    new_cols = []
    for c in df.columns:
        if c == 'uid':
            new_cols.append('uid') # Keep lowercase for backend logic
        elif is_master and c == 'mobile':
            new_cols.append('mobile') # Keep lowercase for backend logic
        elif c == 'name':
            new_cols.append('name') # Keep lowercase for backend logic        
        else:
            new_cols.append(c.replace('_', ' ').title())

    df.columns = new_cols               
    return df
