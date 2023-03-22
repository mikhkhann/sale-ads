from pathlib import Path

import sale_ads

(PKG_DIR,) = sale_ads.__path__
PKG_DIR = Path(PKG_DIR)
APP_DIR = PKG_DIR / "apps"
UNRELATED_UTILS_DIR = APP_DIR / "common/utils/unrelated/src"
SRC_DIR = PKG_DIR.parent
BASE_DIR = SRC_DIR.parent
LOCALE_DIR = BASE_DIR / "locale"
MEDIA_DIR = BASE_DIR / "media"
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"
