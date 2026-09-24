# RetailLab

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://retail-ab-lab-bnwnskexpoqbajnhzqgnkh.streamlit.app/)

**[Live app →](https://retail-ab-lab-bnwnskexpoqbajnhzqgnkh.streamlit.app/)**

## The business problem

Marketing says the e-mail campaign worked. Sales says revenue is up. Finance asks what it actually earned, and whether to keep sending.

Those answers usually disagree because each team counts differently. Click-through reports credit the e-mail with every purchase an e-mailed customer makes, including ones that would have happened anyway. And a revenue lift only matters if it covers the product margin and the cost of sending.

RetailLab settles the question with a real randomized experiment (the Hillstrom e-mail test: 64,000 customers split between men's e-mail, women's e-mail and no e-mail) and a profit-and-loss view, not a p-value alone. It ends in one plain recommendation:

| Verdict | Meaning |
| --- | --- |
| **SHIP** | The lift is real and the campaign earns its hurdle return. |
| **DON'T SHIP** | The campaign hurts revenue, loses money, harms a customer group, or misses the hurdle. |
| **KEEP TESTING** | The evidence isn't decisive yet; the app says how much longer to run. |
| **DON'T TRUST** | The experiment itself looks broken, so its results can't be relied on. |

## The questions it answers

| Business question | What the app shows |
| --- | --- |
| Did the campaign pay for itself? | Profit after product and sending costs, with the chance it lost money |
| How much revenue did the e-mail actually cause? | Credited revenue split into what the e-mail caused and what would have happened anyway |
| Who should get the next send? | Customer groups ranked by the profit the e-mail generated in each |
| Which e-mail should roll out? | Men's vs women's version, head to head |
| Would it pay in a different business? | The same result priced at apparel, grocery and restaurant margins |
| How long should the next test run? | The sample size needed to detect the smallest lift that pays |
| What could fool the team? | Common testing mistakes, and the checks that catch them |

Margin, cost per e-mail and the return hurdle are all adjustable in the sidebar, and the recommendation updates live.

## Headline result

- **Keep sending.** The e-mail roughly doubled revenue per customer, well above the lift needed to break even, with about a 1% chance of losing money.
- **The men's e-mail carries it.** It beats the women's version head to head; the women's e-mail is profitable on average but has about a 1-in-5 chance of losing money.
- **Credited revenue overstates the impact.** About half of the revenue attributed to the e-mail would have come in without it.
- **Margin decides the answer.** The same lift pays comfortably in apparel but is uncertain at grocery or restaurant margins.

## How it's built

- **Python and DuckDB:** one data model feeds every page, so marketing, sales and finance numbers always agree.
- **Streamlit:** the interactive app.
- **Decision rules:** the verdict comes from the same checks in a fixed order, and the first one that applies decides:
  1. **Trust:** did the experiment run correctly? If the customer groups aren't the sizes the design called for, something broke, and the verdict is DON'T TRUST.
  2. **Profitability:** does the campaign lose money or hurt a customer group? If so, DON'T SHIP.
  3. **Evidence:** is the gain real and large enough? If it clears the return hurdle, SHIP; if the result is still unclear, KEEP TESTING.

  The order means a striking profit number from a broken experiment can never lead to SHIP. The rules live in one function in [`src/retaillab/decision.py`](src/retaillab/decision.py), and automated tests check that each scenario produces the right verdict.
- **Proven methods:** the statistics follow published work from teams that run large-scale online experiments, such as Microsoft and LinkedIn. Examples include catching broken experiments, reducing noise so tests finish sooner, and avoiding false winners when results are checked repeatedly or many groups are compared at once. See [REFERENCES.md](REFERENCES.md).

## Run it

```bash
git clone https://github.com/advaithvemurisai/retail-ab-lab.git
cd retail-ab-lab
pip install -r requirements.txt
python scripts/get_data.py          # downloads the public data
streamlit run app/streamlit_app.py
```

Without the data, the app runs on clearly labelled synthetic data instead. Run `pytest` for the tests.

## Data and limitations

- **Data:** the [Hillstrom MineThatData e-mail experiment](https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html) (Kevin Hillstrom, 2008) and sector gross margins from Damodaran (NYU Stern). Both are downloaded at runtime rather than committed; see [DATA_SOURCES.md](DATA_SOURCES.md).
- **Limitations:**
  - The cost per e-mail is an assumption.
  - Sector margins are industry averages, not one retailer's books.
  - Results cover a two-week window, so longer-term effects such as unsubscribes aren't included.
