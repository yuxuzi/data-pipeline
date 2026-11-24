-- Units, orders, and revenue per region and product. Reads the raw table that extract loads.
SELECT
    region,
    product,
    COUNT(*) AS orders,
    CAST(SUM(quantity) AS BIGINT) AS units,
    ROUND(SUM(quantity * unit_price), 2) AS revenue
FROM raw
GROUP BY region, product
ORDER BY region, product;
