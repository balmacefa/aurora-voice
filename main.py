"""Aurora - Punto de entrada principal"""

import sys
from aurora.app import App
from aurora.errors import UnsupportedOSError


def main():
    """Función principal"""
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
