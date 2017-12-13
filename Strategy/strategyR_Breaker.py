#encoding:utf-8
from __future__ import division
import talib as ta
import numpy as np
from datetime import  datetime,time,timedelta
class R_BreakerStrategy(object):
    """DualThrust交易策略"""
    className = 'R_BreakerStrategy'
    author = u'julin'
    pos = 0
    # 策略参数
    fixedSize = 100
    K1 = 0.15
    K2 = 0.15
    bufferSize = 301  # 需要缓存的数据的大小
    bufferCount = 0  # 目前已经缓存了的数据的计数
    highArray = np.zeros(bufferSize)  # K线最高价的数组
    lowArray = np.zeros(bufferSize)  # K线最低价的数组
    closeArray = np.zeros(bufferSize)  # K线收盘价的数组
    openArray = np.zeros(bufferSize)
    volumeArray = np.zeros(bufferSize)
    openintArray = np.zeros(bufferSize)
    timeArray = np.zeros(bufferSize).tolist()
    orderList = []  # 保存委托代码的列表

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'k1',
                 'k2']

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'range',
               'longEntry',
               'shortEntry',
               'exitTime']

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine):
        """Constructor"""
        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）
        # self.preTick = VtTickData()
        # self.preBar  = VtBarData()
        self.ctaEngine = ctaEngine

    # ----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""

        self.closeArray[0:self.bufferSize - 1] = self.closeArray[1:self.bufferSize]
        self.highArray[0:self.bufferSize - 1] = self.highArray[1:self.bufferSize]
        self.lowArray[0:self.bufferSize - 1] = self.lowArray[1:self.bufferSize]
        self.openArray[0:self.bufferSize - 1] = self.openArray[1:self.bufferSize]
        self.volumeArray[0:self.bufferSize - 1] = self.volumeArray[1:self.bufferSize]
        self.openintArray[0:self.bufferSize - 1] = self.openintArray[1:self.bufferSize]
        self.timeArray[0:self.bufferSize - 1] = self.timeArray[1:self.bufferSize]
        self.closeArray[-1] = bar.close
        self.highArray[-1] = bar.high
        self.lowArray[-1] = bar.low
        self.openArray[-1] = bar.open
        self.volumeArray[-1] = bar.volume
        date = bar.strendtime[:10]
        time = bar.strendtime[11:19]
        self.openintArray[-1] = bar.position
        self.timeArray[-1] = datetime.strptime(date + ' ' + time, "%Y-%m-%d %H:%M:%S")
        self.bufferCount += 1

        if self.bufferCount < self.bufferSize:  # 缓存数量小于300则退出继续传入新的bar更新onbar
            return
        # 观察卖出价
        if self.timeArray[-1].day > self.timeArray[-2].day or self.bufferCount==self.bufferSize:  #bar已经更新了一天
            begin_time = (self.timeArray[-1] + timedelta(days=-10)).date()
            history_bar = self.ctaEngine.ret.get_dailybars(self.ctaEngine.symbol,begin_time=begin_time, end_time=date)
            yesterday_bar = history_bar[-2] # history_bar[0]为当天的历史bar数据，1为前一天的bar
            self.Watch_Sell_Price = yesterday_bar.high + 0.35*(yesterday_bar.close - yesterday_bar.low)
            # 观察买入价
            self.Watch_Buy_Price = yesterday_bar.low - 0.35*(yesterday_bar.high - yesterday_bar.close)
            # 反转卖出价
            self.Reverse_Sell_Price = 1.07/2 *(yesterday_bar.high +yesterday_bar.low) - 0.07*yesterday_bar.low
            # 反转买入价
            self.Reverse_Buy_Price = 1.07/2 * (yesterday_bar.high + yesterday_bar.low) - 0.07 * yesterday_bar.high
            # 突破买入价
            self.Broken_Buy_Price = self.Watch_Sell_Price + 0.25*(self.Watch_Sell_Price-self.Watch_Buy_Price)
            # 突破买入价
            self.Broken_Sell_Price = self.Watch_Buy_Price - 0.25*(self.Watch_Sell_Price-self.Watch_Buy_Price)
        before_2_close = self.closeArray[-2]
        before_2_high = self.highArray[-2]
        before_1_close = self.closeArray[-1]
        before_1_high = self.highArray[-1]
        before_1_low = self.lowArray[-1]
        before_1_open = self.openArray[-1]

        ## 趋势
        if before_2_close <= self.Broken_Buy_Price and before_1_close > self.Broken_Buy_Price:
            if self.pos == 0:   # 判断是否空仓
                self.ctaEngine.open(ordersymbol=bar.sec_id,direction =  1,price= bar.close,volume= 1,bar= bar)
            elif self != 0 and self.ctaEngine.offset=='卖开':  # 判断是否持有空单
                self.ctaEngine.close(bar.sec_id ,1 ,price = bar.close,)

        if before_2_close >= self.Broken_Sell_Price and before_1_close < self.Broken_Sell_Price:
            if self.pos == 0 :
                self.ctaEngine.open(ordersymbol=bar.sec_id, direction=-1, price=bar.close, volume=1, bar=bar)
            elif self.pos != 0 and self.ctaEngine.offset=='买开':  #判断是否持有多头
                self.ctaEngine.close(ordersymbol=bar.sec_id, direction=-1, price=bar.close, volume=1, bar=bar)

        ## 反转 (多单反转,如果持有多头就平仓，并开空;)
        #  判断一分钟前最高价是否超过观察卖出价 同时 一分钟收盘价低于反转卖出价
        if before_1_high > self.Watch_Sell_Price and before_1_close < self.Reverse_Sell_Price:
            if  self.pos != 0 and self.ctaEngine.offset=='买开':  #判断是否持有多头
                self.ctaEngine.close(ordersymbol=bar.sec_id, direction=-1, price=bar.close, volume=1, bar=bar)
                self.ctaEngine.open(ordersymbol=bar.sec_id, direction=-1, price=bar.close, volume=1, bar=bar)
        ## 反转（空单反转,如果持有空头就平仓,并开多;）
        #  判断一分钟前最低价是否超过观察买入价 同时 一分钟收盘价低于反转卖出价
        if before_1_low < self.Watch_Buy_Price and before_1_close < self.Reverse_Sell_Price:
            if  self.pos != 0 and self.ctaEngine.offset=='卖开':  #判断是否持有多头
                self.ctaEngine.close(ordersymbol=bar.sec_id, direction=1, price=bar.close, volume=1, bar=bar)
                self.ctaEngine.open(ordersymbol=bar.sec_id, direction=1, price=bar.close, volume=1, bar=bar)

