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
    # Your existing code remains unchanged
    # ...
    return ss_nodes

def parse_ss_url(ss_url):
    """解析SS URL并返回节点信息"""
    # Your existing code remains unchanged
    # ...
    return node_info

def generate_improved_config(nodes_info):
    """生成Surfboard配置文件内容"""
    # Your existing code remains unchanged
    # ...
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
    # Your existing code remains unchanged
    # ...

def save_config(config_content, clash_content):
    """保存配置文件内容"""
    with open('public/surfboard.conf', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    with open('public/clash.yaml', 'w', encoding='utf-8') as f:
        f.write(clash_content)

def save_update_time():
    """保存更新时间"""
    # Your existing code remains unchanged
    # ...

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
    # 创建public目录（如果不存在）
    os.makedirs('public', exist_ok=True)
    
    # 获取SS节点
    print("正在获取节点信息...")
    ss_nodes = fetch_ss_nodes()
    
    if not ss_nodes:
        print("未能获取到有效的SS节点信息")
        return
    
    print(f"获取到 {len(ss_nodes)} 个SS节点")
    
    # 保存原始节点信息
    save_ss_nodes(ss_nodes)
    
    # 解析节点信息
    nodes_info = []
    for node_url in ss_nodes:
        node_info = parse_ss_url(node_url)
        if node_info:
            nodes_info.append(node_info)
    
    if not nodes_info:
        print("无法解析任何节点信息")
        return
    
    # 生成配置文件内容
    surfboard_config = generate_improved_config(nodes_info)
    clash_config = generate_clash_config(nodes_info)
    
    # 保存配置文件
    save_config(surfboard_config, clash_config)
    
    # 保存更新时间
    save_update_time()
    
    # 创建索引页面
    create_index_html()
    
    print("所有文件已生成完毕")

if __name__ == "__main__":
    main()
