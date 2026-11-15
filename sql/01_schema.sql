CREATE TABLE instruments (
    instrument_id INTEGER PRIMARY KEY,
    ticker      VARCHAR NOT NULL,
    name        VARCHAR,
    asset_class VARCHAR,
    currency    VARCHAR
);

CREATE TABLE prices (
    instrument_id INTEGER REFERENCES instruments(instrument_id),
    date        DATE NOT NULL,
    open   DOUBLE, high DOUBLE, low DOUBLE,
    close  DOUBLE, adj_close DOUBLE, volume DOUBLE,
    PRIMARY KEY (instrument_id, date)
);
