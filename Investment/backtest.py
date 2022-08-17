# coding:utf-8
# 第36课 策略与回测系统


import pandas as pd
from os import path
import abc
import numpy as np
from typing import Callable
from ultil import SMA, crossover
from numbers import Number


def assert_msg(condition, msg):
    if not condition:
        raise Exception(msg)


def read_file(filename):
    # 获得文件绝对路径
    filepath = path.join(path.dirname(__file__), filename)

    # 判断文件是否存在
    assert_msg(path.exists(filepath), "文件不存在")

    # 读取csv文件并返回
    return pd.read_csv(filepath, index_col=0, parse_dates=True, infer_datetime_format=True)


# 策略类
class Strategy(metaclass=abc.ABCMeta):
    """
    抽象策略类，用于定义交易策略。

    定义自己的策略类，需要继承这个基类，并实现两个抽象方法：
    Strategy.init
    Strategy.next
    """

    def __init__(self, broker, data):
        """
        构造策略对象。

        @params broker:  ExchangeAPI    交易 API 接口，用于模拟交易
        @params data:    list           行情数据
        """

        self._indicators = []
        self._broker = broker  # type: _Broker
        self._data = data  # type: _Data
        self._tick = 0

    def I(self, func: Callable, *args) -> np.ndarray:
        """
        计算买卖指标向量。买卖指标向量是一个数组，长度和历史数据对应；
        用于判定这个时间点上需要进行 " 买 " 还是 " 卖 "。

        例如计算滑动平均：
        def init():
            self.sma = self.I(utils.SMA, self.data.Close, N)
        """

        value = func(*args)
        value = np.asarray(value)
        assert_msg(value.shape[-1] == len(self._data.Close), "指示器长度必须和data长度相同")

        self._indicators.append(value)
        return value

    @property
    def tick(self):
        return self._tick

    @abc.abstractmethod
    def init(self):
        """
        初始化策略。在策略回测 / 执行过程中调用一次，用于初始化策略内部状态。
        这里也可以预计算策略的辅助参数。比如根据历史行情数据：
        计算买卖的指示器向量；
        训练模型 / 初始化模型参数
        """
        pass

    @abc.abstractmethod
    def next(self, tick):
        """
        步进函数，执行第 tick 步的策略。
        tick 代表当前的 " 时间 "。比如 data[tick] 用于访问当前的市场价格。
        """
        pass

    def buy(self):
        self._broker.buy()

    def sell(self):
        self._broker.sell()

    @property
    def data(self):
        return self._data


class SmaCross(Strategy):
    # 小窗口 SMA 的窗口大小，用于计算 SMA 快线
    fast = 30

    # 大窗口 SMA 的窗口大小，用于计算 SMA 慢线
    slow = 90

    def init(self):
        # 计算历史上每个时刻的快线和慢线
        self.sma1 = self.I(SMA, self.data.Close, self.fast)
        self.sma2 = self.I(SMA, self.data.Close, self.slow)

    def next(self, tick):
        # 快线越过慢线，买入
        if crossover(self.sma1[:tick], self.sma2[:tick]):
            self.buy()

        # 慢线越过快线，卖出
        elif crossover(self.sma2[:tick], self.sma1[:tick]):
            self.sell()

        # 否则，这个时刻不执行任何操作
        else:
            pass


# 交易所类
class ExchangeAPI:
    def __init__(self, data, cash, commission):
        assert_msg(0 < cash, "初始现金数量需大于0，输入初始金额为{}".format(cash))
        assert_msg(0 <= commission <= 0.05, "合理手续费率不大于5%，输入的为{}".format(commission))
        self._initial_cash = cash
        self._data = data
        self._commission = commission
        self._position = 0
        self._cash = cash
        self._i = 0

    @property
    def cash(self):
        """
        :return: 返回当前账户现金数量
        """
        return self._cash

    @property
    def position(self):
        """
        :return: 返回当前账户仓位
        """
        return self._position

    @property
    def initial_cash(self):
        """
        :return: 返回初始现金数量
        """
        return self._initial_cash

    @property
    def market_value(self):
        """
        :return: 返回当前市值
        """
        return self._cash + self._position * self.current_price

    @property
    def current_price(self):
        """
        :return: 返回当前市场价格
        """
        return self._data.Close[self._i]

    def buy(self):
        """
        用当前账户剩余资金，按照市场价格全部买入
        """
        self._position = float(self._cash * (1 - self._commission) / self.current_price)
        self._cash = 0.0

    def sell(self):
        """
        卖出当前账户剩余持仓
        """
        self._cash += float(self._position * self.current_price * (1 - self._commission))
        self._position = 0.0

    def next(self, tick):
        self._i = tick


class Backtest:
    """
    回测类，用于读取历史行情数据，执行策略，模拟交易并估计收益。

    初始化的时候调用 Backtest.run 来执行回测。
    """

    def __init__(self,
                 data: pd.DataFrame,
                 strategy_type: type(Strategy),
                 broker_type: type(ExchangeAPI),
                 cash: float = 10000,
                 commission: float = .0):

        """
        构造回测对象。需要的参数包括：历史数据，策略对象，初始资金数量，手续费率等。
        初始化过程包括检测输入类型，填充数据空值等。

        参数：
        :param data:            pd.DataFrame        pandas Dataframe 格式的历史 OHLCV 数据
        :param strategy_type:   type(Strategy)      策略类型
        :param broker_type:     type(ExchangeAPI)   交易所 API 类型，负责执行买卖操作以及账户状态的维护
        :param cash:            float               初始资金数量
        :param commission:      float               每次交易手续费率。如 2% 的手续费此处为 0.02
        """

        assert_msg(issubclass(strategy_type, Strategy), "strategy_type不是一个Strategy类型")
        assert_msg(issubclass(broker_type, ExchangeAPI), "broker_type不是一个ExchangeAPI类型")
        assert_msg(isinstance(commission, Number), "commission不是浮点数值类型")

        # False代表浅复制，没有内存拷贝
        data = data.copy(False)

        # 如果没有Volume列，填充NaN
        if "Volume" not in data:
            data["Volume"] = np.Nan

        # 验证OHLC数据格式
        assert_msg(len(data.columns & {'Open', 'High', 'Low', 'Close', 'Volume'}) == 5,
                   ("输入的`data`格式不正确，至少需要包含这些列："
                    "'Open', 'High', 'Low', 'Close'"))
        # 检查缺失值
        assert_msg(not data[['Open', 'High', 'Low', 'Close']].max().isnull().any(),
                   ('部分OHLC包含缺失值，请去掉那些行或者通过差值填充. '))

        # 如果行情数据没有按照时间排序，重新排序一下
        if not data.index.is_monotonic_increasing:
            data = data.sort_index()

        # 利用数据，初始化交易所对象和策略对象
        self._data = data  # type: pd.DataFrame
        self._broker = broker_type(data, cash, commission)
        self._strategy = strategy_type(self._broker, self._data)
        self._results = None

    def run(self) -> pd.Series:

        """
        运行回测，迭代历史数据，执行模拟交易并返回回测结果。

        Run the backtest. Returns `pd.Series` with results and statistics.

        Keyword arguments are interpreted as strategy parameters.
        """

        strategy = self._strategy
        broker = self._broker

        # 策略初始化
        strategy.init()

        # 设定回测开始和结束位置
        start = 100
        end = len(self._data)

        # 回测主循环，更新市场状态，执行策略
        for i in range(start, end):
            # 注意要先把市场状态移动到第 i 时刻，然后再执行策略。
            broker.next(i)
            strategy.next(i)

        # 完成策略执行之后，计算结果并返回
        self._results = self._compute_result(broker)
        return self._results

    def _compute_result(self, broker):
        s = pd.Series()
        s["初始市值"] = broker.initial_cash
        s["结束市值"] = broker.market_value
        s["收益"] = broker.market_value - broker.initial_cash
        return s


if __name__ == "__main__":
    # BTCUSD = read_file("BTCUSD_GEMINI.csv")
    # assert_msg(BTCUSD.__len__() > 0, "读取失败")
    # print(BTCUSD.head())

    BTCUSD = read_file("BTCUSD_GEMINI.csv")
    ret = Backtest(BTCUSD, SmaCross, ExchangeAPI, 10000.0, 0.003).run()
    print(ret)
