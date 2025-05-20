#!/usr/bin/env python3
"""
ChessMetrics Pro - Interfaccia Grafica PyQt6
Fornisce un'interfaccia grafica per l'applicazione ChessMetrics Pro.
"""

import os
import sys
import time
from datetime import datetime
from threading import Thread
from typing import Optional, Dict, Any, List, Tuple
# Import the data_utils 
from data_utils import get_db_path, get_log_path, initialize_directories

from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QFileDialog, QCheckBox, 
                           QComboBox, QLineEdit, QProgressBar, QMessageBox, QSplitter,
                           QTableWidget, QTableWidgetItem, QListWidget, QTextBrowser,
                           QGroupBox, QFormLayout, QSpinBox, QRadioButton, QButtonGroup,
                           QScrollArea, QInputDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QSize
from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor
from PyQt6.QtSvgWidgets import QSvgWidget  # Corretto da QtSvg a QtSvgWidgets

# Importiamo matplotlib con backend Qt per i grafici integrati
import matplotlib
matplotlib.use('QtAgg')  # Usa QtAgg invece di Qt5Agg
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

# Per l'analisi dei dati
import pandas as pd
import numpy as np

# Importiamo i moduli dell'applicazione
try:
    from chess_import import ChessDBManager
    from chess_analyzer import ChessAnalyzer
    from chess_game_viewer import ChessGameViewer
except ImportError:
    print("Errore: moduli dell'applicazione non trovati. Assicurati di essere nella directory corretta.")
    sys.exit(1)

# Per la visualizzazione della scacchiera in PyQt
import chess
import chess.svg
from PyQt6.QtCore import QByteArray

# Costanti
VERSION = "1.0"
DEFAULT_DB_PATH = get_db_path()  # Use our utility function
DEFAULT_PGN_FOLDER = "pgn_files"
DEFAULT_PLAYER = "Blackeyes972"


# Thread di importazione PGN
class ImportThread(QThread):
    """Thread per l'importazione PGN in background."""
    
    progress_update = pyqtSignal(int, str)
    import_finished = pyqtSignal(bool, str, dict)
    
    def __init__(self, db_path: str, pgn_folder: str, batch_size: int, skip_existing: bool):
        """Inizializza il thread di importazione."""
        super().__init__()
        self.db_path = db_path
        self.pgn_folder = pgn_folder
        self.batch_size = batch_size
        self.skip_existing = skip_existing
    
    def run(self) -> None:
        """Esegue l'importazione in background."""
        try:
            db_manager = ChessDBManager(self.db_path)
            if not db_manager.connect():
                self.import_finished.emit(False, "Impossibile connettersi al database.", {})
                return
                
            # Verifica che la cartella esista
            if not os.path.exists(self.pgn_folder):
                os.makedirs(self.pgn_folder)
                self.progress_update.emit(0, f"Creata cartella {self.pgn_folder}")
                
            db_manager.setup_database()
            
            # Recupera la lista dei file PGN
            pgn_files = [f for f in os.listdir(self.pgn_folder) if f.lower().endswith('.pgn')]
            if not pgn_files:
                self.import_finished.emit(False, f"Nessun file PGN trovato in {self.pgn_folder}", {})
                return
                
            self.progress_update.emit(0, f"Trovati {len(pgn_files)} file PGN in {self.pgn_folder}")
            
            # Processamento file per file con aggiornamenti di progresso
            total_games = 0
            for i, fname in enumerate(pgn_files, 1):
                file_path = os.path.join(self.pgn_folder, fname)
                
                progress = int((i / len(pgn_files)) * 100)
                self.progress_update.emit(progress, f"Elaborazione di {fname} [{i}/{len(pgn_files)}]")
                
                if self.skip_existing and db_manager.is_file_processed(fname):
                    self.progress_update.emit(progress, f"File {fname} già elaborato, saltato [{i}/{len(pgn_files)}]")
                    continue
                    
                try:
                    games_in_file = db_manager.process_pgn_file(file_path, fname, self.batch_size)
                    total_games += games_in_file
                    
                    # Registra il file come elaborato
                    db_manager.record_processed_file(fname, games_in_file)
                    
                    self.progress_update.emit(progress, f"Elaborato {fname}: {games_in_file} partite [{i}/{len(pgn_files)}]")
                    
                except Exception as e:
                    self.progress_update.emit(progress, f"Errore nell'elaborazione del file {fname}: {e}")
            
            # Creazione viste
            self.progress_update.emit(100, "Creazione viste SQL...")
            db_manager.create_views()
            
            # Statistiche finali
            stats = db_manager.get_statistics()
            
            db_manager.close()
            
            # Segnala il completamento
            self.import_finished.emit(True, f"Importazione completata: {total_games} partite importate.", stats)
            
        except Exception as e:
            self.import_finished.emit(False, f"Errore durante l'importazione: {e}", {})


# Thread di analisi
class AnalysisThread(QThread):
    """Thread per l'analisi in background."""
    
    analysis_update = pyqtSignal(str)
    analysis_data = pyqtSignal(dict)  # Nuovo segnale per i dati da visualizzare
    analysis_finished = pyqtSignal(bool, str)
    
    def __init__(self, db_path: str, player: str, analysis_type: str, 
                 export_csv: bool = False, export_text: bool = False):
        """Inizializza il thread di analisi."""
        super().__init__()
        self.db_path = db_path
        self.player = player
        self.analysis_type = analysis_type
        self.export_csv = export_csv
        self.export_text = export_text
        self.csv_path = "chess_analysis.csv"
        self.text_path = "chess_analysis.txt"
    
    def run(self) -> None:
        """Esegue l'analisi in background."""
        try:
            self.analysis_update.emit(f"Avvio analisi per il giocatore: {self.player}...")
            
            analyzer = ChessAnalyzer(self.db_path, self.player)
            if not analyzer.connect():
                self.analysis_finished.emit(False, "Impossibile connettersi al database.")
                return
                
            if self.export_csv:
                self.analysis_update.emit(f"Esportazione analisi in {self.csv_path}...")
                analyzer.export_all_to_csv(self.csv_path)
                self.analysis_update.emit(f"Analisi esportata con successo in {self.csv_path}")
            
            elif self.export_text:
                self.analysis_update.emit(f"Esportazione analisi in {self.text_path}...")
                analyzer.export_analysis_to_text(self.text_path)
                self.analysis_update.emit(f"Analisi esportata con successo in {self.text_path}")
            
            else:
                # Qui raccogliamo i dati senza creare grafici, che verranno generati nel thread principale
                
                # Analisi delle statistiche di base
                if self.analysis_type == 'basic' or self.analysis_type == 'all':
                    self.analysis_update.emit("Analisi delle statistiche di base...")
                    stats = analyzer.get_basic_stats()
                    self.analysis_update.emit(f"Totale partite: {stats['total_games']}")
                    self.analysis_update.emit(f"Vittorie: {stats['wins']} ({stats['win_percentage']}%)")
                    self.analysis_update.emit(f"Sconfitte: {stats['losses']} ({stats['loss_percentage']}%)")
                    self.analysis_update.emit(f"Pareggi: {stats['draws']} ({stats['draw_percentage']}%)")
                    
                    # Invia i dati per il grafico
                    self.analysis_data.emit({
                        'type': 'basic_stats',
                        'wins': stats['wins'],
                        'losses': stats['losses'],
                        'draws': stats['draws'],
                        'white_games': stats['white_games'],
                        'black_games': stats['black_games'],
                        'total_games': stats['total_games']
                    })
                
                # Analisi delle aperture
                if self.analysis_type == 'openings' or self.analysis_type == 'all':
                    self.analysis_update.emit("Analisi delle aperture...")
                    
                    # Query per le aperture più giocate
                    query_most_played = """
                        SELECT eco, opening, COUNT(*) as games, 
                            SUM(CASE WHEN 
                                (white_player = ? AND result = '1-0') OR
                                (black_player = ? AND result = '0-1')
                                THEN 1 ELSE 0 END) as wins,
                            SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as draws,
                            SUM(CASE WHEN 
                                (white_player = ? AND result = '0-1') OR
                                (black_player = ? AND result = '1-0')
                                THEN 1 ELSE 0 END) as losses,
                            ROUND(SUM(CASE WHEN 
                                (white_player = ? AND result = '1-0') OR
                                (black_player = ? AND result = '0-1')
                                THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_percentage
                        FROM games
                        WHERE (white_player = ? OR black_player = ?) AND eco IS NOT NULL AND eco != ''
                        GROUP BY eco, opening
                        HAVING COUNT(*) >= 2
                        ORDER BY games DESC
                        LIMIT 10
                    """
                    
                    df_most_played = pd.read_sql_query(
                        query_most_played, 
                        analyzer.conn, 
                        params=[self.player] * 8
                    )
                    
                    if not df_most_played.empty:
                        # Invia i dati per il grafico
                        self.analysis_data.emit({
                            'type': 'opening_stats',
                            'eco': df_most_played['eco'].tolist(),
                            'opening': df_most_played['opening'].tolist(),
                            'games': df_most_played['games'].tolist(),
                            'wins': df_most_played['wins'].tolist(),
                            'draws': df_most_played['draws'].tolist(),
                            'losses': df_most_played['losses'].tolist(),
                            'win_percentage': df_most_played['win_percentage'].tolist()
                        })
                    else:
                        self.analysis_update.emit("Nessun dato disponibile per le aperture.")
                
                # Analisi degli avversari
                if self.analysis_type == 'opponents' or self.analysis_type == 'all':
                    self.analysis_update.emit("Analisi degli avversari...")
                    
                    query = """
                        SELECT opponent, COUNT(*) as games_played,
                            SUM(CASE WHEN 
                                (white_player = ? AND result = '1-0') OR
                                (black_player = ? AND result = '0-1')
                                THEN 1 ELSE 0 END) as wins,
                            SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as draws,
                            SUM(CASE WHEN 
                                (white_player = ? AND result = '0-1') OR
                                (black_player = ? AND result = '1-0')
                                THEN 1 ELSE 0 END) as losses,
                            ROUND(SUM(CASE WHEN 
                                (white_player = ? AND result = '1-0') OR
                                (black_player = ? AND result = '0-1')
                                THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_percent,
                            ROUND(AVG(CASE WHEN white_player = ? THEN black_elo ELSE white_elo END)) as avg_opponent_elo
                        FROM (
                            SELECT white_player, black_player, result, white_elo, black_elo,
                                CASE WHEN white_player = ? THEN black_player ELSE white_player END as opponent
                            FROM games
                            WHERE white_player = ? OR black_player = ?
                        ) as opponents
                        GROUP BY opponent
                        HAVING COUNT(*) >= 2
                        ORDER BY games_played DESC
                        LIMIT 15
                    """
                    
                    df = pd.read_sql_query(
                        query, 
                        analyzer.conn, 
                        params=[self.player] * 10
                    )
                    
                    if not df.empty:
                        # Ordina per percentuale di vittoria
                        df = df.sort_values(by='win_percent')
                        
                        # Invia i dati per il grafico
                        self.analysis_data.emit({
                            'type': 'opponents_stats',
                            'opponents': df['opponent'].tolist(),
                            'games': df['games_played'].tolist(),
                            'win_percent': df['win_percent'].tolist()
                        })
                    else:
                        self.analysis_update.emit("Nessun dato disponibile per gli avversari.")
                
                # Analisi delle fasi di gioco
                if self.analysis_type == 'phases' or self.analysis_type == 'all':
                    self.analysis_update.emit("Analisi delle fasi di gioco...")
                    
                    query = """
                        SELECT 
                            CASE 
                                WHEN moves_count <= 10 THEN 'Apertura (≤10)'
                                WHEN moves_count <= 25 THEN 'Mediogioco (11-25)'
                                WHEN moves_count <= 40 THEN 'Tardo mediogioco (26-40)'
                                ELSE 'Finale (>40)'
                            END as fase_partita,
                            COUNT(*) as num_partite,
                            SUM(CASE WHEN 
                                (white_player = ? AND result = '1-0') OR
                                (black_player = ? AND result = '0-1')
                                THEN 1 ELSE 0 END) as vittorie,
                            SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as pareggi,
                            SUM(CASE WHEN 
                                (white_player = ? AND result = '0-1') OR
                                (black_player = ? AND result = '1-0')
                                THEN 1 ELSE 0 END) as sconfitte,
                            ROUND(SUM(CASE WHEN 
                                (white_player = ? AND result = '1-0') OR
                                (black_player = ? AND result = '0-1')
                                THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as perc_vittorie
                        FROM (
                            SELECT g.id, g.white_player, g.black_player, g.result, 
                                CAST(MAX(m.ply_number)/2 + 0.5 AS INTEGER) as moves_count
                            FROM games g
                            JOIN moves m ON g.id = m.game_id
                            WHERE g.white_player = ? OR g.black_player = ?
                            GROUP BY g.id
                        ) as game_lengths
                        GROUP BY fase_partita
                        ORDER BY MIN(moves_count)
                    """
                    
                    df = pd.read_sql_query(
                        query, 
                        analyzer.conn, 
                        params=[self.player] * 8
                    )
                    
                    if not df.empty:
                        # Ordine corretto delle fasi
                        correct_order = ['Apertura (≤10)', 'Mediogioco (11-25)', 'Tardo mediogioco (26-40)', 'Finale (>40)']
                        
                        # Assicurati che tutte le fasi siano presenti
                        fase_dict = {fase: {'num_partite': 0, 'vittorie': 0, 'pareggi': 0, 'sconfitte': 0, 'perc_vittorie': 0} 
                                    for fase in correct_order}
                        
                        for _, row in df.iterrows():
                            fase = row['fase_partita']
                            if fase in fase_dict:
                                fase_dict[fase] = {
                                    'num_partite': row['num_partite'],
                                    'vittorie': row['vittorie'],
                                    'pareggi': row['pareggi'],
                                    'sconfitte': row['sconfitte'],
                                    'perc_vittorie': row['perc_vittorie']
                                }
                        
                        # Invia i dati per il grafico
                        self.analysis_data.emit({
                            'type': 'phases_stats',
                            'fasi': list(fase_dict.keys()),
                            'partite': [fase_dict[fase]['num_partite'] for fase in fase_dict],
                            'vittorie': [fase_dict[fase]['vittorie'] for fase in fase_dict],
                            'pareggi': [fase_dict[fase]['pareggi'] for fase in fase_dict],
                            'sconfitte': [fase_dict[fase]['sconfitte'] for fase in fase_dict],
                            'perc_vittorie': [fase_dict[fase]['perc_vittorie'] for fase in fase_dict]
                        })
                    else:
                        self.analysis_update.emit("Nessun dato disponibile per le fasi di gioco.")
                
                # Analisi dell'evoluzione Elo
                if self.analysis_type == 'elo' or self.analysis_type == 'all':
                    self.analysis_update.emit("Analisi dell'evoluzione Elo...")
                    
                    query = """
                        SELECT date, 
                            CASE WHEN white_player = ? THEN white_elo ELSE black_elo END as elo,
                            CASE 
                                WHEN (white_player = ? AND result = '1-0') OR (black_player = ? AND result = '0-1') THEN 'win'
                                WHEN (white_player = ? AND result = '0-1') OR (black_player = ? AND result = '1-0') THEN 'loss'
                                ELSE 'draw'
                            END as result
                        FROM games
                        WHERE (white_player = ? OR black_player = ?) 
                        AND (white_elo > 0 AND black_elo > 0)
                        ORDER BY date
                    """
                    
                    df = pd.read_sql_query(
                        query, 
                        analyzer.conn, 
                        params=[self.player] * 7
                    )
                    
                    if not df.empty:
                        # Converti le date
                        df['date'] = pd.to_datetime(df['date'], errors='coerce')
                        df = df.dropna(subset=['date'])
                        
                        # Invia i dati per il grafico
                        self.analysis_data.emit({
                            'type': 'elo_progression',
                            'dates': df['date'].dt.strftime('%Y-%m-%d').tolist(),
                            'elo': df['elo'].tolist(),
                            'results': df['result'].tolist()
                        })
                        
                        # Calcola statistiche mensili per secondo grafico
                        df['month_year'] = df['date'].dt.strftime('%Y-%m')
                        monthly_stats = df.groupby('month_year').agg({
                            'elo': ['mean', 'min', 'max', 'count'],
                            'result': lambda x: (x == 'win').sum() / len(x) * 100
                        })
                        
                        monthly_stats.columns = ['avg_elo', 'min_elo', 'max_elo', 'games', 'win_percentage']
                        monthly_stats = monthly_stats.reset_index()
                        monthly_stats['date'] = pd.to_datetime(monthly_stats['month_year'], format='%Y-%m')
                        
                        # Invia anche i dati mensili
                        self.analysis_data.emit({
                            'type': 'elo_monthly',
                            'dates': monthly_stats['date'].dt.strftime('%Y-%m').tolist(),
                            'avg_elo': monthly_stats['avg_elo'].tolist(),
                            'games': monthly_stats['games'].tolist(),
                            'win_percentage': monthly_stats['win_percentage'].tolist()
                        })
                    else:
                        self.analysis_update.emit("Nessun dato Elo disponibile.")
                
                # Analisi degli errori
                if self.analysis_type == 'mistakes' or self.analysis_type == 'all':
                    self.analysis_update.emit("Analisi degli errori comuni...")
                    
                    # Questa è un'analisi delle partite perse rapidamente
                    query = """
                        SELECT g.white_player, g.black_player, g.result, g.eco, g.opening,
                            MAX(m.ply_number)/2 + 0.5 as moves_count
                        FROM games g
                        JOIN moves m ON g.id = m.game_id
                        WHERE (g.white_player = ? OR g.black_player = ?) AND 
                            ((g.white_player = ? AND g.result = '0-1') OR 
                            (g.black_player = ? AND g.result = '1-0'))
                        GROUP BY g.id
                        HAVING moves_count <= 25
                        ORDER BY moves_count ASC
                    """
                    
                    df = pd.read_sql_query(
                        query, 
                        analyzer.conn, 
                        params=[self.player] * 4
                    )
                    
                    if not df.empty:
                        # Analisi per ECO delle sconfitte rapide
                        eco_counts = df['eco'].value_counts().reset_index()
                        eco_counts.columns = ['eco', 'frequency']
                        
                        # Aggiungi nomi delle aperture
                        eco_names = {}
                        for eco, opening in zip(df['eco'], df['opening']):
                            if eco not in eco_names and pd.notna(eco):
                                eco_names[eco] = opening
                        
                        eco_counts['opening'] = eco_counts['eco'].map(lambda x: eco_names.get(x, 'Sconosciuta'))
                        
                        # Distribuzione delle mosse nelle sconfitte
                        move_counts = df['moves_count'].value_counts().sort_index()
                        
                        # Invia i dati per i grafici
                        self.analysis_data.emit({
                            'type': 'quick_losses',
                            'moves': move_counts.index.tolist(),
                            'frequency': move_counts.values.tolist(),
                            'eco': eco_counts['eco'].tolist()[:10],
                            'eco_frequency': eco_counts['frequency'].tolist()[:10],
                            'eco_opening': eco_counts['opening'].tolist()[:10]
                        })
                    else:
                        self.analysis_update.emit("Nessun dato disponibile per le sconfitte rapide.")
                
                # Analisi per categoria ECO
                if self.analysis_type == 'eco' or self.analysis_type == 'all':
                    self.analysis_update.emit("Analisi per categoria ECO...")
                    
                    query = """
                        SELECT SUBSTR(eco, 1, 1) as eco_category,
                            COUNT(*) as games,
                            SUM(CASE WHEN 
                                (white_player = ? AND result = '1-0') OR
                                (black_player = ? AND result = '0-1')
                                THEN 1 ELSE 0 END) as wins,
                            SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as draws,
                            SUM(CASE WHEN 
                                (white_player = ? AND result = '0-1') OR
                                (black_player = ? AND result = '1-0')
                                THEN 1 ELSE 0 END) as losses,
                            ROUND(SUM(CASE WHEN 
                                (white_player = ? AND result = '1-0') OR
                                (black_player = ? AND result = '0-1')
                                THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_percentage
                        FROM games
                        WHERE (white_player = ? OR black_player = ?) AND eco IS NOT NULL AND eco != ''
                        GROUP BY eco_category
                        ORDER BY eco_category
                    """
                    
                    df = pd.read_sql_query(
                        query, 
                        analyzer.conn, 
                        params=[self.player] * 8
                    )
                    
                    if not df.empty:
                        # Aggiungi descrizioni
                        eco_descriptions = {
                            'A': 'Aperture di Fianchetto (1.c4, 1.Nf3, etc.)',
                            'B': 'Aperture Semiaperte (1.e4 eccetto 1...e5)',
                            'C': 'Aperture Aperte (1.e4 e5)',
                            'D': 'Aperture Chiuse (1.d4 d5)',
                            'E': 'Difese Indiane (1.d4 Nf6 eccetto 2.c4 e5)'
                        }
                        
                        df['descrizione'] = df['eco_category'].map(lambda x: eco_descriptions.get(x, 'Sconosciuta'))
                        
                        # Invia i dati per il grafico
                        self.analysis_data.emit({
                            'type': 'eco_category',
                            'categories': df['eco_category'].tolist(),
                            'descriptions': df['descrizione'].tolist(),
                            'games': df['games'].tolist(),
                            'wins': df['wins'].tolist(),
                            'draws': df['draws'].tolist(),
                            'losses': df['losses'].tolist(),
                            'win_percentage': df['win_percentage'].tolist()
                        })
                    else:
                        self.analysis_update.emit("Nessun dato ECO disponibile.")
            
            analyzer.close()
            
            self.analysis_finished.emit(True, "Analisi completata con successo.")
            
        except Exception as e:
            self.analysis_finished.emit(False, f"Errore durante l'analisi: {e}")


# Widget per la scacchiera SVG
class ChessBoardWidget(QSvgWidget):
    """Widget per visualizzare una scacchiera SVG."""
    
    def __init__(self, parent=None):
        """Inizializza il widget della scacchiera."""
        super().__init__(parent)
        self.board = chess.Board()
        self.setMinimumSize(400, 400)
        self.update_board()
    
    def update_board(self):
        """Aggiorna la visualizzazione della scacchiera."""
        svg_data = chess.svg.board(self.board, size=400).encode('utf-8')
        self.load(QByteArray(svg_data))
    
    def set_board(self, board):
        """Imposta una nuova posizione sulla scacchiera."""
        self.board = board
        self.update_board()


# Classe principale dell'applicazione
class ChessMetricsPro(QMainWindow):
    """Finestra principale dell'applicazione ChessMetrics Pro."""
    
    def __init__(self):
        """Inizializza l'applicazione."""
        super().__init__()
        
        self.db_path = DEFAULT_DB_PATH
        self.pgn_folder = DEFAULT_PGN_FOLDER
        
        self.init_ui()
    
    def init_ui(self):
        """Inizializza l'interfaccia utente."""
        self.setWindowTitle(f"ChessMetrics Pro {VERSION}")
        self.setMinimumSize(900, 700)
        
        # Widget centrale con schede
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Schede principali
        self.init_import_tab()
        self.init_analysis_tab()
        self.init_viewer_tab()
        self.init_settings_tab()
        
        # Barra di stato
        self.statusBar().showMessage("Pronto")
        
        # Mostra la finestra
        self.show()
    
    def init_import_tab(self):
        """Inizializza la scheda di importazione PGN."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Sezione superiore: selezione cartella e opzioni
        form_layout = QFormLayout()
        
        # Selezione cartella PGN
        pgn_layout = QHBoxLayout()
        self.pgn_folder_edit = QLineEdit(self.pgn_folder)
        pgn_browse_btn = QPushButton("Sfoglia...")
        pgn_browse_btn.clicked.connect(self.browse_pgn_folder)
        pgn_layout.addWidget(self.pgn_folder_edit)
        pgn_layout.addWidget(pgn_browse_btn)
        form_layout.addRow("Cartella PGN:", pgn_layout)
        
        # Dimensione batch
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(10, 1000)
        self.batch_size_spin.setValue(100)
        self.batch_size_spin.setSingleStep(10)
        form_layout.addRow("Dimensione batch:", self.batch_size_spin)
        
        # Opzione per reimportazione
        self.reimport_check = QCheckBox("Reimporta file già elaborati")
        form_layout.addRow("", self.reimport_check)
        
        # Pulsante di importazione
        import_btn = QPushButton("Importa File PGN")
        import_btn.setMinimumHeight(40)
        import_btn.clicked.connect(self.start_import)
        
        # Barra di progresso
        self.import_progress = QProgressBar()
        self.import_progress.setRange(0, 100)
        self.import_progress.setValue(0)
        
        # Area di log
        log_group = QGroupBox("Log di importazione")
        log_layout = QVBoxLayout()
        self.import_log = QTextBrowser()
        log_layout.addWidget(self.import_log)
        log_group.setLayout(log_layout)
        
        # Assembla il layout
        layout.addLayout(form_layout)
        layout.addWidget(import_btn)
        layout.addWidget(self.import_progress)
        layout.addWidget(log_group)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Importa PGN")
    
    def init_analysis_tab(self):
        """Inizializza la scheda di analisi."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Sezione superiore: opzioni di analisi
        form_layout = QFormLayout()
        
        # Selezione giocatore
        self.player_edit = QLineEdit(DEFAULT_PLAYER)
        form_layout.addRow("Giocatore:", self.player_edit)
        
        # Tipo di analisi
        self.analysis_combo = QComboBox()
        analysis_types = [
            "Tutte le analisi", 
            "Statistiche di base", 
            "Analisi delle aperture",
            "Analisi degli avversari", 
            "Analisi delle fasi di gioco", 
            "Evoluzione dell'Elo",
            "Analisi degli errori", 
            "Analisi per categoria ECO"
        ]
        self.analysis_combo.addItems(analysis_types)
        form_layout.addRow("Tipo di analisi:", self.analysis_combo)
        
        # Opzioni di esportazione
        export_layout = QHBoxLayout()
        self.export_group = QButtonGroup(self)
        
        self.no_export_radio = QRadioButton("Solo visualizzazione")
        self.csv_export_radio = QRadioButton("Esporta in CSV")
        self.text_export_radio = QRadioButton("Esporta in testo")
        
        self.export_group.addButton(self.no_export_radio)
        self.export_group.addButton(self.csv_export_radio)
        self.export_group.addButton(self.text_export_radio)
        
        self.no_export_radio.setChecked(True)
        
        export_layout.addWidget(self.no_export_radio)
        export_layout.addWidget(self.csv_export_radio)
        export_layout.addWidget(self.text_export_radio)
        
        form_layout.addRow("Esportazione:", export_layout)
        
        # Pulsante di analisi
        analyze_btn = QPushButton("Analizza")
        analyze_btn.setMinimumHeight(40)
        analyze_btn.clicked.connect(self.start_analysis)
        
        # Aggiungi un QSplitter per dividere l'area risultati e grafici
        results_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Area risultati testuali
        results_group = QGroupBox("Log dell'analisi")
        results_layout = QVBoxLayout()
        self.analysis_results = QTextBrowser()
        self.analysis_results.setMaximumHeight(200)  # Limita l'altezza per dare più spazio ai grafici
        results_layout.addWidget(self.analysis_results)
        results_group.setLayout(results_layout)
        
        # Area grafici - questo contenitore ospiterà i grafici generati
        graphs_group = QGroupBox("Visualizzazioni")
        
        # Aggiungi un widget scroll per permettere grafici più grandi della finestra
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.graphs_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        
        graphs_group.setLayout(QVBoxLayout())
        graphs_group.layout().addWidget(scroll_area)
        
        # Aggiungi i gruppi al splitter
        results_splitter.addWidget(results_group)
        results_splitter.addWidget(graphs_group)
        results_splitter.setSizes([100, 400])  # Dai più spazio ai grafici
        
        # Assembla il layout
        layout.addLayout(form_layout)
        layout.addWidget(analyze_btn)
        layout.addWidget(results_splitter, 1)  # Fai espandere il splitter
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Analizza")
    
    def init_viewer_tab(self):
        """Inizializza la scheda del visualizzatore di partite."""
        tab = QWidget()
        main_layout = QVBoxLayout()
        
        # Splitter orizzontale per la lista partite e la scacchiera
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Pannello sinistro: ricerca e lista partite
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Controlli di ricerca
        search_group = QGroupBox("Ricerca Partite")
        search_layout = QFormLayout()
        
        self.search_player_edit = QLineEdit()
        search_layout.addRow("Giocatore:", self.search_player_edit)
        
        self.search_date_edit = QLineEdit()
        self.search_date_edit.setPlaceholderText("YYYY.MM.DD")
        search_layout.addRow("Data:", self.search_date_edit)
        
        self.search_event_edit = QLineEdit()
        search_layout.addRow("Evento:", self.search_event_edit)
        
        self.search_eco_edit = QLineEdit()
        search_layout.addRow("Codice ECO:", self.search_eco_edit)
        
        search_btn = QPushButton("Cerca")
        search_btn.clicked.connect(self.search_games)
        search_layout.addRow("", search_btn)
        
        search_group.setLayout(search_layout)
        
        # Lista partite
        games_group = QGroupBox("Partite")
        games_layout = QVBoxLayout()
        
        self.games_list = QTableWidget()
        self.games_list.setColumnCount(5)
        self.games_list.setHorizontalHeaderLabels(["ID", "Bianco", "Nero", "Risultato", "Data"])
        self.games_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.games_list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.games_list.itemDoubleClicked.connect(self.load_selected_game)
        
        games_layout.addWidget(self.games_list)
        games_group.setLayout(games_layout)
        
        left_layout.addWidget(search_group)
        left_layout.addWidget(games_group)
        left_panel.setLayout(left_layout)
        
        # Pannello destro: scacchiera e controlli
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Informazioni partita
        self.game_info = QTextBrowser()
        self.game_info.setMaximumHeight(100)
        
        # Scacchiera
        self.board_widget = ChessBoardWidget()
        
        # Controlli di navigazione
        nav_layout = QHBoxLayout()
        
        self.btn_first = QPushButton("|<")
        self.btn_prev = QPushButton("<")
        self.btn_next = QPushButton(">")
        self.btn_last = QPushButton(">|")
        
        self.btn_first.clicked.connect(self.move_first)
        self.btn_prev.clicked.connect(self.move_prev)
        self.btn_next.clicked.connect(self.move_next)
        self.btn_last.clicked.connect(self.move_last)
        
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_first)
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_next)
        nav_layout.addWidget(self.btn_last)
        nav_layout.addStretch()
        
        # Informazioni sulla mossa
        self.move_info = QLabel("Posizione iniziale")
        self.move_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Pulsante per generare GIF
        gif_btn = QPushButton("Genera GIF")
        gif_btn.clicked.connect(self.generate_gif)
        
        right_layout.addWidget(self.game_info)
        right_layout.addWidget(self.board_widget, 1)
        right_layout.addLayout(nav_layout)
        right_layout.addWidget(self.move_info)
        right_layout.addWidget(gif_btn)
        
        right_panel.setLayout(right_layout)
        
        # Imposta le dimensioni relative dei pannelli nel splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500])
        
        main_layout.addWidget(splitter)
        tab.setLayout(main_layout)
        
        # Inizializza il visualizzatore
        self.viewer = None
        self.current_game_id = None
        
        self.tabs.addTab(tab, "Visualizza")
    
    def init_settings_tab(self):
        """Inizializza la scheda delle impostazioni."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Form per le impostazioni
        form = QFormLayout()
        
        # Database
        db_layout = QHBoxLayout()
        self.db_path_edit = QLineEdit(self.db_path)
        db_browse_btn = QPushButton("Sfoglia...")
        db_browse_btn.clicked.connect(self.browse_db_path)
        db_layout.addWidget(self.db_path_edit)
        db_layout.addWidget(db_browse_btn)
        form.addRow("Database:", db_layout)
        
        # Giocatore predefinito
        self.default_player_edit = QLineEdit(DEFAULT_PLAYER)
        form.addRow("Giocatore predefinito:", self.default_player_edit)
        
        # Pulsante per salvare le impostazioni
        save_btn = QPushButton("Salva Impostazioni")
        save_btn.clicked.connect(self.save_settings)
        
        # Pulsante per reinizializzare il database
        reset_db_btn = QPushButton("Reinizializza Database")
        reset_db_btn.clicked.connect(self.reset_database)
        
        # Informazioni sull'applicazione
        info_group = QGroupBox("Informazioni")
        info_layout = QVBoxLayout()
        
        info_text = QTextBrowser()
        info_text.setHtml(f"""
        <h2>ChessMetrics Pro {VERSION}</h2>
        <p>Un'applicazione professionale per l'analisi delle partite di scacchi.</p>
        <p>Componenti:</p>
        <ul>
            <li>Importatore PGN: Importa file PGN in un database SQLite</li>
            <li>Analizzatore: Fornisce statistiche e analisi sulle partite</li>
            <li>Visualizzatore: Permette di esplorare le partite mossa per mossa</li>
        </ul>
        <p>Sviluppato come progetto open source con licenza GPL v3.</p>
        """)
        
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        
        # Assembla il layout
        layout.addLayout(form)
        layout.addWidget(save_btn)
        layout.addWidget(reset_db_btn)
        layout.addWidget(info_group)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Impostazioni")
    
    def browse_pgn_folder(self):
        """Apre un dialogo per selezionare la cartella PGN."""
        folder = QFileDialog.getExistingDirectory(self, "Seleziona Cartella PGN", self.pgn_folder)
        if folder:
            self.pgn_folder = folder
            self.pgn_folder_edit.setText(folder)
    
    def browse_db_path(self):
        """Apre un dialogo per selezionare il file del database."""
        file, _ = QFileDialog.getOpenFileName(
            self, "Seleziona Database", 
            self.db_path, 
            "Database SQLite (*.db);;Tutti i file (*)"
        )
        if file:
            self.db_path = file
            self.db_path_edit.setText(file)
    
    def save_settings(self):
        """Salva le impostazioni dell'applicazione."""
        # Aggiorna le impostazioni con i valori dai campi
        old_db_path = self.db_path
        self.db_path = self.db_path_edit.text()
        self.pgn_folder = self.pgn_folder_edit.text()
        
        # TODO: Salvare le impostazioni in un file di configurazione
        
        # Se il database è cambiato, reinizializza le connessioni
        if old_db_path != self.db_path:
            if os.path.exists(self.db_path):
                # Chiudi eventuali connessioni esistenti
                if hasattr(self, 'viewer') and self.viewer:
                    self.viewer.close()
                    self.viewer = None
            else:
                # Chiedi se creare un nuovo database
                reply = QMessageBox.question(
                    self, "Database non trovato",
                    f"Il database {self.db_path} non esiste. Vuoi crearlo?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.initialize_database()
        
        QMessageBox.information(self, "Impostazioni", "Impostazioni salvate con successo.")
    
    def initialize_database(self):
        """Inizializza un nuovo database."""
        try:
            db_manager = ChessDBManager(self.db_path)
            if db_manager.connect():
                db_manager.setup_database()
                db_manager.create_views()
                db_manager.close()
                
                QMessageBox.information(
                    self, "Database inizializzato",
                    "Il database è stato inizializzato con successo."
                )
            else:
                QMessageBox.critical(
                    self, "Errore",
                    "Impossibile connettersi al database."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Errore",
                f"Errore durante l'inizializzazione del database: {e}"
            )
    
    def reset_database(self):
        """Reimposta il database eliminando i dati esistenti."""
        reply = QMessageBox.warning(
            self, "Reinizializza Database",
            "Sei sicuro di voler reinizializzare il database? Tutti i dati verranno persi!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Se il file esiste, eliminalo
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
                
                # Crea un nuovo database
                self.initialize_database()
                
                # Chiudi eventuali connessioni esistenti
                if hasattr(self, 'viewer') and self.viewer:
                    self.viewer.close()
                    self.viewer = None
                
            except Exception as e:
                QMessageBox.critical(
                    self, "Errore",
                    f"Errore durante la reinizializzazione del database: {e}"
                )
    
    def start_import(self):
        """Avvia il processo di importazione PGN."""
        # Aggiorna i valori dalle caselle di testo
        self.pgn_folder = self.pgn_folder_edit.text()
        batch_size = self.batch_size_spin.value()
        skip_existing = not self.reimport_check.isChecked()
        
        # Verifica che la cartella esista
        if not os.path.exists(self.pgn_folder):
            reply = QMessageBox.question(
                self, "Cartella non trovata",
                f"La cartella {self.pgn_folder} non esiste. Vuoi crearla?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    os.makedirs(self.pgn_folder)
                except Exception as e:
                    QMessageBox.critical(
                        self, "Errore",
                        f"Impossibile creare la cartella: {e}"
                    )
                    return
            else:
                return
        
        # Pulisci il log e reimposta la barra di progresso
        self.import_log.clear()
        self.import_progress.setValue(0)
        
        # Crea e avvia il thread di importazione
        self.import_thread = ImportThread(self.db_path, self.pgn_folder, batch_size, skip_existing)
        self.import_thread.progress_update.connect(self.update_import_progress)
        self.import_thread.import_finished.connect(self.import_completed)
        self.import_thread.start()
        
        # Aggiorna lo stato
        self.statusBar().showMessage("Importazione in corso...")
    
    @pyqtSlot(int, str)
    def update_import_progress(self, progress, message):
        """Aggiorna la barra di progresso e il log."""
        self.import_progress.setValue(progress)
        self.import_log.append(message)
        # Scorre automaticamente verso il basso
        self.import_log.verticalScrollBar().setValue(self.import_log.verticalScrollBar().maximum())
    
    @pyqtSlot(bool, str, dict)
    def import_completed(self, success, message, stats):
        """Gestisce il completamento dell'importazione."""
        self.import_log.append(message)
        
        if success:
            # Mostra statistiche
            if stats:
                self.import_log.append("\nStatistiche del database:")
                self.import_log.append(f"Totale partite: {stats['total_games']}")
                
                if 'results' in stats:
                    self.import_log.append("\nDistribuzione risultati:")
                    for result, count in stats['results'].items():
                        self.import_log.append(f"  {result}: {count}")
                
                if 'top_openings' in stats:
                    self.import_log.append("\nAperture più comuni:")
                    for i, opening in enumerate(stats['top_openings'], 1):
                        self.import_log.append(f"  {i}. {opening['eco']} - {opening['name']}: {opening['count']} partite")
                
                if 'top_players' in stats:
                    self.import_log.append("\nGiocatori più attivi:")
                    for i, player in enumerate(stats['top_players'], 1):
                        self.import_log.append(f"  {i}. {player['name']}: {player['games']} partite")
            
            QMessageBox.information(
                self, "Importazione completata",
                "L'importazione dei file PGN è stata completata con successo."
            )
        else:
            QMessageBox.warning(
                self, "Importazione completata con errori",
                f"Si sono verificati errori durante l'importazione: {message}"
            )
        
        self.statusBar().showMessage("Pronto")
    
    def start_analysis(self):
        """Avvia il processo di analisi."""
        # Ottieni i parametri dai controlli
        player = self.player_edit.text()
        
        # Mappa l'indice del combobox al tipo di analisi
        analysis_index = self.analysis_combo.currentIndex()
        analysis_types = ['all', 'basic', 'openings', 'opponents', 'phases', 'elo', 'mistakes', 'eco']
        analysis_type = analysis_types[analysis_index] if analysis_index < len(analysis_types) else 'all'
        
        # Determina se esportare
        export_csv = self.csv_export_radio.isChecked()
        export_text = self.text_export_radio.isChecked()
        
        # Pulisci l'area dei risultati e i grafici esistenti
        self.analysis_results.clear()
        self.clear_graphs()
        
        # Crea e avvia il thread di analisi
        self.analysis_thread = AnalysisThread(self.db_path, player, analysis_type, export_csv, export_text)
        self.analysis_thread.analysis_update.connect(self.update_analysis_progress)
        self.analysis_thread.analysis_data.connect(self.handle_analysis_data)
        self.analysis_thread.analysis_finished.connect(self.analysis_completed)
        self.analysis_thread.start()
        
        # Aggiorna lo stato
        self.statusBar().showMessage("Analisi in corso...")
    
    @pyqtSlot(str)
    def update_analysis_progress(self, message):
        """Aggiorna il log dell'analisi."""
        self.analysis_results.append(message)
        # Scorre automaticamente verso il basso
        self.analysis_results.verticalScrollBar().setValue(self.analysis_results.verticalScrollBar().maximum())
    
    @pyqtSlot(dict)
    def handle_analysis_data(self, data):
        """Gestisce i dati di analisi inviati dal thread secondario."""
        # Questo metodo viene eseguito nel thread principale, sicuro per matplotlib
        
        if data['type'] == 'basic_stats':
            self.create_basic_stats_charts(data)
        
        elif data['type'] == 'opening_stats':
            self.create_opening_stats_charts(data)
        
        elif data['type'] == 'opponents_stats':
            self.create_opponents_charts(data)
        
        elif data['type'] == 'phases_stats':
            self.create_phases_charts(data)
        
        elif data['type'] == 'elo_progression':
            self.create_elo_progression_chart(data)
        
        elif data['type'] == 'elo_monthly':
            self.create_elo_monthly_chart(data)
        
        elif data['type'] == 'quick_losses':
            self.create_quick_losses_charts(data)
        
        elif data['type'] == 'eco_category':
            self.create_eco_category_charts(data)
    
    def create_basic_stats_charts(self, data):
        """Crea grafici per le statistiche di base."""
        # Grafico a torta della distribuzione dei risultati
        fig1 = Figure(figsize=(8, 5))
        ax1 = fig1.add_subplot(111)
        
        labels = ['Vittorie', 'Sconfitte', 'Pareggi']
        sizes = [data['wins'], data['losses'], data['draws']]
        colors = ['#2ecc71', '#e74c3c', '#3498db']  # Verde, Rosso, Blu
        
        ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        ax1.set_title(f'Distribuzione dei Risultati ({data["total_games"]} partite)')
        
        self.add_graph_to_ui(fig1, "Distribuzione dei Risultati")
        
        # Grafico a torta per bianco vs nero
        fig2 = Figure(figsize=(6, 5))
        ax2 = fig2.add_subplot(111)
        
        labels = ['Partite con il Bianco', 'Partite con il Nero']
        sizes = [data['white_games'], data['black_games']]
        colors = ['#f1c40f', '#34495e']  # Giallo, Blu scuro
        
        ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax2.axis('equal')
        ax2.set_title('Distribuzione Bianco vs Nero')
        
        self.add_graph_to_ui(fig2, "Distribuzione Bianco vs Nero")
    
    def create_opening_stats_charts(self, data):
        """Crea grafici per le statistiche delle aperture."""
        # Grafico delle aperture più giocate
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Creiamo etichette personalizzate: ECO + Nome apertura
        labels = [f"{eco} - {opening}" for eco, opening in zip(data['eco'], data['opening'])]
        
        # Abbreviamo le etichette se sono troppo lunghe
        labels = [label[:30] + '...' if len(label) > 30 else label for label in labels]
        
        # Invertiamo per avere la più frequente in alto
        y_pos = range(len(labels))
        
        # Creiamo il grafico con i colori per vittorie, pareggi, sconfitte
        bars = ax.barh(y_pos, data['games'], color='#95a5a6')  # Grigio neutro
        
        # Aggiungiamo le percentuali di vittoria
        for i, (bar, win_pct) in enumerate(zip(bars, data['win_percentage'])):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2, 
                   f"{win_pct}% win", va='center', fontsize=9)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.set_xlabel('Numero di partite')
        ax.set_title('Aperture più giocate')
        
        self.add_graph_to_ui(fig, "Aperture più giocate")
        
        # Secondo grafico: performance per apertura
        fig2 = Figure(figsize=(10, 6))
        ax2 = fig2.add_subplot(111)
        
        # Calcoliamo le percentuali
        win_pct = [w / g * 100 for w, g in zip(data['wins'], data['games'])]
        draw_pct = [d / g * 100 for d, g in zip(data['draws'], data['games'])]
        loss_pct = [l / g * 100 for l, g in zip(data['losses'], data['games'])]
        
        # Invertiamo l'ordine per coerenza con il grafico precedente
        ax2.barh(y_pos, win_pct, color='#2ecc71', label='Vittorie')
        ax2.barh(y_pos, draw_pct, left=win_pct, color='#3498db', label='Pareggi')
        ax2.barh(y_pos, loss_pct, left=[w+d for w, d in zip(win_pct, draw_pct)], color='#e74c3c', label='Sconfitte')
        
        # Aggiungiamo le etichette per il numero di partite
        for i, games in enumerate(data['games']):
            ax2.text(101, i, f"  ({games} partite)", va='center', fontsize=9)
        
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(labels)
        ax2.set_xlim(0, 120)  # Spazio per le etichette
        ax2.set_xlabel('Percentuale')
        ax2.set_title('Performance per apertura')
        ax2.legend(loc='lower right')
        
        self.add_graph_to_ui(fig2, "Performance per apertura")
    
    def create_opponents_charts(self, data):
        """Crea grafici per le statistiche degli avversari."""
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Abbreviamo i nomi se sono troppo lunghi
        opponents = [opp[:15] + '...' if len(opp) > 15 else opp for opp in data['opponents']]
        win_pct = data['win_percent']
        games = data['games']
        
        # Coloriamo le barre in base al win rate
        colors = ['#e74c3c' if wp < 40 else '#f39c12' if wp < 60 else '#2ecc71' for wp in win_pct]
        
        y_pos = range(len(opponents))
        ax.barh(y_pos, win_pct, color=colors)
        
        # Aggiungiamo il numero di partite come etichetta
        for i, (pct, game) in enumerate(zip(win_pct, games)):
            ax.text(pct + 1, i, f"  ({game} partite)", va='center')
        
        ax.axvline(x=50, color='gray', linestyle='--', alpha=0.7)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(opponents)
        ax.set_xlabel('Percentuale di vittorie')
        ax.set_title('Performance contro gli avversari')
        ax.set_xlim(0, 110)  # Lasciamo spazio per le etichette
        
        self.add_graph_to_ui(fig, "Performance contro avversari")
    
    def create_phases_charts(self, data):
        """Crea grafici per le statistiche delle fasi di gioco."""
        # Grafico delle performance per fase
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        fasi = data['fasi']
        partite = data['partite']
        vittorie = data['vittorie']
        pareggi = data['pareggi']
        sconfitte = data['sconfitte']
        perc_vittorie = data['perc_vittorie']
        
        # Creiamo un grafico a barre impilate
        bar_width = 0.6
        x_pos = range(len(fasi))
        
        # Prima serie: vittorie
        bars1 = ax.bar(x_pos, vittorie, bar_width, label='Vittorie', color='#2ecc71')
        
        # Seconda serie: pareggi
        bars2 = ax.bar(x_pos, pareggi, bar_width, bottom=vittorie, label='Pareggi', color='#3498db')
        
        # Terza serie: sconfitte
        bars3 = ax.bar(x_pos, sconfitte, bar_width, bottom=[v+p for v, p in zip(vittorie, pareggi)], 
                      label='Sconfitte', color='#e74c3c')
        
        # Aggiungiamo le etichette con la percentuale di vittoria
        for i, pct in enumerate(perc_vittorie):
            ax.text(i, partite[i] + 0.5, f"{pct}% win", ha='center', fontsize=9, fontweight='bold')
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(fasi)
        ax.set_xlabel('Fase della partita')
        ax.set_ylabel('Numero di partite')
        ax.set_title('Performance per fase di gioco')
        ax.legend()
        
        self.add_graph_to_ui(fig, "Numero di partite per fase")
        
        # Grafico percentuale vittorie per fase
        fig2 = Figure(figsize=(10, 6))
        ax2 = fig2.add_subplot(111)
        
        # Calcoliamo le percentuali
        win_pct = [v / p * 100 if p > 0 else 0 for v, p in zip(vittorie, partite)]
        draw_pct = [d / p * 100 if p > 0 else 0 for d, p in zip(pareggi, partite)]
        loss_pct = [s / p * 100 if p > 0 else 0 for s, p in zip(sconfitte, partite)]
        
        ax2.bar(x_pos, win_pct, color='#2ecc71', label='Vittorie')
        ax2.bar(x_pos, draw_pct, bottom=win_pct, color='#3498db', label='Pareggi')
        ax2.bar(x_pos, loss_pct, bottom=[w+d for w, d in zip(win_pct, draw_pct)], color='#e74c3c', label='Sconfitte')
        
        # Aggiungiamo le etichette con il numero di partite
        for i, tot in enumerate(partite):
            ax2.text(i, 103, f"({tot} partite)", ha='center', fontsize=9)
        
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(fasi)
        ax2.set_ylim(0, 110)  # Spazio per le etichette
        ax2.set_xlabel('Fase della partita')
        ax2.set_ylabel('Percentuale')
        ax2.set_title('Distribuzione dei risultati per fase di gioco (%)')
        ax2.legend()
        
        self.add_graph_to_ui(fig2, "Percentuale risultati per fase")
    
    def create_elo_progression_chart(self, data):
        """Crea un grafico per l'evoluzione dell'Elo."""
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        dates = [datetime.strptime(d, '%Y-%m-%d') for d in data['dates']]
        elo = data['elo']
        results = data['results']
        
        # Colori per i diversi risultati
        colors = {
            'win': '#2ecc71',  # Verde
            'loss': '#e74c3c',  # Rosso
            'draw': '#3498db'   # Blu
        }
        
        # Crea il grafico con diversi colori per i risultati
        for result, color in colors.items():
            mask = [r == result for r in results]
            if any(mask):
                date_filtered = [d for d, m in zip(dates, mask) if m]
                elo_filtered = [e for e, m in zip(elo, mask) if m]
                ax.scatter(date_filtered, elo_filtered, c=color, label=result, alpha=0.7)
        
        # Linea di tendenza
        ax.plot(dates, elo, color='black', alpha=0.3, linestyle='-')
        
        ax.set_xlabel('Data')
        ax.set_ylabel('Elo')
        ax.set_title('Progressione dell\'Elo nel tempo')
        ax.legend(title='Risultato')
        ax.grid(True, alpha=0.3)
        
        fig.autofmt_xdate()  # Formattazione migliore delle date
        
        self.add_graph_to_ui(fig, "Evoluzione Elo")
    
    def create_elo_monthly_chart(self, data):
        """Crea un grafico con l'Elo medio mensile e win rate."""
        fig = Figure(figsize=(10, 6))
        
        # Primo asse: Elo medio
        ax1 = fig.add_subplot(111)
        
        # Converti stringhe di date in oggetti datetime
        dates = [datetime.strptime(d, '%Y-%m') for d in data['dates']]
        avg_elo = data['avg_elo']
        win_percentage = data['win_percentage']
        games = data['games']
        
        # Primo asse: Elo medio
        color = '#3498db'  # Blu
        ax1.set_xlabel('Data')
        ax1.set_ylabel('Elo medio', color=color)
        line1 = ax1.plot(dates, avg_elo, color=color, marker='o', label='Elo Medio')
        ax1.tick_params(axis='y', labelcolor=color)
        
        # Secondo asse: percentuale vittorie
        ax2 = ax1.twinx()
        color = '#e74c3c'  # Rosso
        ax2.set_ylabel('Win rate (%)', color=color)
        line2 = ax2.plot(dates, win_percentage, color=color, marker='s', linestyle='--', label='Win Rate')
        ax2.tick_params(axis='y', labelcolor=color)
        
        # Aggiungiamo il numero di partite per mese come etichetta
        for i, (date, elo, game) in enumerate(zip(dates, avg_elo, games)):
            ax1.annotate(f"{int(game)}", 
                        (date, elo),
                        textcoords="offset points",
                        xytext=(0,10),
                        ha='center',
                        fontsize=8)
        
        # Combina le legende
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left')
        
        ax1.set_title('Elo medio mensile e percentuale di vittorie')
        ax1.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        
        self.add_graph_to_ui(fig, "Andamento mensile Elo e Win Rate")
    
    def create_quick_losses_charts(self, data):
        """Crea grafici per l'analisi delle sconfitte rapide."""
        # Distribuzione delle sconfitte per numero di mosse
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        moves = data['moves']
        frequency = data['frequency']
        
        ax.bar(moves, frequency, color='#e74c3c', alpha=0.7, edgecolor='black', linewidth=1.2)
        
        ax.set_xlabel('Numero di mosse')
        ax.set_ylabel('Frequenza')
        ax.set_title('Distribuzione delle sconfitte rapide per numero di mosse')
        ax.grid(True, alpha=0.3)
        
        self.add_graph_to_ui(fig, "Distribuzione sconfitte per mosse")
        
        # Aperture problematiche (sconfitte rapide)
        if 'eco' in data and len(data['eco']) > 0:
            fig2 = Figure(figsize=(10, 6))
            ax2 = fig2.add_subplot(111)
            
            eco = data['eco']
            eco_frequency = data['eco_frequency']
            eco_opening = data['eco_opening']
            
            # Creiamo etichette personalizzate
            labels = [f"{e} - {o}" for e, o in zip(eco, eco_opening)]
            
            # Abbreviamo le etichette se sono troppo lunghe
            labels = [label[:30] + '...' if len(label) > 30 else label for label in labels]
            
            y_pos = range(len(labels))
            ax2.barh(y_pos, eco_frequency, color='#e74c3c')
            
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(labels)
            ax2.set_xlabel('Numero di sconfitte')
            ax2.set_title('Aperture problematiche (sconfitte rapide)')
            
            self.add_graph_to_ui(fig2, "Aperture problematiche")
    
    def create_eco_category_charts(self, data):
        """Crea grafici per l'analisi delle categorie ECO."""
        # Performance per categoria ECO
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        categories = data['categories']
        descriptions = data['descriptions']
        win_percentage = data['win_percentage']
        games = data['games']
        
        # Creiamo un grafico a barre con colori basati sul win rate
        colors = ['#e74c3c' if wp < 40 else '#f39c12' if wp < 60 else '#2ecc71' for wp in win_percentage]
        
        x_pos = range(len(categories))
        bars = ax.bar(x_pos, win_percentage, color=colors)
        
        # Aggiungiamo le etichette con le descrizioni e il numero di partite
        for i, (cat, desc, game) in enumerate(zip(categories, descriptions, games)):
            ax.text(i, win_percentage[i] + 2, f"{desc}", ha='center', fontsize=7, rotation=0)
            ax.text(i, win_percentage[i] + 7, f"({game} partite)", ha='center', fontsize=7)
        
        ax.axhline(y=50, color='gray', linestyle='--', alpha=0.7)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(categories)
        ax.set_xlabel('Categoria ECO')
        ax.set_ylabel('Percentuale di vittorie')
        ax.set_title('Performance per categoria ECO')
        ax.set_ylim(0, 100)
        
        self.add_graph_to_ui(fig, "Performance per categoria ECO")
        
        # Distribuzione delle partite per categoria ECO
        fig2 = Figure(figsize=(8, 6))
        ax2 = fig2.add_subplot(111)
        
        # Creiamo un grafico a torta
        labels = [f"{cat} - {desc[:20]}... ({game} partite)" 
                for cat, desc, game in zip(categories, descriptions, games)]
        
        ax2.pie(games, labels=labels, autopct='%1.1f%%', startangle=90,
               wedgeprops={'linewidth': 1, 'edgecolor': 'white'})
        
        ax2.axis('equal')
        ax2.set_title('Distribuzione delle partite per categoria ECO')
        
        self.add_graph_to_ui(fig2, "Distribuzione partite per ECO")
    
    def add_graph_to_ui(self, fig, title="Grafico"):
        """Aggiunge un grafico matplotlib all'interfaccia utente."""
        # Crea un canvas matplotlib basato sulla figura
        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(400)
        
        # Aggiungi una toolbar per interagire con il grafico
        toolbar = NavigationToolbar(canvas, self)
        
        # Crea un widget per contenere il canvas e la toolbar
        graph_container = QGroupBox(title)
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        
        # Aggiungi pulsante per salvare l'immagine
        save_btn = QPushButton("Salva Immagine")
        save_btn.clicked.connect(lambda: self.save_figure(fig))
        layout.addWidget(save_btn)
        
        graph_container.setLayout(layout)
        
        # Aggiungi il widget al layout dei grafici
        self.graphs_layout.addWidget(graph_container)
    
    def clear_graphs(self):
        """Rimuove tutti i grafici esistenti."""
        # Rimuovi tutti i widget dal layout dei grafici
        while self.graphs_layout.count():
            item = self.graphs_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def save_figure(self, fig):
        """Salva una figura matplotlib come file immagine."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salva Grafico", 
            os.path.join(os.getcwd(), "grafici"), 
            "Immagini (*.png *.jpg *.pdf)"
        )
        
        if file_path:
            try:
                fig.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(
                    self, "Salvataggio Completato",
                    f"Grafico salvato con successo in:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Errore",
                    f"Impossibile salvare il grafico: {e}"
                )
    
    @pyqtSlot(bool, str)
    def analysis_completed(self, success, message):
        """Gestisce il completamento dell'analisi."""
        self.analysis_results.append(message)
        
        if success:
            QMessageBox.information(
                self, "Analisi completata",
                "L'analisi è stata completata con successo."
            )
        else:
            QMessageBox.warning(
                self, "Analisi completata con errori",
                f"Si sono verificati errori durante l'analisi: {message}"
            )
        
        self.statusBar().showMessage("Pronto")
    
    def search_games(self):
        """Cerca partite nel database in base ai criteri forniti."""
        if not hasattr(self, 'viewer') or not self.viewer:
            self.viewer = ChessGameViewer(self.db_path)
            if not self.viewer.connect():
                QMessageBox.critical(
                    self, "Errore",
                    "Impossibile connettersi al database."
                )
                return
        
        # Prepara i criteri di ricerca
        criteria = {}
        
        player = self.search_player_edit.text()
        if player:
            criteria['player'] = player
            
        date = self.search_date_edit.text()
        if date:
            criteria['date'] = date
            
        event = self.search_event_edit.text()
        if event:
            criteria['event'] = event
            
        eco = self.search_eco_edit.text()
        if eco:
            criteria['eco'] = eco
        
        # Esegui la ricerca
        games = self.viewer.search_games(criteria)
        
        # Aggiorna la tabella dei risultati
        self.games_list.setRowCount(0)
        if not games:
            QMessageBox.information(
                self, "Ricerca",
                "Nessuna partita trovata con questi criteri."
            )
            return
        
        # Popola la tabella
        self.games_list.setRowCount(len(games))
        for i, (id, white, black, result, date, event, site) in enumerate(games):
            self.games_list.setItem(i, 0, QTableWidgetItem(str(id)))
            self.games_list.setItem(i, 1, QTableWidgetItem(white))
            self.games_list.setItem(i, 2, QTableWidgetItem(black))
            self.games_list.setItem(i, 3, QTableWidgetItem(result))
            self.games_list.setItem(i, 4, QTableWidgetItem(date))
        
        # Ridimensiona le colonne
        self.games_list.resizeColumnsToContents()
    
    def load_selected_game(self):
        """Carica la partita selezionata dalla lista."""
        selected_items = self.games_list.selectedItems()
        if not selected_items:
            return
            
        # Ottieni l'ID della partita dalla prima colonna
        row = selected_items[0].row()
        game_id = int(self.games_list.item(row, 0).text())
        
        # Carica la partita
        if self.viewer.load_game(game_id):
            self.current_game_id = game_id
            
            # Aggiorna le informazioni della partita
            white = self.games_list.item(row, 1).text()
            black = self.games_list.item(row, 2).text()
            result = self.games_list.item(row, 3).text()
            date = self.games_list.item(row, 4).text()
            
            self.game_info.setHtml(f"""
            <h3>{white} vs {black}</h3>
            <p>Risultato: {result} | Data: {date}</p>
            """)
            
            # Reimposta la scacchiera alla posizione iniziale
            self.board_widget.set_board(chess.Board())
            self.move_info.setText("Posizione iniziale")
            
            # Abilita i pulsanti di navigazione
            self.btn_first.setEnabled(False)
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(True)
            self.btn_last.setEnabled(True)
        else:
            QMessageBox.warning(
                self, "Errore",
                "Impossibile caricare la partita selezionata."
            )
    
    def move_first(self):
        """Torna alla prima mossa della partita."""
        if hasattr(self, 'viewer') and self.viewer and self.current_game_id:
            # Reimposta la scacchiera
            self.board_widget.set_board(chess.Board())
            self.viewer.board = chess.Board()
            self.viewer.current_move_index = -1
            
            # Aggiorna l'interfaccia
            self.move_info.setText("Posizione iniziale")
            self.btn_first.setEnabled(False)
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(True)
            self.btn_last.setEnabled(True)
    
    def move_prev(self):
        """Torna alla mossa precedente."""
        if hasattr(self, 'viewer') and self.viewer and self.current_game_id:
            if self.viewer.current_move_index >= 0:
                self.viewer.board.pop()
                self.viewer.current_move_index -= 1
                
                # Aggiorna la scacchiera
                self.board_widget.set_board(self.viewer.board)
                
                # Aggiorna le informazioni sulla mossa
                if self.viewer.current_move_index >= 0:
                    ply, san, uci, comment = self.viewer.moves[self.viewer.current_move_index]
                    move_number = (ply // 2) + 1
                    color = "Bianco" if ply % 2 == 0 else "Nero"
                    self.move_info.setText(f"Mossa {move_number}. {color}: {san}")
                else:
                    self.move_info.setText("Posizione iniziale")
                
                # Aggiorna i pulsanti
                self.btn_first.setEnabled(self.viewer.current_move_index > 0)
                self.btn_prev.setEnabled(self.viewer.current_move_index >= 0)
                self.btn_next.setEnabled(True)
                self.btn_last.setEnabled(True)
    
    def move_next(self):
        """Avanza alla mossa successiva."""
        if hasattr(self, 'viewer') and self.viewer and self.current_game_id:
            if self.viewer.current_move_index + 1 < len(self.viewer.moves):
                self.viewer.current_move_index += 1
                ply, san, uci, comment = self.viewer.moves[self.viewer.current_move_index]
                
                # Esegui la mossa
                move = chess.Move.from_uci(uci)
                self.viewer.board.push(move)
                
                # Aggiorna la scacchiera
                self.board_widget.set_board(self.viewer.board)
                
                # Aggiorna le informazioni sulla mossa
                move_number = (ply // 2) + 1
                color = "Bianco" if ply % 2 == 0 else "Nero"
                info_text = f"Mossa {move_number}. {color}: {san}"
                if comment:
                    info_text += f" - {comment}"
                self.move_info.setText(info_text)
                
                # Aggiorna i pulsanti
                self.btn_first.setEnabled(True)
                self.btn_prev.setEnabled(True)
                self.btn_next.setEnabled(self.viewer.current_move_index + 1 < len(self.viewer.moves))
                self.btn_last.setEnabled(self.viewer.current_move_index + 1 < len(self.viewer.moves))
            else:
                self.move_info.setText("Fine della partita")
                self.btn_next.setEnabled(False)
                self.btn_last.setEnabled(False)
    
    def move_last(self):
        """Avanza all'ultima mossa della partita."""
        if hasattr(self, 'viewer') and self.viewer and self.current_game_id:
            # Salva l'indice dell'ultima mossa
            last_index = len(self.viewer.moves) - 1
            
            # Reimposta la scacchiera e poi esegui tutte le mosse
            self.viewer.board = chess.Board()
            
            for i in range(last_index + 1):
                ply, san, uci, comment = self.viewer.moves[i]
                move = chess.Move.from_uci(uci)
                self.viewer.board.push(move)
            
            self.viewer.current_move_index = last_index
            
            # Aggiorna la scacchiera
            self.board_widget.set_board(self.viewer.board)
            
            # Aggiorna le informazioni sulla mossa
            if last_index >= 0:
                ply, san, uci, comment = self.viewer.moves[last_index]
                move_number = (ply // 2) + 1
                color = "Bianco" if ply % 2 == 0 else "Nero"
                self.move_info.setText(f"Mossa {move_number}. {color}: {san}")
            
            # Aggiorna i pulsanti
            self.btn_first.setEnabled(True)
            self.btn_prev.setEnabled(True)
            self.btn_next.setEnabled(False)
            self.btn_last.setEnabled(False)
    
    def generate_gif(self):
        """Genera una GIF della partita corrente."""
        if not hasattr(self, 'viewer') or not self.viewer or not self.current_game_id:
            QMessageBox.warning(
                self, "Errore",
                "Nessuna partita selezionata."
            )
            return
        
        # Dialog per le opzioni GIF
        output_path, ok = QFileDialog.getSaveFileName(
            self, "Salva GIF", 
            os.path.join(os.getcwd(), "gif_files"), 
            "GIF Files (*.gif)"
        )
        
        if not ok or not output_path:
            return
        
        # Assicurati che abbia estensione .gif
        if not output_path.lower().endswith('.gif'):
            output_path += '.gif'
        
        # Dialog per il ritardo
        delay, ok = QInputDialog.getInt(
            self, "Ritardo Frame", 
            "Ritardo tra i frame in millisecondi:",
            500, 100, 2000, 100
        )
        
        if not ok:
            return
        
        # Mostra un messaggio di attesa
        wait_msg = QMessageBox(
            QMessageBox.Icon.Information,
            "Generazione GIF",
            "Generazione GIF in corso...\nQuesto processo potrebbe richiedere alcuni minuti.",
            QMessageBox.StandardButton.NoButton,
            self
        )
        wait_msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
        wait_msg.show()
        QApplication.processEvents()
        
        try:
            # Genera la GIF
            result = self.viewer.create_game_gif(output_path, delay)
            wait_msg.hide()
            
            if result:
                QMessageBox.information(
                    self, "GIF Generata",
                    f"La GIF è stata generata con successo.\nSalvata in: {result}"
                )
            else:
                QMessageBox.warning(
                    self, "Errore",
                    "Si è verificato un errore durante la generazione della GIF."
                )
        except Exception as e:
            wait_msg.hide()
            QMessageBox.critical(
                self, "Errore",
                f"Errore durante la generazione della GIF: {e}"
            )


def main():
    """Funzione principale."""
    # Initialize directories before anything else
    initialize_directories()
    app = QApplication(sys.argv)
    window = ChessMetricsPro()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()