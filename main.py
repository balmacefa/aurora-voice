"""Aurora - Punto de entrada principal"""

import sys
from aurora.app import App
from aurora.errors import UnsupportedOSError


def main():
    """Función principal"""
    if "--check-update" in sys.argv:
        import json
        from aurora import update
        print(json.dumps(update.check_for_update(), ensure_ascii=False))
        sys.exit(0)
    if "--update" in sys.argv:
        import json
        from aurora import update
        res = update.check_and_apply(dry_run="--dry-run" in sys.argv)
        print(json.dumps(res, ensure_ascii=False))
        sys.exit(0)
    try:
        app = App()
        app.run()
    except UnsupportedOSError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCerrando Aurora...")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
