import requests
import base64
import json
import pyaes
import binascii
import urllib.parse
import re
import os
import time
from datetime import datetime
import yaml

def ensure_public_dir():
    """创建public目录"""
    os.makedirs('public', exist_ok=True)

def fetch_ss_nodes(max_retry=3):
    """获取SS节点（带重试机制）"""
    url = 'http://api.skrapp.net/api/serverlist'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'data': '4265a9c353cd8624fd2bc7b5d75d2f18b1b5e66ccd37e2dfa628bcb8f73db2f14ba98bc6a1d8d0d1c7ff1ef0823b11264d0addaba2bd6a30bdefe06f4ba994ed'}
    
    key = b'65151f8d966bf596'
    iv = b'88ca0f0ea1ecf975'

    def aes_decrypt(ciphertext):
        cipher = pyaes.AESModeOfOperationCBC(key, iv=iv)
        decrypted = cipher.decrypt(ciphertext)
        return decrypted[:-decrypted[-1]]

    for attempt in range(max_retry):
        try:
            response = requests.post(url, headers=headers, data=data, timeout=15)
            response.raise_for_status()
            
            hex_data = response.text.strip()
            ciphertext = binascii.unhexlify(hex_data)
            decrypted_data = aes_decrypt(ciphertext)
            nodes = json.loads(decrypted_data)
            
            ss_nodes = []
            for node in nodes['data']:
                ss_url = f"ss://{base64.b64encode(f'aes-256-cfb:{node['password']}@{node['ip']}:{node['port']}'.encode()).decode()}##{node['title']}"
                ss_nodes.append(ss_url)
            return ss_nodes
            
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {str(e)}")
            if attempt == max_retry - 1:
                return []
            time.sleep(5)

def parse_ss_url(ss_url):
    """解析SS链接"""
    try:
        if not ss_url.startswith('ss://'):
            return None
            
        parts = ss_url[5:].split('#', 2)
        encoded = parts[0]
        remark = urllib.parse.unquote(parts[2]) if len(parts) > 2 else "Unnamed"
        
        padding = 4 - (len(encoded) % 4)
        decoded = base64.urlsafe_b64decode(encoded + ('=' * padding)).decode()
        
        method_part, server_part = decoded.split('@', 1)
        method, password = method_part.split(':', 1)
        host, port = server_part.split(':', 1)
        
        location = re.sub(r'[^\w\-]', '', remark.split(',')[0].strip().replace(' ', '_'))
        return {
            'method': method,
            'password': password,
            'server': host,
            'port': int(port),
            'name': f"{location}_{host.replace('.', '_')}"
        }
    except Exception as e:
        print(f"解析失败: {ss_url} - {str(e)}")
        return None

def generate_surfboard_config(nodes):
    """生成Surfboard配置"""
    config = f"""[General]
loglevel = notify
dns-server = 8.8.8.8, 8.8.4.4
skip-proxy = 127.0.0.1, 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12
ipv6 = false
test-timeout = 5

[Proxy]
"""
    proxy_names = []
    for node in nodes:
        config += f"{node['name']} = ss, {node['server']}, {node['port']}, encrypt-method={node['method']}, password={node['password']}\n"
        proxy_names.append(node['name'])
    
    config += """
[Proxy Group]
自动选择 = url-test, {}, url=http://www.gstatic.com/generate_204, interval=600, tolerance=50
手动选择 = select, {}
全部节点 = select, {}

[Rule]
FINAL, 自动选择
""".format(', '.join(proxy_names), ', '.join(proxy_names), ', '.join(proxy_names))
    
    return config

def generate_clash_config(nodes):
    """生成Clash配置"""
    config = {
        'port': 7890,
        'socks-port': 7891,
        'allow-lan': False,
        'mode': 'Rule',
        'log-level': 'info',
        'external-controller': '0.0.0.0:9090',
        'proxies': [],
        'proxy-groups': [
            {
                'name': '🚀 自动选择',
                'type': 'url-test',
                'proxies': [node['name'] for node in nodes],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300
            },
            {
                'name': '🔗 手动选择',
                'type': 'select',
                'proxies': [node['name'] for node in nodes]
            }
        ],
        'rules': [
            'DOMAIN-SUFFIX,google.com,🚀 自动选择',
            'DOMAIN-KEYWORD,instagram,🚀 自动选择',
            'IP-CIDR,8.8.8.8/32,🚀 自动选择',
            'GEOIP,CN,DIRECT',
            'MATCH,🚀 自动选择'
        ]
    }

    for node in nodes:
        config['proxies'].append({
            'name': node['name'],
            'type': 'ss',
            'server': node['server'],
            'port': node['port'],
            'cipher': node['method'].split('-')[-1].upper(),
            'password': node['password'],
            'udp': True
        })
    
    return yaml.dump(config, allow_unicode=True, sort_keys=False)

def create_index_html(update_time, node_count):
    """生成状态页面"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>订阅中心</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 20px auto; padding: 0 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 0.5em; }}
        .card {{
            background: #ffffff;
            border-radius: 10px;
            padding: 25px;
            margin: 25px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        input {{
            width: 100%;
            padding: 12px;
            border: 2px solid #3498db;
            border-radius: 6px;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            color: #2c3e50;
        }}
        .stats {{ color: #7f8c8d; font-size: 0.95em; margin-top: 10px; }}
    </style>
</head>
<body>
    <h1>多协议订阅服务</h1>
    
    <div class="card">
        <h2>🏄 Surfboard 订阅</h2>
        <input type="text" value="https://geniusppl.github.io/surfboard-subscribe/surfboard.conf" readonly>
        <p class="stats">📡 节点数量：{node_count} 个</p>
        <p class="stats">⏱️ 更新时间：{update_time}</p>
    </div>

    <div class="card">
        <h2>⚡ Clash 订阅</h2>
        <input type="text" value="https://geniusppl.github.io/surfboard-subscribe/clash.yaml" readonly>
        <p class="stats">📡 节点数量：{node_count} 个</p>
        <p class="stats">🔒 支持协议：Shadowsocks</p>
    </div>
</body>
</html>
"""

def main():
    ensure_public_dir()
    
    ss_nodes = fetch_ss_nodes()
    valid_nodes = [node for node in (parse_ss_url(url) for url in ss_nodes) if node]
    
    if valid_nodes:
        # 保存配置文件
        with open('public/surfboard.conf', 'w', encoding='utf-8') as f:
            f.write(generate_surfboard_config(valid_nodes))
        
        with open('public/clash.yaml', 'w', encoding='utf-8') as f:
            f.write(generate_clash_config(valid_nodes))
        
        # 保存节点列表
        with open('public/ss_nodes.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(ss_nodes))
        
        # 生成状态页
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('public/index.html', 'w', encoding='utf-8') as f:
            f.write(create_index_html(update_time, len(valid_nodes)))
    else:
        print("未获取到有效节点，跳过文件生成")

if __name__ == '__main__':
    main()
