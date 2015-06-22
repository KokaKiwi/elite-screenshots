from pathlib import Path

app_root = Path().resolve()

DATA_PATH = app_root / 'images'

MAKO_TRANSLATE_EXCEPTIONS = False
MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MiB
