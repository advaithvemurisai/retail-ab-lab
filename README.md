# RetailLab

RetailLab turns a randomized e-mail experiment into a finance decision. It prices the measured revenue lift at a sector gross margin and a per-send cost, checks that the experiment can be trusted, and returns one verdict: **SHIP**, **DON'T SHIP**, **KEEP TESTING**, or **DON'T TRUST**. Every assumption sits in the sidebar, and every number traces back to one DuckDB star schema.

## Questions

| Page | Question | How it is answered |
| --- | --- | --- |
| Overview | Should we ship? | SRM check, Welch test on revenue per customer, bootstrap contribution interval, power at break-even |
| Campaign ROI | Did the campaign pay for itself? | Incremental revenue → gross profit → e-mail cost → contribution |
| Attributed vs incremental | How much revenue was caused? | E-mail-attributed revenue split into the control-predicted baseline and causal lift |
| Who to send to | Which customers next? | Segment-level lift, BH-corrected, ranked by contribution per send, filled to a send budget |
| Which e-mail | Men's or women's creative? | Three-arm pairwise Welch tests with BH correction |
| Same lift, different economics | Would it pay in another sector? | Break-even lift per Damodaran sector against the observed lift's 95% interval |
| Test planning | How long should the next test run? | Sample size and weeks for the break-even lift, with and without CUPED |
| Pitfalls lab | What can fool the team? | Peeking simulation, a simulated logging bug caught by SRM, placebo segment slicing |

## Key findings (Hillstrom, Apparel margin, $0.18 per e-mail)

- **Ship the e-mail program.** Revenue per customer rose 91% against a 48% break-even lift. Contribution was about $6.8k (95% CI $1.5k to $11.7k), with a 1% chance of loss.
- **The men's e-mail carries it.** ROI was +143% for the men's e-mail and +34% for the women's, which still has a 21% chance of losing money. The men's e-mail wins head to head after BH correction (p = 0.03).
- **Attributed revenue is not incremental revenue.** 52% of revenue from e-mailed customers would have happened anyway.
- **Margin decides the answer.** The same lift clearly pays at apparel margins and is uncertain at grocery or restaurant margins.
- **CUPED is not free.** Past-year spend correlates with two-week spend at ρ = 0.02, so it removes only 0.05% of variance here.
- **Peeking is expensive.** Ten interim looks at an A/A test produce a false winner about 20% of the time.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/get_data.py        # Hillstrom CSV and Damodaran margin.xls into data/raw/
python scripts/build_warehouse.py # optional: writes data/retaillab.duckdb
streamlit run app/streamlit_app.py
ruff check .
pytest
```

Without `data/raw/`, the app runs on synthetic data shaped like Hillstrom, with clearly labelled placeholder margins, and says so in the sidebar. Set `RETAILLAB_DEMO=1` to force demo mode. The UI tests do this, so CI is deterministic. See [DATA_SOURCES.md](DATA_SOURCES.md) before redistributing data.

## Layout

```
src/retaillab/   data, validity, estimate, variance (CUPED), power, finance, decision, analysis, warehouse
sql/warehouse.sql  dim_customer, dim_campaign, dim_sector_finance, fact_exposure, fact_sales, mart_experiment, mart_pnl
app/             Streamlit multipage app; every decision page reads one cached analyze() readout
tests/           estimator, decision, and warehouse tests plus a render test for every page
```

## Limitations

The cost per e-mail is an assumption. Damodaran margins are averages for US public companies, not one retailer's books. Hillstrom has no timestamps, so the peeking demonstration is a simulation. Revenue covers a two-week window and ignores longer-run effects such as unsubscribes. Segment rankings use point estimates unless the BH filter is on.

## Suggested GitHub topics

`retail` `marketing-analytics` `finance` `ab-testing` `experimentation` `cuped` `duckdb` `streamlit` `incrementality`
