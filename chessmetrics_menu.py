#!/usr/bin/env python3
"""
ChessMetrics Pro - Menu Principale
Integra tutti i componenti dell'applicazione in un'interfaccia unificata.
"""

import os
import sys
import argparse
import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
# Importa le funzioni di utilità per la gestione dei percorsi
from data_utils import get_db_path, get_log_path, initialize_directories
# Importazione dei moduli dell'applicazione
try:
    from chess_import import ChessDBManager
    from chess_analyzer import ChessAnalyzer
    from chess_game_viewer import ChessGameViewer
except ImportError:
    print("Errore: moduli dell'applicazione non trovati. Assicurati di essere nella directory corretta.")
    sys.exit(1)

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(get_log_path("logs/chessmetrics.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Costanti
VERSION = "0.3.0-beta"
DEFAULT_DB_PATH = get_db_path("chess_games.db")  # Usa get_db_path per il percorso del database
DEFAULT_PGN_FOLDER = "pgn_files"
DEFAULT_PLAYER = "Blackeyes972"
CONFIG_FILE = get_db_path("chessmetrics_config.ini")  # Anche il file di configurazione nella cartella data

class ChessMetricsApp:
    """Classe principale per l'applicazione ChessMetrics Pro."""
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """Inizializza l'applicazione.
        
        Args:
            db_path: Percorso del database SQLite
        """
        self.db_path = db_path
        self.config = self.load_config()
        
        # Inizializza i componenti (ma non li connette ancora)
        self.db_manager = None
        self.analyzer = None
        self.viewer = None
        
        # Verifica che il database esista
        self.check_database()
    
    def check_database(self) -> None:
        """Verifica che il database esista e sia valido."""
        if not os.path.exists(self.db_path):
            print(f"Il database {self.db_path} non esiste.")
            create_db = input("Vuoi crearlo? (s/n): ").lower()
            if create_db.startswith('s'):
                self.initialize_database()
            else:
                print("Impossibile procedere senza database.")
                sys.exit(1)
        else:
            try:
                # Verifica che il database sia valido
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                required_tables = ['games', 'moves', 'import_metadata']
                
                if not all(table in tables for table in required_tables):
                    print(f"Il database {self.db_path} non contiene tutte le tabelle necessarie.")
                    reinit_db = input("Vuoi reinizializzarlo? (s/n): ").lower()
                    if reinit_db.startswith('s'):
                        conn.close()
                        self.initialize_database()
                    else:
                        print("Il database potrebbe non funzionare correttamente.")
                
                conn.close()
            except sqlite3.Error as e:
                print(f"Errore durante la verifica del database: {e}")
                sys.exit(1)
    
    def initialize_database(self) -> None:
        """Inizializza il database creando le tabelle necessarie."""
        print(f"Inizializzazione del database {self.db_path}...")
        try:
            self.db_manager = ChessDBManager(self.db_path)
            if self.db_manager.connect():
                self.db_manager.setup_database()
                self.db_manager.create_views()
                print("Database inizializzato con successo.")
            else:
                print("Impossibile connettersi al database.")
                sys.exit(1)
        except Exception as e:
            print(f"Errore durante l'inizializzazione del database: {e}")
            sys.exit(1)
    
    def load_config(self) -> Dict[str, Any]:
        """Carica la configurazione dell'applicazione.
        
        Returns:
            Dict[str, Any]: Configurazione dell'applicazione
        """
        config = {
            'default_player': DEFAULT_PLAYER,
            'pgn_folder': DEFAULT_PGN_FOLDER,
            'db_path': self.db_path,
            'batch_size': 100,
            'default_export_format': 'csv',
            'theme': 'default'
        }
        
        # TODO: Implementare la lettura di un file di configurazione
        
        return config
    
    def save_config(self) -> None:
        """Salva la configurazione dell'applicazione."""
        # TODO: Implementare la scrittura di un file di configurazione
        pass
    
    def clear_screen(self) -> None:
        """Pulisce lo schermo."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self) -> None:
        """Stampa l'intestazione dell'applicazione."""
        self.clear_screen()
        print(f"╔══════════════════════════════════════════════════════════╗")
        print(f"                    CHESSMETRICS PRO {VERSION}                                                                                ")
        print(f"╚══════════════════════════════════════════════════════════╝")
        print()
    
    def print_menu(self, title: str, options: List[str]) -> None:
        """Stampa un menu con opzioni numerate.
        
        Args:
            title: Titolo del menu
            options: Lista di opzioni
        """
        print(f"\n{title}:")
        print("─" * len(title))
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        print("0. Indietro/Esci")
    
    def get_choice(self, max_choice: int) -> int:
        """Ottiene una scelta valida dall'utente.
        
        Args:
            max_choice: Scelta massima valida
            
        Returns:
            int: Scelta dell'utente
        """
        while True:
            try:
                choice = input("\nScegli un'opzione: ")
                if choice.lower() in ('q', 'exit', 'quit'):
                    return 0
                choice = int(choice)
                if 0 <= choice <= max_choice:
                    return choice
                print(f"Scelta non valida. Inserisci un numero tra 0 e {max_choice}.")
            except ValueError:
                print("Inserisci un numero valido.")
    
    def import_pgn_menu(self) -> None:
        """Menu per l'importazione di file PGN."""
        self.print_header()
        print("IMPORTAZIONE FILE PGN")
        
        # Ottieni i parametri di importazione
        pgn_folder = input(f"Cartella PGN [{self.config['pgn_folder']}]: ").strip()
        if not pgn_folder:
            pgn_folder = self.config['pgn_folder']
        
        batch_size = input(f"Dimensione batch [{self.config['batch_size']}]: ").strip()
        try:
            batch_size = int(batch_size) if batch_size else self.config['batch_size']
        except ValueError:
            batch_size = self.config['batch_size']
            print(f"Valore non valido, uso il default: {batch_size}")
        
        force_reimport = input("Reimportare file già elaborati? (s/n): ").lower().startswith('s')
        
        # Verifica che la cartella esista
        if not os.path.exists(pgn_folder):
            create_folder = input(f"La cartella {pgn_folder} non esiste. Crearla? (s/n): ").lower()
            if create_folder.startswith('s'):
                try:
                    os.makedirs(pgn_folder)
                    print(f"Cartella {pgn_folder} creata.")
                except Exception as e:
                    print(f"Errore durante la creazione della cartella: {e}")
                    input("\nPremi Invio per tornare al menu principale...")
                    return
            else:
                print("Impossibile procedere senza cartella PGN.")
                input("\nPremi Invio per tornare al menu principale...")
                return
        
        # Avvia l'importazione
        print(f"\nAvvio importazione da {pgn_folder}...")
        try:
            # Inizializza e connetti il gestore del database se necessario
            if not self.db_manager:
                self.db_manager = ChessDBManager(self.db_path)
                if not self.db_manager.connect():
                    print("Impossibile connettersi al database.")
                    input("\nPremi Invio per tornare al menu principale...")
                    return
            
            start_time = datetime.now()
            
            # Esegui l'importazione
            games_count = self.db_manager.process_pgn_folder(
                pgn_folder,
                batch_size,
                not force_reimport
            )
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print(f"\nImportazione completata: {games_count} partite in {duration}")
            
            # Mostra statistiche
            if games_count > 0:
                show_stats = input("\nVuoi vedere le statistiche del database? (s/n): ").lower()
                if show_stats.startswith('s'):
                    stats = self.db_manager.get_statistics()
                    print("\nStatistiche del database:")
                    print(f"Totale partite: {stats['total_games']}")
                    
                    if 'results' in stats:
                        print("\nDistribuzione risultati:")
                        for result, count in stats['results'].items():
                            print(f"  {result}: {count}")
                    
                    if 'top_openings' in stats:
                        print("\nAperture più comuni:")
                        for i, opening in enumerate(stats['top_openings'], 1):
                            print(f"  {i}. {opening['eco']} - {opening['name']}: {opening['count']} partite")
                    
                    if 'top_players' in stats:
                        print("\nGiocatori più attivi:")
                        for i, player in enumerate(stats['top_players'], 1):
                            print(f"  {i}. {player['name']}: {player['games']} partite")
            
        except Exception as e:
            print(f"Errore durante l'importazione: {e}")
        
        input("\nPremi Invio per tornare al menu principale...")
    
    def analysis_menu(self) -> None:
        """Menu per l'analisi delle partite."""
        while True:
            self.print_header()
            print("ANALISI DELLE PARTITE")
            
            options = [
                "Statistiche di base",
                "Analisi delle aperture",
                "Analisi degli avversari",
                "Analisi delle fasi di gioco",
                "Evoluzione dell'Elo",
                "Analisi degli errori",
                "Analisi per categoria ECO",
                "Esegui tutte le analisi",
                "Esporta analisi in CSV",
                "Esporta analisi in file di testo"
            ]
            
            self.print_menu("Tipo di analisi", options)
            choice = self.get_choice(len(options))
            
            if choice == 0:
                return
            
            # Ottieni il nome del giocatore
            player = input(f"\nNome del giocatore [{self.config['default_player']}]: ").strip()
            if not player:
                player = self.config['default_player']
            
            # Inizializza e connetti l'analizzatore se necessario
            if not self.analyzer:
                self.analyzer = ChessAnalyzer(self.db_path, player)
                if not self.analyzer.connect():
                    print("Impossibile connettersi al database.")
                    input("\nPremi Invio per tornare al menu principale...")
                    return
            else:
                # Aggiorna il nome del giocatore se è cambiato
                if self.analyzer.player_name != player:
                    self.analyzer.close()
                    self.analyzer = ChessAnalyzer(self.db_path, player)
                    if not self.analyzer.connect():
                        print("Impossibile connettersi al database.")
                        input("\nPremi Invio per tornare al menu principale...")
                        return
            
            try:
                if choice == 1:
                    self.analyzer.display_basic_stats()
                elif choice == 2:
                    self.analyzer.analyze_openings()
                elif choice == 3:
                    self.analyzer.analyze_opponents()
                elif choice == 4:
                    self.analyzer.analyze_game_phases()
                elif choice == 5:
                    self.analyzer.analyze_elo_progression()
                elif choice == 6:
                    self.analyzer.analyze_frequent_mistakes()
                elif choice == 7:
                    self.analyzer.analyze_performance_by_eco()
                elif choice == 8:
                    self.analyzer.run_analysis()
                elif choice == 9:
                    filename = input("Nome del file CSV [chess_analysis.csv]: ").strip()
                    if not filename:
                        filename = "chess_analysis.csv"
                    self.analyzer.export_all_to_csv(filename)
                    print(f"Analisi esportata in {filename}")
                elif choice == 10:
                    filename = input("Nome del file di testo [chess_analysis.txt]: ").strip()
                    if not filename:
                        filename = "chess_analysis.txt"
                    self.analyzer.export_analysis_to_text(filename)
                    print(f"Analisi esportata in {filename}")
            
            except Exception as e:
                print(f"Errore durante l'analisi: {e}")
            
            input("\nPremi Invio per continuare...")
    
    def viewer_menu(self) -> None:
        """Menu per la visualizzazione delle partite."""
        self.print_header()
        print("VISUALIZZATORE DI PARTITE")
        
        # Inizializza e connetti il visualizzatore
        if not self.viewer:
            self.viewer = ChessGameViewer(self.db_path)
        
        # Avvia l'interfaccia interattiva del visualizzatore
        self.viewer.run_interactive()
    
    def settings_menu(self) -> None:
        """Menu per le impostazioni dell'applicazione."""
        while True:
            self.print_header()
            print("IMPOSTAZIONI")
            
            options = [
                f"Giocatore predefinito: {self.config['default_player']}",
                f"Cartella PGN: {self.config['pgn_folder']}",
                f"Database: {self.config['db_path']}",
                f"Dimensione batch: {self.config['batch_size']}",
                f"Formato di esportazione predefinito: {self.config['default_export_format']}",
                "Reinizializza database",
                "Salva configurazione"
            ]
            
            self.print_menu("Modifica impostazioni", options)
            choice = self.get_choice(len(options))
            
            if choice == 0:
                return
            
            try:
                if choice == 1:
                    player = input("Nuovo giocatore predefinito: ").strip()
                    if player:
                        self.config['default_player'] = player
                        print(f"Giocatore predefinito impostato a: {player}")
                
                elif choice == 2:
                    folder = input("Nuova cartella PGN: ").strip()
                    if folder:
                        self.config['pgn_folder'] = folder
                        print(f"Cartella PGN impostata a: {folder}")
                
                elif choice == 3:
                    db_path = input("Nuovo percorso database: ").strip()
                    if db_path:
                        change_db = input(f"Cambiare il database da {self.config['db_path']} a {db_path}? (s/n): ").lower()
                        if change_db.startswith('s'):
                            self.config['db_path'] = db_path
                            self.db_path = db_path
                            
                            # Chiudi le connessioni esistenti
                            if self.db_manager:
                                self.db_manager.close()
                                self.db_manager = None
                            if self.analyzer:
                                self.analyzer.close()
                                self.analyzer = None
                            if self.viewer:
                                self.viewer.close()
                                self.viewer = None
                            
                            # Verifica il nuovo database
                            self.check_database()
                            print(f"Database impostato a: {db_path}")
                
                elif choice == 4:
                    batch_size = input("Nuova dimensione batch: ").strip()
                    try:
                        batch_size = int(batch_size)
                        if batch_size > 0:
                            self.config['batch_size'] = batch_size
                            print(f"Dimensione batch impostata a: {batch_size}")
                        else:
                            print("La dimensione del batch deve essere maggiore di zero.")
                    except ValueError:
                        print("Inserisci un numero valido.")
                
                elif choice == 5:
                    format_options = ["csv", "txt"]
                    print("\nFormati disponibili:")
                    for i, fmt in enumerate(format_options, 1):
                        print(f"{i}. {fmt}")
                    
                    fmt_choice = self.get_choice(len(format_options))
                    if fmt_choice > 0:
                        self.config['default_export_format'] = format_options[fmt_choice - 1]
                        print(f"Formato di esportazione impostato a: {self.config['default_export_format']}")
                
                elif choice == 6:
                    confirm = input("Sei sicuro di voler reinizializzare il database? Tutti i dati verranno persi! (s/n): ").lower()
                    if confirm.startswith('s'):
                        self.initialize_database()
                
                elif choice == 7:
                    self.save_config()
                    print("Configurazione salvata.")
            
            except Exception as e:
                print(f"Errore durante la modifica delle impostazioni: {e}")
            
            input("\nPremi Invio per continuare...")
    
    def about_menu(self) -> None:
        """Mostra informazioni sull'applicazione."""
        self.print_header()
        print("INFORMAZIONI SU CHESSMETRICS PRO")
        print("\nChessMetrics Pro è un'applicazione per l'analisi di partite di scacchi.")
        print("Versione:", VERSION)
        print("\nComponenti:")
        print("- Importatore PGN: Importa file PGN in un database SQLite")
        print("- Analizzatore: Fornisce statistiche e analisi sulle partite")
        print("- Visualizzatore: Permette di esplorare le partite mossa per mossa")
        print("\nSviluppato come progetto open source con licenza GNU GPL v3.")
        print("Per ulteriori informazioni, consultare la documentazione.")
        
        input("\nPremi Invio per tornare al menu principale...")
    
    def run(self) -> None:
        """Esegue l'applicazione."""
        try:
            while True:
                self.print_header()
                
                options = [
                    "Importa file PGN",
                    "Analizza partite",
                    "Visualizza partite",
                    "Impostazioni",
                    "Informazioni"
                ]
                
                self.print_menu("Menu Principale", options)
                choice = self.get_choice(len(options))
                
                if choice == 0:
                    confirm_exit = input("Sei sicuro di voler uscire? (s/n): ").lower()
                    if confirm_exit.startswith('s'):
                        break
                elif choice == 1:
                    self.import_pgn_menu()
                elif choice == 2:
                    self.analysis_menu()
                elif choice == 3:
                    self.viewer_menu()
                elif choice == 4:
                    self.settings_menu()
                elif choice == 5:
                    self.about_menu()
        
        except KeyboardInterrupt:
            print("\nUscita forzata.")
        
        finally:
            print("\nChiusura dell'applicazione...")
            # Chiudi le connessioni
            if self.db_manager:
                self.db_manager.close()
            if self.analyzer:
                self.analyzer.close()
            if self.viewer:
                self.viewer.close()
            print("Arrivederci!")


def parse_args() -> argparse.Namespace:
    """Analizza gli argomenti della riga di comando.
    
    Returns:
        argparse.Namespace: Argomenti analizzati
    """
    parser = argparse.ArgumentParser(description='ChessMetrics Pro - Analisi partite di scacchi')
    parser.add_argument('--db-path', default=DEFAULT_DB_PATH, help=f'Percorso del database (default: {DEFAULT_DB_PATH})')
    parser.add_argument('--config', default=CONFIG_FILE, help=f'File di configurazione (default: {CONFIG_FILE})')
    return parser.parse_args()


def main() -> None:
    """Funzione principale."""
    # Inizializza le directory prima di tutto il resto
    initialize_directories()
    args = parse_args()
    
    app = ChessMetricsApp(args.db_path)
    app.run()


if __name__ == "__main__":
    main()