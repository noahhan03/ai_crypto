# 필요한 라이브러리 로드
library(dplyr)

# 데이터 로드
input_file <- "ai-crypto-project-3-live-btc-krw.csv"
data <- read.csv(input_file)

# 데이터 구조 확인
str(data)

# 데이터 샘플 확인
head(data)

# PnL 계산 및 누적
cumulative_pnl <- 0

for (i in 1:nrow(data)) {
  pnl <- 0
  if (data$side[i] == 0) {  # 매도 거래인 경우
    pnl <- (data$price[i] - data$amount[i] / data$quantity[i]) * data$quantity[i] - data$fee[i]
  } else if (data$side[i] == 1) {  # 매수 거래인 경우
    pnl <- (data$amount[i] / data$quantity[i] - data$price[i]) * data$quantity[i] - data$fee[i]
  }
  cumulative_pnl <- cumulative_pnl + pnl
}

# 누적 PnL 출력
cat("Final cumulative PnL:", cumulative_pnl, "\n")