"""pitchplan: answer "how should we pitch to this hitter?" from Statcast data."""
from .pipeline import PlanResult, build_plan
from .report import plan_bullets, write_html

__all__ = ["PlanResult", "build_plan", "plan_bullets", "write_html"]
__version__ = "0.1.0"
