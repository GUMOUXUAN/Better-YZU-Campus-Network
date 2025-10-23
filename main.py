import httpx
import json
import re
import sys
import time
import urllib.parse

SERVICE_LIST: list = [
    "学校互联网服务", 
    "联通互联网服务", 
    "移动互联网服务", 
    "电信互联网服务", 
    "校内免费服务"
]

USER_ID = "243502232"
#请在此处填写你的学工号          
PASSWORD = "66261034@Ray"  
#请在此处填写你的密码              
SERVICE_INDEX = 4  
#请在此处选择服务索引
# "学校互联网服务"=1,"联通互联网服务"=2,"移动互联网服务"=3"电信互联网服务"=4, "校内免费服务"=5（不常用）请依据实际情况填写                 

YZU_INITIAL_URL = "https://sso.yzu.edu.cn/login?service=http%3A%2F%2F10.245.2.19%2Feportal%2Findex.jsp%3Fwlanuserip%3Dc1540554e2c21d6b3693fd0482f8b649%26wlanacname%3D204fb75956663440ab648612b65bef09%26ssid%3D%26nasip%3D586cbd9f283ee1edd79c04f1889b6358%26snmpagentip%3D%26mac%3Dc72cd2a5bd1273d4971ac7136c9ba92a%26t%3Dwireless-v2%26url%3Dfa95582fdeb195ec7e657f7f668b1adb%26apmac%3D%26nasid%3D204fb75956663440ab648612b65bef09%26vid%3Df270612dc42ac801%26port%3D894f1726b0f77e48%26nasportid%3Defc04e823eeb5679bfc7a150e5af1c46cf0c4832aa31a7c93df4dd744671315b9ddd87ddb2ee518a"

def show_msg(msg: str, duration: int = 5):
    print(f"[通知] {msg}")

def get_redirect_info(client: httpx.Client, initial_sso_url: str) -> tuple[str, str, str]:
    show_msg("正在解析认证服务器信息...", 2)
    
    parsed_url = urllib.parse.urlparse(initial_sso_url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    
    if 'service' not in query_params:
        raise ConnectionError("意外错误，请联系原作者github:https://github.com/GUMOUXUAN")
        
    new_url = query_params['service'][0]

    show_msg(f"正在获取参数desuwa...", 2)
    
    parsed_new_url = urllib.parse.urlparse(new_url)
    
    ip = parsed_new_url.netloc.split(':')[0] 
    
    match_query = re.search(r"\?(.*)", new_url)
    
    if not ip or not match_query:
        raise ConnectionError(f"无法从解析出的 URL 中提取 IP 或 QueryString。当前URL: {new_url}")
    
    query_string = match_query.group(1)
    
    login_url = f"http://{ip}/eportal/InterFace.do?method=login"
    
    client.get(new_url, timeout=5)

    client.headers.update({"Referer": new_url})
    
    return login_url, ip, query_string

def login_attempt(client: httpx.Client):
    if not 1 <= SERVICE_INDEX <= len(SERVICE_LIST):
        show_msg("服务索引必须在 1 到 5 之间", 3)
        return

    try:
        login_url, _, query_string = get_redirect_info(client, YZU_INITIAL_URL)
        
        show_msg("正在尝试登录...", 2)
        
        data = {
            "userId": USER_ID,
            "password": PASSWORD,
            "service": SERVICE_LIST[SERVICE_INDEX - 1],
            "queryString": query_string,
            "operatorPwd": "",
            "operatorUserId": "",
            "validcode": "",
            "passwordEncrypt": "",
        }
        
        res = client.post(login_url, data=data, timeout=10)
        
        # --- 针对断网/无效响应的修改 ---
        try:
            res_json = res.json()
        except json.JSONDecodeError:
            # 当服务器返回空内容或非JSON内容时捕获此错误
            show_msg("登录失败：服务器响应格式错误。可能原因：您正处于断网状态，且网关返回了非标准错误页面。", 5)
            # 打印响应文本帮助调试，如果是空字符串则打印 <EMPTY RESPONSE>
            print(f"原始响应文本: {res.text if res.text else '<EMPTY RESPONSE>'}")
            return
        # --- 针对断网/无效响应的修改结束 ---
        
        if res_json.get("result") == "success":
            show_msg("校园网成功连接了，Ciallo～(∠・ω< )～", 5)
        elif res_json.get("result") == "fail":
            show_msg(f"登录失败: {res_json.get('message', '未知错误')}", 5)
        else:
            show_msg(f"登录响应异常: {res.text}", 5)

    except (httpx.ConnectTimeout, httpx.ConnectError):
        show_msg("网络连接错误：可能未联网或服务器无响应。", 5)
    except ConnectionError as e:
        show_msg(f"流程错误: {e}", 5)
    except Exception as e:
        print(f"发生意外错误: {e}")
        show_msg("发生意外错误，请检查控制台。", 5)

if __name__ == "__main__":
    if not all([USER_ID, PASSWORD, 1 <= SERVICE_INDEX <= 5]):
        show_msg("请在代码开头填写您正确的USER_ID, PASSWORD 和SERVICE_INDEX。喂！等下我绝对说过了吧喵（？）", 8)
        sys.exit(1)
        
    show_msg("启动了喵...困困困喵", 1)
    
    with httpx.Client(verify=False) as client: 
        client.headers.update({
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        })
        
        while True:
            login_attempt(client)
            time.sleep(10)