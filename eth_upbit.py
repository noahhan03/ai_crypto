import datetime
import time
import pyupbit
import pandas as pd 


now = datetime.datetime.now()
print("Current Time : ",now.strftime('%H:%M:%S'))
# print("반복 횟수 입력 n : ")
# n=int(input())

# print("n 시간 동작 입력 받기 : ")
hours = 24
end_time = now + datetime.timedelta(hours=hours)
cnt=0
current_day = now.date()
file_name = f"{current_day}_upbit_orderbook.csv"


with open(file_name, 'w') as f:
    f.write('price|quantity|type|timestamp\n')

while datetime.datetime.now() < end_time:
    now = datetime.datetime.now()
    new_day = now.date()
    if new_day != current_day:
        current_day = new_day
        file_name = f"{current_day}_upbit_orderbook.csv"
        with open(file_name, 'w') as f:
            f.write('price|quantity|type|timestamp\n')
    orderbook = pyupbit.get_orderbook(ticker="KRW-ETH")
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    # print(orderbook)
    # timestamp = datetime.datetime.now()
    # req_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    
    cnt=cnt+1
    
    asks = sorted([(item['ask_price'], item['ask_size']) for item in orderbook['orderbook_units']], key=lambda x: x[0])
    bids = sorted([(item['bid_price'], item['bid_size']) for item in orderbook['orderbook_units']], key=lambda x: x[0], reverse=True)

    # print("매도(Ask) 목록:")
    # ask_n=0
    # for ask in asks:
    #     print(f"가격: {ask[0]}, 수량: {ask[1]}")
    #     ask_n=ask_n+
    #     if(ask_n==5):
    #         print("방금 윗줄이 level 5임")
    
    # print("\n매수(Bid) 목록:")
    # bid_n=0
    # for bid in bids:
    #     print(f"가격: {bid[0]}, 수량: {bid[1]}")
    #     bid_n=bid_n+1
    #     if(bid_n==5):
    #         print("방금 윗줄이 level 5임")
    top_asks = asks[:5]  # 상위 5개 레벨
    top_bids = bids[:5]  

    combined = [{'price': ask[0], 'quantity': ask[1], 'type': 1, 'timestamp':timestamp} for ask in top_asks] + [
        {'price': bid[0], 'quantity': bid[1], 'type': 0, 'timestamp': timestamp} for bid in top_bids]

    df = pd.DataFrame(combined)
    # df.to_csv('orderbook.csv', index=False,sep='|')
    with open(file_name, 'a') as f:
        df.to_csv(f, header=False, index=False, sep='|')
    # if n==cnt: 
    #     break

    time.sleep(5.0)

print("END")