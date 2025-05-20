#!/usr/bin/env python3
"""
Chess Engine Analysis - Modulo di analisi con motori di scacchi per ChessMetrics Pro
"""

import os
import sys
import sqlite3
import chess
import chess.engine
import chess.pgn
import chess.svg
import argparse
import json
import logging
import tempfile
import webbrowser
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any, Union
# Import the data_utils 
from data_utils import get_db_path, get_log_path, initialize_directories
# Importa componenti esistenti di ChessMetrics Pro
try:
    from chess_game_viewer import ChessGameViewer
except ImportError:
    print("Avviso: Impossibile importare ChessGameViewer. Alcune funzionalità potrebbero essere limitate.")
    ChessGameViewer = None

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(get_log_path("logs/chess_engine_analysis.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Costanti
VERSION = "1.0"
DEFAULT_DB_PATH = get_db_path()  # Use our utility function
DEFAULT_PGN_FOLDER = "pgn_files"
DEFAULT_PLAYER = "Blackeyes972"
EXPORT_FOLDER = "export"  # Cartella per esportazioni

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
        self.db_path = db_path or DEFAULT_DB_PATH
        self.engine_path = engine_path or self._find_engine()
        self.depth = depth
        self.multipv = multipv
        self.time_limit = time_limit
        self.conn = None
        self.cursor = None
        self.engine = None
        
        # Crea cartella di esportazione se non esiste
        os.makedirs(EXPORT_FOLDER, exist_ok=True)
        
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
        logger.warning("Nessun motore di scacchi trovato automaticamente. Specificare il percorso manualmente.")
        return None
    
    def connect(self) -> bool:
        """Connette al database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Per accedere ai risultati per nome di colonna
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            logger.error(f"Errore di connessione al database: {e}")
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
            logger.info("Schema del database per l'analisi del motore inizializzato con successo")
        except sqlite3.Error as e:
            logger.error(f"Errore nell'inizializzazione del database: {e}")
            raise
    
    def start_engine(self) -> bool:
        """Avvia il motore di scacchi."""
        if not self.engine_path:
            logger.error("Percorso del motore di scacchi non specificato.")
            return False
            
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            
            # Configura opzioni comuni
            try:
                self.engine.configure({"Threads": 4, "Hash": 128})
            except chess.engine.EngineError:
                logger.warning("Impossibile configurare alcune opzioni del motore.")
                
            logger.info(f"Motore avviato: {self.engine.id['name']}")
            return True
        except Exception as e:
            logger.error(f"Errore nell'avvio del motore: {e}")
            return False
    
    def stop_engine(self) -> None:
        """Ferma il motore di scacchi."""
        if self.engine:
            self.engine.quit()
            self.engine = None
            logger.info("Motore fermato")
    
    def analyze_position(self, board: chess.Board, depth: int = None, 
                         multipv: int = None, time_limit: float = None) -> List[Dict]:
        """Analizza una posizione sulla scacchiera.
        
        Args:
            board: Posizione da analizzare
            depth: Profondità di analisi
            multipv: Numero di varianti da analizzare
            time_limit: Limite di tempo in secondi
            
        Returns:
            List[Dict]: Lista di risultati dell'analisi
        """
        if not self.engine:
            logger.error("Motore non avviato.")
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
            
        except Exception as e:
            logger.error(f"Errore durante l'analisi: {e}")
            return []
    
    def analyze_game(self, game_id: int, start_ply: int = 0, end_ply: int = None,
                     min_time: float = 0.5, important_only: bool = False) -> bool:
        """Analizza una partita dal database.
        
        Args:
            game_id: ID della partita nel database
            start_ply: Mossa iniziale da analizzare (0 per la prima)
            end_ply: Mossa finale da analizzare (None per tutte)
            min_time: Tempo minimo per l'analisi di una posizione
            important_only: Se True, analizza solo le posizioni importanti
            
        Returns:
            bool: True se l'analisi è stata completata con successo
        """
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
                logger.error(f"Nessuna mossa trovata per la partita con ID {game_id}")
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
                # (Implementazione semplificata per ora)
                positions_to_analyze = list(range(start_ply, end_ply + 1, 4))  # Ogni 4 mosse
            else:
                positions_to_analyze = list(range(start_ply, end_ply + 1))
            
            # Analizza ogni posizione selezionata
            for i, (ply, san, uci) in enumerate(moves_data):
                if i > 0 and i - 1 in positions_to_analyze:
                    # Calcola il tempo di analisi in base all'importanza della posizione
                    # Più avanti nella partita = più tempo
                    position_time = min_time * (1 + (i / len(moves_data)))
                    
                    # Analizza la posizione
                    logger.info(f"Analisi posizione dopo {ply//2+1}.{'' if ply%2==0 else '..'} {san}")
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
            logger.info(f"Analisi della partita {game_id} completata con successo")
            return True
            
        except Exception as e:
            logger.error(f"Errore durante l'analisi della partita: {e}")
            self.conn.rollback()
            return False
    
    def _save_analysis(self, game_id: int, ply: int, engine_name: str, 
                      analysis_date: str, depth: int, results: List[Dict]) -> None:
        """Salva i risultati dell'analisi nel database.
        
        Args:
            game_id: ID della partita
            ply: Numero della mossa
            engine_name: Nome del motore
            analysis_date: Data dell'analisi
            depth: Profondità dell'analisi
            results: Risultati dell'analisi
        """
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
    
    def get_game_analysis(self, game_id: int) -> List[Dict]:
        """Recupera l'analisi completa di una partita.
        
        Args:
            game_id: ID della partita
            
        Returns:
            List[Dict]: Lista di risultati dell'analisi per ogni posizione
        """
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
                logger.info(f"Nessuna analisi trovata per la partita con ID {game_id}")
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
            
        except Exception as e:
            logger.error(f"Errore nel recupero dell'analisi: {e}")
            return []
    
    def analyze_critical_positions(self, game_id: int, threshold: int = 100) -> List[Dict]:
        """Analizza tutte le posizioni di una partita e identifica quelle critiche.
        
        Args:
            game_id: ID della partita
            threshold: Soglia di variazione della valutazione per considerare una posizione critica
            
        Returns:
            List[Dict]: Lista di posizioni critiche con analisi
        """
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
                logger.error(f"Nessuna mossa trovata per la partita con ID {game_id}")
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
            logger.info(f"Analisi delle posizioni critiche per la partita {game_id} completata")
            return positions
            
        except Exception as e:
            logger.error(f"Errore durante l'analisi delle posizioni critiche: {e}")
            self.conn.rollback()
            return []
    
    def _get_comment_type(self, eval_diff: int, prev_eval: int, new_eval: int) -> str:
        """Determina il tipo di commento in base alla variazione della valutazione.
        
        Args:
            eval_diff: Differenza di valutazione in centipawns
            prev_eval: Valutazione precedente
            new_eval: Nuova valutazione
            
        Returns:
            str: Tipo di commento ('blunder', 'mistake', ecc.)
        """
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
        """Genera un commento basato sul tipo e sulla variazione della valutazione.
        
        Args:
            comment_type: Tipo di commento
            eval_diff: Differenza di valutazione
            prev_eval: Valutazione precedente
            new_eval: Nuova valutazione
            
        Returns:
            str: Commento testuale
        """
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
    
    def get_game_comments(self, game_id: int) -> List[Dict]:
        """Recupera i commenti di una partita.
        
        Args:
            game_id: ID della partita
            
        Returns:
            List[Dict]: Lista di commenti
        """
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
            
        except Exception as e:
            logger.error(f"Errore nel recupero dei commenti: {e}")
            return []
    
    def export_analysis_to_pgn(self, game_id: int, output_path: str) -> bool:
        """Esporta l'analisi di una partita in formato PGN.
        
        Args:
            game_id: ID della partita
            output_path: Percorso del file PGN di output
            
        Returns:
            bool: True se l'esportazione è stata completata con successo
        """
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
                logger.error(f"Partita con ID {game_id} non trovata.")
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
                        
                    except Exception as e:
                        logger.warning(f"Impossibile aggiungere commento di variante per ply {ply}: {e}")
            
            # Scrivi il PGN su file
            try:
                with open(output_path, "w") as f:
                    exporter = chess.pgn.FileExporter(f)
                    game.accept(exporter)
                logger.info(f"Analisi esportata con successo in {output_path}")
                return True
            except Exception as write_error:
                logger.error(f"Errore durante la scrittura del file PGN: {write_error}")
                return False
            
        except Exception as e:
            logger.error(f"Errore durante l'esportazione dell'analisi: {e}")
            return False
    
    def export_analysis_to_html(self, game_id: int, output_path: str = None) -> bool:
        """Esporta l'analisi di una partita in formato HTML con diagrammi interattivi.
        
        Args:
            game_id: ID della partita
            output_path: Percorso del file HTML di output (se None, lo genera automaticamente)
            
        Returns:
            bool: True se l'esportazione è stata completata con successo
        """
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
                logger.error(f"Partita con ID {game_id} non trovata.")
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
                output_path = os.path.join(EXPORT_FOLDER, filename)
            
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
            
            logger.info(f"Analisi HTML esportata con successo in {output_path}")
            
            # Opzionalmente apri il file nel browser
            try:
                webbrowser.open('file://' + os.path.abspath(output_path))
            except:
                pass
                
            return True
            
        except Exception as e:
            logger.error(f"Errore durante l'esportazione dell'analisi HTML: {e}")
            return False
    
    def get_player_stats(self, player_name: str) -> Dict:
        """Recupera le statistiche di un giocatore.
        
        Args:
            player_name: Nome del giocatore
            
        Returns:
            Dict: Statistiche del giocatore
        """
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
            
        except Exception as e:
            logger.error(f"Errore nel recupero delle statistiche del giocatore: {e}")
            return {}
    
    def close(self) -> None:
        """Chiude le connessioni e le risorse."""
        self.stop_engine()
        
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None


def parse_args() -> argparse.Namespace:
    """Analizza gli argomenti della linea di comando."""
    parser = argparse.ArgumentParser(
        description='Analisi con motori di scacchi per ChessMetrics Pro',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
  python chess_engine_analysis.py --list-games                    # Elenca le partite
  python chess_engine_analysis.py --game-id 123                   # Analizza completa
  python chess_engine_analysis.py --game-id 123 --critical-only   # Solo posizioni critiche
  python chess_engine_analysis.py --game-id 123 --export-pgn partita.pgn  # Esporta in PGN
  python chess_engine_analysis.py --game-id 123 --export-html     # Esporta in HTML
  python chess_engine_analysis.py --player-stats "Blackeyes972"   # Statistiche giocatore
        """
    )
    
    parser.add_argument('--db-path', default=DEFAULT_DB_PATH, 
                        help=f'Percorso del database SQLite (default: {DEFAULT_DB_PATH})')
    
    parser.add_argument('--engine-path', 
                        help='Percorso al motore di scacchi (se non specificato, cerca Stockfish nel PATH)')
    
    parser.add_argument('--game-id', type=int, 
                        help='ID della partita da analizzare')
    
    parser.add_argument('--depth', type=int, default=18, 
                        help='Profondità di analisi predefinita')
    
    parser.add_argument('--multipv', type=int, default=3, 
                        help='Numero di varianti da analizzare')
    
    parser.add_argument('--critical-only', action='store_true', 
                        help='Analizza solo le posizioni critiche')
    
    parser.add_argument('--export-pgn', 
                        help='Esporta l\'analisi in un file PGN')
    
    parser.add_argument('--export-html', action='store_true',
                       help='Esporta l\'analisi in formato HTML con diagrammi')
    
    parser.add_argument('--list-games', action='store_true',
                        help='Elenca le partite disponibili nel database')
    
    parser.add_argument('--show-analysis', action='store_true',
                        help='Mostra l\'analisi di una partita')
    
    parser.add_argument('--player-stats', 
                        help='Mostra statistiche per un giocatore specifico')
    
    parser.add_argument('--verbose', action='store_true',
                        help='Abilita log dettagliati')
    
    return parser.parse_args()


def list_games(analyzer: ChessEngineAnalyzer) -> None:
    """Elenca le partite disponibili nel database."""
    try:
        analyzer.cursor.execute("""
            SELECT id, white_player, black_player, result, date, event
            FROM games
            ORDER BY id DESC
            LIMIT 20
        """)
        
        games = analyzer.cursor.fetchall()
        
        print("\nPartite disponibili nel database:")
        print("=" * 80)
        print(f"{'ID':^5} | {'Bianco':<15} | {'Nero':<15} | {'Risultato':<7} | {'Data':<10} | {'Evento':<20}")
        print("-" * 80)
        
        for game in games:
            game_id, white, black, result, date, event = game
            print(f"{game_id:^5} | {white:<15} | {black:<15} | {result:<7} | {date:<10} | {event:<20}")
            
        print("=" * 80)
        print("Visualizzate le ultime 20 partite. Specificare --game-id per l'analisi.")
        
    except Exception as e:
        print(f"Errore durante l'elenco delle partite: {e}")


def show_analysis(analyzer: ChessEngineAnalyzer, game_id: int) -> None:
    """Mostra l'analisi esistente di una partita."""
    # Recupera i dettagli della partita
    analyzer.cursor.execute("""
        SELECT white_player, black_player, result, date, event
        FROM games
        WHERE id = ?
    """, (game_id,))
    
    game_details = analyzer.cursor.fetchone()
    if not game_details:
        print(f"Partita con ID {game_id} non trovata.")
        return
    
    white, black, result, date, event = game_details
    
    print("\nANALISI DELLA PARTITA")
    print("=" * 80)
    print(f"Partita: {white} vs {black}, {result}")
    print(f"Data: {date}, Evento: {event}")
    print("-" * 80)
    
    # Recupera i commenti dell'analisi
    comments = analyzer.get_game_comments(game_id)
    
    if not comments:
        print("Nessuna analisi trovata per questa partita.")
        print("Esegui prima l'analisi con --game-id e --critical-only")
        return
    
    # Mostra i commenti
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
        
        print(f"{move_num}{turn} {san} {symbol}")
        print(f"  {comment_text}")
        print()


def show_player_stats(analyzer: ChessEngineAnalyzer, player_name: str) -> None:
    """Mostra le statistiche di un giocatore."""
    stats = analyzer.get_player_stats(player_name)
    
    print(f"\nStatistiche per {player_name}")
    print("=" * 80)
    
    if stats.get("total_games", 0) == 0:
        print(f"Nessuna statistica disponibile per {player_name}.")
        print("Esegui prima l'analisi di alcune partite di questo giocatore.")
        return
    
    print(f"Partite totali: {stats['total_games']}")
    print(f"Vittorie: {stats['wins']} ({stats['win_percentage']:.1f}%)")
    print(f"Pareggi: {stats['draws']} ({(stats['draws']/stats['total_games']*100):.1f}%)")
    print(f"Sconfitte: {stats['losses']} ({(stats['losses']/stats['total_games']*100):.1f}%)")
    print(f"Media errori gravi per partita: {stats['avg_blunders']:.2f}")
    print(f"Media errori per partita: {stats['avg_mistakes']:.2f}")


def main() -> None:
    """Funzione principale."""

    # Initialize directories before anything else
    initialize_directories()
    args = parse_args()
    
    # Configura il livello di log
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Inizializza l'analizzatore
    analyzer = ChessEngineAnalyzer(
        args.db_path,
        args.engine_path,
        args.depth,
        args.multipv
    )
    
    # Connetti al database
    if not analyzer.connect():
        print("Impossibile connettersi al database.")
        sys.exit(1)
    
    try:
        # Inizializza lo schema del database
        analyzer.setup_database()
        
        # Lista delle partite disponibili
        if args.list_games:
            list_games(analyzer)
            sys.exit(0)
        
        # Mostra l'analisi esistente
        if args.show_analysis and args.game_id:
            show_analysis(analyzer, args.game_id)
            sys.exit(0)
        
        # Mostra statistiche del giocatore
        if args.player_stats:
            show_player_stats(analyzer, args.player_stats)
            sys.exit(0)
        
        # Analizza una partita specifica
        if args.game_id:
            # Avvia il motore
            if not analyzer.start_engine():
                print("Impossibile avviare il motore di scacchi.")
                sys.exit(1)
            
            print(f"Analisi della partita {args.game_id} in corso...")
            
            if args.critical_only:
                # Analizza solo le posizioni critiche
                positions = analyzer.analyze_critical_positions(args.game_id)
                
                print(f"Analizzate {len(positions)} posizioni critiche.")
                
                # Mostra l'analisi
                show_analysis(analyzer, args.game_id)
            else:
                # Analizza tutta la partita
                success = analyzer.analyze_game(args.game_id)
                
                if success:
                    print("Analisi completata con successo.")
                else:
                    print("Errore durante l'analisi.")
            
            # Esporta l'analisi in PGN se richiesto
            if args.export_pgn:
                # Gestisci il percorso di esportazione
                export_path = args.export_pgn
                # Se è solo un nome file senza percorso, salvalo nella cartella export
                if not os.path.isabs(export_path) and not os.path.dirname(export_path):
                    export_path = os.path.join(EXPORT_FOLDER, export_path)
                
                success = analyzer.export_analysis_to_pgn(args.game_id, export_path)
                if success:
                    print(f"Analisi esportata con successo in {export_path}")
                else:
                    print(f"Errore nell'esportazione dell'analisi in {export_path}")
            
            # Esporta l'analisi in HTML se richiesto
            if args.export_html:
                output_path = os.path.join(EXPORT_FOLDER, f"analysis_game_{args.game_id}.html")
                success = analyzer.export_analysis_to_html(args.game_id, output_path)
                if success:
                    print(f"Analisi HTML esportata con successo in {output_path}")
                else:
                    print(f"Errore nell'esportazione dell'analisi HTML.")
        
        else:
            # Se nessuna opzione è specificata, mostra l'aiuto
            if not (args.list_games or args.player_stats):
                print("Nessuna partita specificata per l'analisi.")
                print("Usa --list-games per vedere le partite disponibili o --help per le opzioni.")
    
    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Chiudi le risorse
        analyzer.close()


if __name__ == "__main__":
    main()