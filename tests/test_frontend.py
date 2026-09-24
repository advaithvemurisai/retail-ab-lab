from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

APP = Path(__file__).parents[1] / "app" / "streamlit_app.py"
PAGES = [
    "campaign_roi", "attribution", "targeting", "promotion", "economics", "planning",
    "pitfalls", "data_model", "research", "case_study",
]


@pytest.fixture(autouse=True)
def demo_mode(monkeypatch):
    """Pin every UI test to the synthetic data so results do not depend on data/raw."""
    monkeypatch.setenv("RETAILLAB_DEMO", "1")
    st.cache_data.clear()
    st.cache_resource.clear()


def run(page: str | None = None) -> AppTest:
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    if page:
        app.switch_page(f"views/{page}.py").run()
    assert not app.exception, [item.value for item in app.exception]
    return app


def verdict(app: AppTest) -> str:
    return next(item.value for item in app.markdown if 'class="verdict' in item.value)


def test_landing_page_shows_a_verdict():
    app = run()
    assert any("RetailLab" in item.value for item in app.markdown)
    assert "<h2>SHIP</h2>" in verdict(app)
    assert [metric.label for metric in app.metric] == [
        "Incremental revenue", "Contribution", "ROI", "Chance of loss",
    ]
    assert any("Synthetic demo data" in item.value for item in app.warning)


@pytest.mark.parametrize("page", PAGES)
def test_every_page_renders(page):
    run(page)


def test_sidebar_cost_changes_the_verdict():
    app = run()
    app.number_input(key="email_cost").set_value(2.0).run()
    assert not app.exception
    assert "<h2>DON&#x27;T SHIP</h2>" in verdict(app)


def test_sidebar_variant_and_custom_margin():
    app = run()
    app.selectbox(key="variant").set_value("womens").run()
    app.selectbox(key="margin_source").set_value("Custom margin").run()
    app.slider(key="custom_margin").set_value(0.1).run()
    assert not app.exception
    assert "Women&#x27;s e-mail" in verdict(app)
    assert "<h2>SHIP</h2>" not in verdict(app)


def test_no_legacy_pages_folder():
    """A pages/ folder beside the entry script makes Streamlit run a deep-linked page
    before streamlit_app.py sets sys.path, so a cold start on /targeting fails to import."""
    assert not (APP.parent / "pages").exists()
