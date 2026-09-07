# Standard-Setting Impact Analysis
#
# Reads the pipeline's CSV exports (produced by `python -m src.pipeline`) and
# runs the statistical side of the impact-measurement methodology:
#   1. An OLS regression of illustrative post-adoption audit fees on adoption
#      timing (days relative to the standard's effective date) and sector,
#      to test whether late adoption is associated with higher audit fees.
#   2. A logistic regression of restatement incidence on adoption lag.
#   3. Summary tables of adoption-lag distribution and deliberation lag
#      (comment-close to issuance) by ASC topic, for comparison across
#      standard-setting cycles.
#
# Run from the project root: Rscript r_analysis/impact_analysis.R

suppressWarnings(suppressMessages({
  library(utils)
}))

exports_dir <- file.path("exports")
standards <- read.csv(file.path(exports_dir, "asu_standards.csv"), stringsAsFactors = FALSE)
adoptions <- read.csv(file.path(exports_dir, "firm_adoptions.csv"), stringsAsFactors = FALSE)

standards$effective_date_public <- as.Date(standards$effective_date_public)
standards$issued_date <- as.Date(standards$issued_date)
adoptions$adoption_date <- as.Date(adoptions$adoption_date)

panel <- merge(adoptions, standards[, c("asu_number", "topic_code", "effective_date_public", "issued_date")],
               by = "asu_number")
panel$lag_days <- as.numeric(panel$adoption_date - panel$effective_date_public)
panel$sector <- factor(panel$sector)
panel$restatement_filed <- as.integer(panel$restatement_filed)

cat("=== Standard-Setting Impact Analysis ===\n\n")
cat(sprintf("Standards analyzed: %d\n", nrow(standards)))
cat(sprintf("Firm-standard adoption records: %d\n\n", nrow(panel)))

# --- 1. Audit fee ~ adoption lag + sector -----------------------------------
fee_model <- lm(audit_fee_usd ~ lag_days + sector, data = panel)
cat("--- OLS: audit_fee_usd ~ lag_days + sector ---\n")
print(summary(fee_model))

# --- 2. Restatement incidence ~ adoption lag --------------------------------
restatement_model <- glm(restatement_filed ~ lag_days, data = panel, family = binomial())
cat("\n--- Logistic regression: restatement_filed ~ lag_days ---\n")
print(summary(restatement_model))
cat(sprintf(
  "\nOdds ratio per +30 days of adoption lag: %.3f\n",
  exp(coef(restatement_model)["lag_days"] * 30)
))

# --- 3. Adoption-lag distribution by ASC topic ------------------------------
cat("\n--- Adoption lag (days) by ASC topic ---\n")
lag_by_topic <- aggregate(lag_days ~ topic_code, data = panel,
                           FUN = function(x) c(mean = mean(x), median = median(x), sd = sd(x)))
print(lag_by_topic)

# --- 4. Deliberation lag (comment close -> issuance) vs. issuance-to-effective lag ---
# comment_deadline marks when the exposure draft's public comment window
# closed, which precedes final issuance -- so deliberation_lag_days is the
# time FASB spent re-deliberating after comments closed, before finalizing.
standards$comment_deadline <- as.Date(standards$comment_deadline)
standards$deliberation_lag_days <- as.numeric(standards$issued_date - standards$comment_deadline)
standards$issuance_to_effective_days <- as.numeric(standards$effective_date_public - standards$issued_date)

cat("\n--- Deliberation lag vs. issuance-to-effective lag, by standard ---\n")
print(standards[order(standards$issued_date),
                 c("asu_number", "topic_code", "deliberation_lag_days", "issuance_to_effective_days")])

correlation <- cor(standards$deliberation_lag_days, standards$issuance_to_effective_days, use = "complete.obs")
cat(sprintf("\nCorrelation(deliberation_lag_days, issuance_to_effective_days) = %.3f\n", correlation))

# Persist a compact results summary for downstream consumption (e.g. the VBA macro).
results <- data.frame(
  metric = c("fee_model_lag_days_coef", "fee_model_r_squared",
             "restatement_model_lag_days_coef", "deliberation_vs_effective_lag_correlation"),
  value = c(coef(fee_model)["lag_days"], summary(fee_model)$r.squared,
            coef(restatement_model)["lag_days"], correlation)
)
write.csv(results, file.path(exports_dir, "r_analysis_summary.csv"), row.names = FALSE)
cat("\nWrote exports/r_analysis_summary.csv\n")
