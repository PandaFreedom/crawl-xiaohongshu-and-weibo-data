import requests

# 发送请求，模拟浏览器
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# 发送请求到小红书页面
response = requests.get("https://www.xiaohongshu.com", headers=headers)

# 获取并打印 cookies
cookies = response.cookies
print(cookies)
