# RetailLab

RetailLab is an interactive retail decision lab that joins marketing experiments, sales outcomes, and finance benchmarks. It answers six questions for a CFO or CMO in 30 seconds, while keeping the statistical evidence inspectable.

## Questions

| Question | Data joined | Default answer |
| --- | --- | --- |
| Did the campaign pay for itself? | randomized email, revenue, margin | incremental contribution after contact cost |
| How much was incremental? | treatment and control revenue | attributed revenue overstates causal revenue |
| Who should receive the next send? | segment outcomes and economics | rank profit per dollar, then correct inference |
| Which promotion should roll out? | store clusters, weekly sales, restaurant margin | cluster-aware rollout economics |
| Can the same lift pay elsewhere? | contact cost and sector margins | break-even depends on unit economics |
| How long should the next test run? | power, CUPED, peeking | plan in weeks and dollars |

## Key findings

- Revenue up is not profit up.
- Attributed revenue is not incremental revenue.
- Public sector margins are benchmarks, not a retailer's books.
- CUPED can shorten a test when pre-period spend predicts the outcome.
- Peeking and broken splits can create false confidence.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/get_data.py
python scripts/build_warehouse.py
streamlit run app/streamlit_app.py
ruff check .
pytest
```

The app runs in deterministic demo mode until licensed raw files are placed in `data/raw/`. See [DATA_SOURCES.md](DATA_SOURCES.md) before downloading or redistributing data. The DuckDB model includes dimensions for customers, stores, markets, campaigns, and sector finance plus exposure, sales, pre-period, experiment, and P&L marts in the production path.

## Limitations

Contact costs are assumptions. Damodaran margins are public-company averages. Hillstrom has no timestamps, so peeking is a resampling demonstration. Fast Food has few independent stores. The datasets come from different companies and years and are joined through a common model, not one company's books. The demo fixture is not a published business result.

## Suggested GitHub topics

`retail` `marketing-analytics` `sales-analytics` `finance` `ab-testing` `experimentation` `cuped` `duckdb` `streamlit` `incrementality`
