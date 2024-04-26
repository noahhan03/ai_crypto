import time
import requests
import pandas as pd
import datetime
import os

def create_filename():
    """현재 날짜를 기반으로 파일 이름 생성"""
    return datetime.datetime.now().strftime("%Y-%m-%d") + "-orderbook.csv"

filename = create_filename()

while True:
    try:
        # 현재 시간이 자정을 넘었는지 확인하여 파일 이름 업데이트
        if filename != create_filename():
            filename = create_filename()
            print("New day! Creating a new file:", filename)

        # Bithumb API를 통해 orderbook 데이터 가져오기
        response = requests.get('https://api.bithumb.com/public/orderbook/BTC_KRW/?count=5')
        book = response.json()

        data = book['data']

        bids = pd.DataFrame(data['bids'])
        bids.sort_values('price', ascending=False, inplace=True)
        bids['type'] = 0  # bid 타입은 0

        asks = pd.DataFrame(data['asks'])
        asks.sort_values('price', ascending=True, inplace=True)
        asks['type'] = 1  # ask 타입은 1

        # 현재 시간을 포함한 데이터프레임 생성
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # 소수점 다섯 자리까지
        bids['timestamp'] = timestamp
        asks['timestamp'] = timestamp

        # bids와 asks를 하나의 데이터프레임으로 합치기
        df = pd.concat([bids, asks])

        # 소수점 4자리까지 반올림
        df['quantity'] = df['quantity'].round(decimals=4)

        # 파일 경로 설정
        script_dir = os.path.dirname(__file__) if __file__ != '' else os.getcwd()
        file_path = os.path.join(script_dir, filename)

        # 출력 형식 변경 및 파일로 저장
        df.to_csv(file_path, index=False, mode='a', header=not os.path.exists(file_path), sep='|')

        print(f"Orderbook data saved to {file_path}")

        # 5초간 대기
        time.sleep(5)

    except Exception as e:
        print("An error occurred:", e)

