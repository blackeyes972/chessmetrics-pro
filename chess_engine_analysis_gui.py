#!/usr/bin/env python3
"""
ChessEngine GUI - Interfaccia grafica completa per l'analisi con motori di scacchi
Versione ottimizzata con tutte le funzionalità dell'engine
"""

import os
import sys
import csv
import json
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QComboBox, 
                            QSpinBox, QDoubleSpinBox, QCheckBox, QTextEdit, QFileDialog, 
                            QMessageBox, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QGroupBox, QFormLayout, QProgressBar,
                            QTabWidget, QSplitter, QLineEdit, QRadioButton, 
                            QButtonGroup, QScrollArea, QGridLayout, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtGui import QIcon, QColor, QFont, QPixmap
from PyQt6.QtSvgWidgets import QSvgWidget
import chess
import chess.svg
import chess.pgn
import chess.engine
import sqlite3
import webbrowser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Importa le funzioni e classi necessarie da data_utils
from data_utils import get_db_path, get_log_path, initialize_directories


class ChessEngineAnalyzer:
    """Gestore dell'analisi con motori di scacchi."""
    
    def __init__(self, db_path: str, engine_path: str = None, depth: int = 18, 
                 multipv: int = 3, time_limit: float = 0.5):
        """Inizializza l'analizzatore.
        
        Args:
            db_path: Percorso al database SQLite
            engine_path: Percorso al motore di scacchi (se None, cerca Stockfish nel PATH)
            depth: Profondità di analisi predefinita
            multipv: Numero di varianti da analizzare
            time_limit: Limite di tempo per analisi in secondi
        """
        self.db_path = db_path
        self.engine_path = engine_path or self._find_engine()
        self.depth = depth
        self.multipv = multipv
        self.time_limit = time_limit
        self.conn = None
        self.cursor = None
        self.engine = None
        
        # Crea cartella di esportazione se non esiste
        self.EXPORT_FOLDER = "export"
        os.makedirs(self.EXPORT_FOLDER, exist_ok=True)
        
    def _find_engine(self) -> str:
        """Cerca un motore di scacchi installato."""
        # Percorsi comuni per Stockfish
        common_paths = [
            "stockfish",  # Se è nel PATH
            "/usr/local/bin/stockfish",
            "/usr/bin/stockfish",
            "C:\\Program Files\\stockfish\\stockfish.exe",
            os.path.join(os.path.expanduser("~"), "stockfish", "stockfish"),
            # Aggiunti altri percorsi comuni per diversi sistemi operativi
            "/usr/games/stockfish",
            "/opt/homebrew/bin/stockfish",
            os.path.join(os.path.expanduser("~"), "Documents", "stockfish", "stockfish")
        ]
        
        # Verifica se uno dei percorsi esiste
        for path in common_paths:
            try:
                # Verifica se il motore è disponibile
                engine = chess.engine.SimpleEngine.popen_uci(path)
                engine.quit()
                return path
            except (FileNotFoundError, chess.engine.EngineTerminatedError):
                continue
                
        # Nessun motore trovato
        return None
    
    def connect(self) -> bool:
        """Connette al database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Per accedere ai risultati per nome di colonna
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error:
            return False
    
    def setup_database(self) -> None:
        """Crea le tabelle necessarie per l'analisi del motore."""
        try:
            # Crea le tabelle se non esistono
            self.cursor.executescript('''
            -- Tabella principale per l'analisi del motore
            CREATE TABLE IF NOT EXISTS engine_analysis (
                id INTEGER PRIMARY KEY,
                game_id INTEGER NOT NULL,
                ply_number INTEGER NOT NULL,
                eval_centipawns INTEGER,
                eval_mate INTEGER,
                depth INTEGER NOT NULL,
                engine_name TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
                UNIQUE(game_id, ply_number, engine_name)
            );
            
            -- Tabella per le varianti principali
            CREATE TABLE IF NOT EXISTS engine_variations (
                id INTEGER PRIMARY KEY,
                analysis_id INTEGER NOT NULL,
                variation_index INTEGER NOT NULL,
                moves TEXT NOT NULL,
                eval_centipawns INTEGER,
                eval_mate INTEGER,
                FOREIGN KEY(analysis_id) REFERENCES engine_analysis(id) ON DELETE CASCADE,
                UNIQUE(analysis_id, variation_index)
            );
            
            -- Tabella per i commenti sull'analisi
            CREATE TABLE IF NOT EXISTS engine_comments (
                id INTEGER PRIMARY KEY,
                game_id INTEGER NOT NULL,
                ply_number INTEGER NOT NULL,
                comment_type TEXT NOT NULL,  -- 'blunder', 'mistake', 'inaccuracy', 'good', 'excellent', etc.
                comment_text TEXT NOT NULL,
                FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE
            );
            
            -- Tabella per statistiche del giocatore
            CREATE TABLE IF NOT EXISTS player_stats (
                id INTEGER PRIMARY KEY,
                player_name TEXT NOT NULL,
                total_games INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                draws INTEGER DEFAULT 0,
                avg_blunders REAL DEFAULT 0,
                avg_mistakes REAL DEFAULT 0,
                common_mistakes TEXT,
                last_updated TEXT,
                UNIQUE(player_name)
            );
            
            -- Indici per ottimizzare le query
            CREATE INDEX IF NOT EXISTS idx_engine_analysis_game_id ON engine_analysis(game_id);
            CREATE INDEX IF NOT EXISTS idx_engine_variations_analysis_id ON engine_variations(analysis_id);
            CREATE INDEX IF NOT EXISTS idx_engine_comments_game_id ON engine_comments(game_id);
            CREATE INDEX IF NOT EXISTS idx_engine_comments_type ON engine_comments(comment_type);
            ''')
            
            self.conn.commit()
        except sqlite3.Error:
            raise
    
    def start_engine(self) -> bool:
        """Avvia il motore di scacchi."""
        if not self.engine_path:
            return False
            
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            
            # Configura opzioni comuni
            try:
                self.engine.configure({"Threads": 4, "Hash": 128})
            except chess.engine.EngineError:
                pass
                
            return True
        except Exception:
            return False
    
    def stop_engine(self) -> None:
        """Ferma il motore di scacchi."""
        if self.engine:
            self.engine.quit()
            self.engine = None
    
    def analyze_position(self, board: chess.Board, depth: int = None, 
                         multipv: int = None, time_limit: float = None):
        """Analizza una posizione sulla scacchiera."""
        if not self.engine:
            return []
            
        depth = depth or self.depth
        multipv = multipv or self.multipv
        time_limit = time_limit or self.time_limit
        
        try:
            # Configura l'analisi
            limit = chess.engine.Limit(depth=depth, time=time_limit)
            
            # Esegui l'analisi multipv
            result = self.engine.analyse(
                board,
                limit,
                multipv=multipv,
                info=chess.engine.INFO_ALL
            )
            
            # Formatta i risultati
            analysis_results = []
            
            for i, info in enumerate(result):
                # Estrai la valutazione
                score = info.get("score")
                eval_cp = None
                eval_mate = None
                
                if score:
                    try:
                        eval_cp = score.relative.score()
                    except ValueError:
                        eval_mate = score.relative.mate()
                
                # Estrai la variante principale
                pv = info.get("pv", [])
                variation_moves = []
                
                # Crea una copia della scacchiera per generare la notazione SAN
                temp_board = board.copy()
                for move in pv:
                    san = temp_board.san(move)
                    variation_moves.append(san)
                    temp_board.push(move)
                
                analysis_results.append({
                    "multipv": i + 1,
                    "depth": info.get("depth", 0),
                    "eval_cp": eval_cp,
                    "eval_mate": eval_mate,
                    "pv": variation_moves,
                    "nodes": info.get("nodes", 0),
                    "nps": info.get("nps", 0),
                    "time": info.get("time", 0)
                })
            
            return analysis_results
            
        except Exception:
            return []
    
    def analyze_game(self, game_id: int, start_ply: int = 0, end_ply: int = None,
                     min_time: float = 0.5, important_only: bool = False) -> bool:
        """Analizza una partita dal database."""
        try:
            # Carica mosse della partita
            self.cursor.execute("""
                SELECT ply_number, san, uci
                FROM moves
                WHERE game_id = ?
                ORDER BY ply_number
            """, (game_id,))
            
            moves_data = self.cursor.fetchall()
            if not moves_data:
                return False
            
            # Limita il range delle mosse
            if end_ply is None:
                end_ply = len(moves_data) - 1
            else:
                end_ply = min(end_ply, len(moves_data) - 1)
            
            # Inizializza la scacchiera
            board = chess.Board()
            
            # Avvia il motore se non è già avviato
            if not self.engine and not self.start_engine():
                return False
            
            # Recupera informazioni sul motore
            engine_name = self.engine.id.get("name", "Unknown Engine")
            analysis_date = datetime.now().isoformat()
            
            # Determina quali posizioni analizzare
            positions_to_analyze = []
            if important_only:
                # Identifica posizioni importanti
                positions_to_analyze = list(range(start_ply, end_ply + 1, 4))  # Ogni 4 mosse
            else:
                positions_to_analyze = list(range(start_ply, end_ply + 1))
            
            # Analizza ogni posizione selezionata
            for i, (ply, san, uci) in enumerate(moves_data):
                if i > 0 and i - 1 in positions_to_analyze:
                    # Calcola il tempo di analisi in base all'importanza della posizione
                    position_time = min_time * (1 + (i / len(moves_data)))
                    
                    # Analizza la posizione
                    analysis_results = self.analyze_position(
                        board, 
                        time_limit=position_time,
                        multipv=self.multipv
                    )
                    
                    if analysis_results:
                        # Salva l'analisi nel database
                        self._save_analysis(
                            game_id, i-1, engine_name, analysis_date, 
                            analysis_results[0]["depth"], analysis_results
                        )
                
                # Esegui la mossa sulla scacchiera
                move = chess.Move.from_uci(uci)
                board.push(move)
            
            self.conn.commit()
            return True
            
        except Exception:
            self.conn.rollback()
            return False
    
    def _save_analysis(self, game_id: int, ply: int, engine_name: str, 
                      analysis_date: str, depth: int, results):
        """Salva i risultati dell'analisi nel database."""
        # Inserisci l'analisi principale
        main_result = results[0]
        self.cursor.execute("""
            INSERT OR REPLACE INTO engine_analysis
            (game_id, ply_number, eval_centipawns, eval_mate, depth, engine_name, analysis_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            game_id, ply, 
            main_result.get("eval_cp"), main_result.get("eval_mate"),
            depth, engine_name, analysis_date
        ))
        
        # Recupera l'ID dell'analisi appena inserita
        analysis_id = self.cursor.lastrowid
        
        # Inserisci le varianti
        for result in results:
            # Converti la lista di mosse PV in una stringa JSON
            pv_json = json.dumps(result.get("pv", []))
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO engine_variations
                (analysis_id, variation_index, moves, eval_centipawns, eval_mate)
                VALUES (?, ?, ?, ?, ?)
            """, (
                analysis_id, result.get("multipv"),
                pv_json, result.get("eval_cp"), result.get("eval_mate")
            ))
    
    def get_game_analysis(self, game_id: int):
        """Recupera l'analisi completa di una partita."""
        try:
            # Recupera tutte le posizioni analizzate per questa partita
            self.cursor.execute("""
                SELECT a.id, a.ply_number, a.eval_centipawns, a.eval_mate, 
                       a.depth, a.engine_name, a.analysis_date,
                       m.san, m.uci, g.white_player, g.black_player
                FROM engine_analysis a
                JOIN moves m ON a.game_id = m.game_id AND a.ply_number = m.ply_number
                JOIN games g ON a.game_id = g.id
                WHERE a.game_id = ?
                ORDER BY a.ply_number
            """, (game_id,))
            
            analysis_data = self.cursor.fetchall()
            if not analysis_data:
                return []
            
            # Prepara i risultati
            results = []
            
            for (aid, ply, eval_cp, eval_mate, depth, engine, date, 
                 san, uci, white, black) in analysis_data:
                
                # Recupera le varianti per questa analisi
                self.cursor.execute("""
                    SELECT variation_index, moves, eval_centipawns, eval_mate
                    FROM engine_variations
                    WHERE analysis_id = ?
                    ORDER BY variation_index
                """, (aid,))
                
                variations_data = self.cursor.fetchall()
                variations = []
                
                for var_idx, moves_json, var_cp, var_mate in variations_data:
                    # Converte la stringa JSON in lista
                    moves = json.loads(moves_json)
                    
                    variations.append({
                        "index": var_idx,
                        "moves": moves,
                        "eval_cp": var_cp,
                        "eval_mate": var_mate
                    })
                
                # Determina il turno e il numero della mossa
                move_number = (ply // 2) + 1
                turn = "white" if ply % 2 == 0 else "black"
                player = white if turn == "white" else black
                
                # Aggiungi l'analisi ai risultati
                results.append({
                    "ply": ply,
                    "move_number": move_number,
                    "turn": turn,
                    "player": player,
                    "san": san,
                    "uci": uci,
                    "eval_cp": eval_cp,
                    "eval_mate": eval_mate,
                    "depth": depth,
                    "engine": engine,
                    "date": date,
                    "variations": variations
                })
            
            return results
            
        except Exception:
            return []
    
    def analyze_critical_positions(self, game_id: int, threshold: int = 100):
        """Analizza tutte le posizioni di una partita e identifica quelle critiche."""
        try:
            # Carica mosse della partita
            self.cursor.execute("""
                SELECT ply_number, san, uci
                FROM moves
                WHERE game_id = ?
                ORDER BY ply_number
            """, (game_id,))
            
            moves_data = self.cursor.fetchall()
            if not moves_data:
                return []
            
            # Inizializza la scacchiera
            board = chess.Board()
            
            # Avvia il motore se non è già avviato
            if not self.engine and not self.start_engine():
                return False
            
            # Recupera informazioni sul motore
            engine_name = self.engine.id.get("name", "Unknown Engine")
            analysis_date = datetime.now().isoformat()
            
            # Analizza ogni posizione
            positions = []
            prev_eval = 0
            
            for i, (ply, san, uci) in enumerate(moves_data):
                # Analizza la posizione attuale
                analysis_results = self.analyze_position(board, time_limit=0.3)
                
                if analysis_results:
                    eval_cp = analysis_results[0].get("eval_cp", 0)
                    eval_mate = analysis_results[0].get("eval_mate")
                    
                    # Converti scacco matto in centipawns per semplificare il confronto
                    if eval_mate is not None:
                        eval_cp = 10000 if eval_mate > 0 else -10000
                    
                    # Calcola la variazione della valutazione
                    eval_diff = abs(eval_cp - prev_eval)
                    
                    # Se la variazione supera la soglia, considera la posizione critica
                    if eval_diff >= threshold:
                        positions.append({
                            "ply": ply,
                            "move": san,
                            "prev_eval": prev_eval,
                            "new_eval": eval_cp,
                            "diff": eval_diff,
                            "analysis": analysis_results
                        })
                        
                        # Salva l'analisi nel database
                        self._save_analysis(
                            game_id, ply, engine_name, analysis_date, 
                            analysis_results[0]["depth"], analysis_results
                        )
                        
                        # Aggiungi un commento sul cambio di valutazione
                        comment_type = self._get_comment_type(eval_diff, prev_eval, eval_cp)
                        comment_text = self._generate_comment(comment_type, eval_diff, prev_eval, eval_cp)
                        
                        self.cursor.execute("""
                            INSERT OR REPLACE INTO engine_comments
                            (game_id, ply_number, comment_type, comment_text)
                            VALUES (?, ?, ?, ?)
                        """, (game_id, ply, comment_type, comment_text))
                    
                    prev_eval = eval_cp
                
                # Esegui la mossa sulla scacchiera
                move = chess.Move.from_uci(uci)
                board.push(move)
            
            self.conn.commit()
            return positions
            
        except Exception:
            self.conn.rollback()
            return []
    
    def _get_comment_type(self, eval_diff: int, prev_eval: int, new_eval: int) -> str:
        """Determina il tipo di commento in base alla variazione della valutazione."""
        # Determina il segno della variazione (positivo = miglioramento, negativo = peggioramento)
        is_improvement = (new_eval > prev_eval)
        
        # Classifica in base alla magnitudine della differenza
        if eval_diff >= 300:
            return "excellent_move" if is_improvement else "blunder"
        elif eval_diff >= 150:
            return "good_move" if is_improvement else "mistake"
        elif eval_diff >= 50:
            return "inaccuracy" if not is_improvement else "interesting_move"
        else:
            return "neutral"
    
    def _generate_comment(self, comment_type: str, eval_diff: int, 
                         prev_eval: int, new_eval: int) -> str:
        """Genera un commento basato sul tipo e sulla variazione della valutazione."""
        # Converti le valutazioni in formato leggibile
        def format_eval(cp):
            if abs(cp) >= 10000:  # Scacco matto
                return "scacco matto"
            
            pawns = cp / 100.0
            sign = "+" if pawns > 0 else ""
            return f"{sign}{pawns:.2f}"
        
        prev_str = format_eval(prev_eval)
        new_str = format_eval(new_eval)
        
        # Genera commento in base al tipo
        if comment_type == "blunder":
            return f"Errore grave. La valutazione cambia da {prev_str} a {new_str}."
        elif comment_type == "mistake":
            return f"Errore. La valutazione cambia da {prev_str} a {new_str}."
        elif comment_type == "inaccuracy":
            return f"Imprecisione. La valutazione cambia da {prev_str} a {new_str}."
        elif comment_type == "excellent_move":
            return f"Mossa eccellente! La valutazione cambia da {prev_str} a {new_str}."
        elif comment_type == "good_move":
            return f"Buona mossa. La valutazione cambia da {prev_str} a {new_str}."
        elif comment_type == "interesting_move":
            return f"Mossa interessante. La valutazione cambia da {prev_str} a {new_str}."
        else:
            return f"La valutazione è {new_str}."
    
    def get_game_comments(self, game_id: int):
        """Recupera i commenti di una partita."""
        try:
            # Recupera tutti i commenti per questa partita
            self.cursor.execute("""
                SELECT c.ply_number, c.comment_type, c.comment_text,
                       m.san, m.uci
                FROM engine_comments c
                JOIN moves m ON c.game_id = m.game_id AND c.ply_number = m.ply_number
                WHERE c.game_id = ?
                ORDER BY c.ply_number
            """, (game_id,))
            
            comments_data = self.cursor.fetchall()
            
            # Prepara i risultati
            results = []
            
            for ply, comment_type, comment_text, san, uci in comments_data:
                # Determina il turno e il numero della mossa
                move_number = (ply // 2) + 1
                turn = "white" if ply % 2 == 0 else "black"
                
                results.append({
                    "ply": ply,
                    "move_number": move_number,
                    "turn": turn,
                    "san": san,
                    "uci": uci,
                    "comment_type": comment_type,
                    "comment_text": comment_text
                })
            
            return results
            
        except Exception:
            return []
    
    def export_analysis_to_pgn(self, game_id: int, output_path: str) -> bool:
        """Esporta l'analisi di una partita in formato PGN."""
        try:
            # Recupera i dettagli della partita
            self.cursor.execute("""
                SELECT event, site, date, round, white_player, black_player, 
                       result, white_elo, black_elo, eco, opening
                FROM games
                WHERE id = ?
            """, (game_id,))
            
            game_details = self.cursor.fetchone()
            if not game_details:
                return False
            
            # Recupera le mosse della partita
            self.cursor.execute("""
                SELECT ply_number, san, uci
                FROM moves
                WHERE game_id = ?
                ORDER BY ply_number
            """, (game_id,))
            
            moves_data = self.cursor.fetchall()
            
            # Recupera i commenti dell'analisi
            self.cursor.execute("""
                SELECT ply_number, comment_text
                FROM engine_comments
                WHERE game_id = ?
                ORDER BY ply_number
            """, (game_id,))
            
            comments_data = {ply: text for ply, text in self.cursor.fetchall()}
            
            # Recupera le varianti dell'analisi
            self.cursor.execute("""
                SELECT a.ply_number, v.variation_index, v.moves
                FROM engine_analysis a
                JOIN engine_variations v ON a.id = v.analysis_id
                WHERE a.game_id = ?
                AND v.variation_index = 1
                ORDER BY a.ply_number
            """, (game_id,))
            
            variations_data = {}
            for ply, idx, moves_json in self.cursor.fetchall():
                variations_data[ply] = json.loads(moves_json)
            
            # Crea l'oggetto partita
            game = chess.pgn.Game()
            
            # Imposta gli header
            event, site, date, round_num, white, black, result, w_elo, b_elo, eco, opening = game_details
            
            game.headers["Event"] = event or "?"
            game.headers["Site"] = site or "?"
            game.headers["Date"] = date or "????.??.??"
            game.headers["Round"] = round_num or "?"
            game.headers["White"] = white or "?"
            game.headers["Black"] = black or "?"
            game.headers["Result"] = result or "*"
            
            if w_elo:
                game.headers["WhiteElo"] = str(w_elo)
            if b_elo:
                game.headers["BlackElo"] = str(b_elo)
            if eco:
                game.headers["ECO"] = eco
            if opening:
                game.headers["Opening"] = opening
            
            # Aggiungi informazioni sull'analisi
            game.headers["Annotator"] = "ChessEngineAnalyzer"
            
            # Dizionario per tracciare i nodi corrispondenti a ogni ply
            ply_to_node = {}
            
            # Aggiungi le mosse
            node = game
            ply_to_node[-1] = node  # Il nodo radice rappresenta la posizione iniziale (ply -1)
            
            for ply, san, uci in moves_data:
                move = chess.Move.from_uci(uci)
                node = node.add_variation(move)
                ply_to_node[ply] = node  # Memorizza il nodo per questo ply
                
                # Aggiungi commento se presente
                if ply in comments_data:
                    node.comment = comments_data[ply]
            
            # Aggiungi varianti come commenti testuali piuttosto che come rami alternativi
            for ply, variation in variations_data.items():
                if ply in ply_to_node and variation:
                    try:
                        # Ottieni il nodo corrispondente al ply
                        target_node = ply_to_node[ply]
                        
                        # Crea un commento che include la variante
                        if not hasattr(target_node, 'comment') or not target_node.comment:
                            target_node.comment = ""
                        
                        # Aggiungi le mosse della variante come testo
                        target_node.comment += f"\nAnalisi del motore: {' '.join(variation)}"
                        
                    except Exception:
                        pass
            
            # Scrivi il PGN su file
            try:
                with open(output_path, "w") as f:
                    exporter = chess.pgn.FileExporter(f)
                    game.accept(exporter)
                return True
            except Exception:
                return False
            
        except Exception:
            return False
    
    def export_analysis_to_html(self, game_id: int, output_path: str = None) -> bool:
        """Esporta l'analisi di una partita in formato HTML con diagrammi interattivi."""
        try:
            # Recupera i dettagli della partita
            self.cursor.execute("""
                SELECT event, site, date, round, white_player, black_player, 
                       result, white_elo, black_elo, eco, opening
                FROM games
                WHERE id = ?
            """, (game_id,))
            
            game_details = self.cursor.fetchone()
            if not game_details:
                return False
            
            event, site, date, round_num, white, black, result, w_elo, b_elo, eco, opening = game_details
            
            # Recupera le mosse della partita
            self.cursor.execute("""
                SELECT ply_number, san, uci
                FROM moves
                WHERE game_id = ?
                ORDER BY ply_number
            """, (game_id,))
            
            moves_data = self.cursor.fetchall()
            
            # Recupera i commenti dell'analisi
            self.cursor.execute("""
                SELECT c.ply_number, c.comment_type, c.comment_text
                FROM engine_comments c
                WHERE c.game_id = ?
                ORDER BY c.ply_number
            """, (game_id,))
            
            comments_data = self.cursor.fetchall()
            comments_by_ply = {ply: (ctype, text) for ply, ctype, text in comments_data}
            
            # Recupera TUTTE le varianti dell'analisi, non solo quelle con commenti
            self.cursor.execute("""
                SELECT a.ply_number, v.moves
                FROM engine_analysis a
                JOIN engine_variations v ON a.id = v.analysis_id
                WHERE a.game_id = ? AND v.variation_index = 1
                ORDER BY a.ply_number
            """, (game_id,))
            
            variations_data = {ply: json.loads(moves) for ply, moves in self.cursor.fetchall()}
            
            # Genera il file HTML
            if output_path is None:
                filename = f"analysis_game_{game_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                output_path = os.path.join(self.EXPORT_FOLDER, filename)
            
            with open(output_path, "w") as f:
                # Scrivi l'intestazione HTML
                f.write(f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analisi: {white} vs {black}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; }}
        h1, h2 {{ color: #333; }}
        .game-header {{ margin-bottom: 30px; }}
        .game-info {{ display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px; }}
        .game-info div {{ flex: 1; min-width: 200px; }}
        .move {{ padding: 10px; margin-bottom: 10px; border-left: 4px solid #ddd; }}
        .move-header {{ font-weight: bold; margin-bottom: 5px; }}
        .blunder {{ border-left-color: #e74c3c; }}
        .mistake {{ border-left-color: #e67e22; }}
        .inaccuracy {{ border-left-color: #f39c12; }}
        .excellent_move {{ border-left-color: #2ecc71; }}
        .good_move {{ border-left-color: #27ae60; }}
        .interesting_move {{ border-left-color: #3498db; }}
        .neutral {{ border-left-color: #95a5a6; }}
        .comment {{ margin-top: 5px; margin-bottom: 10px; font-weight: bold; }}
        .diagram {{ margin: 20px 0; text-align: center; }}
        .analysis {{ margin-top: 5px; font-style: italic; color: #555; background-color: #f9f9f9; padding: 8px; border-radius: 4px; }}
        .nav-buttons {{ margin: 20px 0; text-align: center; }}
        .nav-buttons a {{ display: inline-block; padding: 8px 12px; margin: 0 5px; background-color: #3498db; color: white; text-decoration: none; border-radius: 4px; }}
        .nav-buttons a:hover {{ background-color: #2980b9; }}
        .critical-positions {{ margin-bottom: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 6px; }}
        .critical-positions h3 {{ margin-top: 0; }}
        .critical-positions ul {{ columns: 2; }}
        .critical-positions a {{ color: #3498db; text-decoration: none; }}
        .critical-positions a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="game-header">
        <h1>Analisi della Partita</h1>
        <div class="game-info">
            <div>
                <p><strong>Bianco:</strong> {white}{' (' + str(w_elo) + ')' if w_elo else ''}</p>
                <p><strong>Nero:</strong> {black}{' (' + str(b_elo) + ')' if b_elo else ''}</p>
                <p><strong>Risultato:</strong> {result}</p>
            </div>
            <div>
                <p><strong>Evento:</strong> {event or "N/A"}</p>
                <p><strong>Data:</strong> {date or "N/A"}</p>
                <p><strong>Apertura:</strong> {eco or ""} {opening or "N/A"}</p>
            </div>
        </div>
    </div>
""")

                # Crea un indice delle posizioni critiche
                if comments_by_ply:
                    f.write("""
    <div class="critical-positions">
        <h3>Posizioni Critiche</h3>
        <ul>
""")
                    for ply in sorted(comments_by_ply.keys()):
                        comment_type, _ = comments_by_ply[ply]
                        move_number = (ply // 2) + 1
                        turn = "..." if ply % 2 == 1 else "."
                        # Cerca la mossa corrispondente
                        move_san = ""
                        for p, san, _ in moves_data:
                            if p == ply:
                                move_san = san
                                break
                        f.write(f'            <li><a href="#move-{ply}" class="{comment_type}">{move_number}{turn} {move_san}</a></li>\n')
                    f.write("""
        </ul>
    </div>
""")
                
                f.write("""
    <h2>Analisi delle Mosse</h2>
""")

                # Crea una lista di nodi per ciascuna mossa
                board = chess.Board()
                for i, (ply, san, uci) in enumerate(moves_data):
                    # Calcola informazioni sulla mossa
                    move_number = (ply // 2) + 1
                    turn = "..." if ply % 2 == 1 else "."
                    
                    # Esegui la mossa sulla scacchiera
                    move = chess.Move.from_uci(uci)
                    board.push(move)
                    
                    # Classe CSS per il tipo di commento (se presente)
                    comment_class = ""
                    if ply in comments_by_ply:
                        comment_type, _ = comments_by_ply[ply]
                        comment_class = f" {comment_type}"
                    
                    # Inizia una sezione per ogni mossa
                    f.write(f"""
    <div class="move{comment_class}" id="move-{ply}">
        <div class="move-header">{move_number}{turn} {san}</div>
""")
                    
                    # Se è una posizione critica, aggiungi il diagramma e il commento
                    if ply in comments_by_ply:
                        comment_type, comment_text = comments_by_ply[ply]
                        svg = chess.svg.board(board, size=300)
                        f.write(f"""
        <div class="diagram">{svg}</div>
        <div class="comment">{comment_text}</div>
""")
                    
                    # Aggiungi l'analisi del motore, se disponibile
                    if ply in variations_data:
                        variation_moves = variations_data[ply]
                        f.write(f"""
        <div class="analysis">Analisi del motore: {' '.join(variation_moves)}</div>
""")
                        
                    f.write("    </div>\n")
                
                # Chiudi il documento HTML
                f.write("""
</body>
</html>
""")
            
            # Opzionalmente apri il file nel browser
            try:
                webbrowser.open('file://' + os.path.abspath(output_path))
            except:
                pass
                
            return True
            
        except Exception:
            return False
    
    def get_player_stats(self, player_name: str):
        """Recupera le statistiche di un giocatore."""
        try:
            self.cursor.execute("""
                SELECT * FROM player_stats
                WHERE player_name = ?
            """, (player_name,))
            
            stats = self.cursor.fetchone()
            if not stats:
                return {
                    "player_name": player_name,
                    "total_games": 0,
                    "wins": 0,
                    "losses": 0,
                    "draws": 0,
                    "win_percentage": 0,
                    "avg_blunders": 0,
                    "avg_mistakes": 0,
                    "common_mistakes": None,
                    "last_updated": None
                }
            
            # Converti row in dizionario
            stats_dict = dict(stats)
            
            # Calcola la percentuale di vittorie
            if stats_dict["total_games"] > 0:
                stats_dict["win_percentage"] = (stats_dict["wins"] / stats_dict["total_games"]) * 100
            else:
                stats_dict["win_percentage"] = 0
            
            return stats_dict
            
        except Exception:
            return {}
    
    def get_player_games(self, player_name: str, limit: int = 20):
        """Recupera le partite giocate da un giocatore."""
        try:
            self.cursor.execute("""
                SELECT id, white_player, black_player, result, date, event
                FROM games
                WHERE white_player = ? OR black_player = ?
                ORDER BY date DESC
                LIMIT ?
            """, (player_name, player_name, limit))
            
            return self.cursor.fetchall()
        except Exception:
            return []
    
    def calculate_player_stats(self, player_name: str) -> bool:
        """Calcola e aggiorna le statistiche di un giocatore."""
        try:
            # Recupera tutte le partite del giocatore
            self.cursor.execute("""
                SELECT id, white_player, black_player, result
                FROM games
                WHERE white_player = ? OR black_player = ?
            """, (player_name, player_name))
            
            games = self.cursor.fetchall()
            
            if not games:
                return False
            
            # Conteggio vittorie, sconfitte, pareggi
            total_games = len(games)
            wins = 0
            losses = 0
            draws = 0
            
            for game_id, white, black, result in games:
                is_white = (white == player_name)
                
                if result == "1-0" and is_white or result == "0-1" and not is_white:
                    wins += 1
                elif result == "1-0" and not is_white or result == "0-1" and is_white:
                    losses += 1
                elif result == "1/2-1/2":
                    draws += 1
            
            # Conta errori
            self.cursor.execute("""
                SELECT g.id, ec.comment_type
                FROM games g
                JOIN moves m ON g.id = m.game_id
                JOIN engine_comments ec ON m.game_id = ec.game_id AND m.ply_number = ec.ply_number
                WHERE (g.white_player = ? AND m.ply_number % 2 = 0) 
                   OR (g.black_player = ? AND m.ply_number % 2 = 1)
                AND ec.comment_type IN ('blunder', 'mistake', 'inaccuracy')
            """, (player_name, player_name))
            
            errors_data = self.cursor.fetchall()
            
            # Conta i tipi di errori
            blunders = sum(1 for _, ctype in errors_data if ctype == 'blunder')
            mistakes = sum(1 for _, ctype in errors_data if ctype == 'mistake')
            
            # Calcola le medie
            avg_blunders = blunders / total_games if total_games > 0 else 0
            avg_mistakes = mistakes / total_games if total_games > 0 else 0
            
            # Salva o aggiorna le statistiche
            self.cursor.execute("""
                INSERT OR REPLACE INTO player_stats
                (player_name, total_games, wins, losses, draws, 
                 avg_blunders, avg_mistakes, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player_name, total_games, wins, losses, draws, 
                avg_blunders, avg_mistakes, datetime.now().isoformat()
            ))
            
            self.conn.commit()
            return True
            
        except Exception:
            self.conn.rollback()
            return False
    
    def export_player_stats_to_csv(self, player_name: str, output_path: str) -> bool:
        """Esporta le statistiche di un giocatore in CSV."""
        try:
            # Recupera statistiche
            stats = self.get_player_stats(player_name)
            
            if not stats:
                return False
            
            # Recupera errori per tipo di apertura
            self.cursor.execute("""
                SELECT g.opening, COUNT(ec.id) as error_count
                FROM games g
                JOIN moves m ON g.id = m.game_id
                JOIN engine_comments ec ON m.game_id = ec.game_id AND m.ply_number = ec.ply_number
                WHERE (g.white_player = ? AND m.ply_number % 2 = 0) 
                   OR (g.black_player = ? AND m.ply_number % 2 = 1)
                AND ec.comment_type IN ('blunder', 'mistake')
                GROUP BY g.opening
                ORDER BY error_count DESC
            """, (player_name, player_name))
            
            opening_errors = self.cursor.fetchall()
            
            # Esporta statistiche principali
            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Statistica', 'Valore'])
                writer.writerow(['Giocatore', stats['player_name']])
                writer.writerow(['Partite totali', stats['total_games']])
                writer.writerow(['Vittorie', stats['wins']])
                writer.writerow(['Pareggi', stats['draws']])
                writer.writerow(['Sconfitte', stats['losses']])
                writer.writerow(['Percentuale vittorie', f"{stats['win_percentage']:.1f}%"])
                writer.writerow(['Media errori gravi per partita', f"{stats['avg_blunders']:.2f}"])
                writer.writerow(['Media errori per partita', f"{stats['avg_mistakes']:.2f}"])
                
                writer.writerow([])
                writer.writerow(['Errori per apertura', ''])
                writer.writerow(['Apertura', 'Numero errori'])
                
                for opening, count in opening_errors:
                    writer.writerow([opening or 'Sconosciuta', count])
            
            return True
            
        except Exception:
            return False
    
    def close(self) -> None:
        """Chiude le connessioni e le risorse."""
        self.stop_engine()
        
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None


class AnalysisThread(QThread):
    """Thread per eseguire l'analisi in background."""
    
    progress_update = pyqtSignal(str)
    analysis_completed = pyqtSignal(bool, object)
    
    def __init__(self, db_path, engine_path, depth, multipv, game_id, 
                 critical_only=False, critical_threshold=100, export_path=None, 
                 export_html=False, time_limit=0.5):
        super().__init__()
        self.db_path = db_path
        self.engine_path = engine_path
        self.depth = depth
        self.multipv = multipv
        self.game_id = game_id
        self.critical_only = critical_only
        self.critical_threshold = critical_threshold
        self.export_path = export_path
        self.export_html = export_html
        self.time_limit = time_limit
    
    def run(self):
        analyzer = None
        try:
            # Creiamo un nuovo analyzer nel thread corrente
            self.progress_update.emit(f"Inizializzazione analyzer per la partita {self.game_id}...")
            analyzer = ChessEngineAnalyzer(
                db_path=self.db_path,
                engine_path=self.engine_path,
                depth=self.depth,
                multipv=self.multipv,
                time_limit=self.time_limit
            )
            
            if not analyzer.connect():
                self.progress_update.emit("Errore: Impossibile connettersi al database.")
                self.analysis_completed.emit(False, None)
                return
                
            analyzer.setup_database()
            
            # Avvia il motore
            self.progress_update.emit("Avvio del motore di scacchi...")
            if not analyzer.start_engine():
                self.progress_update.emit("Errore: Impossibile avviare il motore di scacchi.")
                self.analysis_completed.emit(False, None)
                return
            
            self.progress_update.emit(f"Avvio analisi della partita {self.game_id}...")
            
            if self.critical_only:
                self.progress_update.emit(f"Analisi delle posizioni critiche in corso (soglia: {self.critical_threshold} centipawns)...")
                positions = analyzer.analyze_critical_positions(self.game_id, self.critical_threshold)
                self.progress_update.emit(f"Analizzate {len(positions)} posizioni critiche.")
                comments = analyzer.get_game_comments(self.game_id)
                
            else:
                self.progress_update.emit("Analisi completa della partita in corso...")
                success = analyzer.analyze_game(self.game_id)
                self.progress_update.emit("Recupero dei commenti generati...")
                comments = analyzer.get_game_comments(self.game_id)
                self.progress_update.emit(f"Recuperati {len(comments)} commenti.")
            
            if self.export_path:
                self.progress_update.emit(f"Esportazione analisi in PGN: {self.export_path}...")
                analyzer.export_analysis_to_pgn(self.game_id, self.export_path)
                self.progress_update.emit("Esportazione PGN completata.")
            
            if self.export_html:
                self.progress_update.emit("Esportazione analisi in HTML...")
                html_path = os.path.join(analyzer.EXPORT_FOLDER, f"analysis_game_{self.game_id}.html")
                analyzer.export_analysis_to_html(self.game_id, html_path)
                self.progress_update.emit(f"Esportazione HTML completata: {html_path}")
            
            self.progress_update.emit("Arresto del motore di scacchi...")
            analyzer.stop_engine()
            
            self.progress_update.emit("Chiusura della connessione al database...")
            analyzer.close()
            
            self.progress_update.emit("Analisi completata con successo.")
            self.analysis_completed.emit(True, comments)
        
        except Exception as e:
            self.progress_update.emit(f"Errore durante l'analisi: {e}")
            if analyzer:
                try:
                    self.progress_update.emit("Tentativo di arresto del motore dopo errore...")
                    analyzer.stop_engine()
                    self.progress_update.emit("Chiusura della connessione al database...")
                    analyzer.close()
                except Exception as close_error:
                    self.progress_update.emit(f"Errore nella chiusura delle risorse: {close_error}")
            self.analysis_completed.emit(False, None)


class PlayerStatsThread(QThread):
    """Thread per calcolare le statistiche di un giocatore."""
    
    progress_update = pyqtSignal(str)
    stats_completed = pyqtSignal(bool, dict)
    
    def __init__(self, db_path, player_name):
        super().__init__()
        self.db_path = db_path
        self.player_name = player_name
    
    def run(self):
        analyzer = None
        try:
            self.progress_update.emit(f"Calcolo statistiche per {self.player_name}...")
            analyzer = ChessEngineAnalyzer(db_path=self.db_path)
            
            if not analyzer.connect():
                self.progress_update.emit("Errore: Impossibile connettersi al database.")
                self.stats_completed.emit(False, {})
                return
            
            analyzer.setup_database()
            
            # Calcola le statistiche
            self.progress_update.emit("Elaborazione delle partite e degli errori...")
            analyzer.calculate_player_stats(self.player_name)
            
            # Recupera le statistiche aggiornate
            self.progress_update.emit("Recupero statistiche aggiornate...")
            stats = analyzer.get_player_stats(self.player_name)
            
            analyzer.close()
            self.progress_update.emit("Calcolo statistiche completato.")
            self.stats_completed.emit(True, stats)
            
        except Exception as e:
            self.progress_update.emit(f"Errore durante il calcolo delle statistiche: {e}")
            if analyzer:
                analyzer.close()
            self.stats_completed.emit(False, {})


class EvaluationGraphWidget(FigureCanvas):
    """Widget per visualizzare il grafico dell'andamento della valutazione."""
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        
        # Inizializza il grafico vuoto
        self.axes.set_title('Valutazione della Partita')
        self.axes.set_xlabel('Mosse')
        self.axes.set_ylabel('Valutazione (pawns)')
        self.axes.axhline(y=0, color='grey', linestyle='-', alpha=0.3)
        self.axes.grid(True, alpha=0.3)
        
        super().__init__(self.fig)
        self.setParent(parent)
    
    def update_graph(self, analysis_data):
        """Aggiorna il grafico con i dati dell'analisi."""
        self.axes.clear()
        
        # Estrai i dati
        plies = []
        evals = []
        critical_points = []
        critical_evals = []
        
        for pos in analysis_data:
            ply = pos["ply"]
            eval_cp = pos.get("eval_cp")
            eval_mate = pos.get("eval_mate")
            
            # Converti scacco matto in centipawns per il grafico
            if eval_mate is not None:
                # Limita il valore per il grafico
                eval_cp = 15 if eval_mate > 0 else -15
            
            # Converti in pedoni
            if eval_cp is not None:
                eval_pawns = eval_cp / 100.0
                
                plies.append(ply)
                evals.append(eval_pawns)
                
                # Evidenzia posizioni critiche
                if "comment_type" in pos and pos["comment_type"] in ("blunder", "mistake", "excellent_move"):
                    critical_points.append(ply)
                    critical_evals.append(eval_pawns)
        
        # Disegna il grafico principale
        self.axes.plot(plies, evals, '-', color='blue', linewidth=2, label='Valutazione')
        
        # Evidenzia i punti critici
        if critical_points:
            self.axes.scatter(critical_points, critical_evals, color='red', s=50, zorder=5, label='Posizioni critiche')
        
        # Miglioramenti grafici
        self.axes.set_title('Valutazione della Partita')
        self.axes.set_xlabel('Numero della mossa')
        self.axes.set_ylabel('Valutazione (pedoni)')
        self.axes.axhline(y=0, color='grey', linestyle='-', alpha=0.3)
        self.axes.grid(True, alpha=0.3)
        
        # Limita l'asse y per mantenere visibilità
        max_eval = max(abs(min(evals + [-3])), max(evals + [3]))
        self.axes.set_ylim(-max_eval - 1, max_eval + 1)
        
        # Aggiungi legenda
        self.axes.legend(loc='best')
        
        # Aggiorna il grafico
        self.fig.tight_layout()
        self.draw()


class ChessBoardWidget(QSvgWidget):
    """Widget per visualizzare una scacchiera con SVG."""
    
    def __init__(self, parent=None, flip=False):
        super().__init__(parent)
        self.board = chess.Board()
        self.flip = flip
        self.setMinimumSize(400, 400)
        self.update_board()
    
    def update_board(self):
        svg_data = chess.svg.board(
            self.board, 
            size=400, 
            flipped=self.flip
        ).encode('utf-8')
        self.load(svg_data)
    
    def set_position_from_fen(self, fen):
        try:
            self.board = chess.Board(fen)
            self.update_board()
        except Exception:
            pass
    
    def flip_board(self):
        """Capovolge la scacchiera."""
        self.flip = not self.flip
        self.update_board()


class ChessEngineAnalysisGUI(QMainWindow):
    """Interfaccia grafica per l'analisi con motori di scacchi."""
    
    def __init__(self):
        super().__init__()
        
        # Inizializza directory necessarie
        initialize_directories()
        
        # Impostazioni iniziali
        self.db_path = get_db_path()
        self.analyzer = None
        self.games_data = []
        
        self.init_ui()
        self.init_analyzer()
    
    def init_ui(self):
        """Inizializza l'interfaccia utente."""
        self.setWindowTitle("ChessEngine Analysis")
        self.setMinimumSize(1100, 800)
        
        # Widget principale con tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Inizializza le schede
        self.init_analysis_tab()
        self.init_viewer_tab()
        self.init_stats_tab()
        self.init_settings_tab()
        
        # Statusbar
        self.statusBar().showMessage("Pronto")
        
        # Mostra l'interfaccia
        self.show()
    
    def init_analyzer(self):
        """Inizializza l'analizzatore."""
        try:
            self.analyzer = ChessEngineAnalyzer(
                db_path=self.db_path
            )
            
            if not self.analyzer.connect():
                QMessageBox.critical(
                    self, "Errore",
                    "Impossibile connettersi al database."
                )
                return
            
            self.analyzer.setup_database()
            self.load_games_list()
            self.load_players_list()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Errore",
                f"Errore nell'inizializzazione dell'analizzatore: {e}"
            )
    
    def init_analysis_tab(self):
        """Inizializza la scheda di analisi."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Sezione selezione partita
        game_group = QGroupBox("Seleziona Partita")
        game_layout = QVBoxLayout()
        
        # Tabella delle partite
        self.games_table = QTableWidget()
        self.games_table.setColumnCount(6)
        self.games_table.setHorizontalHeaderLabels(["ID", "Bianco", "Nero", "Risultato", "Data", "Evento"])
        self.games_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.games_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.games_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        refresh_btn = QPushButton("Aggiorna Lista")
        refresh_btn.clicked.connect(self.load_games_list)
        
        game_layout.addWidget(self.games_table)
        game_layout.addWidget(refresh_btn)
        game_group.setLayout(game_layout)
        
        # Sezione opzioni analisi
        options_group = QGroupBox("Opzioni di Analisi")
        options_layout = QFormLayout()
        
        # Profondità analisi
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 30)
        self.depth_spin.setValue(18)
        options_layout.addRow("Profondità:", self.depth_spin)
        
        # MultiPV
        self.multipv_spin = QSpinBox()
        self.multipv_spin.setRange(1, 5)
        self.multipv_spin.setValue(3)
        options_layout.addRow("Varianti (MultiPV):", self.multipv_spin)
        
        # Tempo analisi
        self.time_spin = QDoubleSpinBox()
        self.time_spin.setRange(0.1, 10.0)
        self.time_spin.setValue(0.5)
        self.time_spin.setSingleStep(0.1)
        self.time_spin.setSuffix(" s")
        options_layout.addRow("Tempo per posizione:", self.time_spin)
        
        # Tipo di analisi
        self.analysis_type_group = QGroupBox("Tipo di Analisi")
        self.analysis_type_layout = QVBoxLayout()
        
        self.analysis_type_buttons = QButtonGroup()
        self.full_analysis_radio = QRadioButton("Analisi completa")
        self.critical_only_radio = QRadioButton("Solo posizioni critiche")
        self.analysis_type_buttons.addButton(self.full_analysis_radio)
        self.analysis_type_buttons.addButton(self.critical_only_radio)
        self.full_analysis_radio.setChecked(True)
        
        self.analysis_type_layout.addWidget(self.full_analysis_radio)
        self.analysis_type_layout.addWidget(self.critical_only_radio)
        
        # Soglia posizioni critiche
        self.critical_threshold_layout = QHBoxLayout()
        self.critical_threshold_label = QLabel("Soglia (centipawns):")
        self.critical_threshold_spin = QSpinBox()
        self.critical_threshold_spin.setRange(50, 500)
        self.critical_threshold_spin.setValue(100)
        self.critical_threshold_spin.setSingleStep(10)
        self.critical_threshold_spin.setEnabled(False)
        
        self.critical_threshold_layout.addWidget(self.critical_threshold_label)
        self.critical_threshold_layout.addWidget(self.critical_threshold_spin)
        
        # Collega l'attivazione della soglia
        self.critical_only_radio.toggled.connect(
            lambda checked: self.critical_threshold_spin.setEnabled(checked)
        )
        
        self.analysis_type_layout.addLayout(self.critical_threshold_layout)
        self.analysis_type_group.setLayout(self.analysis_type_layout)
        
        options_layout.addRow(self.analysis_type_group)
        
        # Percorso del motore
        self.engine_path_layout = QHBoxLayout()
        self.engine_path_edit = QLineEdit()
        self.engine_path_edit.setPlaceholderText("Percorso del motore (lasciare vuoto per auto-detection)")
        
        engine_browse_btn = QPushButton("Sfoglia...")
        engine_browse_btn.clicked.connect(self.browse_engine_path)
        
        self.engine_path_layout.addWidget(self.engine_path_edit)
        self.engine_path_layout.addWidget(engine_browse_btn)
        options_layout.addRow("Motore:", self.engine_path_layout)
        
        # Opzioni di esportazione
        export_group = QGroupBox("Opzioni di Esportazione")
        export_layout = QVBoxLayout()
        
        # Esporta in PGN
        self.export_pgn_layout = QHBoxLayout()
        self.export_pgn_check = QCheckBox("Esporta analisi in PGN")
        self.export_pgn_edit = QLineEdit()
        self.export_pgn_edit.setPlaceholderText("Percorso file PGN")
        self.export_pgn_edit.setEnabled(False)
        
        export_pgn_browse_btn = QPushButton("Sfoglia...")
        export_pgn_browse_btn.clicked.connect(self.browse_export_pgn_path)
        export_pgn_browse_btn.setEnabled(False)
        
        self.export_pgn_check.stateChanged.connect(lambda state: (
            self.export_pgn_edit.setEnabled(state == Qt.CheckState.Checked),
            export_pgn_browse_btn.setEnabled(state == Qt.CheckState.Checked)
        ))
        
        self.export_pgn_layout.addWidget(self.export_pgn_edit)
        self.export_pgn_layout.addWidget(export_pgn_browse_btn)
        
        export_layout.addWidget(self.export_pgn_check)
        export_layout.addLayout(self.export_pgn_layout)
        
        # Esporta in HTML
        self.export_html_check = QCheckBox("Esporta analisi in HTML con diagrammi interattivi")
        export_layout.addWidget(self.export_html_check)
        
        export_group.setLayout(export_layout)
        options_layout.addRow(export_group)
        
        options_group.setLayout(options_layout)
        
        # Pulsanti azioni
        actions_layout = QHBoxLayout()
        
        analyze_btn = QPushButton("Avvia Analisi")
        analyze_btn.setMinimumHeight(40)
        analyze_btn.clicked.connect(self.start_analysis)
        
        show_analysis_btn = QPushButton("Mostra Analisi Esistente")
        show_analysis_btn.clicked.connect(self.show_existing_analysis)
        
        actions_layout.addWidget(analyze_btn)
        actions_layout.addWidget(show_analysis_btn)
        
        # Area risultati
        results_group = QGroupBox("Risultati dell'Analisi")
        results_layout = QVBoxLayout()
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 0)  # Modalità indeterminata
        self.progress_bar.hide()
        
        results_layout.addWidget(self.analysis_text)
        results_layout.addWidget(self.progress_bar)
        
        results_group.setLayout(results_layout)
        
        # Assembla il layout
        layout.addWidget(game_group)
        layout.addWidget(options_group)
        layout.addLayout(actions_layout)
        layout.addWidget(results_group)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Analisi")
    
    def init_viewer_tab(self):
        """Inizializza la scheda visualizzatore."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Splitter per dividere la lista partite dalla scacchiera
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Pannello sinistro: lista partite analizzate
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        analyzed_group = QGroupBox("Partite Analizzate")
        analyzed_layout = QVBoxLayout()
        
        self.analyzed_table = QTableWidget()
        self.analyzed_table.setColumnCount(6)
        self.analyzed_table.setHorizontalHeaderLabels(["ID", "Bianco", "Nero", "Risultato", "Data", "Evento"])
        self.analyzed_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.analyzed_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.analyzed_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.analyzed_table.itemSelectionChanged.connect(self.load_selected_analysis)
        
        refresh_analyzed_btn = QPushButton("Aggiorna Lista")
        refresh_analyzed_btn.clicked.connect(self.load_analyzed_games)
        
        analyzed_layout.addWidget(self.analyzed_table)
        analyzed_layout.addWidget(refresh_analyzed_btn)
        analyzed_group.setLayout(analyzed_layout)
        
        left_layout.addWidget(analyzed_group)
        left_panel.setLayout(left_layout)
        
        # Pannello destro: visualizzatore
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Splitter verticale per scacchiera e analisi
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Pannello superiore con scacchiera
        board_panel = QWidget()
        board_layout = QVBoxLayout()
        
        # Scacchiera
        board_group = QGroupBox("Posizione")
        board_layout_inner = QVBoxLayout()
        
        self.chess_board = ChessBoardWidget()
        
        # Aggiungi pulsante per capovolgere la scacchiera
        flip_btn = QPushButton("Capovolgi scacchiera")
        flip_btn.clicked.connect(lambda: self.chess_board.flip_board())
        
        board_layout_inner.addWidget(self.chess_board)
        board_layout_inner.addWidget(flip_btn)
        board_group.setLayout(board_layout_inner)
        
        board_layout.addWidget(board_group)
        board_panel.setLayout(board_layout)
        
        # Pannello inferiore con analisi
        analysis_panel = QWidget()
        analysis_layout = QVBoxLayout()
        
        # Grafico valutazione
        eval_group = QGroupBox("Grafico Valutazione")
        eval_layout = QVBoxLayout()
        
        self.eval_graph = EvaluationGraphWidget()
        
        eval_layout.addWidget(self.eval_graph)
        eval_group.setLayout(eval_layout)
        
        # Analisi della posizione
        position_group = QGroupBox("Analisi della Posizione")
        position_layout = QVBoxLayout()
        
        self.position_text = QTextEdit()
        self.position_text.setReadOnly(True)
        
        # Controlli di navigazione
        nav_layout = QHBoxLayout()
        
        self.first_btn = QPushButton("|<")
        self.prev_btn = QPushButton("<")
        self.position_label = QLabel("Posizione: 0/0")
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_btn = QPushButton(">")
        self.last_btn = QPushButton(">|")
        
        self.first_btn.clicked.connect(self.show_first_position)
        self.prev_btn.clicked.connect(self.show_prev_position)
        self.next_btn.clicked.connect(self.show_next_position)
        self.last_btn.clicked.connect(self.show_last_position)
        
        nav_layout.addWidget(self.first_btn)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.position_label)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.last_btn)
        
        position_layout.addWidget(self.position_text)
        position_layout.addLayout(nav_layout)
        
        # Pulsanti di esportazione
        export_layout = QHBoxLayout()
        
        export_pgn_btn = QPushButton("Esporta PGN")
        export_pgn_btn.clicked.connect(self.export_current_analysis_pgn)
        
        export_html_btn = QPushButton("Esporta HTML")
        export_html_btn.clicked.connect(self.export_current_analysis_html)
        
        export_layout.addWidget(export_pgn_btn)
        export_layout.addWidget(export_html_btn)
        
        position_layout.addLayout(export_layout)
        position_group.setLayout(position_layout)
        
        analysis_layout.addWidget(eval_group)
        analysis_layout.addWidget(position_group)
        analysis_panel.setLayout(analysis_layout)
        
        # Aggiungi pannelli al splitter
        right_splitter.addWidget(board_panel)
        right_splitter.addWidget(analysis_panel)
        
        right_layout.addWidget(right_splitter)
        right_panel.setLayout(right_layout)
        
        # Aggiungi i pannelli allo splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
        tab.setLayout(layout)
        
        # Inizializza variabili per la navigazione
        self.current_analysis = None
        self.current_position_index = 0
        
        self.tabs.addTab(tab, "Visualizzatore")
    
    def init_stats_tab(self):
        """Inizializza la scheda delle statistiche."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Selezione giocatore
        player_group = QGroupBox("Seleziona Giocatore")
        player_layout = QHBoxLayout()
        
        self.player_combo = QComboBox()
        self.player_combo.setEditable(True)
        
        refresh_players_btn = QPushButton("Aggiorna Lista")
        refresh_players_btn.clicked.connect(self.load_players_list)
        
        calculate_stats_btn = QPushButton("Calcola Statistiche")
        calculate_stats_btn.clicked.connect(self.calculate_player_stats)
        
        player_layout.addWidget(self.player_combo)
        player_layout.addWidget(refresh_players_btn)
        player_layout.addWidget(calculate_stats_btn)
        
        player_group.setLayout(player_layout)
        
        # Risultati statistiche
        stats_group = QGroupBox("Statistiche del Giocatore")
        stats_layout = QVBoxLayout()
        
        # Crea un widget scorrevole per le statistiche
        stats_scroll = QScrollArea()
        stats_scroll.setWidgetResizable(True)
        stats_widget = QWidget()
        self.stats_form_layout = QFormLayout(stats_widget)
        
        # Campi statistiche
        self.stats_fields = {
            "name": QLabel(""),
            "total_games": QLabel(""),
            "wins": QLabel(""),
            "losses": QLabel(""),
            "draws": QLabel(""),
            "win_percent": QLabel(""),
            "avg_blunders": QLabel(""),
            "avg_mistakes": QLabel(""),
            "last_updated": QLabel("")
        }
        
        # Aggiungi campi al layout
        self.stats_form_layout.addRow("<b>Giocatore:</b>", self.stats_fields["name"])
        self.stats_form_layout.addRow("<b>Partite totali:</b>", self.stats_fields["total_games"])
        self.stats_form_layout.addRow("<b>Vittorie:</b>", self.stats_fields["wins"])
        self.stats_form_layout.addRow("<b>Pareggi:</b>", self.stats_fields["draws"])
        self.stats_form_layout.addRow("<b>Sconfitte:</b>", self.stats_fields["losses"])
        self.stats_form_layout.addRow("<b>Percentuale vittorie:</b>", self.stats_fields["win_percent"])
        self.stats_form_layout.addRow("<b>Media errori gravi per partita:</b>", self.stats_fields["avg_blunders"])
        self.stats_form_layout.addRow("<b>Media errori per partita:</b>", self.stats_fields["avg_mistakes"])
        self.stats_form_layout.addRow("<b>Ultimo aggiornamento:</b>", self.stats_fields["last_updated"])
        
        stats_scroll.setWidget(stats_widget)
        
        # Grafico con statistiche
        self.stats_figure = Figure(figsize=(4, 3), dpi=100)
        self.stats_canvas = FigureCanvas(self.stats_figure)
        self.stats_canvas.setMinimumHeight(200)
        
        # Pulsanti per esportazione
        stats_buttons_layout = QHBoxLayout()
        
        export_stats_btn = QPushButton("Esporta Statistiche CSV")
        export_stats_btn.clicked.connect(self.export_player_stats_csv)
        
        stats_buttons_layout.addWidget(export_stats_btn)
        
        stats_layout.addWidget(stats_scroll)
        stats_layout.addWidget(self.stats_canvas)
        stats_layout.addLayout(stats_buttons_layout)
        
        stats_group.setLayout(stats_layout)
        
        # Partite del giocatore
        games_group = QGroupBox("Partite Giocate")
        games_layout = QVBoxLayout()
        
        self.player_games_table = QTableWidget()
        self.player_games_table.setColumnCount(6)
        self.player_games_table.setHorizontalHeaderLabels(["ID", "Bianco", "Nero", "Risultato", "Data", "Evento"])
        self.player_games_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.player_games_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.player_games_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        load_player_game_btn = QPushButton("Carica Partita Selezionata nel Visualizzatore")
        load_player_game_btn.clicked.connect(self.load_player_game_in_viewer)
        
        games_layout.addWidget(self.player_games_table)
        games_layout.addWidget(load_player_game_btn)
        
        games_group.setLayout(games_layout)
        
        # Stato operazione
        self.stats_progress_bar = QProgressBar()
        self.stats_progress_bar.setTextVisible(True)
        self.stats_progress_bar.setRange(0, 0)  # Modalità indeterminata
        self.stats_progress_bar.hide()
        
        # Assembla il layout
        layout.addWidget(player_group)
        layout.addWidget(stats_group)
        layout.addWidget(games_group)
        layout.addWidget(self.stats_progress_bar)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Statistiche")
    
    def init_settings_tab(self):
        """Inizializza la scheda impostazioni."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Form impostazioni
        settings_group = QGroupBox("Impostazioni")
        settings_layout = QFormLayout()
        
        # Percorso database
        self.db_path_layout = QHBoxLayout()
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setText(self.db_path)
        
        db_browse_btn = QPushButton("Sfoglia...")
        db_browse_btn.clicked.connect(self.browse_db_path)
        
        self.db_path_layout.addWidget(self.db_path_edit)
        self.db_path_layout.addWidget(db_browse_btn)
        
        settings_layout.addRow("Database:", self.db_path_layout)
        
        # Percorso motore default
        self.default_engine_layout = QHBoxLayout()
        self.default_engine_edit = QLineEdit()
        
        default_engine_browse_btn = QPushButton("Sfoglia...")
        default_engine_browse_btn.clicked.connect(self.browse_default_engine_path)
        
        self.default_engine_layout.addWidget(self.default_engine_edit)
        self.default_engine_layout.addWidget(default_engine_browse_btn)
        
        settings_layout.addRow("Motore predefinito:", self.default_engine_layout)
        
        # Opzioni di visualizzazione
        display_group = QGroupBox("Opzioni di Visualizzazione")
        display_layout = QVBoxLayout()
        
        self.highlight_blunders_check = QCheckBox("Evidenzia errori gravi")
        self.highlight_blunders_check.setChecked(True)
        
        self.auto_flip_check = QCheckBox("Capovolgi automaticamente scacchiera in base al turno")
        
        display_layout.addWidget(self.highlight_blunders_check)
        display_layout.addWidget(self.auto_flip_check)
        
        display_group.setLayout(display_layout)
        
        # Informazioni
        info_group = QGroupBox("Informazioni")
        info_layout = QVBoxLayout()
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setHtml("""
        <h2>ChessEngine Analysis GUI</h2>
        <p>Interfaccia grafica per l'analisi delle partite di scacchi con motori di scacchi.</p>
        <p>Questa applicazione permette di:</p>
        <ul>
            <li>Analizzare partite di scacchi con un motore esterno (Stockfish)</li>
            <li>Identificare posizioni critiche nelle partite</li>
            <li>Visualizzare l'analisi con commenti</li>
            <li>Esportare l'analisi in formato PGN e HTML interattivo</li>
            <li>Calcolare statistiche avanzate per i giocatori</li>
        </ul>
        <p>Versione: 1.0</p>
        """)
        
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        
        # Pulsante per salvare impostazioni
        save_btn = QPushButton("Salva Impostazioni")
        save_btn.clicked.connect(self.save_settings)
        
        settings_group.setLayout(settings_layout)
        
        layout.addWidget(settings_group)
        layout.addWidget(display_group)
        layout.addWidget(save_btn)
        layout.addWidget(info_group)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Impostazioni")
    
    def load_games_list(self):
        """Carica la lista delle partite dal database."""
        if not self.analyzer or not self.analyzer.conn:
            QMessageBox.warning(
                self, "Avviso",
                "Database non connesso."
            )
            return
        
        try:
            # Recupera le partite
            self.analyzer.cursor.execute("""
                SELECT id, white_player, black_player, result, date, event
                FROM games
                ORDER BY id DESC
                LIMIT 100
            """)
            
            self.games_data = self.analyzer.cursor.fetchall()
            
            # Aggiorna la tabella
            self.games_table.setRowCount(0)
            
            for row_idx, (game_id, white, black, result, date, event) in enumerate(self.games_data):
                self.games_table.insertRow(row_idx)
                
                self.games_table.setItem(row_idx, 0, QTableWidgetItem(str(game_id)))
                self.games_table.setItem(row_idx, 1, QTableWidgetItem(white))
                self.games_table.setItem(row_idx, 2, QTableWidgetItem(black))
                self.games_table.setItem(row_idx, 3, QTableWidgetItem(result))
                self.games_table.setItem(row_idx, 4, QTableWidgetItem(date))
                self.games_table.setItem(row_idx, 5, QTableWidgetItem(event))
            
            self.statusBar().showMessage(f"Caricate {len(self.games_data)} partite")
            
        except Exception as e:
            QMessageBox.warning(
                self, "Errore",
                f"Errore nel caricamento delle partite: {e}"
            )
    
    def load_players_list(self):
        """Carica la lista dei giocatori dal database."""
        if not self.analyzer or not self.analyzer.conn:
            return
        
        try:
            # Recupera tutti i giocatori unici (bianchi e neri)
            self.analyzer.cursor.execute("""
                SELECT DISTINCT white_player AS player FROM games
                UNION
                SELECT DISTINCT black_player AS player FROM games
                ORDER BY player
            """)
            
            players = [row[0] for row in self.analyzer.cursor.fetchall()]
            
            current_text = self.player_combo.currentText()
            
            # Aggiorna la combobox
            self.player_combo.clear()
            self.player_combo.addItems(players)
            
            # Ripristina il testo selezionato
            if current_text and current_text in players:
                index = self.player_combo.findText(current_text)
                if index >= 0:
                    self.player_combo.setCurrentIndex(index)
            
        except Exception:
            pass
    
    def load_analyzed_games(self):
        """Carica la lista delle partite analizzate."""
        if not self.analyzer or not self.analyzer.conn:
            QMessageBox.warning(
                self, "Avviso",
                "Database non connesso."
            )
            return
        
        try:
            # Recupera le partite analizzate (quelle con commenti)
            self.analyzer.cursor.execute("""
                SELECT DISTINCT g.id, g.white_player, g.black_player, g.result, g.date, g.event
                FROM games g
                JOIN engine_comments c ON g.id = c.game_id
                ORDER BY g.id DESC
            """)
            
            analyzed_games = self.analyzer.cursor.fetchall()
            
            # Aggiorna la tabella
            self.analyzed_table.setRowCount(0)
            
            for row_idx, (game_id, white, black, result, date, event) in enumerate(analyzed_games):
                self.analyzed_table.insertRow(row_idx)
                
                self.analyzed_table.setItem(row_idx, 0, QTableWidgetItem(str(game_id)))
                self.analyzed_table.setItem(row_idx, 1, QTableWidgetItem(white))
                self.analyzed_table.setItem(row_idx, 2, QTableWidgetItem(black))
                self.analyzed_table.setItem(row_idx, 3, QTableWidgetItem(result))
                self.analyzed_table.setItem(row_idx, 4, QTableWidgetItem(date))
                self.analyzed_table.setItem(row_idx, 5, QTableWidgetItem(event))
            
            self.statusBar().showMessage(f"Caricate {len(analyzed_games)} partite analizzate")
            
        except Exception as e:
            QMessageBox.warning(
                self, "Errore",
                f"Errore nel caricamento delle partite analizzate: {e}"
            )
    
    def browse_engine_path(self):
        """Apre un dialogo per selezionare il percorso del motore."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleziona Motore di Scacchi",
            filter="Eseguibili (*.exe);;Tutti i file (*)"
        )
        
        if file_path:
            self.engine_path_edit.setText(file_path)
    
    def browse_default_engine_path(self):
        """Apre un dialogo per selezionare il percorso predefinito del motore."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleziona Motore di Scacchi Predefinito",
            filter="Eseguibili (*.exe);;Tutti i file (*)"
        )
        
        if file_path:
            self.default_engine_edit.setText(file_path)
    
    def browse_export_pgn_path(self):
        """Apre un dialogo per selezionare il percorso di esportazione PGN."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salva File PGN",
            filter="File PGN (*.pgn);;Tutti i file (*)"
        )
        
        if file_path:
            self.export_pgn_edit.setText(file_path)
    
    def browse_db_path(self):
        """Apre un dialogo per selezionare il percorso del database."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleziona Database SQLite",
            filter="Database SQLite (*.db);;Tutti i file (*)"
        )
        
        if file_path:
            self.db_path_edit.setText(file_path)
    
    def save_settings(self):
        """Salva le impostazioni."""
        new_db_path = self.db_path_edit.text()
        default_engine = self.default_engine_edit.text()
        
        # Aggiorna l'impostazione del motore predefinito nella scheda analisi
        if default_engine:
            self.engine_path_edit.setText(default_engine)
        
        if new_db_path != self.db_path:
            reply = QMessageBox.question(
                self, "Cambio Database",
                "Cambiare il database richiede il riavvio dell'applicazione. Continuare?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.db_path = new_db_path
                QMessageBox.information(
                    self, "Impostazioni Salvate",
                    "Le impostazioni sono state salvate. Riavvia l'applicazione per applicare le modifiche."
                )
            
        else:
            QMessageBox.information(
                self, "Impostazioni Salvate",
                "Le impostazioni sono state salvate."
            )
    
    def start_analysis(self):
        """Avvia l'analisi della partita selezionata."""
        # Ottieni la partita selezionata
        selected_rows = self.games_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(
                self, "Avviso",
                "Seleziona una partita da analizzare."
            )
            return
        
        # Ottieni l'ID della partita selezionata
        row = selected_rows[0].row()
        game_id = int(self.games_table.item(row, 0).text())
        
        # Ottieni le opzioni di analisi
        depth = self.depth_spin.value()
        multipv = self.multipv_spin.value()
        time_limit = self.time_spin.value()
        critical_only = self.critical_only_radio.isChecked()
        critical_threshold = self.critical_threshold_spin.value() if critical_only else 100
        engine_path = self.engine_path_edit.text() or None
        
        # Verifica se esportare in PGN
        export_path = None
        if self.export_pgn_check.isChecked():
            export_path = self.export_pgn_edit.text()
            if not export_path:
                QMessageBox.warning(
                    self, "Avviso",
                    "Specificare un percorso per l'esportazione PGN."
                )
                return
        
        # Verifica se esportare in HTML
        export_html = self.export_html_check.isChecked()
        
        # Prepara l'interfaccia per l'analisi
        self.analysis_text.clear()
        self.progress_bar.show()
        
        # Crea e avvia il thread di analisi
        self.analysis_thread = AnalysisThread(
            self.db_path,        # Percorso del database
            engine_path,         # Percorso del motore
            depth,               # Profondità dell'analisi
            multipv,             # Numero varianti
            game_id,             # ID della partita
            critical_only,       # Solo posizioni critiche
            critical_threshold,  # Soglia per posizioni critiche
            export_path,         # Percorso esportazione PGN
            export_html,         # Esportazione HTML
            time_limit           # Limite di tempo per posizione
        )
        self.analysis_thread.progress_update.connect(self.update_analysis_progress)
        self.analysis_thread.analysis_completed.connect(self.analysis_completed)
        self.analysis_thread.start()
        
        # Aggiorna lo stato
        self.statusBar().showMessage("Analisi in corso...")

    @pyqtSlot(str)
    def update_analysis_progress(self, message):
        """Aggiorna il progresso dell'analisi."""
        self.analysis_text.append(message)
        # Scorri automaticamente verso il basso
        scroll_bar = self.analysis_text.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
    
    @pyqtSlot(bool, object)
    def analysis_completed(self, success, comments):
        """Gestisce il completamento dell'analisi."""
        self.progress_bar.hide()
        
        if success:
            self.statusBar().showMessage("Analisi completata con successo")
            
            # Mostra i commenti se disponibili
            if comments:
                self.analysis_text.append("\n===== COMMENTI DELL'ANALISI =====")
                
                for comment in comments:
                    move_num = comment["move_number"]
                    turn = "..." if comment["turn"] == "black" else "."
                    san = comment["san"]
                    comment_type = comment["comment_type"]
                    comment_text = comment["comment_text"]
                    
                    # Simboli per diversi tipi di commento
                    symbols = {
                        "blunder": "??",
                        "mistake": "?",
                        "inaccuracy": "?!",
                        "excellent_move": "!!",
                        "good_move": "!",
                        "interesting_move": "!?"
                    }
                    
                    symbol = symbols.get(comment_type, "")
                    
                    self.analysis_text.append(f"{move_num}{turn} {san} {symbol}")
                    self.analysis_text.append(f"  {comment_text}")
                    self.analysis_text.append("")
            
            # Fai refresh della lista delle partite analizzate
            self.load_analyzed_games()
            
            # Offri di caricare l'analisi nel visualizzatore
            reply = QMessageBox.question(
                self, "Analisi Completata",
                "Vuoi caricare questa partita nel visualizzatore?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Passa alla scheda visualizzatore
                self.tabs.setCurrentIndex(1)  # Indice della scheda visualizzatore
                
                # Trova la partita nella tabella e selezionala
                for row in range(self.analyzed_table.rowCount()):
                    if int(self.analyzed_table.item(row, 0).text()) == int(self.analysis_thread.game_id):
                        self.analyzed_table.selectRow(row)
                        break
                
        else:
            self.statusBar().showMessage("Errore durante l'analisi")
    
    def show_existing_analysis(self):
        """Mostra l'analisi esistente per la partita selezionata."""
        # Ottieni la partita selezionata
        selected_rows = self.games_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(
                self, "Avviso",
                "Seleziona una partita da visualizzare."
            )
            return
        
        # Ottieni l'ID della partita selezionata
        row = selected_rows[0].row()
        game_id = int(self.games_table.item(row, 0).text())
        
        # Recupera i commenti dell'analisi
        comments = self.analyzer.get_game_comments(game_id)
        
        if not comments:
            QMessageBox.information(
                self, "Informazione",
                "Nessuna analisi trovata per questa partita.\nEsegui prima l'analisi."
            )
            return
        
        # Mostra i commenti
        self.analysis_text.clear()
        self.analysis_text.append("===== ANALISI ESISTENTE =====")
        
        for comment in comments:
            move_num = comment["move_number"]
            turn = "..." if comment["turn"] == "black" else "."
            san = comment["san"]
            comment_type = comment["comment_type"]
            comment_text = comment["comment_text"]
            
            # Simboli per diversi tipi di commento
            symbols = {
                "blunder": "??",
                "mistake": "?",
                "inaccuracy": "?!",
                "excellent_move": "!!",
                "good_move": "!",
                "interesting_move": "!?"
            }
            
            symbol = symbols.get(comment_type, "")
            
            self.analysis_text.append(f"{move_num}{turn} {san} {symbol}")
            self.analysis_text.append(f"  {comment_text}")
            self.analysis_text.append("")
        
        self.statusBar().showMessage("Analisi caricata")
        
        # Offri di caricare l'analisi nel visualizzatore
        reply = QMessageBox.question(
            self, "Analisi Caricata",
            "Vuoi caricare questa partita nel visualizzatore?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Passa alla scheda visualizzatore
            self.tabs.setCurrentIndex(1)  # Indice della scheda visualizzatore
            
            # Trova la partita nella tabella e selezionala
            for row in range(self.analyzed_table.rowCount()):
                if int(self.analyzed_table.item(row, 0).text()) == game_id:
                    self.analyzed_table.selectRow(row)
                    break
    
    def load_selected_analysis(self):
        """Carica l'analisi della partita selezionata nel visualizzatore."""
        # Ottieni la partita selezionata
        selected_rows = self.analyzed_table.selectedIndexes()
        if not selected_rows:
            return
        
        # Ottieni l'ID della partita selezionata
        row = selected_rows[0].row()
        game_id = int(self.analyzed_table.item(row, 0).text())
        
        try:
            # Recupera i dettagli della partita
            self.analyzer.cursor.execute("""
                SELECT white_player, black_player, result
                FROM games
                WHERE id = ?
            """, (game_id,))
            
            game_details = self.analyzer.cursor.fetchone()
            white, black, result = game_details
            
            # Recupera le mosse della partita
            self.analyzer.cursor.execute("""
                SELECT ply_number, san, uci
                FROM moves
                WHERE game_id = ?
                ORDER BY ply_number
            """, (game_id,))
            
            moves_data = self.analyzer.cursor.fetchall()
            
            # Recupera i commenti dell'analisi
            comments = self.analyzer.get_game_comments(game_id)
            comments_by_ply = {c["ply"]: c for c in comments}
            
            # Recupera l'analisi completa
            analysis_data = self.analyzer.get_game_analysis(game_id)
            analysis_by_ply = {a["ply"]: a for a in analysis_data}
            
            # Prepara i dati per la visualizzazione
            positions = []
            board = chess.Board()
            
            positions.append({
                "ply": -1,
                "board": board.copy(),
                "move_text": "Posizione iniziale",
                "comment": None,
                "analysis": None
            })
            
            for ply, san, uci in moves_data:
                move = chess.Move.from_uci(uci)
                board.push(move)
                
                move_number = (ply // 2) + 1
                turn = "..." if ply % 2 == 1 else "."
                move_text = f"{move_number}{turn} {san}"
                
                comment = comments_by_ply.get(ply)
                analysis = analysis_by_ply.get(ply)
                
                positions.append({
                    "ply": ply,
                    "board": board.copy(),
                    "move_text": move_text,
                    "comment": comment,
                    "analysis": analysis
                })
            
            # Salva i dati per la navigazione
            self.current_analysis = {
                "game_id": game_id,
                "white": white,
                "black": black,
                "result": result,
                "positions": positions
            }
            
            # Aggiorna il grafico dell'analisi
            self.update_eval_graph(analysis_data + list(comments_by_ply.values()))
            
            self.current_position_index = 0
            self.update_position_display()
            
            self.statusBar().showMessage(f"Partita caricata: {white} vs {black}, {result}")
            
        except Exception as e:
            QMessageBox.warning(
                self, "Errore",
                f"Errore nel caricamento dell'analisi: {e}"
            )
    
    def update_eval_graph(self, analysis_data):
        """Aggiorna il grafico della valutazione."""
        if analysis_data:
            self.eval_graph.update_graph(analysis_data)
    
    def update_position_display(self):
        """Aggiorna la visualizzazione della posizione corrente."""
        if not self.current_analysis:
            return
        
        position = self.current_analysis["positions"][self.current_position_index]
        
        # Gestisci il capovolgimento automatico della scacchiera
        if self.auto_flip_check.isChecked() and position["ply"] >= 0:
            # Capovolgi se è il turno del nero
            turn = position["ply"] % 2 == 1
            if self.chess_board.flip != turn:
                self.chess_board.flip = turn
        
        # Aggiorna la scacchiera
        self.chess_board.board = position["board"]
        self.chess_board.update_board()
        
        # Aggiorna l'etichetta della posizione
        self.position_label.setText(f"Posizione: {self.current_position_index}/{len(self.current_analysis['positions'])-1}")
        
        # Aggiorna il testo dell'analisi
        self.position_text.clear()
        
        # Intestazione
        if self.current_position_index == 0:
            self.position_text.append("<h3>Posizione iniziale</h3>")
            self.position_text.append(f"<p><b>Partita:</b> {self.current_analysis['white']} vs {self.current_analysis['black']} ({self.current_analysis['result']})</p>")
        else:
            # Mostra mossa
            self.position_text.append(f"<h3>Mossa: {position['move_text']}</h3>")
        
        # Analisi del motore
        if position["analysis"]:
            eval_cp = position["analysis"].get("eval_cp")
            eval_mate = position["analysis"].get("eval_mate")
            
            # Formatta la valutazione
            if eval_mate is not None:
                eval_str = f"Matto in {abs(eval_mate)}" if eval_mate != 0 else "Patta forzata"
                if eval_mate > 0:
                    eval_str = f"+{eval_str}"
                else:
                    eval_str = f"-{eval_str}"
            elif eval_cp is not None:
                pawns = eval_cp / 100.0
                eval_str = f"{'+' if pawns > 0 else ''}{pawns:.2f}"
            else:
                eval_str = "?"
            
            # Mostra la valutazione
            self.position_text.append(f"<p><b>Valutazione:</b> {eval_str}</p>")
            
            # Varianti
            if "variations" in position["analysis"] and position["analysis"]["variations"]:
                self.position_text.append("<p><b>Varianti:</b></p>")
                self.position_text.append("<ol>")
                
                for var in position["analysis"]["variations"]:
                    moves = " ".join(var["moves"])
                    self.position_text.append(f"<li>{moves}</li>")
                
                self.position_text.append("</ol>")
        
        # Commento dell'analisi
        if position["comment"]:
            comment_type = position["comment"]["comment_type"]
            comment_text = position["comment"]["comment_text"]
            
            # Colori per diversi tipi di commento
            colors = {
                "blunder": "#e74c3c",
                "mistake": "#e67e22",
                "inaccuracy": "#f39c12",
                "excellent_move": "#2ecc71",
                "good_move": "#27ae60",
                "interesting_move": "#3498db"
            }
            
            color = colors.get(comment_type, "black")
            
            self.position_text.append(f'<div style="margin-top: 10px; padding: 10px; background-color: #f8f9fa; border-left: 5px solid {color};">')
            self.position_text.append(f'<p style="color:{color}; font-weight:bold;">{comment_text}</p>')
            self.position_text.append('</div>')
    
    def show_first_position(self):
        """Mostra la prima posizione."""
        if self.current_analysis:
            self.current_position_index = 0
            self.update_position_display()
    
    def show_prev_position(self):
        """Mostra la posizione precedente."""
        if self.current_analysis and self.current_position_index > 0:
            self.current_position_index -= 1
            self.update_position_display()
    
    def show_next_position(self):
        """Mostra la posizione successiva."""
        if self.current_analysis and self.current_position_index < len(self.current_analysis["positions"]) - 1:
            self.current_position_index += 1
            self.update_position_display()
    
    def show_last_position(self):
        """Mostra l'ultima posizione."""
        if self.current_analysis:
            self.current_position_index = len(self.current_analysis["positions"]) - 1
            self.update_position_display()
    
    def export_current_analysis_pgn(self):
        """Esporta l'analisi corrente in PGN."""
        if not self.current_analysis:
            QMessageBox.warning(
                self, "Avviso",
                "Nessuna analisi caricata."
            )
            return
        
        game_id = self.current_analysis["game_id"]
        
        # Chiedi il percorso di esportazione
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salva Analisi PGN",
            f"analysis_game_{game_id}.pgn",
            "File PGN (*.pgn);;Tutti i file (*)"
        )
        
        if file_path:
            success = self.analyzer.export_analysis_to_pgn(game_id, file_path)
            
            if success:
                QMessageBox.information(
                    self, "Esportazione Completata",
                    f"Analisi esportata con successo in:\n{file_path}"
                )
            else:
                QMessageBox.warning(
                    self, "Errore",
                    "Errore durante l'esportazione dell'analisi."
                )
    
    def export_current_analysis_html(self):
        """Esporta l'analisi corrente in HTML."""
        if not self.current_analysis:
            QMessageBox.warning(
                self, "Avviso",
                "Nessuna analisi caricata."
            )
            return
        
        game_id = self.current_analysis["game_id"]
        
        # Chiedi il percorso di esportazione
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salva Analisi HTML",
            f"analysis_game_{game_id}.html",
            "File HTML (*.html);;Tutti i file (*)"
        )
        
        if file_path:
            success = self.analyzer.export_analysis_to_html(game_id, file_path)
            
            if success:
                QMessageBox.information(
                    self, "Esportazione Completata",
                    f"Analisi esportata con successo in:\n{file_path}"
                )
                
                # Chiedi se aprire il file HTML
                reply = QMessageBox.question(
                    self, "Apri HTML",
                    "Vuoi aprire il file HTML nel browser?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        webbrowser.open('file://' + os.path.abspath(file_path))
                    except:
                        pass
            else:
                QMessageBox.warning(
                    self, "Errore",
                    "Errore durante l'esportazione dell'analisi."
                )
    
    def calculate_player_stats(self):
        """Calcola le statistiche per il giocatore selezionato."""
        player_name = self.player_combo.currentText()
        
        if not player_name:
            QMessageBox.warning(
                self, "Avviso",
                "Seleziona un giocatore."
            )
            return
        
        # Prepara l'interfaccia
        self.stats_progress_bar.show()
        
        # Avvia il thread per calcolare le statistiche
        self.stats_thread = PlayerStatsThread(self.db_path, player_name)
        self.stats_thread.progress_update.connect(self.update_stats_progress)
        self.stats_thread.stats_completed.connect(self.stats_calculation_completed)
        self.stats_thread.start()
        
        # Carica le partite del giocatore
        self.load_player_games(player_name)
    
    @pyqtSlot(str)
    def update_stats_progress(self, message):
        """Aggiorna il progresso del calcolo delle statistiche."""
        self.statusBar().showMessage(message)
    
    @pyqtSlot(bool, dict)
    def stats_calculation_completed(self, success, stats):
        """Gestisce il completamento del calcolo delle statistiche."""
        self.stats_progress_bar.hide()
        
        if success and stats:
            # Aggiorna i campi delle statistiche
            self.stats_fields["name"].setText(stats["player_name"])
            self.stats_fields["total_games"].setText(str(stats["total_games"]))
            self.stats_fields["wins"].setText(str(stats["wins"]))
            self.stats_fields["losses"].setText(str(stats["losses"]))
            self.stats_fields["draws"].setText(str(stats["draws"]))
            self.stats_fields["win_percent"].setText(f"{stats['win_percentage']:.1f}%")
            self.stats_fields["avg_blunders"].setText(f"{stats['avg_blunders']:.2f}")
            self.stats_fields["avg_mistakes"].setText(f"{stats['avg_mistakes']:.2f}")
            
            last_updated = stats.get("last_updated", "")
            if last_updated:
                try:
                    # Formatta la data
                    date_obj = datetime.fromisoformat(last_updated)
                    formatted_date = date_obj.strftime("%d/%m/%Y %H:%M")
                    self.stats_fields["last_updated"].setText(formatted_date)
                except:
                    self.stats_fields["last_updated"].setText(last_updated)
            
            # Aggiorna il grafico delle statistiche
            self.update_stats_graph(stats)
            
            self.statusBar().showMessage(f"Statistiche calcolate per {stats['player_name']}")
        else:
            QMessageBox.warning(
                self, "Avviso",
                "Errore nel calcolo delle statistiche o nessun dato disponibile."
            )
            self.statusBar().showMessage("Errore nel calcolo delle statistiche")
    
    def update_stats_graph(self, stats):
        """Aggiorna il grafico delle statistiche."""
        # Pulisci il grafico esistente
        self.stats_figure.clear()
        
        # Crea un grafico a torta per il risultato delle partite
        ax = self.stats_figure.add_subplot(121)
        labels = ['Vittorie', 'Pareggi', 'Sconfitte']
        sizes = [stats['wins'], stats['draws'], stats['losses']]
        colors = ['#2ecc71', '#95a5a6', '#e74c3c']
        
        # Evita dividere per zero se non ci sono partite
        if sum(sizes) > 0:
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                   startangle=90, wedgeprops={'width': 0.5})
            ax.set_title('Risultati Partite')
        else:
            ax.text(0.5, 0.5, "Nessun dato", ha='center', va='center')
        
        # Crea un grafico a barre per gli errori
        ax2 = self.stats_figure.add_subplot(122)
        error_types = ['Errori Gravi', 'Errori']
        error_values = [stats['avg_blunders'], stats['avg_mistakes']]
        bars = ax2.bar(error_types, error_values, color=['#e74c3c', '#f39c12'])
        
        # Aggiungi i valori sopra le barre
        for bar in bars:
            height = bar.get_height()
            ax2.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
        
        ax2.set_ylabel('Media per partita')
        ax2.set_title('Errori Commessi')
        
        # Adatta il layout
        self.stats_figure.tight_layout()
        self.stats_canvas.draw()
    
    def load_player_games(self, player_name):
        """Carica le partite giocate da un giocatore."""
        if not self.analyzer or not self.analyzer.conn:
            return
        
        try:
            # Recupera le partite del giocatore
            games = self.analyzer.get_player_games(player_name)
            
            # Aggiorna la tabella
            self.player_games_table.setRowCount(0)
            
            for row_idx, (game_id, white, black, result, date, event) in enumerate(games):
                self.player_games_table.insertRow(row_idx)
                
                self.player_games_table.setItem(row_idx, 0, QTableWidgetItem(str(game_id)))
                self.player_games_table.setItem(row_idx, 1, QTableWidgetItem(white))
                self.player_games_table.setItem(row_idx, 2, QTableWidgetItem(black))
                self.player_games_table.setItem(row_idx, 3, QTableWidgetItem(result))
                self.player_games_table.setItem(row_idx, 4, QTableWidgetItem(date))
                self.player_games_table.setItem(row_idx, 5, QTableWidgetItem(event))
            
        except Exception:
            pass
    
    def load_player_game_in_viewer(self):
        """Carica la partita selezionata del giocatore nel visualizzatore."""
        # Ottieni la partita selezionata
        selected_rows = self.player_games_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(
                self, "Avviso",
                "Seleziona una partita da visualizzare."
            )
            return
        
        # Ottieni l'ID della partita selezionata
        row = selected_rows[0].row()
        game_id = int(self.player_games_table.item(row, 0).text())
        
        # Passa alla scheda visualizzatore
        self.tabs.setCurrentIndex(1)  # Indice della scheda visualizzatore
        
        # Trova la partita nella tabella e selezionala
        for row in range(self.analyzed_table.rowCount()):
            if int(self.analyzed_table.item(row, 0).text()) == game_id:
                self.analyzed_table.selectRow(row)
                return
        
        # Se la partita non è nella lista analizzata, chiedi se analizzarla
        reply = QMessageBox.question(
            self, "Partita Non Analizzata",
            "Questa partita non è stata ancora analizzata. Vuoi analizzarla ora?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Passa alla scheda analisi
            self.tabs.setCurrentIndex(0)  # Indice della scheda analisi
            
            # Trova la partita nella tabella e selezionala
            for row in range(self.games_table.rowCount()):
                if int(self.games_table.item(row, 0).text()) == game_id:
                    self.games_table.selectRow(row)
                    
                    # Imposta l'opzione di analisi critica per essere più veloce
                    self.critical_only_radio.setChecked(True)
                    
                    # Avvia l'analisi
                    self.start_analysis()
                    break
    
    def export_player_stats_csv(self):
        """Esporta le statistiche del giocatore in CSV."""
        player_name = self.player_combo.currentText()
        
        if not player_name:
            QMessageBox.warning(
                self, "Avviso",
                "Seleziona un giocatore."
            )
            return
        
        # Chiedi il percorso di esportazione
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salva Statistiche CSV",
            f"{player_name}_stats.csv",
            "File CSV (*.csv);;Tutti i file (*)"
        )
        
        if file_path:
            success = self.analyzer.export_player_stats_to_csv(player_name, file_path)
            
            if success:
                QMessageBox.information(
                    self, "Esportazione Completata",
                    f"Statistiche esportate con successo in:\n{file_path}"
                )
            else:
                QMessageBox.warning(
                    self, "Errore",
                    "Errore durante l'esportazione delle statistiche."
                )
    
    def closeEvent(self, event):
        """Gestisce la chiusura dell'applicazione."""
        if self.analyzer:
            self.analyzer.close()
        event.accept()


def main():
    """Funzione principale."""
    # Inizializza directory 
    initialize_directories()
    
    # Crea l'applicazione Qt
    app = QApplication(sys.argv)
    
    # Crea la finestra principale
    window = ChessEngineAnalysisGUI()
    
    # Avvia il loop dell'applicazione
    sys.exit(app.exec())


if __name__ == "__main__":
    main()