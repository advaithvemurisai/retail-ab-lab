"""Web API: prices the precomputed experiment statistics under the viewer's assumptions.

It imports only FastAPI and `pricing`, so it runs as a small Vercel function without pandas or
scipy. The statistics come from `webdata.build_readout`, written to readout.json at build time.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Query, Response

from .pricing import (
    Assumptions,
    mart_pnl,
    next_test_plan,
    price,
    promotion,
    sector_table,
    targeting_plan,
)

Variant = Literal["any", "mens", "womens"]
SegmentColumn = Literal["history_segment", "channel", "zip_code", "newbie"]
VARIANTS = ("any", "mens", "womens")
# Results depend only on the query and the deployed data, so the CDN can keep them.
CACHE = "public, max-age=300, s-maxage=86400, stale-while-revalidate=604800"


def clean(value):
    """JSON-safe: tuples to lists, dataclasses to dicts, non-finite floats to null."""
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return clean(asdict(value))
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def assumptions(
    variant: Variant = "any",
    margin: float = Query(0.4, gt=0, le=1),
    cost: float = Query(0.18, ge=0, le=10),
    min_roi: float = Query(0.0, ge=-1, le=10),
    weekly: int = Query(10_000, ge=1, le=10_000_000),
    cuped: bool = True,
) -> Assumptions:
    return Assumptions(
        variant=variant, gross_margin=margin, contact_cost=cost, minimum_roi=min_roi,
        weekly_customers=weekly, use_cuped=cuped,
    )


Priced = Annotated[Assumptions, Depends(assumptions)]


def priced(readout: dict, a: Assumptions) -> dict:
    block = readout["variants"][a.variant]
    metric = block["metrics"]["cuped" if a.use_cuped else "raw"]
    return price(
        metric["revenue"], block["baseline_revenue"], metric["draws"],
        metric["segments"]["history_segment"], a, readout["validity"]["failed"],
    )


def create_app(readout_path: str | Path | None = None, readout: dict | None = None) -> FastAPI:
    """Pass the readout itself (tests) or the path of readout.json (deployments)."""
    app = FastAPI(title="RetailLab API", docs_url="/api/docs", openapi_url="/api/openapi.json")
    state: dict = {"readout": readout}

    def data() -> dict:
        if state["readout"] is None:
            state["readout"] = json.loads(Path(readout_path).read_text())
        return state["readout"]

    @app.get("/api/readout")
    def get_readout(response: Response, a: Priced) -> dict:
        """The verdict for every e-mail, plus the sector, creative and warehouse tables."""
        d = data()
        readouts = {v: priced(d, Assumptions(**{**asdict(a), "variant": v})) for v in VARIANTS}
        current = readouts[a.variant]
        revenue = d["variants"][a.variant]["metrics"]["cuped" if a.use_cuped else "raw"]["revenue"]
        promo = d["promotion"]["cuped" if a.use_cuped else "raw"]
        response.headers["Cache-Control"] = CACHE
        return clean(
            {
                "readouts": readouts,
                "sectors": sector_table(
                    d["margins"]["sectors"], revenue["difference"], current["baseline_revenue"],
                    current["revenue_lift_ci"], a.contact_cost,
                ),
                "promotion": promotion(promo["summary"], promo["pairs"], a),
                "mart_pnl": mart_pnl(d["warehouse"]["arms"], d["margins"]["sectors"], a.contact_cost),
            }
        )

    @app.get("/api/targeting")
    def get_targeting(
        response: Response,
        a: Priced,
        by: SegmentColumn = "history_segment",
        cap: int = Query(..., ge=0),
        significant: bool = False,
    ) -> dict:
        """Segments ranked by contribution per send, filled to the send budget."""
        d = data()
        segments = d["variants"][a.variant]["metrics"]["cuped" if a.use_cuped else "raw"]["segments"][by]
        response.headers["Cache-Control"] = CACHE
        return clean(targeting_plan(segments, d["audience"][by], a, cap, significant))

    @app.get("/api/planning")
    def get_planning(
        response: Response,
        a: Priced,
        lift: float = Query(..., gt=0, le=10),
        power: float = Query(0.8, gt=0, lt=1),
        share: float = Query(0.5, gt=0, lt=1),
    ) -> dict:
        """Customers and weeks the next test needs, and power by duration."""
        d = data()
        block = d["variants"][a.variant]
        response.headers["Cache-Control"] = CACHE
        return clean(
            next_test_plan(
                block["baseline_revenue"], block["pooled_sd"]["raw"], block["pooled_sd"]["cuped"],
                a, lift, power, share,
            )
        )

    return app
