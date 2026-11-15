import duckdb
import sys

lines = [l for l in open(sys.argv[1]) if not l.strip().startswith("--")]
con = duckdb.connect("data/market.duckdb")
for stmt in "\n".join(lines).split(";"):
    if stmt.strip():
        result = con.execute(stmt)
        if result is not None:
            df = result.fetchdf()
            if not df.empty:
                print(df.to_string())
                print("-" * 70)
con.close()
