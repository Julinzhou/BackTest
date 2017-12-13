# encoding: UTF-8

""" l
展示如何执行策略回测。
"""
from __future__ import division
import  time
import  os
from BackTestingEngine.backtestingEngine import BacktestEngine
if __name__ == '__main__':
    t1 = time.time()
    from Strategy.strategyDualThrust import DualThrustStrategy
    # 创建回测引擎
    engine = BacktestEngine()
    # 设置引擎的回测模式为K线
    # 设置回测用的数据起始日期
    engine.setStartDate("2015-01-01 09:00:00")
    engine.setEndDate("2015-01-30 15:00:00")
    # 设置产品相关参数
    engine.setSlippage(0)  # 股指1跳
    engine.setRate(0.0003)  # 万0.3
    engine.setSize(10)  # 股指合约大小
    engine.setPriceTick(1) # 股指最小价格变动
    # 在引擎中创建策略对象
    engine.initStrategy(DualThrustStrategy)
    # 设置使用的历史数据
    engine.setDataRet("CZCE.SR",60 ,engine.startDate,engine.endDate)
    engine.runBacktesting()
    # 显示回测结果
    engine.showBacktestingResult()
    t2 = time.time()
    print('spending %s seconds for whole procession') % (t2 - t1)