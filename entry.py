import requests
from datetime import datetime
import time
# 使用する時間足
chart_sec = 900


# CryptowatchでBTCFXの価格データを取得
def get_price(min, before=0, after=0):
	price = []
	params = {"periods" : min }
	if before != 0:
		params["before"] = before
	if after != 0:
		params["after"] = after
	response = requests.get("https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc",params)
	data = response.json()
	
	if data["result"][str(min)] is not None:
		for i in data["result"][str(min)]:
			price.append({ "close_time" : i[0],
				"close_time_dt" : datetime.fromtimestamp(i[0]).strftime('%Y/%m/%d %H:%M'),
				"open_price" : i[1],
				"high_price" : i[2],
				"low_price" : i[3],
				"close_price": i[4] })
	return price


# 単純移動平均を計算する関数
def calculate_MA( value,before=None ):
	if before is not None:
		MA = sum(i["close_price"] for i in price[-1*value + before: before]) / value
	else:
		MA = sum(i["close_price"] for i in price[-1*value:]) / value
	return round(MA)

# 指数移動平均を計算する関数
def calculate_EMA( value,before=None ):
	if before is not None:
		MA = sum(i["close_price"] for i in price[-2*value + before : -1*value + before]) / value
		EMA = (price[-1*value + before]["close_price"] * 2 / (value+1)) + (MA * (value-1) / (value+1))
		for i in range(value-1):
			EMA = (price[-1*value+before+1 + i]["close_price"] * 2 /(value+1)) + (EMA * (value-1) / (value+1))
	else:
		MA = sum(i["close_price"] for i in price[-2*value: -1*value]) / value
		EMA = (price[-1*value]["close_price"] * 2 / (value+1)) + (MA * (value-1) / (value+1))
		for i in range(value-1):
			EMA = (price[-1*value+1 + i]["close_price"] * 2 /(value+1)) + (EMA * (value-1) / (value+1))
	return round(EMA)

#---- ここからメインの実行処理----
price=get_price(60)
def signal(value,before):
    macd=calculate_EMA(12,before)-calculate_EMA(26,before)
    MACD=[]
    for i in range(value):
        md=calculate_EMA(12,before-i)-calculate_EMA(26,before-i)
        MACD.append(md)
    SIGNAL=round(sum(MACD)/value)
    return macd-SIGNAL

def dx(value):
    PRICEhigh=[price[-27+value+i]["high_price"] for i in range(14)]
    PRICElow=[price[-27+value+i]["low_price"] for i in range(14)]
    PRICEclose=[price[-27+value+i]["close_price"] for i in range(14)]
    PRICEopen=[price[-27+value+i]["open_price"] for i in range(14)]
    DMup=[]
    DMdown=[]
    up=0
    down=0
    for i in range(13):
        if PRICEhigh[i+1]>PRICEhigh[i]:
            up=PRICEhigh[i+1]-PRICEhigh[i]
        if PRICElow[i]>PRICElow[i+1]:
            down=PRICEhigh[i]-PRICEhigh[i+1]
        if up>down:
            DMup.append(up)
        else:DMdown.append(down)
        up=0
        down=0
    TR=[]
    a=0#当日の高値-当日の安値
    b=0#当日の高値-前日の高値
    c=0#前日の終値-当日の安値
    for i in range(13):
        a=PRICEhigh[i+1]-PRICElow[i+1]
        b=PRICEhigh[i+1]-PRICEclose[i]
        c=PRICEclose[i]-PRICElow[i]
        if a>=b or a>=c:
            TR.append(a)
        elif a<b:
            TR.append(b)
        else:TR.append(c)
    DIup=sum(DMup)/sum(TR)
    DIdown=sum(DMdown)/sum(TR)
    DX=abs(DIup-DIdown)/(DIup+DIdown)*100
    return DX
def adx():
    adx=[]
    for i in range(14):
        adx.append(dx(i))
    result=round(sum(adx)/14)
    return result

def rsi():
    PRICE=[price[-14+i]["close_price"] for i in range(14)]
    RSIup=[]
    RSIdown=[]
    for i in range(13):
        dif=PRICE[i+1]-PRICE[i]
        if dif>0:
            RSIup.append(dif)
        else:RSIdown.append(abs(dif))
    result=((sum(RSIup)/14)/((sum(RSIup)+sum(RSIdown))/14))*100
    return round(result)
#print(calculate_EMA(12)-calculate_EMA(26),signal(9,-1))
def stk(value):
    price_high=[]
    price_low=[]
    price_HIGH=[]
    price_LOW=[]
    price=get_price(900)
    close=[]
    perK=[]
    perD=[]
    slowD=[]
    for j in range(3):
        for v in range(3):
            for i in range(1,10):
                price_high.append(price[-i-v-j]["high_price"])
                price_low.append(price[-i-v-j]["low_price"])
                if j==0 and v==0 and i==9:
                    perK.append((price[-1]["close_price"]-min(price_low))/(max(price_high)-min(price_low))*100)
            close.append(price[-j-v-1]["close_price"])
            price_HIGH.append(max(price_high))
            price_LOW.append(min(price_low))
            price_high=[]
            price_low=[]
            if j==0 and v==2:
                perD.append(((sum(close)-sum(price_LOW))/(sum(price_HIGH)-sum(price_LOW)))*100)
                slowD.append(((sum(close)-sum(price_LOW))/(sum(price_HIGH)-sum(price_LOW)))*100)
                price_HIGH=[]
                price_LOW=[]
                close=[]
            if (j==1 or j==2) and v ==2:
                slowD.append(((sum(close)-sum(price_LOW))/(sum(price_HIGH)-sum(price_LOW)))*100)
                price_HIGH=[]
                price_LOW=[]
                close=[]
    slowD=sum(slowD)/3
    return round(perK[0]),round(perD[0]),round(slowD)

while True:
    price=get_price(3600)
    ADX=adx()
    RSI=rsi()
    STK=stk(9)
    lastdata=signal(9,-1)
    data=signal(9,0)
    macd=calculate_EMA(12)-calculate_EMA(26)
    EMA200=calculate_EMA(200)
    now_price=price[-1]["close_price"]
    print(EMA200,macd,data,now_price,ADX,RSI,STK)
    if (lastdata>0 and data<0) and ADX>25:
        print("sell")
    elif (lastdata<0 and data>0) and ADX>25:
        print("buy")
    time.sleep(900)


