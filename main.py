"""Thin entrypoint — the application lives in src/firemap.

Run `pip install -e .` once, then either `python main.py` or the
installed `firemap` console script.
"""

from firemap.main import main

if __name__ == "__main__":
    main()
