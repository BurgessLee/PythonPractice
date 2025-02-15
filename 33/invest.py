# coding:utf-8
# 第33课 带你初探量化世界


import json
import requests
import matplotlib.pyplot as plt
import pandas as pd


########## GEMINI 行情接口 ##########
## https://api.gemini.com/v1/pubticker/:symbol


# 获取Gemini交易所报价数据
def get_price():
    gemini_ticker = "https://api.gemini.com/v1/pubticker/{}"
    symbol = "btcusd"
    btc_data = requests.get(gemini_ticker.format(symbol)).json()
    print(json.dumps(btc_data, indent=4))


# 获取最近一个小时交易数据并绘图
def get_hour_price():
    # 选择要获取的数据时间段
    periods = "3600"

    # 通过 Http 抓取 btc 历史价格数据
    resp = requests.get("https://api.cryptowat.ch/markets/gemini/btcusd/ohlc", params={
        "periods": periods
    })
    data = resp.json()

    # 转换成 pandas data frame
    df = pd.DataFrame(
        data["result"][periods],
        columns=[
            "收盘时间",
            "开盘时间",
            "最高价",
            "最低价",
            "收盘价",
            "成交量",
            "NA"
        ]
    )

    # 输出 DataFrame 的头部几行
    print(df.head())

    # 绘制 btc 价格曲线
    ax = df["收盘价"].plot(figsize=(14, 7))

    # 绘制图形
    fig = ax.get_figure()
    fig.savefig("closeprice.png")


if __name__ == "__main__":
    # get_price()
    get_hour_price()
