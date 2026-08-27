"""Entry point for python -m hypertext.tgc

Usage:
  python -m hypertext.tgc prep --cards-dir demo_cards
  python -m hypertext.tgc print --cards-dir demo_cards
  python -m hypertext.tgc upload --cards-dir demo_cards
"""

import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m hypertext.tgc <command> [options]")
        print("")
        print("Commands:")
        print("  prep    Prepare cards for manual TGC upload (batched into 25s)")
        print("  print   Export cards to print-ready PDF for Office Depot")
        print("  upload  Upload cards to TGC via API")
        print("")
        print("Examples:")
        print("  python -m hypertext.tgc prep --cards-dir demo_cards")
        print("  python -m hypertext.tgc print --cards-dir demo_cards")
        print("  python -m hypertext.tgc print --cards-dir demo_cards --output playtest.pdf")
        print("  python -m hypertext.tgc upload --cards-dir demo_cards --dry-run")
        sys.exit(1)

    command = sys.argv[1]
    sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove command from argv

    if command == "prep":
        from .prep import main as prep_main
        sys.exit(prep_main())
    elif command == "print":
        from .print_export import main as print_main
        sys.exit(print_main())
    elif command == "upload":
        from .upload import main as upload_main
        upload_main()
    else:
        print(f"Unknown command: {command}")
        print("Use 'prep', 'print', or 'upload'")
        sys.exit(1)


if __name__ == "__main__":
    main()
