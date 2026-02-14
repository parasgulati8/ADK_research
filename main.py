"""
Entry point to trigger the research-dev swarm.
Run: python main.py "Your research query"
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.core.orchestrator import Orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Research-to-Dev Swarm")
    parser.add_argument("query", nargs="?", default="", help="Research query or technical goal")
    parser.add_argument("--research-only", action="store_true", help="Run only the research wing")
    parser.add_argument("--config", type=Path, default=None, help="Path to config dir")
    args = parser.parse_args()

    if not args.query.strip():
        parser.error("Provide a non-empty query (e.g. python main.py 'How to implement X')")

    orchestrator = Orchestrator(config_path=args.config)
    if args.research_only:
        result = orchestrator.run_research_wing(args.query)
    else:
        result = orchestrator.run_full_swarm(args.query)

    print("Result:", result)


if __name__ == "__main__":
    main()
