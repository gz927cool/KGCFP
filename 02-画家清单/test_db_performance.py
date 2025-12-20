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
            "headers": {} # 有些旧服务器不喜欢现代 User-Agent
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
                # 如果是 403，尝试下一个策略（可能是 UA 问题）
                last_error = f"⚠️ {status} Forbidden"
                continue 
            elif status == 404:
                return "❌ 404 Not Found", duration, "链接失效", False
            else:
                last_error = f"⚠️ {status}"
                continue

        except requests.exceptions.SSLError:
            last_error = "SSL错误"
            # SSL 错误会自动尝试下一个策略（包含 verify=False）
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

    # 如果所有策略都失败，返回最后一次的错误
    return f"❌ {last_error}", 0, "多次尝试失败", False

def test_database_performance():
    # 设置路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    input_file = os.path.join(project_root, '01-基础资源清单', '数据库清单.csv')
    output_file = os.path.join(base_dir, '数据库访问性能测试报告.md')
    
    search_topic = "中国古代画家"
    print(f"正在读取资源列表: {input_file}")
    print(f"测试主题: {search_topic}")
    print("采用多策略重试机制 (标准 -> 忽略SSL -> 长超时 -> 无UA)...")

    results = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None) 
            
            rows = list(reader)
            total = len(rows)
            print(f"共发现 {total} 个资源，开始测试...")

            for index, row in enumerate(rows):
                if len(row) < 3: continue
                
                db_name = row[1].strip()
                url = row[2].strip()
                
                print(f"[{index+1}/{total}] 测试: {db_name}...", end="", flush=True)
                
                if not url.startswith('http'):
                    results.append(f"| {db_name} | {url} | ❌ 无效URL | - | - |")
                    print(" 跳过 (无效URL)")
                    continue

                status_icon, duration, note, success = check_url_with_strategies(url, db_name)
                
                duration_str = f"{duration:.0f} ms" if duration > 0 else "-"
                results.append(f"| {db_name} | {url} | {status_icon} | {duration_str} | {note} |")
                
                print(f" {status_icon} ({duration_str})")

    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
        return

    # 生成报告
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# 数据库访问性能测试报告 (增强版)\n\n")
        f.write(f"**测试时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**测试策略**: 针对连接失败的资源，脚本自动尝试了忽略SSL证书、延长超时时间(20s)、更换User-Agent等多种方式。\n\n")
        f.write("| 资源名称 | URL | 状态 | 响应时间 | 备注 |\n")
        f.write("|---|---|---|---|---|\n")
        for line in results:
            f.write(line + "\n")

    print(f"\n测试结束。报告已生成: {output_file}")

if __name__ == "__main__":
    test_database_performance()
