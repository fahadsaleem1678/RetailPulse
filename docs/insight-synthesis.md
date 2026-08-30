# Insight Synthesis Checklist

Use this checklist after `analysis/core_metrics.sql` has run.

## Finding Selection

Choose 2 to 3 findings that have clear numbers and a decision-oriented implication:

- One funnel drop-off finding.
- One retention or repurchase finding.
- One segment, brand, category, or revenue concentration finding.

## Required Evidence

Each recommendation must cite:

- The metric table used.
- The time period covered.
- The denominator used.
- The metric value and comparison point.

## Writing Format

For each finding, write:

- Business question.
- Method.
- Metric result.
- Interpretation.
- Recommendation.

## Guardrails

- Do not claim causality from observational clickstream behavior.
- Do not hide missing `brand` or `category_code` rows.
- Do not mix event-level and session-level denominators.
- Keep chart titles explicit about denominator and time period.
- Keep the final case study readable in 5 minutes.
