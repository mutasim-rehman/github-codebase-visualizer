import sys
from analyzer.cli import main

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nAnalysis cancelled by user.")
        sys.exit(130)
