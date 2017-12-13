# encoding:UTF-8
from __future__ import division
from collections import  OrderedDict
from gmsdk import  StrategyBase
import  pandas as pd
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import os
from pyecharts import Kline,Line,Grid,Overlap,Bar,Scatter,EffectScatter
import  numpy as np
from datetime import  datetime,timedelta
from  BackTestingEngine.vtObject import VtOrderData
class BacktestEngine(object):
    def __init__(self):
        #记录交易信息
        self.tradeDict = pd.DataFrame(columns=["vtSymbol","tradeID","direction","offset","volume","dtime","price"])
        self.tradeCount = 0
        self.symbol = ''  # 交易品种
        # 设置log列表
        self.logList = []
        # 设置起始日期和结束日期
        self.startDate = ""
        self.endDate = ""
        # 设置滑点 、佣金比例、合约大小、最小价格变动
        self.slippage = 0  # 回测时假设的滑点
        self.rate = 0  # 回测时假设的佣金比例（适用于百分比佣金）
        self.size = 1  # 合约大小，默认为1
        self.priceTick = 0  # 价格最小变动
        # 回测相关
        self.strategy = None  # 回测策略
        self.tick = None
        self.bar = None
        self.dt = None  # 最新的时间

        # 设置掘金api接口
        self.offset = ''
        self.order = []
        self.order_list = OrderedDict()
        self.ret = StrategyBase(username='13554406825', password='qq532357515')
    def initStrategy(self ,strategy):
        self.strategy = strategy(self)
    def setDataRet(self, symbol, bartype ,start_time ,end_time):
        self.symbol = symbol
        print(u'开始载入数据')
        start_time = datetime.strptime(start_time,"%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        delta_time = end_time-start_time #判断时间区间长度,因为掘金单次取的长度有限，不超过120天
        if delta_time.days < 120:
            start_time = datetime.strftime(start_time, "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strftime(end_time, "%Y-%m-%d %H:%M:%S")
            self.dbCursor = self.ret.get_bars(symbol, bartype, start_time, end_time)
        elif delta_time.days >120 and delta_time.days <240:

            middle_time = datetime.strftime((start_time + timedelta(days=120)),"%Y-%m-%d %H:%M:%S")
            start_time = datetime.strftime(start_time, "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strftime(end_time, "%Y-%m-%d %H:%M:%S")
            self.dbCursor =  self.ret.get_bars(symbol, bartype, start_time,middle_time)
            dbCursor = self.ret.get_bars(symbol, bartype, middle_time,end_time)
            self.dbCursor.extend(dbCursor)
        elif delta_time.days>240:

            middle_time0 = datetime.strftime((start_time + timedelta(days=120)), "%Y-%m-%d %H:%M:%S")
            middle_time1 = datetime.strftime((start_time + timedelta(days=240)), "%Y-%m-%d %H:%M:%S")
            start_time = datetime.strftime(start_time, "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strftime(end_time, "%Y-%m-%d %H:%M:%S")
            self.dbCursor = self.ret.get_bars(symbol, bartype, start_time, middle_time0)
            dbCursor = self.ret.get_bars(symbol, bartype,middle_time0, middle_time1)
            dbCursor1 = self.ret.get_bars(symbol, bartype, middle_time1, end_time)
            self.dbCursor.extend(dbCursor)
            self.dbCursor.extend(dbCursor1)

        print("载入数据完成")
    def runBacktesting(self):
        for bar in self.dbCursor:
            self.newBar(bar)
    def newBar(self, bar):
        """新的K线"""
        self.crossorder(bar)
        self.strategy.onBar(bar)  # 推送K线到策略中
    def open(self,ordersymbol , direction,price ,volume ,bar): # 开仓 ，direction表示方向，1表示多，-1表示空
        self.strategy.pos = self.strategy.pos + direction*volume
        self.tradeCount += 1
        self.offset = ["买开" if direction==1 else "卖开"][0]
        date = bar.strendtime[:10]
        time = bar.strendtime[11:19]
        self.dt = datetime.strptime(date +' '+time,"%Y-%m-%d %H:%M:%S")
        self.order = [bar.sec_id, self.tradeCount, direction, self.offset, volume,self.dt]
        self.order_list[self.tradeCount] = self.order
    def close(self, ordersymbol ,direction, price , volume, bar):# 平仓，1表示买平，-1表示卖平
        self.strategy.pos = self.strategy.pos + direction * volume
        self.tradeCount += 1
        self.offset = ["买平" if direction==1 else "卖平"][0]
        date = bar.strendtime[:10]
        time = bar.strendtime[11:19]
        self.dt = datetime.strptime(date + ' ' + time, "%Y-%m-%d %H:%M:%S")
        self.order=[ bar.sec_id, self.tradeCount, direction, self.offset, volume,self.dt]  #生成订单,此时不包括成交价格，
        self.order_list[self.tradeCount] = self.order                              # 等下一个bar传来按照收盘价成交
    def crossorder(self,bar):
        for orderID, order in self.order_list.items():
            order.append(bar.open)             #增加订单成交价格
            self.tradeDict.loc[order[1]] = order
        self.order_list.clear()
    def calculateBacktestingResult(self):
        """
        计算回测结果
        """
        print(u'计算回测结果')

        # 首先基于回测后的成交记录，计算每笔交易的盈亏
        resultList = []  # 交易结果列表
        longTrade = []  # 未平仓的多头交易
        shortTrade = []  # 未平仓的空头交易
        tradeTimeList = []  # 每笔成交时间戳
        posList = [0]  # 每笔成交后的持仓情况
        for i in range(len(self.tradeDict)):
            trade = self.tradeDict.iloc[i]
            # 多头交易
            if trade.direction == 1:
                # 如果尚无空头交易
                if not shortTrade:
                    longTrade.append(trade)
                # 当前多头交易为平空
                else:
                    while True:
                        entryTrade = shortTrade[0]
                        exitTrade = trade

                        # 清算开平仓交易
                        closedVolume = min(exitTrade.volume, entryTrade.volume)
                        result = TradingResult(entryTrade.price, entryTrade.dtime,
                        exitTrade.price, exitTrade.dtime,
                        -closedVolume, self.rate, self.slippage, self.size)
                        resultList.append(result)
                        posList.extend([-1, 0])
                        tradeTimeList.extend([result.entryDt, result.exitDt])
                        # 计算未清算部分
                        entryTrade.volume -= closedVolume
                        exitTrade.volume -= closedVolume

                        # 如果开仓交易已经全部清算，则从列表中移除
                        if not entryTrade.volume:
                            shortTrade.pop(0)

                        # 如果平仓交易已经全部清算，则退出循环
                        if not exitTrade.volume:
                            break

                        # 如果平仓交易未全部清算，
                        if exitTrade.volume:
                            # 且开仓交易已经全部清算完，则平仓交易剩余的部分
                            # 等于新的反向开仓交易，添加到队列中
                            if not shortTrade:
                                longTrade.append(exitTrade)
                                break
                            # 如果开仓交易还有剩余，则进入下一轮循环
                            else:
                                pass

            # 空头交易
            else:
                # 如果尚无多头交易
                if not longTrade:
                    shortTrade.append(trade)
                # 当前空头交易为平多
                else:
                    while True:
                        entryTrade = longTrade[0]
                        exitTrade = trade

                        # 清算开平仓交易
                        closedVolume = min(exitTrade.volume, entryTrade.volume)
                        result = TradingResult(entryTrade.price, entryTrade.dtime,
                                               exitTrade.price, exitTrade.dtime,
                                               closedVolume, self.rate, self.slippage, self.size)
                        resultList.append(result)

                        posList.extend([1, 0])
                        tradeTimeList.extend([result.entryDt, result.exitDt])

                        # 计算未清算部分
                        entryTrade.volume -= closedVolume
                        exitTrade.volume -= closedVolume

                        # 如果开仓交易已经全部清算，则从列表中移除
                        if not entryTrade.volume:
                            longTrade.pop(0)

                        # 如果平仓交易已经全部清算，则退出循环
                        if not exitTrade.volume:
                            break

                        # 如果平仓交易未全部清算，
                        if exitTrade.volume:
                            # 且开仓交易已经全部清算完，则平仓交易剩余的部分
                            # 等于新的反向开仓交易，添加到队列中
                            if not longTrade:
                                shortTrade.append(exitTrade)
                                break
                            # 如果开仓交易还有剩余，则进入下一轮循环
                            else:
                                pass

        # 检查是否有交易
        if not resultList:
            print(u'无交易结果')
            return {}

        # 然后基于每笔交易的结果，我们可以计算具体的盈亏曲线和最大回撤等
        capital = 0        # 资金
        maxCapital = 0     # 资金最高净值
        drawdown = 0       # 回撤

        totalResult = 0    # 总成交数量
        totalTurnover = 0  # 总成交金额（合约面值）
        totalCommission = 0# 总手续费
        totalSlippage = 0  # 总滑点

        timeList = []      # 时间序列
        pnlList = []       # 每笔盈亏序列
        capitalList = []   # 盈亏汇总的时间序列
        drawdownList = []  # 回撤的时间序列

        winningResult = 0  # 盈利次数
        losingResult = 0  # 亏损次数
        totalWinning = 0  # 总盈利金额
        totalLosing = 0  # 总亏损金额

        for result in resultList:
            capital += result.pnl
            maxCapital = max(capital, maxCapital)
            drawdown = capital - maxCapital

            pnlList.append(result.pnl)
            timeList.append(result.exitDt)  # 交易的时间戳使用平仓时间
            capitalList.append(capital)
            drawdownList.append(drawdown)

            totalResult += 1
            totalTurnover += result.turnover
            totalCommission += result.commission
            totalSlippage += result.slippage

            if result.pnl >= 0:
                winningResult += 1
                totalWinning += result.pnl
            else:
                losingResult += 1
                totalLosing += result.pnl

        #计算盈亏相关数据
        winningRate = winningResult / totalResult * 100  # 胜率

        averageWinning = 0  # 这里把数据都初始化为0
        averageLosing = 0
        profitLossRatio = 0
        if winningResult:
            averageWinning = totalWinning / winningResult  # 平均每笔盈利
        if losingResult:
            averageLosing = totalLosing / losingResult  # 平均每笔亏损
        if averageLosing:
            profitLossRatio = -averageWinning / averageLosing  # 盈亏比
        # 返回回测结果
        d = {}
        d['capital'] = capital
        d['maxCapital'] = maxCapital
        d['drawdown'] = drawdown
        d['totalResult'] = totalResult
        d['totalTurnover'] = totalTurnover
        d['totalCommission'] = totalCommission
        d['totalSlippage'] = totalSlippage
        d['timeList'] = timeList
        d['pnlList'] = pnlList
        d['capitalList'] = capitalList
        d['drawdownList'] = drawdownList
        d['winningRate'] = winningRate
        d['averageWinning'] = averageWinning
        d['averageLosing'] = averageLosing
        d['profitLossRatio'] = profitLossRatio
        d['posList'] = posList
        d['tradeTimeList'] = tradeTimeList

        return d
    def output(self, content):
        """输出内容"""
        print str(datetime.now()) + "\t" + content
    def showBacktestingResult(self):
        """显示回测结果"""
        d = self.calculateBacktestingResult()
        # 输出
        self.output('-' * 30)
        self.output(u'第一笔交易：\t%s' % d['timeList'][0])
        self.output(u'最后一笔交易：\t%s' % d['timeList'][-1])
        self.output(u'总交易次数：\t%s' % formatNumber(d['totalResult']))
        self.output(u'总盈亏：\t%s' % formatNumber(d['capital']))
        self.output(u'最大回撤: \t%s' % formatNumber(min(d['drawdownList'])))
        self.output(u'平均每笔盈利：\t%s' % formatNumber(d['capital'] / d['totalResult']))
        self.output(u'平均每笔滑点：\t%s' % formatNumber(d['totalSlippage'] / d['totalResult']))
        self.output(u'平均每笔佣金：\t%s' % formatNumber(d['totalCommission'] / d['totalResult']))
        self.output(u'胜率\t\t%s%%' % formatNumber(d['winningRate']))
        self.output(u'盈利交易平均值\t%s' % formatNumber(d['averageWinning']))
        self.output(u'亏损交易平均值\t%s' % formatNumber(d['averageLosing']))
        self.output(u'盈亏比：\t%s' % formatNumber(d['profitLossRatio']))
        self.tradeDict.to_csv(os.getcwd()+"/trading_record/"+"交易记录.csv") #生成交易记录
        self.SaveTradeKline(d)                                              #生成K线
        # 绘图
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns           # 如果安装了seaborn则设置为白色风格
            sns.set_style('whitegrid')
        except ImportError:
            pass

        pCapital = plt.subplot(4, 1, 1)
        pCapital.set_ylabel("capital")
        pCapital.plot(d['timeList'], d['capitalList'], color='r', lw=0.8)
        pDD = plt.subplot(4, 1, 2)
        pDD.set_ylabel("DD")
        pDD.bar(range(len(d['drawdownList'])), d['drawdownList'], color='g')
        pPnl = plt.subplot(4, 1, 3)
        pPnl.set_ylabel("pnl")
        pPnl.hist(d['pnlList'], bins=50, color='c')
        pPos = plt.subplot(4, 1, 4)
        pPos.set_ylabel("Position")
        if d['posList'][-1] == 0:
            del d['posList'][-1]
        tradeTimeIndex = [item.strftime("%m/%d %H:%M:%S") for item in d['tradeTimeList']]
        xindex = np.arange(0, len(tradeTimeIndex), np.int(len(tradeTimeIndex) / 10))
        tradeTimeIndex = map(lambda i: tradeTimeIndex[i], xindex)
        pPos.plot(d['posList'], color='k', drawstyle='steps-pre')
        pPos.set_ylim(-1.2, 1.2)
        plt.sca(pPos)
        plt.tight_layout()
        plt.xticks(xindex, tradeTimeIndex,rotation=30)  # 旋转15
        # plt.savefig('%s+.png'%str(d['timeList'][0]))
        plt.show()
#-------------------------------------------------------------------
    # 生成交易K线
    def SaveTradeKline(self, d):
        Daily_bar = []
        Daily_time = []
        Daily_volume = []
        mark_points = []
        for i in self.dbCursor:
            time_now = datetime.strptime(i.strendtime[:10] + ' ' + i.strendtime[11:19], '%Y-%m-%d %H:%M:%S')
            if (Daily_bar == [] or (Daily_bar[-1][-1].day==time_now.day)):
                Daily_bar.extend([[i.open, i.high, i.low, i.close, time_now]])
                Daily_time.append(i.strendtime[11:19])
                Daily_volume.append(i.volume)
            elif (Daily_bar[-1][-1].day!=time_now.day):
                for j in range(len(self.tradeDict)):
                    if (self.tradeDict.loc[j+1].dtime > Daily_bar[0][4] and self.tradeDict.loc[j+1].dtime < Daily_bar[-1][4]):
                        mark_points.append(self.tradeDict.loc[j+1])
                self.process_html(Daily_time, Daily_bar, Daily_volume, mark_points)
                Daily_bar = []
                Daily_bar.extend([[i.open, i.high, i.low, i.close, time_now]])
                Daily_time = []
                Daily_time.append(i.strendtime[11:19])
                Daily_volume = []
                Daily_volume.append(i.volume)
                mark_points = []
        if Daily_bar != []:
            self.process_html(Daily_time, Daily_bar, Daily_volume, mark_points)
    def process_html(self,v1, v2, v3,v4):  # v1为k线数据，v2是时间字符串数据
        buy_point_time = [datetime.strftime(i.dtime, "%H:%M:%S") for i in v4 if i.direction==1]
        buy_point_price = [i.price for i in v4 if i.direction==1]
        sell_point_time = [datetime.strftime(i.dtime, "%H:%M:%S") for i in v4 if i.direction==-1]
        sell_point_price = [i.price for i in v4 if i.direction == -1]
#columns=["vtSymbol","tradeID","direction","offset","volume","dtime","price"])

        kline = Kline("%s k线" % v2[-1][-1],  width=1500,height=2000)  # 设置k线名称
        kline.add("分钟K线", v1, v2, is_datazoom_show=True)

        es1 = EffectScatter()
        es1.add(u"买点", buy_point_time,buy_point_price, effect_scale=3)
        es1.add(u"卖点",sell_point_time ,sell_point_price ,effect_scale=3,symbol="rect")
        overlap = Overlap()
        overlap.add(kline)
        overlap.add(es1)
        overlap.render(os.getcwd() + "/KLine_file/" + "%s__%s k线" %(self.symbol, v2[-1][-1]) + '.html')
#---------------------------------------------------------------------------------
# ----------------------------------------------------------------------
    def setSlippage(self, slippage):
        """设置滑点点数"""
        self.slippage = slippage
# ----------------------------------------------------------------------
    def setSize(self, size):
        """设置合约大小"""
        self.size = size

# ----------------------------------------------------------------------
    def setRate(self, rate):
        """设置佣金比例"""
        self.rate = rate
#--------------------------------------------------------------------
    def setStartDate(self, startDate='2010-04-16', initDays=10):
        """设置回测的启动日期"""
        self.startDate = startDate

# ----------------------------------------------------------------------
    def setEndDate(self, endDate=''):
        """设置回测的结束日期"""
        self.endDate = endDate
# ---------------------------------------------------------------------
    def setPriceTick(self, priceTick):
        """设置价格最小变动"""
        self.priceTick = priceTick
#---------------------------------------------------------------------------------
def formatNumber(n):
    """格式化数字到字符串"""
    rn = round(n, 2)  # 保留两位小数
    return format(rn, ',')  # 加上千分符
#--------------------------------------------------------------------------------
class TradingResult(object):
    """每笔交易的结果"""
    # ----------------------------------------------------------------------
    def __init__(self, entryPrice, entryDt, exitPrice,
                 exitDt, volume, rate, slippage, size):
        """Constructor"""
        self.entryPrice = entryPrice  # 开仓价格
        self.exitPrice = exitPrice  # 平仓价格

        self.entryDt = entryDt  # 开仓时间datetime
        self.exitDt = exitDt  # 平仓时间

        self.volume = volume  # 交易数量（+/-代表方向）

        self.turnover = (self.entryPrice + self.exitPrice) * size * abs(volume)  # 成交金额
        self.commission = self.turnover * rate  # 手续费成本
        self.slippage = slippage * 2 * size * abs(volume)  # 滑点成本
        self.pnl = ((self.exitPrice - self.entryPrice) * volume * size
                    - self.commission - self.slippage)  # 净盈亏
        self.yield_rate = self.pnl / self.exitPrice


