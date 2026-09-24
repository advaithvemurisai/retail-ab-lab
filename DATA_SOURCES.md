# Data sources

Raw files are downloaded at runtime by `scripts/get_data.py` into `data/raw/`, which is git-ignored.

- **Hillstrom MineThatData E-Mail Challenge** (2008): https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html. The data has 64,000 customers randomized in equal thirds to Mens E-Mail, Womens E-Mail, and No E-Mail, with two-week visit, conversion, and spend outcomes. Credit Kevin Hillstrom. The source page states no redistribution license, so the CSV is not committed.
- **Damodaran Margins by Sector**: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/margin.html. RetailLab reads `Apparel`, `Retail (Grocery and Food)`, and `Restaurant/Dining` from `margin.xls`. The as-of date comes from the workbook's "Date updated" cell. No margin values are hard-coded.

## Demo mode

When the raw files are absent, `retaillab.data.demo_email` generates synthetic customers with the Hillstrom schema, and `data/fixtures/sector_margins_demo.csv` supplies placeholder margins. The app labels both as illustrative. Neither is a published result.

## Considered and not used

- X5 RetailHero uplift and the Kaggle Fast Food Marketing Campaign A/B test. Both need manual download and license review. The Fast Food test also has too few independent stores for a credible cluster-level readout.
- Dunnhumby Complete Journey. It is observational, so it cannot support causal claims.
