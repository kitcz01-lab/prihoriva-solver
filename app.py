#!/usr/bin/env python3
"""
Přihořívá Solver - Standalone Application (Web Server & CLI)
No external dependencies required (Pure Python 3).
"""

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.parse
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from solver import PrihorivaSolver, get_temperature_info

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")


class PrihorivaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # SSE Stream Endpoint for Autonomous Solving
        if path == "/api/solve/stream":
            self.handle_solve_stream(query)
            return

        # Metadata Endpoint
        elif path == "/api/meta":
            self.handle_meta(query)
            return

        # Fallback to static files
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/guess":
            self.handle_manual_guess()
            return
        elif path == "/api/history/clear":
            self.handle_clear_history()
            return
        elif path == "/api/server/restart":
            self.handle_server_restart()
            return

        self.send_error(404, "Endpoint not found")

    def handle_meta(self, query):
        lang = query.get("lang", ["cs"])[0]
        mode = query.get("mode", ["daily"])[0]

        solver = PrihorivaSolver(lang=lang, mode=mode)
        poll_data = solver.get_poll_stats()
        yesterday = solver.get_yesterdays_word()

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        response = {
            "yesterdays_word": yesterday,
            "mode": mode,
            "poll": poll_data,
            "session": {
                "guesses": solver.guesses_history,
                "best": solver.get_best_guess(),
                "is_won": solver.is_won,
                "winning_word": solver.winning_word,
                "total": len(solver.guesses_history),
            },
        }
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))

    def handle_clear_history(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body) if body.strip() else {}
        except Exception:
            data = {}
        lang = data.get("lang", "cs")
        mode = data.get("mode", "daily")

        solver = PrihorivaSolver(lang=lang, mode=mode)
        solver.clear_session()

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"success": True}).encode("utf-8"))

    def handle_server_restart(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
        
        # Spustí asynchronní proces, který za 1 vteřinu restartuje server pomocí launch.sh
        subprocess.Popen(
            "nohup bash -c 'sleep 1 && ./launch.sh stop && ./launch.sh' >/dev/null 2>&1 &",
            shell=True,
            cwd=BASE_DIR
        )

    def handle_manual_guess(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            data = json.loads(body)
            word = data.get("word", "").strip().lower()
            lang = data.get("lang", "cs")
            mode = data.get("mode", "daily")
            guess_number = data.get("guessNumber", 1)

            if not word:
                self.send_error(400, "Missing word")
                return

            solver = PrihorivaSolver(lang=lang, mode=mode)

            # Ověření podmínky: běžná česká slova v jednotném čísle a v 1. pádě
            if lang == "cs" and not solver.is_valid_search_word(word):
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(
                    json.dumps({
                        "error": "Slovo nesplňuje pravidla: Hledaná slova jsou pouze běžná česká slova v jednotném čísle a v 1. pádě (nominativ singuláru)."
                    }, ensure_ascii=False).encode("utf-8")
                )
                return

            sim = solver.submit_guess(word, enforce_valid=(lang == "cs"))

            if sim is None:
                err_msg = getattr(solver, "last_error", "") or "Slovo nebylo serverem přijato"
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": err_msg}, ensure_ascii=False).encode("utf-8"))
                return

            score_pct = round(sim * 100, 2)
            label, color, emoji = get_temperature_info(score_pct)

            entry = {
                "number": guess_number,
                "word": word,
                "raw_similarity": sim,
                "score_pct": score_pct,
                "label": label,
                "color": color,
                "emoji": emoji,
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"entry": entry}).encode("utf-8"))

        except Exception as e:
            self.send_error(500, f"Error processing guess: {str(e)}")

    def handle_solve_stream(self, query):
        lang = query.get("lang", ["cs"])[0]
        mode = query.get("mode", ["daily"])[0]
        delay = float(query.get("delay", [0.4])[0])
        max_guesses = int(query.get("max", [100])[0])

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        solver = PrihorivaSolver(lang=lang, mode=mode, delay_sec=delay)

        try:
            for event in solver.solve_generator(max_guesses=max_guesses):
                payload = f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                self.wfile.write(payload.encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


def run_cli(lang: str = "cs", mode: str = "daily", delay: float = 0.35, max_guesses: int = 150):
    mode_label = "MEGASLOVO (TÝDENNÍ HRA)" if mode == "mega" else "DENNÍ HRA"
    print("=" * 60)
    print(f"🔥 PŘIHOŘÍVÁ SOLVER - CLI REŽIM ({mode_label} / {lang.upper()})")
    print("=" * 60)

    solver = PrihorivaSolver(lang=lang, mode=mode, delay_sec=delay)

    # Info
    yesterday = solver.get_yesterdays_word()
    if yesterday:
        label = "Minulé týdenní slovo bylo" if mode == "mega" else "Včerejší slovo bylo"
        print(f"📅 {label}: '{yesterday}'")
    word_type = "týdenního megaslova" if mode == "mega" else "slova dne"
    print(f"🚀 Zahajuji sémantické vyhledávání {word_type}...\n")

    start_time = time.time()
    for event in solver.solve_generator(max_guesses=max_guesses):
        ev_type = event.get("type")
        if ev_type == "resumed":
            print(f"🔄 {event['message']}")
            print(f"   Přeskakuji již otestovaná slova a pokračuji v prohledávání...\n")
        elif ev_type == "strategy_pivot":
            print(f"\n💡 {event['message']}")
        elif ev_type in ("hotspot_found", "lockin", "scorching"):
            print(f"\n⚡ {event['message']}")
        elif ev_type == "phase":
            print(f"\n[Fáze {event['phase']}] {event['title']}")
            print("-" * 40)
        elif ev_type == "clusters_ranked":
            print("  Top domény:", ", ".join([f"{c['name']} ({c['score']}%)" for c in event['ranking']]))
        elif ev_type == "guess":
            entry = event["entry"]
            attempts_info = ""
            if "mega_attempts_left" in entry:
                attempts_info = f" | zbývá pokusů: {entry['mega_attempts_left']}"
            print(f"  #{entry['number']:2d} | {entry['word']:14} | {entry['score_pct']:6.2f}% | {entry['emoji']} {entry['label']}{attempts_info}")
        elif ev_type == "win":
            elapsed = time.time() - start_time
            print("\n" + "=" * 60)
            if event.get("already_won"):
                print(f"🎉 Tajné slovo již bylo odhaleno: '{event['word'].upper()}'")
            else:
                print(f"🎉 VÍTĚZSTVÍ! Tajné slovo je: '{event['word'].upper()}'")
                print("🏆 Výsledek byl úspěšně zaznamenán na server!")
            print(f"🎯 Celkem pokusů: {event['total']}")
            print("=" * 60)
            return
        elif ev_type == "done_unsolved":
            print(f"\n⚠️ {event['message']}")
            best = event.get("best")
            if best:
                print(f"Nejlepší nalezené slovo: '{best['word']}' ({best['score_pct']}%)")
            return


def main():
    parser = argparse.ArgumentParser(description="Přihořívá Solver - Automatický řešitel pro prihorivahori.cz")
    parser.add_argument("--cli", action="store_true", help="Spustit v terminálovém (CLI) režimu místo webu")
    parser.add_argument("--port", type=int, default=8080, help="Port pro webový server (výchozí: 8080)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host rozhraní (výchozí: 127.0.0.1)")
    parser.add_argument("--lang", type=str, default="cs", choices=["cs", "sk", "pl", "hr", "de"], help="Jazyk hry")
    parser.add_argument("--mode", type=str, default="daily", choices=["daily", "mega"], help="Režim hry")
    parser.add_argument("--delay", type=float, default=0.35, help="Prodleva mezi požadavky v sekundách")
    parser.add_argument("--max", type=int, default=150, help="Maximální počet pokusů")

    args = parser.parse_args()

    if args.cli:
        run_cli(lang=args.lang, mode=args.mode, delay=args.delay, max_guesses=args.max)
    else:
        server_address = (args.host, args.port)
        httpd = ThreadingHTTPServer(server_address, PrihorivaHandler)
        print("=" * 60)
        print(f"🔥 PŘIHOŘÍVÁ SOLVER - WEBOVÁ APLIKACE")
        print(f"🌐 Server běží na: http://{args.host}:{args.port}")
        print(f"📁 Otevřete tento odkaz ve svém prohlížeči")
        print("=" * 60)
        print("Pro ukončení stiskněte Ctrl+C.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer byl zastaven.")
            httpd.server_close()


if __name__ == "__main__":
    main()
