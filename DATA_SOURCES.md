# Data sources

- Hillstrom MineThatData Email Challenge: https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html. Runtime download only from the CSV link on Kevin Hillstrom's post. The post describes 64,000 customers randomized across Mens E-Mail, Womens E-Mail, and No E-Mail and tracks two-week outcomes. Credit Kevin Hillstrom. No redistribution license is stated on the source page, so verify before publication.
- X5 RetailHero uplift: https://ods.ai/competitions/x5-retailhero-uplift-modeling/data. The page identifies `clients.csv`, `purchases.csv`, and `uplift_train.csv`; use `uplift_train` only because `uplift_test` has no outcomes. Review the competition terms and the site's data-use terms before use.
- Fast Food Marketing Campaign A/B Test: Kaggle `chebotinaa`, originally an IBM Watson Analytics sample. Place `WA_Marketing-Campaign.csv` in `data/raw/` and confirm its license.
- Damodaran Margins by Sector: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/margin.html. The page states the data is as of January 2026 and links `margin.xls`. RetailLab maps exact source sectors `Apparel`, `Retail (Grocery and Food)`, and `Restaurant/Dining`; production values are read from the workbook and never hardcoded.

Dunnhumby Complete Journey is README-only because it is observational and is not used for causal claims. CI uses deterministic fixtures and no network. Verify the Kaggle and X5 terms before publication.
