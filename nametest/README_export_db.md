# 数据库导出为 CSV（Access / SQLite）

本工具脚本 `nametest/export_db_to_csv.py` 可将 Access(.accdb/.mdb) 与 SQLite(.sqlite/.db) 的所有表导出为 CSV 文件（默认编码为 `utf-8-sig`，便于在 Windows Excel 打开）。

## 依赖
- Python 3.8+
- SQLite: 无额外依赖（标准库 sqlite3）
- Access: 需要 `pyodbc`，并在 Windows 上安装 Microsoft Access Database Engine（与 Office 位数一致，推荐 2016 版 Redistributable）。

安装依赖（仅 Access 需要 pyodbc）:

```bash
pip install -r nametest/requirements.txt
```

## 用法

- 自动识别类型（根据文件后缀）并导出所有表：

```bash
python nametest/export_db_to_csv.py --db "D:/data/YourDB.accdb" --out exports
```

- 指定数据库类型（无法识别或自定义情况）：

```bash
python nametest/export_db_to_csv.py --db "D:/data/YourDB.mdb" --type access --out exports
```

- 仅导出部分表（逗号分隔）：

```bash
python nametest/export_db_to_csv.py --db "D:/data/YourDB.accdb" --tables "Table1,Table2" --out exports
```

- 指定 CSV 编码（默认 `utf-8-sig`，Excel 友好）：

```bash
python nametest/export_db_to_csv.py --db "D:/data/YourDB.sqlite" --encoding "utf-8-sig"
```

导出完成后，CSV 文件将位于 `--out` 指定的目录（默认 `exports/`）。
