"""Extract, transform, validate, and load, as plain typed functions.

The steps share one in-memory DuckDB connection. ``extract`` loads the CSV into the ``raw``
table, ``validate`` refuses bad input before anything is written, ``transform`` runs the SQL in
``transform.sql``, and ``load`` writes Parquet.
"""

from pathlib import Path

import duckdb

SQL_PATH = Path(__file__).with_name("transform.sql")
RAW_TABLE = "raw"
COLUMN_TYPES = {
    "order_id": "BIGINT",
    "region": "VARCHAR",
    "product": "VARCHAR",
    "quantity": "INTEGER",
    "unit_price": "DECIMAL(12,2)",
}
REQUIRED_COLUMNS = ("order_id", "region", "product", "quantity", "unit_price")


class ValidationError(ValueError):
    """Raised when input data fails a check. The message names the column or the check."""


def extract(con: duckdb.DuckDBPyConnection, source: Path) -> None:
    """Read the CSV at ``source`` into the raw table, with the expected column types."""
    if not source.is_file():
        raise FileNotFoundError(f"input file not found: {source}")
    columns = ", ".join(f"'{name}': '{sql_type}'" for name, sql_type in COLUMN_TYPES.items())
    try:
        con.execute(
            f"CREATE OR REPLACE TABLE {RAW_TABLE} AS "
            f"SELECT * FROM read_csv(?, header = true, columns = {{{columns}}})",
            [str(source)],
        )
    except duckdb.Error as exc:
        raise ValidationError(
            f"{source} does not match the expected columns and types: {exc}"
        ) from exc


def validate(con: duckdb.DuckDBPyConnection) -> None:
    """Raise ``ValidationError`` unless the raw table has rows, no nulls, and no negative values."""
    checks = ["COUNT(*)"]
    checks += [f"COUNT(*) FILTER (WHERE {name} IS NULL)" for name in REQUIRED_COLUMNS]
    checks.append("COUNT(*) FILTER (WHERE quantity < 0 OR unit_price < 0)")
    total, *null_counts, negatives = _fetch_ints(
        con, f"SELECT {', '.join(checks)} FROM {RAW_TABLE}"
    )
    if total == 0:
        raise ValidationError("input has no rows: the file has a header but no data")
    for name, nulls in zip(REQUIRED_COLUMNS, null_counts, strict=True):
        if nulls:
            raise ValidationError(f"column {name} has {nulls} null value(s) in {total} row(s)")
    if negatives:
        raise ValidationError(f"quantity or unit_price is negative in {negatives} row(s)")


def transform(con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyRelation:
    """Run the aggregation in ``transform.sql`` over the raw table."""
    relation = con.sql(SQL_PATH.read_text(encoding="utf-8"))
    if relation is None:
        raise RuntimeError(f"{SQL_PATH.name} did not return a result set")
    return relation


def load(summary: duckdb.DuckDBPyRelation, output: Path) -> None:
    """Write the summary to ``output`` as Parquet, creating its folder if needed."""
    output.parent.mkdir(parents=True, exist_ok=True)
    summary.write_parquet(str(output))


def run_pipeline(source: Path, output: Path) -> Path:
    """Run every step in order on ``source`` and return the Parquet path written to ``output``."""
    con = duckdb.connect(":memory:")
    try:
        extract(con, source)
        validate(con)
        load(transform(con), output)
    finally:
        con.close()
    return output


def _fetch_ints(con: duckdb.DuckDBPyConnection, sql: str) -> tuple[int, ...]:
    rows = con.execute(sql).fetchall()
    if len(rows) != 1:
        raise RuntimeError(f"query returned {len(rows)} rows instead of one: {sql}")
    return tuple(int(value) for value in rows[0])
