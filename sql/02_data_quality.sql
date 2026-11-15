SELECT i.ticker,
    COUNT(*) AS n_rows,
    COUNT(DISTINCT p.date) AS n_dates,
    MIN(p.date) AS first_date,
    MAX(p.date) AS last_date,
    SUM(CASE WHEN p.adj_close <= 0 OR p.adj_close IS NULL 
             THEN 1 ELSE 0 END) AS bad_prices

FROM prices p
JOIN instruments i USING (instrument_id)
GROUP BY i.ticker
ORDER BY i.ticker;


SELECT instrument_id, date, COUNT(*) AS n
FROM prices
GROUP BY instrument_id, date
HAVING COUNT(*) > 1;


SELECT ticker, gap_start, gap_end FROM(
    SELECT i.ticker, d.date AS gap_start,
        LEAD(d.date) OVER (PARTITION BY d.instrument_id ORDER BY d.date) AS gap_end
    FROM(SELECT DISTINCT instrument_id, date FROM prices) d 
    JOIN instruments i USING (instrument_id)
)
WHERE DATE_DIFF('day', gap_start, gap_end) > 4;