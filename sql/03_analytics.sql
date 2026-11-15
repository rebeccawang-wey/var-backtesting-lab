CREATE OR REPLACE VIEW v_returns AS
SELECT instrument_id, 
       date, 
       adj_close,
       LN(adj_close / LAG(adj_close) OVER ( 
            Partition BY instrument_id ORDER BY date)) AS log_ret
FROM prices; 

CREATE OR REPLACE VIEW v_vol AS
SELECT instrument_id, 
       date, 
       log_ret, 
       STDDEV(log_ret) OVER (
        PARTITION BY instrument_id ORDER BY date
        ROWS BETWEEN 249 PRECEDING AND CURRENT ROW) * SQRT(252) AS vol_250d
FROM v_returns;

CREATE OR REPLACE VIEW v_hs_var AS
SELECT instrument_id,
       date, 
       log_ret,
       -quantile_cont(log_ret, 0.05) OVER (
            PARTITION BY instrument_id ORDER BY date
            ROWS BETWEEN 249 PRECEDING AND CURRENT ROW) AS var95_hs
FROM v_returns;

SELECT * FROM v_vol WHERE instrument_id = 1 ORDER BY date DESC LIMIT 5;
SELECT * FROM v_hs_var WHERE instrument_id = 1 ORDER BY date DESC LIMIT 5;