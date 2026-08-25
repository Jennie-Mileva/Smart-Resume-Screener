from backend.app.database import Base, engine
from backend.app.models.candidate import Candidate
from backend.app.models.resume_profile import ResumeProfile
from backend.app.models.job import Job
from backend.app.models.screening_result import ScreeningResult


def test_database_tables_exist():
    tables = Base.metadata.tables

    assert "candidates" in tables
    assert "resume_profiles" in tables
    assert "jobs" in tables
    assert "screening_results" in tables


def test_database_can_connect():
    with engine.connect() as connection:
        result = connection.exec_driver_sql(
            "SELECT 1"
        )

        assert result.scalar() == 1