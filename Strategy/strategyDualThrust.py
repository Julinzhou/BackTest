#encoding:utf-8
from __future__ import division
import talib as ta
import numpy as np
from datetime import  datetime,time
class DualThrustStrategy(object):
    """DualThrust交易策略"""
    className = 'DualThrustStrategy'
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
        self.openintArray[-1] = bar.position
        self.bufferCount += 1

        if self.bufferCount < self.bufferSize:  # 缓存数量小于300则退出继续传入新的bar更新onbar
            return
        self.HH = max(self.highArray)
        self.LC = min(self.closeArray)
        self.HC = max(self.closeArray)
        self.LL = min(self.lowArray)
        self.Range = max(self.HH-self.LC,self.HC-self.LL)
        self.BuyLine = self.openArray[-1] + self.K1 * self.Range
        self.SellLine =self.openArray[-1] - self.K2 * self.Range
        if self.closeArray[-1]> self.BuyLine:
            if self.pos!=0 and (self.ctaEngine.offset=="卖开"):
                self.ctaEngine.close(bar.sec_id , 1 ,bar.close ,1 ,bar)
            elif self.pos==0:
                self.ctaEngine.open(bar.sec_id, 1, bar.close, 1, bar)
        elif self.closeArray[-1] < self.SellLine:
            if self.pos!=0 and (self.ctaEngine.offset=="买开"):
                self.ctaEngine.close(bar.sec_id ,-1,bar.close ,1 ,bar)
            elif self.pos==0:
                self.ctaEngine.open(bar.sec_id ,-1,bar.close ,1 ,bar)

        # 当价格向上突破上轨时，如果当时持有空仓，则先平仓，再开多仓；如果没有仓位，则直接开多仓；
        # 当价格向下突破下轨时，如果当时持有多仓，则先平仓，再开空仓；如果没有仓位，则直接开空仓；

