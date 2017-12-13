# encoding:utf-8
from gmsdk import  StrategyBase
import  pandas as pd
import  numpy as np
import  os,sys
from datetime import  datetime ,timedelta
ret = StrategyBase(username='13554406825', password='qq532357515')
#获取所需品种数据
def get_test_data(code , start_time, end_time):
    ret = StrategyBase(username='13554406825', password='qq532357515')
    Start_time = datetime.strptime(start_time , "%Y-%m-%d %H:%M:%S")
    End_time = datetime.strptime(end_time , "%Y-%m-%d %H:%M:%S")
    delta = Start_time - End_time
    a1 = delta.days / 120
    tem_end_time = start_time
    for i in range(a1+1):
        Start_time = Start_time + timedelta(days = i*120)
        tem_start_time = Start_time.strftime("%Y-%m-%d %H:%M:%S")
        End_time = Start_time + timedelta(days=(i+1) * 120)
        tem_end_time = End_time.strftime("%Y-%m-%d %H:%M:%S")
        data = ret.get_bars(code,60 ,tem_start_time , tem_end_time )
        Class_to_Pandas(data)
    data =  ret.get_bars(code,60 ,tem_end_time , end_time )
    Class_to_Pandas(data)
def Class_to_Pandas(data):# data 为bar列表
    tem_data =  pd.DataFrame(columns=["Symbol","date","time",
                                      "open","high","low","close",
                                      "volume","openIntrest","adj_factor","amount"])
    num = 0
    for i in data:
        row_value = [i.sec_id , i.strendtime[:10],i.strendtime[11:19],i.open,i.high,i.low ,i.close,
                     i.volume ,i.position ,i.adj_factor ,i.amount ]
        tem_data.loc[num] = row_value
        num +=1
    date0 = data[0].strendtime[:10]
    date1 = data[1].strendtime[:10]
    tem_data.to_csv(os.path.join(os.path.dirname(os.getcwd()) + "/csv_data/" , "%s__%s.csv"%(date0,date1)))
    print ("已经导入%s----%s的数据"%(date0,date1))

if __name__ == '__main__':
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # 现在的时间
    start_time = "2017-01-01 09:00:00"  # 数据起始时间
    get_test_data("SHFE.CU",start_time,time_now)  # 存数据到本地

