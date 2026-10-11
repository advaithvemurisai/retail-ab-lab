"""Normal-approximation power and sample size for a difference in means.

Implemented in `pricing` without scipy so the web API can use them; re-exported here.
"""

from .pricing import power_two_means, required_total_n, weeks_needed

__all__ = ["power_two_means", "required_total_n", "weeks_needed"]
