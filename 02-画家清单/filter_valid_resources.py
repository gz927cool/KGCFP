import csv
import time
import requests
import os
import warnings
from urllib.parse import urlparse

# 忽略 SSL 警告
warnings.filterwarnings("ignore")

def check_url_with_strategies(url, db_name):
    """
    尝试多种策略连接 URL
    返回: (status_icon, duration, note, success)
    """
    strategies = [
        {
            "name": "标准连接",
            "verify": True,
            "timeout": 10,
            "headers": {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        },
        {
            "name": "忽略SSL证书",
            "verify": False,
            "timeout": 10,
            "headers": {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        },
        {
            "name": "更长超时(20s)",
            "verify": True,
            "timeout": 20,
            "headers": {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        },
        {
            "name": "无User-Agent",
            "verify": False,
            "timeout": 15,
            "headers": {} 
        }
    ]

    last_error = ""
    
    for strategy in strategies:
        try:
            start_time = time.time()
            response = requests.get(
                url, 
                headers=strategy["headers"], 
                timeout=strategy["timeout"], 
                verify=strategy["verify"]
            )
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            
            status = response.status_code
            
            if status == 200:
                note = "连接正常"
                if not strategy["verify"]:
                    note += " (忽略SSL)"
                return "✅ 200 OK", duration, note, True
            elif status in [403, 401]:
                last_error = f"⚠️ {status} Forbidden"
                continue 
            elif status == 404:
                return "❌ 404 Not Found", duration, "链接失效", False
            else:
                last_error = f"⚠️ {status}"
                continue

        except requests.exceptions.SSLError:
            last_error = "SSL错误"
            continue
        except requests.exceptions.Timeout:
            last_error = "超时"
            continue
        except requests.exceptions.ConnectionError:
            last_error = "连接失败"
            continue
        except Exception as e:
            last_error = f"错误: {str(e)[:20]}"
            continue

    return f"❌ {last_error}", 0, "多次尝试失败", False

def filter_valid_resources():
    # 设置路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    input_file = os.path.join(project_root, '01-基础资源清单', '数据库清单.csv')
    output_file = os.path.join(project_root, '01-基础资源清单', '数据库清单_有效.csv')
    
    print(f"正在读取资源列表: {input_file}")
    print("开始过滤无效连接...")

    valid_rows = []
    removed_count = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None) 
            if header:
                valid_rows.append(header)
            
            rows = list(reader)
            total = len(rows)

            for index, row in enumerate(rows):
                if len(row) < 3: continue
                
                db_name = row[1].strip()
                url = row[2].strip()
                
                print(f"[{index+1}/{total}] 检查: {db_name}...", end="", flush=True)
                
                if not url.startswith('http'):
                    print(" ❌ 跳过 (无效URL)")
                    removed_count += 1
                    continue

                status_icon, duration, note, success = check_url_with_strategies(url, db_name)
                
                if success:
                    valid_rows.append(row)
                    print(f" ✅ 保留")
                else:
                    print(f" ❌ 移除 ({note})")
                    removed_count += 1

    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
        return

    # 写入新文件
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(valid_rows)

    print(f"\n过滤完成。")
    print(f"- 原始总数: {total}")
    print(f"- 移除无效: {removed_count}")
    print(f"- 有效保留: {len(valid_rows) - 1}") # 减去表头
    print(f"- 新文件已生成: {output_file}")

if __name__ == "__main__":
    filter_valid_resources()
