JOB_ROLE_LABELS: dict[str, str] = {
    "frontend_dev":   "Frontend Developer",
    "backend_dev":    "Backend Developer",
    "data_scientist": "Data Scientist",
}

# Bases de datos permitidas por job role
JOB_ROLE_DB_POLICY: dict[str, set[str]] = {
    "frontend_dev":   {"DataCo Analytics"},
    "backend_dev":    {"DataCo Analytics", "Reporting DB"},
    "data_scientist": {"DataCo Analytics", "Data Warehouse", "Reporting DB"},
}

JOB_ROLES = list(JOB_ROLE_LABELS.keys())


def get_allowed_databases(job_role: str | None) -> set[str]:
    """Retorna las BDs permitidas para un job role. Sin rol = sin acceso."""
    if not job_role:
        return set()
    return JOB_ROLE_DB_POLICY.get(job_role, set())


def can_access_database(job_role: str | None, database_name: str) -> bool:
    return database_name in get_allowed_databases(job_role)
