import os
import tempfile

_db_dir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_db_dir}/test.db".replace("\\", "/")

from sqlalchemy.dialects.postgresql import JSONB  # noqa: E402
from sqlalchemy.ext.compiler import compiles  # noqa: E402


# custom_commands.responses is Postgres JSONB, which SQLite can't create.
# Store it as plain JSON in the test database instead.
@compiles(JSONB, "sqlite")
def _jsonb_as_json_on_sqlite(type_, compiler, **kw):
    return "JSON"


import pytest  # noqa: E402
import database  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

assert database.DATABASE_ENGINE.dialect.name == "sqlite"


@pytest.fixture(autouse=True)
def clean_grants():
    yield
    with Session(database.DATABASE_ENGINE) as session:
        session.query(database.SummaryGrants).delete()
        session.query(database.SheetTethers).delete()
        session.commit()
