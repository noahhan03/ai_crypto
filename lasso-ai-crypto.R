library('stringr')
library('glmnet')

# Coefficients extraction function
extract <- function(o, s) { 
  index <- which(coef(o, s) != 0) 
  data.frame(name=rownames(coef(o))[index], coef=coef(o, s)[index]) 
}

# Suppress scientific notation
options(scipen=999)

# Command-line arguments
args <- commandArgs(TRUE)

# Input and model file names
input_file <- args[1]
model_file <- paste0(str_replace(input_file, ".csv", ""), "-lasso-5s-2std.csv")

# Read data
filtered <- read.csv(input_file)
mid_std <- sd(filtered$mid_price)
message(round(mid_std, 0))

# Data preprocessing
filtered_no_time_mid <- subset(filtered, select = -c(mid_price, timestamp))

# Calculate return_diff
return_diff <- c(0, diff(filtered$mid_price) / head(filtered$mid_price, -1))
filtered$return_val <- return_diff

# Remove NA values
filtered <- na.omit(filtered)

# Check for non-numeric columns and convert them to numeric
filtered_no_time_mid[] <- lapply(filtered_no_time_mid, function(x) {
  if (is.factor(x)) x <- as.numeric(as.character(x))
  x
})

# Add return_val to filtered_no_time_mid
filtered_no_time_mid$return_val <- filtered$return_val

# Remove rows with NA values
filtered_no_time_mid <- na.omit(filtered_no_time_mid)

# Define x and y
y <- filtered_no_time_mid$return_val
x <- subset(filtered_no_time_mid, select = -return_val)

# Ensure x columns are numeric
x[] <- lapply(x, function(col) {
  as.numeric(as.character(col))
})

# Convert x to matrix
x <- as.matrix(x)

# Model fitting
cv_fit <- cv.glmnet(x = x, y = y, alpha = 1, intercept = FALSE, lower.limits = 0, nfolds = 5)
fit <- glmnet(x = x, y = y, alpha = 1, lambda = cv_fit$lambda.1se, intercept = FALSE, lower.limits = 0)

# Extract coefficients
df <- extract(fit, s = 0.1)
df <- t(as.data.frame(df))

# Save the results to CSV
write.csv(df, file = model_file, row.names = FALSE)

cat("Results have been saved in", model_file, "\n")