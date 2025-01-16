import requests
from datetime import datetime
import json
import re
import os

def sign_in():
    # 从环境变量获取账号密码
    email = os.environ.get('CORDCLOUD_EMAIL')
    password = os.environ.get('CORDCLOUD_PASSWORD')
    
    if not email or not password:
        print("错误：未设置环境变量 CORDCLOUD_EMAIL 或 CORDCLOUD_PASSWORD")
        return False
    
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
    
    try:
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
        print(f"登录响应状态码: {login_response.status_code}")
        print(f"登录响应内容: {login_response.text}")
        
        if login_response.status_code != 200:
            raise Exception(f"登录失败，状态码：{login_response.status_code}")
        
        try:
            response_json = login_response.json()
            if 'ret' in response_json and response_json['ret'] != 1:
                raise Exception(f"登录失败：{response_json.get('msg', '未知错误')}")
        except json.JSONDecodeError:
            print("警告：响应不是JSON格式")
        
        # 获取用户页面，检查签到状态
        user_response = session.get(user_url, headers=headers)
        if "今日已签到" in user_response.text:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 今日已经签到过了")
            try:
                # 修复正则表达式
                match = re.search(r'上次签到时间：(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', user_response.text)
                if match:
                    print(f"上次签到时间: {match.group(1)}")
            except Exception as e:
                print(f"获取上次签到时间失败: {str(e)}")
            return True
            
        # 签到
        checkin_response = session.post(checkin_url, headers=headers)
        print(f"签到响应状态码: {checkin_response.status_code}")
        print(f"签到响应内容: {checkin_response.text}")
        
        # 记录日志
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if checkin_response.status_code == 200:
            try:
                checkin_json = checkin_response.json()
                if checkin_json.get('ret') == 1:
                    print(f"[{current_time}] 签到成功！")
                    return True
                else:
                    print(f"[{current_time}] 签到失败：{checkin_json.get('msg', '未知错误')}")
                    return False
            except json.JSONDecodeError:
                print(f"[{current_time}] 签到失败：响应格式错误")
                return False
        else:
            print(f"[{current_time}] 签到失败：HTTP状态码 {checkin_response.status_code}")
            return False
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 发生错误：{str(e)}")
        return False

if __name__ == "__main__":
    sign_in() 