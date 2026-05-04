import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def tmp_db(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path}/test.db"


def test_migration_upgrade_creates_all_tables(tmp_db: str, tmp_path: Path) -> None:
    pkg_dir = Path(__file__).parents[1]  # packages/app/
    env = {
        **os.environ,
        "ECHOBOX_APP_DB_URL": tmp_db,
        "ECHOBOX_APP_LLM_API_KEY": "stub",
    }
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=pkg_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"alembic stderr: {result.stderr}"

    import sqlite3

    db_path = tmp_db.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {row[0] for row in cur.fetchall()}
    conn.close()

    expected = {
        "alembic_version",
        "annotations",
        "chat_messages",
        "images",
        "labels",
        "prediction_runs",
        "projects",
    }
    assert expected.issubset(tables), f"missing tables: {expected - tables}"
