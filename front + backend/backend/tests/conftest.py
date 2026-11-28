import os
import tempfile

# Tests use a throwaway database so they never add rows to the real one.
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test_soc_events.db"
