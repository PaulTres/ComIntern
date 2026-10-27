import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["COMINTERN_DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["COMINTERN_UPLOAD_DIR"] = f"{_tmp}/uploads"
