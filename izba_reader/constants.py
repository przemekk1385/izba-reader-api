from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

THREE_DECIMAL_PLACES = Decimal(10) ** -3
VALID_ASPECT_RATIO = Decimal("4") / Decimal("3")
