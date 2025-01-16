import requests
from datetime import datetime, timezone, timedelta
import json
import re
import os
from pathlib import Path

def save_log(content):
    try:
        # 确保logs目录存在
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        print(f"日志目录创建成功: {log_dir.absolute()}")
        
        # 按月份创建日志文件
        current_month = (datetime.now().astimezone(timezone(timedelta(hours=8)))).strftime("%Y-%m")
        log_file = log_dir / f"checkin-{current_month}.md"
        print(f"准备写入日志文件: {log_file.absolute()}")
        
        # 获取今天的日期作为标题
        beijing_time = datetime.now().astimezone(timezone(timedelta(hours=8)))
        today = beijing_time.strftime("%Y-%m-%d")
        current_time = beijing_time.strftime("%H:%M:%S")
        
        # 格式化日志内容
        log_content = f"""
## {today} {current_time}

<details>
<summary>签到详情</summary>

```

{content}
```

</details>

---
"""
        
        # 追加内容到日志文件
        with open(log_file, "a", encoding='utf-8') as f:
            f.write(log_content)
        print(f"日志写入成功")
        
        # 列出目录内容
        print("当前目录内容:")
        os.system("ls -la")
        print("\nlogs 目录内容:")
        os.system("ls -la logs/")
        
    except Exception as e:
        print(f"保存日志时发生错误: {str(e)}")
        raise

def sign_in():
    # 创建一个列表来收集输出信息
    output_lines = []
    
    def log_print(*args, **kwargs):
        # 同时打印到控制台和保存到列表
        line = " ".join(map(str, args))
        print(line, **kwargs)
        output_lines.append(line)
    
    try:
        log_print(f"开始执行签到任务: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 从环境变量获取账号密码
        email = os.environ.get('CORDCLOUD_EMAIL')
        password = os.environ.get('CORDCLOUD_PASSWORD')
        
        if not email or not password:
            log_print("错误：未设置环境变量 CORDCLOUD_EMAIL 或 CORDCLOUD_PASSWORD")
            save_log("\n".join(output_lines))
            return False
        
        log_print(f"使用账号 {email} 开始签到")
        
        # 登录URL和签到URL
        base_url = "https://cordc.net"
        login_url = f"{base_url}/auth/login"
        checkin_url = f"{base_url}/user/checkin"
        user_url = f"{base_url}/user"
        
        # 创建session保持登录状态
        session = requests.Session()
        
        # 设置请求头，模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': base_url,
            'Referer': base_url
        }
        
        # 先访问主页获取cookie
        session.get(base_url, headers=headers)
        
        # 登录数据
        login_data = {
            "email": email,
            "passwd": password,
            "remember_me": "week"
        }
        
        # 登录
        login_response = session.post(login_url, data=login_data, headers=headers)
        log_print(f"登录响应状态码: {login_response.status_code}")
        log_print(f"登录响应内容: {login_response.text}")
        
        if login_response.status_code != 200:
            raise Exception(f"登录失败，状态码：{login_response.status_code}")
        
        try:
            response_json = login_response.json()
            if 'ret' in response_json and response_json['ret'] != 1:
                raise Exception(f"登录失败：{response_json.get('msg', '未知错误')}")
        except json.JSONDecodeError:
            log_print("警告：响应不是JSON格式")
        
        # 获取用户页面，检查签到状态
        user_response = session.get(user_url, headers=headers)
        
        # 提取更多用户信息
        try:
            # 提取账号等级
            vip_match = re.search(r'<dd>(VIP \d+)</dd>', user_response.text)
            if vip_match:
                log_print(f"账号等级: {vip_match.group(1)}")
            
            # 提取等级到期时间
            vip_expire_match = re.search(r'等级到期时间\s*([\d-]+ [\d:]+)', user_response.text)
            if vip_expire_match:
                log_print(f"等级到期时间: {vip_expire_match.group(1)}")
            
            # 提取剩余流量
            traffic_match = re.search(r'剩余流量.*?<code.*?>(.*?)</code>', user_response.text)
            if traffic_match:
                log_print(f"当前剩余流量: {traffic_match.group(1)}")
            
            # 提取已用流量
            used_traffic_match = re.search(r'过去已用.*?<code.*?>(.*?)</code>', user_response.text)
            if used_traffic_match:
                log_print(f"已使用流量: {used_traffic_match.group(1)}")
            
            # 提取今日已用流量
            today_traffic_match = re.search(r'今日已用.*?<code.*?>(.*?)</code>', user_response.text)
            if today_traffic_match:
                log_print(f"今日已用流量: {today_traffic_match.group(1)}")
            
            # 提取账户有效期
            expire_match = re.search(r'账户有效时间：(.*?)(?=</div>)', user_response.text)
            if expire_match:
                log_print(f"账户有效期至: {expire_match.group(1)}")
            
            # 提取在线设备数
            online_match = re.search(r'在线设备数.*?<dd>(.*?)</dd>', user_response.text)
            if online_match:
                log_print(f"在线设备: {online_match.group(1)}")
            
            # 提取上次使用时间
            last_use_match = re.search(r'上次使用：([\d-]+ [\d:]+)', user_response.text)
            if last_use_match:
                log_print(f"上次使用时间: {last_use_match.group(1)}")
            
            # 提取端口速率
            speed_match = re.search(r'端口速率.*?<dd>(.*?)</dd>', user_response.text)
            if speed_match:
                log_print(f"端口速率: {speed_match.group(1)}")
            
        except Exception as e:
            log_print(f"提取用户信息时发生错误: {str(e)}")
        
        if "今日已签到" in user_response.text:
            log_print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 今日已经签到过了")
            try:
                match = re.search(r'上次签到时间：(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', user_response.text)
                if match:
                    log_print(f"上次签到时间: {match.group(1)}")
            except Exception as e:
                log_print(f"获取上次签到时间失败: {str(e)}")
            save_log("\n".join(output_lines))
            return True
            
        # 签到
        checkin_response = session.post(checkin_url, headers=headers)
        log_print(f"签到响应状态码: {checkin_response.status_code}")
        log_print(f"签到响应内容: {checkin_response.text}")
        
        # 记录日志
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if checkin_response.status_code == 200:
            try:
                checkin_json = checkin_response.json()
                if checkin_json.get('ret') == 1:
                    # 提取签到获得的流量
                    msg = checkin_json.get('msg', '')
                    traffic_match = re.search(r'获得了\s*([\d.]+\s*[KMGT]?B)', msg)
                    if traffic_match:
                        log_print(f"签到获得流量: {traffic_match.group(1)}")
                    log_print(f"[{current_time}] 签到成功！")
                    save_log("\n".join(output_lines))
                    return True
                else:
                    log_print(f"[{current_time}] 签到失败：{checkin_json.get('msg', '未知错误')}")
                    save_log("\n".join(output_lines))
                    return False
            except json.JSONDecodeError:
                log_print(f"[{current_time}] 签到失败：响应格式错误")
                save_log("\n".join(output_lines))
                return False
        else:
            log_print(f"[{current_time}] 签到失败：HTTP状态码 {checkin_response.status_code}")
            save_log("\n".join(output_lines))
            return False
            
    except Exception as e:
        log_print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 发生错误：{str(e)}")
        save_log("\n".join(output_lines))
        return False

    # 确保在函数结束前保存日志
    save_log("\n".join(output_lines))
    return True

if __name__ == "__main__":
    sign_in() 