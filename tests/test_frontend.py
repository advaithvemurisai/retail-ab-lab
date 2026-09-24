from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).parents[1] / "app" / "streamlit_app.py"

def test_landing_page_renders():
    app = AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    assert any("RetailLab" in item.value for item in app.markdown)
    assert len(app.metric) == 3

def test_campaign_page_renders():
    app = AppTest.from_file(APP).run(timeout=30)
    app.switch_page("pages/campaign_roi.py").run(timeout=30)
    assert not app.exception
    assert len(app.metric) == 2
