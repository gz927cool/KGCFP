import argparse
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional


def sanitize_filename(name: str) -> str:
    # Replace characters invalid on Windows file systems
    return re.sub(r'[\\/:*?\"<>|]', '_', name).strip() or 'table'


def ensure_out_dir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)


def detect_type(db_path: Path) -> str:
    suf = db_path.suffix.lower()
    if suf in {'.accdb', '.mdb'}:
        return 'access'
    if suf in {'.sqlite', '.sqlite3', '.db'}:
        return 'sqlite'
    return 'unknown'


def list_tables_sqlite(conn) -> List[str]:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    return [r[0] for r in cur.fetchall()]


def list_tables_access(conn) -> List[str]:
    cur = conn.cursor()
    tables = []
    for row in cur.tables(tableType='TABLE'):
        # row.table_name available across drivers
        tables.append(row.table_name)
    return sorted(tables)


def export_table_to_csv(cursor, query: str, out_file: Path, encoding: str = 'utf-8-sig') -> None:
    import csv

    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    with out_file.open('w', newline='', encoding=encoding) as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        while True:
            rows = cursor.fetchmany(1000)
            if not rows:
                break
            writer.writerows(rows)


def run_sqlite(db_path: Path, out_dir: Path, tables_filter: Optional[Iterable[str]], encoding: str) -> None:
    import sqlite3

    conn = sqlite3.connect(str(db_path))
    try:
        all_tables = list_tables_sqlite(conn)
        if tables_filter:
            targets = [t for t in all_tables if t in set(tables_filter)]
        else:
            targets = all_tables

        if not targets:
            print('No tables to export.')
            return

        cur = conn.cursor()
        for t in targets:
            safe = sanitize_filename(t)
            out_file = out_dir / f"{safe}.csv"
            print(f"Exporting table (SQLite): {t} -> {out_file}")
            export_table_to_csv(cur, f"SELECT * FROM \"{t}\"", out_file, encoding)
    finally:
        conn.close()


def run_access(db_path: Path, out_dir: Path, tables_filter: Optional[Iterable[str]], encoding: str) -> None:
    try:
        import pyodbc  # type: ignore
    except Exception:
        print('缺少依赖: 需要安装 pyodbc。\n安装示例: pip install pyodbc')
        raise

    # Driver note: requires Microsoft Access Database Engine installed on Windows
    # Common driver name includes both mdb & accdb patterns
    conn_str = (
        f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};"
    )
    try:
        conn = pyodbc.connect(conn_str)
    except pyodbc.Error:
        print('无法连接 Access 数据库。可能缺少 Microsoft Access Database Engine 驱动。')
        print('请安装 Microsoft Access Database Engine 2016 Redistributable（与 Office 位数一致），再重试。')
        raise

    try:
        all_tables = list_tables_access(conn)
        if tables_filter:
            targets = [t for t in all_tables if t in set(tables_filter)]
        else:
            targets = all_tables

        if not targets:
            print('No tables to export.')
            return

        cur = conn.cursor()
        for t in targets:
            safe = sanitize_filename(t)
            out_file = out_dir / f"{safe}.csv"
            print(f"Exporting table (Access): {t} -> {out_file}")
            # Square brackets cover names with spaces or non-ascii
            export_table_to_csv(cur, f"SELECT * FROM [{t}]", out_file, encoding)
    finally:
        conn.close()


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description='Export Access/SQLite database tables to CSV files.')
    p.add_argument('--db', required=True, help='Path to database file (.accdb/.mdb/.sqlite/.db)')
    p.add_argument('--out', default='exports', help='Output directory for CSV files (default: exports)')
    p.add_argument('--type', choices=['access', 'sqlite'], help='Force database type detection (optional)')
    p.add_argument('--tables', help='Comma-separated table names to export (default: all)')
    p.add_argument('--encoding', default='utf-8-sig', help='Output CSV encoding (default: utf-8-sig suitable for Excel)')

    args = p.parse_args(argv)

    db_path = Path(args.db).expanduser().resolve()
    if not db_path.exists():
        print(f"找不到数据库文件: {db_path}")
        return 2

    out_dir = Path(args.out).expanduser().resolve()
    ensure_out_dir(out_dir)

    tables_filter: Optional[List[str]] = None
    if args.tables:
        tables_filter = [t.strip() for t in args.tables.split(',') if t.strip()]

    db_type = args.type or detect_type(db_path)
    if db_type == 'access':
        run_access(db_path, out_dir, tables_filter, args.encoding)
    elif db_type == 'sqlite':
        run_sqlite(db_path, out_dir, tables_filter, args.encoding)
    else:
        print('无法自动识别数据库类型，请使用 --type 指定为 access 或 sqlite')
        return 3

    print(f"导出完成，CSV 文件保存在: {out_dir}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
