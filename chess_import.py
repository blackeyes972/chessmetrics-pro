#!/usr/bin/env python3
"""
Chess Database Manager: importa file PGN in un database SQLite e fornisce funzionalità di analisi.
Supporta l'elaborazione in batch, la gestione degli errori, e l'ottimizzazione delle prestazioni.
"""

import os
import sqlite3
import chess.pgn
import argparse
from datetime import datetime
import logging
import sys
import re
from typing import List, Dict, Tuple, Optional, Any, Union

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chess_import.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChessDBManager:
    """Gestisce le operazioni del database per l'archiviazione delle partite di scacchi."""
    
    def __init__(self, db_path: str):
        """Inizializza il gestore del database.
        
        Args:
            db_path: Percorso del file database SQLite
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.processed_files = set()
        self.games_added = 0
        self.games_skipped = 0
        self.file_errors = 0
        
    def connect(self) -> bool:
        """Stabilisce la connessione al database.
        
        Returns:
            bool: True se la connessione ha successo, False altrimenti
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            logger.error(f"Errore di connessione al database: {e}")
            return False
    
    def setup_database(self) -> None:
        """Crea le tabelle e gli indici necessari."""
        try:
            # Abilita i vincoli delle chiavi esterne
            self.cursor.execute("PRAGMA foreign_keys = ON")
            
            # Creazione schema
            self.cursor.executescript('''
            -- Tabella per i metadati di importazione
            CREATE TABLE IF NOT EXISTS import_metadata (
                id INTEGER PRIMARY KEY,
                filename TEXT UNIQUE,
                import_date TEXT,
                games_count INTEGER,
                checksum TEXT
            );
            
            -- Tabella principale delle partite
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY,
                event TEXT,
                site TEXT,
                date TEXT,
                round TEXT,
                white_player TEXT,
                black_player TEXT,
                result TEXT,
                white_elo INTEGER,
                black_elo INTEGER,
                eco TEXT,
                opening TEXT,
                time_control TEXT,
                termination TEXT,
                pgn_filename TEXT,
                import_date TEXT,
                signature TEXT
            );
            
            -- Tabella delle mosse
            CREATE TABLE IF NOT EXISTS moves (
                id INTEGER PRIMARY KEY,
                game_id INTEGER,
                ply_number INTEGER,
                san TEXT,
                uci TEXT,
                comment TEXT,
                nag TEXT,
                FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE
            );
            
            -- Indici per migliorare le prestazioni delle query
            CREATE INDEX IF NOT EXISTS idx_games_eco ON games(eco);
            CREATE INDEX IF NOT EXISTS idx_games_result ON games(result);
            CREATE INDEX IF NOT EXISTS idx_games_white_player ON games(white_player);
            CREATE INDEX IF NOT EXISTS idx_games_black_player ON games(black_player);
            CREATE INDEX IF NOT EXISTS idx_games_date ON games(date);
            CREATE INDEX IF NOT EXISTS idx_games_signature ON games(signature);
            CREATE INDEX IF NOT EXISTS idx_moves_game_id ON moves(game_id);
            ''')
            
            # Ottimizzazioni SQLite
            self.cursor.executescript('''
            PRAGMA journal_mode = WAL;
            PRAGMA synchronous = NORMAL;
            PRAGMA cache_size = -64000;  -- Circa 64MB di cache
            PRAGMA temp_store = MEMORY;
            ''')
            
            self.conn.commit()
            logger.info("Database inizializzato con successo")
        except sqlite3.Error as e:
            logger.error(f"Errore durante l'inizializzazione del database: {e}")
            raise
    
    def create_views(self) -> None:
        """Crea viste SQL per analisi comuni."""
        try:
            self.cursor.executescript('''
            -- Vista per statistiche aperture dettagliata
            CREATE VIEW IF NOT EXISTS opening_stats AS
            SELECT
                eco,
                opening,
                COUNT(*) AS total_games,
                SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) AS white_wins,
                SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) AS black_wins,
                SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) AS draws,
                ROUND(SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS white_win_percent,
                ROUND(SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS black_win_percent,
                ROUND(SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS draw_percent,
                ROUND(AVG(white_elo)) AS avg_white_elo,
                ROUND(AVG(black_elo)) AS avg_black_elo,
                MIN(date) AS first_played,
                MAX(date) AS last_played
            FROM games
            WHERE eco IS NOT NULL
            GROUP BY eco
            ORDER BY total_games DESC;
            
            -- Vista per performance giocatori
            CREATE VIEW IF NOT EXISTS player_performance AS
            SELECT
                player_name,
                COUNT(*) AS games_played,
                SUM(CASE WHEN (player_color = 'white' AND result = '1-0') OR 
                            (player_color = 'black' AND result = '0-1') 
                    THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) AS draws,
                SUM(CASE WHEN (player_color = 'white' AND result = '0-1') OR 
                            (player_color = 'black' AND result = '1-0') 
                    THEN 1 ELSE 0 END) AS losses,
                ROUND(
                    (SUM(CASE WHEN (player_color = 'white' AND result = '1-0') OR 
                                (player_color = 'black' AND result = '0-1') 
                        THEN 1 ELSE 0 END) + 
                    SUM(CASE WHEN result = '1/2-1/2' THEN 0.5 ELSE 0 END)) * 100.0 / 
                    COUNT(*), 2
                ) AS score_percent,
                ROUND(AVG(elo)) AS avg_elo
            FROM (
                SELECT white_player AS player_name, 'white' AS player_color, result, white_elo AS elo
                FROM games
                UNION ALL
                SELECT black_player AS player_name, 'black' AS player_color, result, black_elo AS elo
                FROM games
            ) AS player_games
            GROUP BY player_name
            ORDER BY games_played DESC;
            
            -- Vista per statistiche temporali
            CREATE VIEW IF NOT EXISTS time_stats AS
            SELECT
                SUBSTR(date, 1, 4) AS year,
                COUNT(*) AS games_count,
                ROUND(AVG(white_elo)) AS avg_white_elo,
                ROUND(AVG(black_elo)) AS avg_black_elo,
                SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS white_win_percent,
                SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS black_win_percent,
                SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS draw_percent
            FROM games
            WHERE date LIKE '____.__.__'
            GROUP BY year
            ORDER BY year;
            
            -- Vista per le sequenze di apertura più comuni
            CREATE VIEW IF NOT EXISTS common_opening_sequences AS
            SELECT 
                m1.san AS move1, 
                m2.san AS move2, 
                m3.san AS move3, 
                m4.san AS move4,
                COUNT(*) AS frequency
            FROM 
                moves m1
                JOIN moves m2 ON m1.game_id = m2.game_id AND m2.ply_number = 2
                JOIN moves m3 ON m1.game_id = m3.game_id AND m3.ply_number = 3
                JOIN moves m4 ON m1.game_id = m4.game_id AND m4.ply_number = 4
            WHERE 
                m1.ply_number = 1
            GROUP BY 
                m1.san, m2.san, m3.san, m4.san
            ORDER BY 
                frequency DESC
            LIMIT 100;
            ''')
            
            self.conn.commit()
            logger.info("Viste create con successo")
        except sqlite3.Error as e:
            logger.error(f"Errore durante la creazione delle viste: {e}")
            raise
    
    def is_file_processed(self, filename: str) -> bool:
        """Verifica se un file è già stato elaborato.
        
        Args:
            filename: Nome del file da verificare
            
        Returns:
            bool: True se il file è già stato elaborato, False altrimenti
        """
        self.cursor.execute("SELECT id FROM import_metadata WHERE filename = ?", (filename,))
        return self.cursor.fetchone() is not None
    
    def compute_game_signature(self, game: chess.pgn.Game) -> str:
        """Calcola una firma unica per una partita basata sui suoi attributi e sulle prime mosse.
        
        Args:
            game: Oggetto partita di python-chess
            
        Returns:
            str: Firma univoca della partita
        """
        import hashlib
        
        # Raccogliamo informazioni chiave dagli header
        headers = game.headers
        key_info = [
            headers.get('White', '?'),
            headers.get('Black', '?'),
            headers.get('Date', '????.??.??'),
            headers.get('Event', '?'),
            headers.get('Site', '?'),
            headers.get('Round', '?'),
            headers.get('Result', '*')
        ]
        
        # Aggiungiamo le prime 10 mosse (o meno se la partita è più breve)
        moves = []
        node = game
        count = 0
        while not node.is_end() and count < 10:
            next_node = node.variations[0] if node.variations else None
            if next_node:
                moves.append(next_node.move.uci())
                node = next_node
                count += 1
            else:
                break
        
        # Combiniamo tutte le informazioni in una stringa
        signature_data = "|".join(key_info + moves)
        
        # Calcoliamo l'hash SHA-256
        return hashlib.sha256(signature_data.encode()).hexdigest()
    
    def is_game_duplicate(self, signature: str) -> bool:
        """Verifica se una partita con questa firma esiste già nel database.
        
        Args:
            signature: Firma univoca della partita
            
        Returns:
            bool: True se la partita è un duplicato, False altrimenti
        """
        self.cursor.execute("SELECT id FROM games WHERE signature = ?", (signature,))
        return self.cursor.fetchone() is not None
    
    def record_processed_file(self, filename: str, games_count: int, checksum: Optional[str] = None) -> None:
        """Registra un file come elaborato.
        
        Args:
            filename: Nome del file elaborato
            games_count: Numero di partite nel file
            checksum: Checksum opzionale del file
        """
        now = datetime.now().isoformat()
        self.cursor.execute(
            "INSERT OR REPLACE INTO import_metadata (filename, import_date, games_count, checksum) VALUES (?, ?, ?, ?)",
            (filename, now, games_count, checksum)
        )
        self.conn.commit()
    
    def process_pgn_folder(self, folder_path: str, batch_size: int = 1000, skip_existing: bool = True) -> int:
        """Elabora tutti i file PGN in una cartella.
        
        Args:
            folder_path: Percorso della cartella contenente i file PGN
            batch_size: Dimensione del batch per le insert
            skip_existing: Se True, salta i file già elaborati
            
        Returns:
            int: Numero totale di partite importate
        """
        if not os.path.exists(folder_path):
            logger.error(f"La cartella {folder_path} non esiste")
            return 0
            
        total_games = 0
        pgn_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pgn')]
        
        if not pgn_files:
            logger.warning(f"Nessun file PGN trovato in {folder_path}")
            return 0
            
        logger.info(f"Trovati {len(pgn_files)} file PGN in {folder_path}")
        
        for i, fname in enumerate(pgn_files, 1):
            file_path = os.path.join(folder_path, fname)
            
            if skip_existing and self.is_file_processed(fname):
                logger.info(f"File {fname} già elaborato, saltato [{i}/{len(pgn_files)}]")
                self.games_skipped += 1
                continue
                
            try:
                logger.info(f"Elaborazione di {fname} [{i}/{len(pgn_files)}]")
                games_in_file = self.process_pgn_file(file_path, fname, batch_size)
                total_games += games_in_file
                
                # Registra il file come elaborato
                self.record_processed_file(fname, games_in_file)
                
            except Exception as e:
                logger.error(f"Errore nell'elaborazione del file {fname}: {e}")
                self.file_errors += 1
                
        logger.info(f"Importazione completata: {total_games} partite importate, {self.games_skipped} file saltati, {self.file_errors} file con errori")
        return total_games
    
    def process_pgn_file(self, file_path: str, filename: str, batch_size: int = 1000) -> int:
        """Elabora un singolo file PGN.
        
        Args:
            file_path: Percorso del file PGN
            filename: Nome del file (per registrazione)
            batch_size: Dimensione del batch per le insert
            
        Returns:
            int: Numero di partite importate dal file
        """
        games_in_file = 0
        games_batch = []
        moves_batch = []
        import_date = datetime.now().isoformat()
        duplicate_games = 0
        
        # Prova prima con UTF-8, poi con latin-1 se necessario
        encodings = ['utf-8', 'latin-1', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, encoding=encoding, errors='replace') as pgn_file:
                    current_batch_game_index = 0
                    
                    while True:
                        try:
                            game = chess.pgn.read_game(pgn_file)
                            if game is None:
                                break
                                
                            # Calcola la firma della partita per verificare duplicati
                            signature = self.compute_game_signature(game)
                            
                            # Verifica se la partita è un duplicato
                            if self.is_game_duplicate(signature):
                                duplicate_games += 1
                                logger.debug(f"Partita duplicata saltata: {game.headers.get('White')} vs {game.headers.get('Black')}, {game.headers.get('Date')}")
                                continue
                                
                            # Estrai header
                            headers = game.headers
                            
                            # Prepara i dati della partita
                            game_data = (
                                headers.get('Event', '?'),
                                headers.get('Site', '?'),
                                headers.get('Date', '????.??.??'),
                                headers.get('Round', '?'),
                                headers.get('White', '?'),
                                headers.get('Black', '?'),
                                headers.get('Result', '*'),
                                self.parse_elo(headers.get('WhiteElo', '0')),
                                self.parse_elo(headers.get('BlackElo', '0')),
                                headers.get('ECO', ''),
                                headers.get('Opening', ''),
                                headers.get('TimeControl', ''),
                                headers.get('Termination', ''),
                                filename,
                                import_date,
                                signature
                            )
                            
                            games_batch.append(game_data)
                            games_in_file += 1
                            
                            # Prepara il game_id temporaneo (sarà sostituito dopo l'inserimento)
                            # Usiamo un valore negativo per indicare che è temporaneo
                            temp_game_id = -(current_batch_game_index + 1)
                            current_batch_game_index += 1
                            
                            # Estrai mosse
                            moves_for_game = self.extract_moves(game, temp_game_id)
                            moves_batch.extend(moves_for_game)
                            
                            # Inserisci in batch quando raggiungi BATCH_SIZE
                            if len(games_batch) >= batch_size:
                                self.insert_games_batch(games_batch, moves_batch)
                                games_batch = []
                                moves_batch = []
                                current_batch_game_index = 0
                                
                        except Exception as e:
                            logger.warning(f"Errore nella lettura di una partita: {e}")
                            continue
                
                # Inserisci le partite rimanenti
                if games_batch:
                    self.insert_games_batch(games_batch, moves_batch)
                
                # Se siamo arrivati qui senza eccezioni, abbiamo trovato l'encoding giusto
                logger.info(f"File {filename} elaborato con encoding {encoding}, {games_in_file} partite importate, {duplicate_games} partite duplicate saltate")
                break
                
            except UnicodeDecodeError:
                if encoding == encodings[-1]:
                    logger.error(f"Impossibile decodificare il file {filename} con nessuno degli encoding provati")
                    raise
                logger.warning(f"Encoding {encoding} non compatibile con {filename}, provo con {encodings[encodings.index(encoding) + 1]}")
                
            except Exception as e:
                logger.error(f"Errore nell'elaborazione del file {filename}: {e}")
                raise
                
        return games_in_file
    
    def extract_moves(self, game: chess.pgn.Game, game_id: int) -> List[Tuple]:
        """Estrae le mosse da una partita.
        
        Args:
            game: Oggetto partita di python-chess
            game_id: ID della partita nel database
            
        Returns:
            List[Tuple]: Lista di tuple con i dati delle mosse
        """
        moves = []
        node = game
        ply = 0
        
        while node.variations:
            next_node = node.variations[0]
            board = node.board()
            move = next_node.move
            
            # Estrai informazioni sulla mossa
            san = board.san(move)
            uci = move.uci()
            comment = next_node.comment
            nags = ','.join(str(nag) for nag in next_node.nags) if next_node.nags else None
            
            moves.append((game_id, ply, san, uci, comment, nags))
            
            node = next_node
            ply += 1
            
        return moves
    
    def insert_games_batch(self, games_batch: List[Tuple], moves_batch: List[Tuple]) -> None:
        """Inserisce un batch di partite e relative mosse nel database.
        
        Args:
            games_batch: Lista di tuple con i dati delle partite
            moves_batch: Lista di tuple con i dati delle mosse
        """
        try:
            # Inizia una transazione
            self.conn.execute("BEGIN TRANSACTION")
            
            # Crea un dizionario per mappare gli ID temporanei con gli ID reali
            temp_to_real_id = {}
            
            # Inserisci le partite una alla volta e memorizza gli ID
            for i, game_data in enumerate(games_batch):
                self.cursor.execute('''
                    INSERT INTO games (
                        event, site, date, round,
                        white_player, black_player, result,
                        white_elo, black_elo, eco, opening,
                        time_control, termination, pgn_filename, import_date, signature
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', game_data)
                
                # Memorizza l'ID reale per questo gioco
                real_id = self.cursor.lastrowid
                temp_id = -(i + 1)  # Calcola l'ID temporaneo che avevamo assegnato
                temp_to_real_id[temp_id] = real_id
            
            # Aggiorna gli ID delle mosse con gli ID reali
            updated_moves = []
            for move in moves_batch:
                temp_game_id = move[0]
                if temp_game_id < 0:
                    # Se è un ID temporaneo, sostituiscilo con l'ID reale
                    if temp_game_id in temp_to_real_id:
                        real_game_id = temp_to_real_id[temp_game_id]
                        updated_moves.append((real_game_id,) + move[1:])
                    else:
                        # Questo non dovrebbe accadere se la logica è corretta
                        logger.warning(f"ID temporaneo {temp_game_id} non trovato nella mappa")
                else:
                    # Se è già un ID reale, usalo così com'è
                    updated_moves.append(move)
            
            # Inserisci le mosse con gli ID corretti
            if updated_moves:
                self.cursor.executemany('''
                    INSERT INTO moves (
                        game_id, ply_number, san, uci, comment, nag
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', updated_moves)
            
            # Commit della transazione
            self.conn.commit()
            self.games_added += len(games_batch)
            logger.debug(f"Batch di {len(games_batch)} partite inserito con successo")
            
        except sqlite3.Error as e:
            # Rollback in caso di errore
            self.conn.rollback()
            logger.error(f"Errore durante l'inserimento del batch: {e}")
            raise
    
    def safe_insert_game(self, game_data: Tuple, moves_data: List[Tuple]) -> bool:
        """Inserisce una singola partita e le sue mosse in modo sicuro.
        
        Args:
            game_data: Tupla con i dati della partita
            moves_data: Lista di tuple con i dati delle mosse
            
        Returns:
            bool: True se l'inserimento ha avuto successo, False altrimenti
        """
        try:
            self.conn.execute("BEGIN TRANSACTION")
            
            # Inserisci la partita
            self.cursor.execute('''
                INSERT INTO games (
                    event, site, date, round,
                    white_player, black_player, result,
                    white_elo, black_elo, eco, opening,
                    time_control, termination, pgn_filename, import_date, signature
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', game_data)
            
            game_id = self.cursor.lastrowid
            
            # Aggiorna gli ID delle mosse
            updated_moves = [(game_id,) + move[1:] for move in moves_data]
            
            # Inserisci le mosse
            if updated_moves:
                self.cursor.executemany('''
                    INSERT INTO moves (
                        game_id, ply_number, san, uci, comment, nag
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', updated_moves)
            
            self.conn.commit()
            self.games_added += 1
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Errore nell'inserimento della partita: {e}")
            return False
    
    @staticmethod
    def parse_elo(elo_str: str) -> int:
        """Converte una stringa di ELO in un intero.
        
        Args:
            elo_str: Stringa contenente l'ELO
            
        Returns:
            int: Valore ELO come intero
        """
        try:
            # Estrai solo i numeri dalla stringa
            digits = re.sub(r'[^\d]', '', elo_str)
            return int(digits) if digits else 0
        except (ValueError, TypeError):
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Raccoglie statistiche dal database.
        
        Returns:
            Dict[str, Any]: Dizionario con varie statistiche
        """
        stats = {}
        
        try:
            # Numero totale di partite
            self.cursor.execute("SELECT COUNT(*) FROM games")
            stats['total_games'] = self.cursor.fetchone()[0]
            
            # Distribuzione dei risultati
            self.cursor.execute('''
                SELECT result, COUNT(*) as count
                FROM games
                GROUP BY result
                ORDER BY count DESC
            ''')
            stats['results'] = {row[0]: row[1] for row in self.cursor.fetchall()}
            
            # Aperture più comuni
            self.cursor.execute('''
                SELECT eco, opening, COUNT(*) as count
                FROM games
                WHERE eco != ''
                GROUP BY eco
                ORDER BY count DESC
                LIMIT 10
            ''')
            stats['top_openings'] = [
                {'eco': row[0], 'name': row[1] or 'Sconosciuta', 'count': row[2]}
                for row in self.cursor.fetchall()
            ]
            
            # Giocatori più attivi
            self.cursor.execute('''
                SELECT player, COUNT(*) as count
                FROM (
                    SELECT white_player as player FROM games
                    UNION ALL
                    SELECT black_player as player FROM games
                )
                GROUP BY player
                ORDER BY count DESC
                LIMIT 10
            ''')
            stats['top_players'] = [
                {'name': row[0], 'games': row[1]}
                for row in self.cursor.fetchall()
            ]
            
            return stats
            
        except sqlite3.Error as e:
            logger.error(f"Errore durante il recupero delle statistiche: {e}")
            return {'error': str(e)}
    
    def close(self) -> None:
        """Chiude la connessione al database."""
        if self.conn:
            self.conn.close()
            logger.debug("Connessione al database chiusa")


def parse_args() -> argparse.Namespace:
    """Analizza gli argomenti della linea di comando.
    
    Returns:
        argparse.Namespace: Argomenti analizzati
    """
    parser = argparse.ArgumentParser(description='Importa file PGN in un database SQLite')
    parser.add_argument('--pgn-folder', default='pgn_files', help='Cartella contenente i file PGN')
    parser.add_argument('--db-path', default='chess_games.db', help='Percorso del database SQLite')
    parser.add_argument('--batch-size', type=int, default=100, help='Dimensione batch per insert')
    parser.add_argument('--force-reimport', action='store_true', help='Rielabora anche file già importati')
    parser.add_argument('--stats', action='store_true', help='Mostra statistiche dopo l\'importazione')
    parser.add_argument('--verbose', action='store_true', help='Mostra log dettagliati')
    return parser.parse_args()


def main() -> None:
    """Funzione principale."""
    args = parse_args()
    
    # Imposta il livello di log in base all'argomento verbose
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    start_time = datetime.now()
    logger.info(f"Inizio importazione da {args.pgn_folder}")
    
    db_manager = ChessDBManager(args.db_path)
    if not db_manager.connect():
        sys.exit(1)
    
    try:
        # Verifica che la cartella esista
        if not os.path.exists(args.pgn_folder):
            os.makedirs(args.pgn_folder)
            logger.info(f"Creata cartella {args.pgn_folder}")
        
        db_manager.setup_database()
        games_count = db_manager.process_pgn_folder(
            args.pgn_folder, 
            args.batch_size,
            not args.force_reimport
        )
        db_manager.create_views()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info(f"Importazione completata: {games_count} partite in {duration}")
        print(f"Importazione completata: {games_count} partite in {duration}")
        
        if args.stats and games_count > 0:
            stats = db_manager.get_statistics()
            print("\nStatistiche del database:")
            print(f"Totale partite: {stats['total_games']}")
            print("\nDistribuzione risultati:")
            for result, count in stats.get('results', {}).items():
                print(f"  {result}: {count}")
            
            print("\nAperture più comuni:")
            for i, opening in enumerate(stats.get('top_openings', []), 1):
                print(f"  {i}. {opening['eco']} - {opening['name']}: {opening['count']} partite")
            
            print("\nGiocatori più attivi:")
            for i, player in enumerate(stats.get('top_players', []), 1):
                print(f"  {i}. {player['name']}: {player['games']} partite")
    
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione: {e}")
        sys.exit(1)
    
    finally:
        db_manager.close()


if __name__ == "__main__":
    main()