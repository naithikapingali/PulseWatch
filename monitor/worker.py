"""Optional independent scheduler; run in a second terminal."""
import argparse
import time
from .database import init_db
from .service import run_checks


def main():
    parser = argparse.ArgumentParser(description="Periodic HTTP health checker")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between rounds (minimum 10)")
    parser.add_argument("--once", action="store_true", help="Check once and exit")
    args = parser.parse_args()
    if args.interval < 10:
        parser.error("Interval must be at least 10 seconds")
    init_db()
    try:
        while True:
            outcomes = run_checks()
            print(f"Checked {len(outcomes)} endpoints; healthy={sum(x['healthy'] for x in outcomes)}", flush=True)
            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Monitor stopped")


if __name__ == "__main__":
    main()
