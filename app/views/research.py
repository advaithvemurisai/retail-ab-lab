import streamlit as st

from app.ui.components import header

header("Evidence", "Research")
st.markdown("""
**Methods**
- [CUPED](https://exp-platform.com/Documents/2013-02-CUPED-ImprovingSensitivityOfControlledExperiments.pdf) (Deng, Xu, Kohavi, Walker 2013): pre-period covariates reduce variance by ρ².
- [SRM taxonomy](https://exp-platform.com/Documents/2019_KDDFabijanGupchupFuptaOmhoverVermeerDmitriev.pdf) (Fabijan et al. 2019): allocation failures should stop interpretation.
- [Always-valid inference](https://arxiv.org/abs/1512.04922) (Johari, Pekelis, Walsh 2015): repeated looks need sequential correction.
- [Benjamini and Hochberg (1995)](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x): false discovery rate control across segments.
- [Observational vs randomized ad measurement](https://kellogg.northwestern.edu/faculty/gordon_b/files/fb_comparison.pdf) (Gordon et al.): why attribution overstates.

**Data**
- [Hillstrom MineThatData e-mail challenge](https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html) (2008) and [Radcliffe's analysis](https://stochasticsolutions.com/pdf/HillstromChallenge.pdf).
- [Damodaran margins by sector](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/margin.html).
""")
