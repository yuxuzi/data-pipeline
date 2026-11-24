"""Extract, transform, validate, and load, as plain typed functions, with Polars.

``extract`` reads the CSV into a DataFrame with the expected schema, ``validate`` refuses bad
input before anything is written, ``transform`` is one Polars expression chain, and ``load``
writes Parquet.
"""

from pathlib import Path

import polars as pl

REQUIRED_COLUMNS = ("order_id", "region", "product", "quantity", "unit_price")
SCHEMA: dict[str, pl.DataType] = {
    "order_id": pl.Int64(),
    "region": pl.String(),
    "product": pl.String(),
    "quantity": pl.Int32(),
    "unit_price": pl.Float64(),
}


class ValidationError(ValueError):
    """Raised when input data fails a check. The message names the column or the check."""


def extract(source: Path) -> pl.DataFrame:
    """Read the CSV at ``source`` with the expected schema."""
    if not source.is_file():
        raise FileNotFoundError(f"input file not found: {source}")
    try:
        return pl.read_csv(source, schema=SCHEMA)
    except pl.exceptions.PolarsError as exc:
        raise ValidationError(
            f"{source} does not match the expected columns and types: {exc}"
        ) from exc


def validate(df: pl.DataFrame) -> None:
    """Raise ``ValidationError`` unless the frame has rows, no nulls, and no negative values."""
    if df.height == 0:
        raise ValidationError("input has no rows: the file has a header but no data")
    nulls = df.select(pl.col(REQUIRED_COLUMNS).null_count()).row(0, named=True)
    for name in REQUIRED_COLUMNS:
        if nulls[name]:
            raise ValidationError(
                f"column {name} has {nulls[name]} null value(s) in {df.height} row(s)"
            )
    negatives = df.filter((pl.col("quantity") < 0) | (pl.col("unit_price") < 0)).height
    if negatives:
        raise ValidationError(f"quantity or unit_price is negative in {negatives} row(s)")


def transform(df: pl.DataFrame) -> pl.DataFrame:
    """Units, orders, and revenue per region and product, sorted by region and product."""
    return (
        df.group_by("region", "product")
        .agg(
            pl.len().alias("orders"),
            pl.col("quantity").sum().cast(pl.Int64).alias("units"),
            (pl.col("quantity") * pl.col("unit_price")).sum().round(2).alias("revenue"),
        )
        .sort("region", "product")
    )


def load(summary: pl.DataFrame, output: Path) -> None:
    """Write the summary to ``output`` as Parquet, creating its folder if needed."""
    output.parent.mkdir(parents=True, exist_ok=True)
    summary.write_parquet(output)


def run_pipeline(source: Path, output: Path) -> Path:
    """Run every step in order on ``source`` and return the Parquet path written to ``output``."""
    df = extract(source)
    validate(df)
    load(transform(df), output)
    return output
