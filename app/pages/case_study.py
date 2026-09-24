import streamlit as st

from app.ui.components import header, money
from app.ui.context import get_readout, load_data, load_margin_table
from retaillab.data import campaign_view
from retaillab.finance import attributed_incremental

data, source = load_data()
margins = load_margin_table()
pooled, mens, womens = (get_readout(variant) for variant in ("any", "mens", "womens"))
a = pooled.assumptions
attribution = attributed_incremental(campaign_view(data, "any"))
leader, trailer = (mens, womens) if mens.economics["roi"] >= womens.economics["roi"] else (
    womens, mens
)
names = {"mens": "men's", "womens": "women's"}

header("Portfolio", "Case study")
if source == "demo":
    st.info("Figures below come from synthetic demo data until the raw files are downloaded.")

st.markdown(
    f"""
### Problem
A retailer's marketing team reports that an e-mail campaign drove
{money(attribution['attributed'], markdown=True)} in attributed revenue. Finance wants to know what it earned, and whether to keep sending.

### Approach
- **Randomized evidence.** {len(data):,} customers split into thirds: no e-mail, men's e-mail,
  women's e-mail (Hillstrom, 2008). A split check (SRM) runs before anything is interpreted.
- **Unit economics.** Revenue lift is priced at {a.gross_margin:.1%} gross margin
  ({'Damodaran, ' + margins['as_of'] if margins['source'] == 'damodaran' else 'placeholder'})
  and \\${a.contact_cost:.2f} per e-mail, then reported as contribution with a bootstrap interval.
- **One decision rule.** Validity, downside, segment harm, ROI hurdle, and power feed one verdict.

### Findings
- **Pooled campaign: {pooled.verdict.label}.** Revenue per customer rose
  {pooled.revenue_lift:+.0%} against a {pooled.break_even_lift:.0%} break-even bar;
  contribution {money(pooled.economics['contribution'], markdown=True)}
  (95% CI {money(pooled.contribution['ci_low'], markdown=True)} to
  {money(pooled.contribution['ci_high'], markdown=True)}).
- **The {names[leader.assumptions.variant]} e-mail carries it.** {leader.revenue_lift:+.0%} lift
  and {leader.economics['roi']:+.0%} ROI, against {trailer.revenue_lift:+.0%} and
  {trailer.economics['roi']:+.0%} for the {names[trailer.assumptions.variant]} e-mail, whose
  chance of loss is {trailer.contribution['chance_of_loss']:.0%}.
- **Attribution overstates.** {attribution['gap_pct']:.0%} of revenue from e-mailed customers
  would have happened without the e-mail.
- **CUPED is not free sensitivity.** Past-year spend explains
  {pooled.cuped['variance_reduction']:.2%} of two-week spend variance here, so it saves almost
  nothing.

### Limitations
Contact cost is an assumption. Damodaran margins are US public-company sector averages, not
this retailer's books. Hillstrom has no timestamps, so peeking is simulated. Revenue is a
two-week window and ignores longer-run effects such as unsubscribes.
"""
)
