"""Populate sample endpoints once (no live requests during seeding)."""
from .database import init_db, list_endpoints, add_endpoint

SAMPLES = [
    ("Example Website", "https://example.com", "GET", 200, "Example Domain"),
    ("HTTPBin Status", "https://httpbin.org/status/200", "GET", 200, ""),
    ("HTTPBin JSON", "https://httpbin.org/json", "GET", 200, "slideshow"),
]


def seed(db_path=None):
    init_db(db_path)
    if not list_endpoints(db_path):
        for item in SAMPLES:
            add_endpoint(*item, db_path=db_path)
        return len(SAMPLES)
    return 0


if __name__ == "__main__":
    print(f"Added {seed()} sample endpoints")
