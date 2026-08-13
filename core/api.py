from __future__ import annotations

import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


def _rows(connection: sqlite3.Connection, query: str, parameters: tuple = ()) -> list[dict]:
    return [dict(row) for row in connection.execute(query, parameters).fetchall()]


def create_handler(database_path: str):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            route = urlparse(self.path).path.rstrip("/") or "/"
            with sqlite3.connect(database_path) as connection:
                connection.row_factory = sqlite3.Row
                if route == "/health":
                    payload = {"status": "ok", "database": "available"}
                elif route == "/api/companies":
                    payload = _rows(connection, "SELECT company_id,display_name,ticker,sector FROM companies ORDER BY display_name")
                elif route == "/api/predictions":
                    payload = _rows(connection, """
                      SELECT p.*,c.display_name,r.resolution_status,r.outcome_id
                      FROM predictions p JOIN companies c USING(company_id)
                      LEFT JOIN prediction_resolutions r USING(prediction_id)
                      ORDER BY information_cutoff_at DESC,prediction_target
                    """)
                elif route.startswith("/api/companies/"):
                    company_id = route.split("/")[3]
                    company = _rows(connection, "SELECT * FROM companies WHERE company_id=?", (company_id,))
                    if not company:
                        self.send_error(404); return
                    payload = {"company": company[0],
                               "predictions": _rows(connection, """SELECT p.*,r.resolution_status,r.outcome_id
                                 FROM predictions p LEFT JOIN prediction_resolutions r USING(prediction_id)
                                 WHERE company_id=?""", (company_id,)),
                               "evidence": _rows(connection, "SELECT evidence_id,title,available_at,source_url FROM evidence WHERE company_id=? ORDER BY available_at", (company_id,))}
                elif route == "/api/backtests":
                    payload = _rows(connection, """
                      SELECT r.*,COUNT(x.backtest_result_id) AS predictions,AVG(x.brier_component) AS brier_score
                      FROM backtest_runs r LEFT JOIN backtest_results x USING(backtest_run_id)
                      GROUP BY r.backtest_run_id ORDER BY r.started_at DESC
                    """)
                else:
                    self.send_error(404); return
            body = json.dumps(payload, default=str).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:5173")
            self.end_headers(); self.wfile.write(body)

        def log_message(self, _format: str, *_args: object) -> None:
            pass
    return Handler


def serve(database_path: str, host: str = "127.0.0.1", port: int = 8765) -> None:
    ThreadingHTTPServer((host, port), create_handler(database_path)).serve_forever()
