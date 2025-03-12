import requests
import base64
import json
import pyaes
import binascii
import urllib.parse
import re
import os
import yaml
from datetime import datetime

def fetch_ss_nodes():
    """获取SS节点信息"""
    a = 'http://api.skrapp.net/api/serverlist'
    b = {
        'accept': '/',
        'accept-language': 'zh-Hans-CN;q=1, en-CN;q=0.9',
        'appversion': '1.3.1',
        'user-agent': 'SkrKK/1.3.1 (iPhone; iOS 13.5; Scale/2.00)',
        'content-type': 'application/x-www-form-urlencoded',
        'Cookie': 'PHPSESSID=fnffo1ivhvt0ouo6ebqn86a0d4'
    }
    c = {'data': '4265a9c353cd8624fd2bc7b5d75d2f18b1b5e66ccd37e2dfa628bcb8f73db2f14ba98bc6a1d8d0d1c7ff1ef0823b11264d0addaba2bd6a30bdefe06f4ba994ed'}
    d = b'65151f8d966bf596'
    e = b'88ca0f0ea1ecf975'

    def f(g, d, e):
        h = pyaes.AESModeOfOperationCBC(d, iv=e)
        i = b''.join(h.decrypt(g[j:j+16]) for j in range(0, len(g), 16))
        return i[:-i[-1]]

    j = requests.post(a, headers=b, data=c)
    ss_nodes = []

    if j.status_code == 200:
        k = j.text.strip()
        l = binascii.unhexlify(k)
        m = f(l, d, e)
        n = json.loads(m)
        for o in n['data']:
            p = f"aes-256-cfb:{o['password']}@{o['ip']}:{o['port']}"
            q = base64.b64encode(p.encode('utf-8')).decode('utf-8')
            r = f"ss://{q}#{o['title']}"
            ss_nodes.append(r)
    
    return ss_nodes

def parse_ss_url(ss_url):
    """解析SS URL并返回节点信息"""
    if not ss_url.startswith('ss://'):
        return None
    
    ss_data = ss_url[5:]
    
    if '#' in ss_data:
        encoded_data, tag = ss_data.split('#', 1)
        tag = urllib.parse.unquote(tag)
    else:
        encoded_data = ss_data
        tag = "Unnamed"
    
    try:
        padding_needed = len(encoded_data) % 4
        if padding_needed:
            encoded_data += '=' * (4 - padding_needed)
            
        decoded = base64.urlsafe_b64decode(encoded_data).decode('utf-8')
        
        method_pwd, host_port = decoded.split('@', 1)
        method, password = method_pwd.split(':', 1)
        host, port = host_port.split(':', 1)
        
        # 使用节点的地名作为名称
        location_match = re.search(r'([A-Z]{2})[,\s]*(.*)', tag)
        if location_match:
            country_code = location_match.group(1)
            location = location_match.group(2).strip() if location_match.group(2) else country_code
            node_name = f"{country_code}_{location.replace(' ', '_')}"
        else:
            node_name = tag.replace(' ', '_')
        
        # 确保名称干净且不含特殊字符
        node_name = re.sub(r'[^\w_-]', '', node_name)
        if not node_name:
            node_name = f"Node_{host.replace('.', '_')}"
            
        return {
            'method': method,
            'password': password,
            'server': host,
            'port': int(port),
            'name': node_name,
            'original_name': tag
        }
    except Exception as e:
        print(f"Error parsing SS URL: {e}")
        return None

def generate_improved_config(nodes_info):
    """生成配置文件内容，包含自动选择延迟最低节点的功能"""
    if not nodes_info:
        return "No valid SS nodes found"
    
    config = """[General]
loglevel = warning
dns-server = system, 8.8.8.8
skip-proxy = 127.0.0.1, 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 100.64.0.0/10, localhost, *.local
proxy-test-url = http://www.gstatic.com/generate_204
internet-test-url = http://www.gstatic.com/generate_204
test-timeout = 5

[Proxy]
"""
    
    for node in nodes_info:
        config += f'{node["name"]} = ss, {node["server"]}, {node["port"]}, encrypt-method={node["method"]}, password={node["password"]}\n'
    
    config += "\n[Proxy Group]\n"
    node_names = [node['name'] for node in nodes_info]
    
    config += "Auto = url-test, " + ", ".join(node_names) + ", url=http://www.gstatic.com/generate_204, interval=300, tolerance=100\n"
    config += "Manual = select, " + ", ".join(node_names) + "\n"
    config += "Proxy = select, Auto, Manual\n"
    
    config += "\n[Rule]\nFINAL,Proxy\n"
    
    return config

def generate_clash_config(nodes_info):
    """生成Clash配置文件内容"""
    if not nodes_info:
        return None
    
    clash_config = {
        "port": 7890,
        "socks-port": 7891,
        "allow-lan": True,
        "mode": "Rule",
        "log-level": "info",
        "external-controller": "127.0.0.1:9090",
        "proxies": [],
        "proxy-groups": [
            {
                "name": "Auto",
                "type": "url-test",
                "proxies": [],
                "url": "http://www.gstatic.com/generate_204",
                "interval": 300,
                "tolerance": 100
            },
            {
                "name": "Manual",
                "type": "select",
                "proxies": []
            },
            {
                "name": "PROXY",
                "type": "select",
                "proxies": ["Auto", "Manual"]
            }
        ],
        "rules": ["MATCH,PROXY"]
    }
    
    # 添加代理节点
    for node in nodes_info:
        proxy = {
            "name": node["name"],
            "type": "ss",
            "server": node["server"],
            "port": node["port"],
            "cipher": node["method"],
            "password": node["password"]
        }
        clash_config["proxies"].append(proxy)
        clash_config["proxy-groups"][0]["proxies"].append(node["name"])
        clash_config["proxy-groups"][1]["proxies"].append(node["name"])
    
    return yaml.dump(clash_config, allow_unicode=True, sort_keys=False)

def save_ss_nodes(ss_nodes):
    """保存原始SS节点到文件"""
    with open('public/ss_nodes.txt', 'w', encoding='utf-8') as f:
        for node in ss_nodes:
            f.write(f"{node}\n")

def save_config(config_content, clash_content):
    """保存配置文件内容"""
    with open('public/surfboard.conf', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    with open('public/clash.yaml', 'w', encoding='utf-8') as f:
        f.write(clash_content)

def save_update_time():
    """保存更新时间"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('public/update_time.txt', 'w', encoding='utf-8') as f:
        f.write(now)

def create_index_html():
    """创建简单的HTML页面"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代理配置订阅</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            color: #2c3e50;
        }
        .container {
            background-color: #f9f9f9;
            border-radius: 5px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        code {
            background-color: #f1f1f1;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: monospace;
            word-break: break-all;
        }
        .update-time {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 10px;
        }
        .button {
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 10px 15px;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 15px;
        }
        .button:hover {
            background-color: #2980b9;
        }
        .tab {
            overflow: hidden;
            border: 1px solid #ccc;
            background-color: #f1f1f1;
            border-radius: 5px 5px 0 0;
        }
        .tab button {
            background-color: inherit;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 14px 16px;
            transition: 0.3s;
            font-size: 17px;
        }
        .tab button:hover {
            background-color: #ddd;
        }
        .tab button.active {
            background-color: #3498db;
            color: white;
        }
        .tabcontent {
            display: none;
            padding: 20px;
            border: 1px solid #ccc;
            border-top: none;
            border-radius: 0 0 5px 5px;
        }
    </style>
</head>
<body>
    <h1>代理配置订阅</h1>
    <div class="container">
        <div class="tab">
            <button class="tablinks active" onclick="openTab(event, 'Surfboard')">Surfboard</button>
            <button class="tablinks" onclick="openTab(event, 'Clash')">Clash</button>
        </div>

        <div id="Surfboard" class="tabcontent" style="display: block;">
            <h2>Surfboard 订阅链接</h2>
            <p>将以下链接添加到 Surfboard 应用中：</p>
            <code id="surfboardUrl"></code>
            <p>
                <a href="" id="surfboardLink" class="button">点击直接添加到 Surfboard</a>
            </p>
            
            <h3>使用说明</h3>
            <ol>
                <li>复制上面的订阅链接</li>
                <li>打开 Surfboard 应用</li>
                <li>点击右上角的 "+" 按钮</li>
                <li>选择 "从 URL 下载" 选项</li>
                <li>粘贴订阅链接并点击确认</li>
            </ol>
        </div>

        <div id="Clash" class="tabcontent">
            <h2>Clash 订阅链接</h2>
            <p>将以下链接添加到 Clash 应用中：</p>
            <code id="clashUrl"></code>
            
            <h3>使用说明</h3>
            <ol>
                <li>复制上面的订阅链接</li>
                <li>打开 Clash 应用</li>
                <li>添加配置文件</li>
                <li>选择 "从 URL 导入" 选项</li>
                <li>粘贴订阅链接并点击确认</li>
            </ol>
        </div>
        
        <p>配置文件已经设置了自动选择延迟最低的节点，也可以手动选择节点。</p>
        
        <div class="update-time">
            最后更新时间: <span id="lastUpdateTime">加载中...</span>
        </div>
    </div>

    <script>
        // 获取当前URL
        const currentUrl = window.location.href;
        const baseUrl = currentUrl.split('/index.html')[0];
        const surfboardUrl = baseUrl + '/surfboard.conf';
        const clashUrl = baseUrl + '/clash.yaml';
        
        // 更新页面上的订阅链接
        document.getElementById('surfboardUrl').textContent = surfboardUrl;
        document.getElementById('surfboardLink').href = "surfboard:///install-config?url=" + encodeURIComponent(surfboardUrl);
        document.getElementById('clashUrl').textContent = clashUrl;
        
        // 获取最后更新时间
        fetch('update_time.txt')
            .then(response => response.text())
            .then(data => {
                document.getElementById('lastUpdateTime').textContent = data;
            })
            .catch(error => {
                document.getElementById('lastUpdateTime').textContent = "未知";
            });
            
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].style.display = "none";
            }
            tablinks = document.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }
    </script>
</body>
</html>
"""
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    """主程序"""
    #
