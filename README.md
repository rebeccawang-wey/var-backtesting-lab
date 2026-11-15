# Multi-Asset VaR Backtesting Lab

A learn-by-doing project by Rebecca (U of T RC): backtesting Value-at-Risk (VaR) modesl on six assets, SPY, XIC.TO, TLT, HYG, CAD=X, GLD, from 2007 to present.

## Models 

- Historical Simulation, HS
- Parametric normal and Student-t, param-norm & param-t
- Exponentially Weighted Moving Average, EWMA (lambda = 0.94)
- Generalized Autoregressive Conditional Heteroskedasticity, GARCH(1,1)

## Backtests (in progress)

- Kupiec proportion-of-failures test
- Christoffersen independence test 
- Basel traffic light test

## Structure 

- 'sql/' - schema, date-quality checks, analytics views
- 'python/' - date pull, VaR engines, backtests
- 'data/' - DuckDB warehouse (not committed; rebuild with 'python python/01_pull_data.py')

## Status

- Week 1 (done): data warehouse and data-quality checks
- Week 2 (done): SQL analytics views - log returns, rolling volatility, historical-simulation VaR
- Week 3 (done): Python VaR engines - parametric normal and Student-t, EWMA, GARCH
- Week 4 (in progress): backtests - Kupiec and Christoffersen; Basel traffic light planned
- Week 5 (planned): crisis case studies - 2008, 2020, 2022
- Week 6 (planned): validation-style verdict report

> [!NOTE]
## How could this project be reused

The pieces are generic and can be borrowed separately: 
- the SQL analytics views work on any price table with the same schema, so you can swap in your own tickers
- the Python VaR engines run per instrument, so they work on any asset in the warehouse
- the test functions in `python/03_backtests.py` can be lifted into your own script to test any VaR series