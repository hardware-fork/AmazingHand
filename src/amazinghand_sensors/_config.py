import tomllib
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def load_config() -> dict:
    """Return the parsed config.toml, cached after the first read."""
    path = Path(__file__).parent / "config.toml"
    with path.open("rb") as f:
        return tomllib.load(f)
