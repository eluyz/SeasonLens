"""Loopback-only CSV import and exploration of a private SQLite database."""
import argparse
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import tempfile

from .csv_import import import_csv
from .dashboard import render_dashboard
from .storage import SeriesMetadata, list_series, read_series, upsert_series, validate_private_path

MAX_UPLOAD = 12 * 1024 * 1024


def database_series(db):
    return {m['series_id']: {**m, 'frame': read_series(db, m['series_id'])}
            for m in list_series(db)}


def create_server(db, *, as_of, port=8765):
    """Serve only localhost. Uploaded content requires a same-origin header.

    CSV validation happens before a transaction. Existing source/quote metadata
    cannot change silently. No provider credentials or raw data are logged.
    """
    db = Path(db).resolve()
    # Fail before opening a socket if there is no usable database.
    initial = database_series(db)
    if initial:
        render_dashboard(initial, as_of=as_of)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _allowed(self):
            return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

        def _send(self, status, payload, kind='application/json'):
            if not isinstance(payload, bytes):
                payload = json.dumps(payload).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', kind+'; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if not self._allowed():
                return self._send(403, {'error':'Local host required.'})
            if self.path != '/':
                return self._send(404, {'error':'Not found.'})
            try:
                current = database_series(db)
                if current:
                    html = render_dashboard(current, as_of=as_of, local_import=True)
                else:
                    # Preserve the import UI without inventing an observed series.
                    from .dashboard import render_empty_dashboard
                    html = render_empty_dashboard(as_of=as_of)
                self._send(200, html.encode('utf-8'), 'text/html')
            except (ValueError, OSError) as exc:
                self._send(400, {'error':str(exc)})

        def do_POST(self):
            origin = self.headers.get('Origin')
            allowed_origins = {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}
            if (not self._allowed() or self.headers.get('X-SeasonLens') != 'local-import'
                    or (origin is not None and origin not in allowed_origins)):
                return self._send(403, {'error':'Same-origin local import required.'})
            if self.path != '/import':
                return self._send(404, {'error':'Not found.'})
            try:
                size = int(self.headers.get('Content-Length','0'))
                if size <= 0 or size > MAX_UPLOAD:
                    return self._send(413, {'error':'Upload must be between 1 byte and 12 MiB.'})
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict) or not isinstance(body.get('csv'),str):
                    raise ValueError('Expected an object containing CSV text.')
                if not isinstance(body.get('skip_missing'), bool):
                    raise ValueError('Blank-value policy must be explicit.')
                existing = database_series(db)
                if body['series_id'] in ('EUR_PLN','EUR_USD','USD_PLN'):
                    raise ValueError('ECB series IDs are reserved for the direct ECB updater. Use a distinct ID for CSV imports.')
                prior = existing.get(body['series_id'])
                provenance = prior['provenance'] if prior else 'Local graphical CSV import; definition supplied by the owner.'
                metadata = SeriesMetadata(body['series_id'],body['title'],body['unit'],body['source'],body['semantics'],provenance)
                with tempfile.TemporaryDirectory(prefix='seasonlens-import-') as temporary:
                    path = Path(temporary)/'input.csv'
                    path.write_text(body['csv'],encoding='utf-8')
                    prepared = import_csv(path,date_column=body['date_column'],value_column=body['value_column'],
                                          date_format=body['date_format'],delimiter=body['delimiter'],decimal=body['decimal'],
                                          instrument_column=body.get('instrument_column') or None,
                                          instrument=body.get('instrument_filter') or None,
                                          missing_values='skip' if body['skip_missing'] else 'reject',skip_rows=int(body['skip_rows']))
                candidate = existing
                combined = prepared.frame
                if prior:
                    import pandas as pd
                    combined = pd.concat([prior['frame'],prepared.frame]).drop_duplicates('date',keep='last').sort_values('date')
                candidate[metadata.series_id] = dict(frame=combined,title=metadata.title,unit=metadata.unit,
                                                    source=metadata.source,quote_semantics=metadata.quote_semantics)
                render_dashboard(candidate,as_of=as_of)
                summary = upsert_series(db,metadata,prepared.frame)
                self._send(200,{'ok':True,'skipped_missing_count':len(prepared.skipped_missing_rows)})
            except (ValueError, OSError, KeyError, TypeError) as exc:
                self._send(400,{'error':str(exc)})

    return HTTPServer(('127.0.0.1',port), Handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Explore a private SeasonLens database locally')
    parser.add_argument('--db',required=True)
    parser.add_argument('--as-of',required=True,type=date.fromisoformat)
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--output',help='Write a standalone private snapshot instead of running a server')
    args = parser.parse_args(argv)
    if args.output:
        output = validate_private_path(args.output)
        if output == Path(args.db).resolve():
            parser.error('The output must not overwrite the database.')
        html = render_dashboard(database_series(args.db),as_of=args.as_of)
        output.parent.mkdir(parents=True,exist_ok=True)
        with output.open('x',encoding='utf-8') as stream:
            stream.write(html)
        print('Private standalone explorer written.')
        return 0
    server = create_server(args.db,as_of=args.as_of,port=args.port)
    print(f'Open http://127.0.0.1:{server.server_port} in your browser. Press Ctrl+C to stop.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
