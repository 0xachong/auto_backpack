# backpack刷量代码 design by 0x阿冲(微信plans001) 推特@0xachong
import os
import time
import requests
import ed25519
import json
import base64
bp_key = os.environ.get('bp_key')
bp_secret = os.environ.get('bp_secret')

# X-Timestamp - 发送请求的 Unix 时间（以毫秒为单位）。
# X-Window - 请求有效的时间窗口（以毫秒为单位）。
# X-API-Key - ED25519密钥对的 Base64 编码验证密钥。
# X-Signature - 请求体的 Base64 编码签名。
# 根据以上信息生成HTTP请求头
def Signature(instruction="balanceQuery",data={},ts=str(int(time.time() * 1000)),window=5000):
    '''生成签名
    instruction: 指令
    data: 待签名的数据
    ts: 时间戳
    window: 时间窗口
    '''
    if len(data) == 0:
        data = ""
    else:
        data_list = [f"{k}={v}" for k,v in data.items()]
        data_list.sort()
        data = "&".join(data_list) + "&"
        data = data.replace("False","false").replace("True","true")
    s = f"instruction={instruction}&{data}timestamp={ts}&window={window}"
    ed25519_private_key = ed25519.SigningKey(base64.b64decode(bp_secret))
    signed = ed25519_private_key.sign(s.encode('utf-8'))
    return base64.b64encode(signed).decode()

def GetHeaders(instruction,data,ts,window=5000):
    '''获取请求头'''
    headers= {
    "X-Timestamp": ts,
    "X-Window": f"{window}",
    "X-API-Key": bp_key,
    "X-Signature": Signature(instruction,data,ts,window),
    "Content-Type": "application/json"
    }
    return headers

def GetAsset():
    '''获取资产'''
    url = "https://api.backpack.exchange/api/v1/assets"
    return requests.get(url)

def GetMarkgets():
    '''获取市场'''
    url = "https://api.backpack.exchange/api/v1/markets"
    return requests.get(url)

def GetTicker(symbol="SOL_USDC"):
    '''获取市场行情，symbol为交易对，如SOL_USDC'''
    url = f"https://api.backpack.exchange/api/v1/ticker?symbol={symbol}"
    return requests.get(url)

def GetOpenOrder():
    '''获取未成交订单'''
    url = "https://api.backpack.exchange/api/v1/order"
    return requests.get(url)

def GetKline(symbol="SOL_USDC",interval="1m"):
    '''获取K线数据'''
    return requests.get(f"https://api.backpack.exchange/api/v1/klines?symbol={symbol}&interval={interval}")
    
def GetDepth(symbol="SOL_USDC"):
    '''获取深度数据'''
    url = f"https://api.backpack.exchange/api/v1/depth?symbol={symbol}"
    return requests.get(url,{"Content-Type": "application/json"})
    
def GetCapital():
    '''获取余额'''
    ts = str(int(time.time() * 1000))
    headers = GetHeaders("balanceQuery",{},ts)
    url = "https://api.backpack.exchange/api/v1/capital"
    return requests.get(url,headers=headers)

def GetOpenOrder():
    url = "https://api.backpack.exchange/api/v1/order"

def Buy(price,quantity):
    '''买入'''
    return ExeOrder("Bid",price,quantity)

def Sell(price,quantity):
    '''卖出'''
    return ExeOrder("Ask",price,quantity)

def ExeOrder(side,price,quantity):
    '''执行订单'''
    ts = str(int(time.time() * 1000))
    data = {
        "orderType":"Limit",
        "postOnly":True, # 是否只做maker,就是如果为false可以挂限价单，true为市价单，无法成交即时取消
        "price":price,
        "quantity":quantity,
        "side":side, # bid是买入，ask是卖出
        "symbol":"SOL_USDC",
    }
    headers = GetHeaders("orderExecute",data,ts)
    url = "https://api.backpack.exchange/api/v1/order"
    res = requests.post(url,data=json.dumps(data),headers=headers)
    if res.status_code == 200:
        print(json.dumps(data))
    return res

def PrintCapital(pair):
    capital = GetCapital().json()
    pair_0 = pair.split("_")[0]
    pair_1 = pair.split("_")[1]
    start_p_0 = capital[pair_0]["available"]
    start_p_1 = capital[pair_1]["available"]
    # print(get_ticker().json()["lastPrice"])
    tick_price =float(GetTicker().json()["lastPrice"])
    total = float(start_p_0)*tick_price+float(start_p_1)
    print(">>>>> 钱包余额情况:")
    print(f"余额:{pair_0} {start_p_0}\n余额:{pair_1} {start_p_1}\nU本位:{total}")
    return total

def AutoTrade():
    '''自动交易'''
    global bp_key,bp_secret
    if bp_key is None or bp_secret is None:
        bp_key = input("输入你的key")
        bp_secret = input("输入你的secret")
    
    pair = input("请输入交易对(default:SOL_USDC)")
    pair = pair if pair != "" else "SOL_USDC"
    start_total = PrintCapital(pair)

    times=input(">>>>> 请输入交易次数(default:100)")
    times = int(times) if times != "" else 100
    trade_num=input(">>>>> 请输入交易数量(default:0.5)")
    trade_num = int(trade_num) if trade_num != "" else 0.5
    i = 0
    while i <int(times):
        depth= GetDepth().json()
        asks = depth["asks"]
        bids = depth["bids"]
        ask = asks[0][0]
        bid = bids[-1][0]
        res = Buy(ask,trade_num)
        # print(res.status_code,res.text)
        res = Sell(bid,trade_num)
        # print(res.status_code,res.text)
        if res.status_code == 200:
            i += 1
    end_total = PrintCapital(pair)
    price =float(GetTicker().json()["lastPrice"])
    volumn = float(price)*trade_num*times*2 # 买卖各记一次交易额
    print(f"交易结束，交易额{volumn},磨损{end_total-start_total} 磨损比{(end_total-start_total)/volumn:.4%}")

if __name__=="__main__":
    AutoTrade()
