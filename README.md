# Feishu Document Connector

## Installation

```bash
pip install feishuconnector
```

## Code Usage

```python
from feishuconnector import FeishuConnector

fc = FeishuConnector()
fc.init("user***", "pass***")
```

## Actual Usage Process

On the edit page of the Bitable, the URL is generally like this: `https://puyuan.feishu.cn/wiki/wikcnlBvPJ8xoTSfVtQwGBkrUWc?table=tblGZPQYMzrwRMeo&view=vewWhDJdAM`. Note to extract `node_token=wikcnlBvPJ8xoTSfVtQwGBkrUWc` and `table_id=tblGZPQYMzrwRMeo`.

## API Usage

```python
from feishuconnector import FeishuConnector

fc = FeishuConnector()
fc.init("user***", "pass***")

# Get all records from the Bitable
records = fc.get_bitable_records('wikcnlBvPJ8xoTSfVtQwGBkrUWc', 'tblGZPQYMzrwRMeo')

# Insert records into the Bitable
fc.insert_bitable_records('wikcnlBvPJ8xoTSfVtQwGBkrUWc', 'tblGZPQYMzrwRMeo', records)

# Get all data in a specific range of a standard spreadsheet, values is a list(rows) of list(cols)
values = fc.get_sheet_data("wikcnQgBgZCWUx7w6ZpzzLXX3bc", "e792af")

# Append data to a standard spreadsheet
fc.append_sheet_data("wikcnQgBgZCWUx7w6ZpzzLXX3bc", "e792af", values)
```
