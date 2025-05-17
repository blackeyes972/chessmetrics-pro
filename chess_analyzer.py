#!/usr/bin/env python3
"""
Chess Analytics: Script per l'analisi completa delle partite di scacchi da un database SQLite.
Fornisce varie analisi statistiche, grafici e insights per migliorare il tuo gioco.
"""

import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
import sys
from datetime import datetime
import argparse
from typing import Dict, List, Tuple, Any, Optional, Union

# Impostazioni grafiche
plt.style.use('ggplot')
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 7)
plt.rcParams['font.size'] = 12

# Configurazione colori
COLORS = {
    'win': '#2ecc71',  # Verde
    'loss': '#e74c3c',  # Rosso
    'draw': '#3498db',  # Blu
    'white': '#f1c40f',  # Giallo
    'black': '#34495e',  # Blu scuro
    'neutral': '#95a5a6'  # Grigio
}

class ChessAnalyzer:
    """Classe principale per l'analisi del database di partite di scacchi."""
    
    def __init__(self, db_path: str, player_name: str = 'Blackeyes972'):
        """Inizializza l'analizzatore.
        
        Args:
            db_path: Percorso del database SQLite
            player_name: Nome del giocatore principale da analizzare
        """
        self.db_path = db_path
        self.player_name = player_name
        self.conn = None
        self.cursor = None
        
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
            print(f"Errore di connessione al database: {e}")
            return False
    
    def close(self) -> None:
        """Chiude la connessione al database."""
        if self.conn:
            self.conn.close()
            
    def get_basic_stats(self) -> Dict[str, Any]:
        """Ottiene statistiche di base sulle partite.
        
        Returns:
            Dict[str, Any]: Dizionario con varie statistiche
        """
        stats = {}
        
        # Numero totale di partite
        self.cursor.execute(
            "SELECT COUNT(*) FROM games WHERE white_player = ? OR black_player = ?", 
            (self.player_name, self.player_name)
        )
        stats['total_games'] = self.cursor.fetchone()[0]
        
        # Partite con il bianco vs nero
        self.cursor.execute(
            "SELECT COUNT(*) FROM games WHERE white_player = ?", 
            (self.player_name,)
        )
        stats['white_games'] = self.cursor.fetchone()[0]
        stats['black_games'] = stats['total_games'] - stats['white_games']
        
        # Statistiche vittorie, sconfitte, pareggi
        self.cursor.execute("""
            SELECT 
                SUM(CASE WHEN 
                        (white_player = ? AND result = '1-0') OR 
                        (black_player = ? AND result = '0-1') 
                    THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN 
                        (white_player = ? AND result = '0-1') OR 
                        (black_player = ? AND result = '1-0') 
                    THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as draws
            FROM games
            WHERE white_player = ? OR black_player = ?
        """, (self.player_name, self.player_name, self.player_name, self.player_name, self.player_name, self.player_name))
        
        row = self.cursor.fetchone()
        stats['wins'] = row[0] or 0
        stats['losses'] = row[1] or 0
        stats['draws'] = row[2] or 0
        
        # Calcola percentuali
        if stats['total_games'] > 0:
            stats['win_percentage'] = round((stats['wins'] / stats['total_games']) * 100, 2)
            stats['loss_percentage'] = round((stats['losses'] / stats['total_games']) * 100, 2)
            stats['draw_percentage'] = round((stats['draws'] / stats['total_games']) * 100, 2)
        else:
            stats['win_percentage'] = 0
            stats['loss_percentage'] = 0
            stats['draw_percentage'] = 0
        
        # Lunghezza media delle partite
        self.cursor.execute("""
            SELECT AVG(moves_count) FROM (
                SELECT g.id, MAX(m.ply_number)/2 + 1 as moves_count
                FROM games g
                JOIN moves m ON g.id = m.game_id
                WHERE g.white_player = ? OR g.black_player = ?
                GROUP BY g.id
            )
        """, (self.player_name, self.player_name))
        
        stats['avg_game_length'] = round(self.cursor.fetchone()[0] or 0, 1)
        
        # Media Elo
        self.cursor.execute("""
            SELECT 
                AVG(CASE WHEN white_player = ? THEN white_elo ELSE black_elo END) as avg_player_elo,
                AVG(CASE WHEN white_player = ? THEN black_elo ELSE white_elo END) as avg_opponent_elo
            FROM games
            WHERE white_player = ? OR black_player = ?
        """, (self.player_name, self.player_name, self.player_name, self.player_name))
        
        row = self.cursor.fetchone()
        stats['avg_player_elo'] = round(row[0] or 0)
        stats['avg_opponent_elo'] = round(row[1] or 0)
        
        return stats
    
    def display_basic_stats(self) -> None:
        """Visualizza statistiche di base sulle partite."""
        stats = self.get_basic_stats()
        
        print("\n===== PANORAMICA GENERALE =====")
        print(f"Giocatore: {self.player_name}")
        print(f"Totale partite: {stats['total_games']}")
        print(f"Partite con il bianco: {stats['white_games']} ({round(stats['white_games']/stats['total_games']*100 if stats['total_games'] > 0 else 0, 1)}%)")
        print(f"Partite con il nero: {stats['black_games']} ({round(stats['black_games']/stats['total_games']*100 if stats['total_games'] > 0 else 0, 1)}%)")
        print(f"Vittorie: {stats['wins']} ({stats['win_percentage']}%)")
        print(f"Sconfitte: {stats['losses']} ({stats['loss_percentage']}%)")
        print(f"Pareggi: {stats['draws']} ({stats['draw_percentage']}%)")
        print(f"Lunghezza media partite: {stats['avg_game_length']} mosse")
        print(f"Elo medio del giocatore: {stats['avg_player_elo']}")
        print(f"Elo medio degli avversari: {stats['avg_opponent_elo']}")
        
        # Creiamo anche un grafico della distribuzione dei risultati
        labels = ['Vittorie', 'Sconfitte', 'Pareggi']
        sizes = [stats['wins'], stats['losses'], stats['draws']]
        colors = [COLORS['win'], COLORS['loss'], COLORS['draw']]
        
        plt.figure(figsize=(10, 6))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
        plt.title(f'Distribuzione dei Risultati ({stats["total_games"]} partite)')
        plt.tight_layout()
        plt.show()
        
        # Grafico partite bianco vs nero
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Grafico a torta bianco vs nero
        labels = ['Bianco', 'Nero']
        sizes = [stats['white_games'], stats['black_games']]
        colors = [COLORS['white'], COLORS['black']]
        
        ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        ax1.set_title('Partite con Bianco vs Nero')
        
        # Grafico a barre dei risultati per colore
        query = """
            SELECT 
                CASE WHEN white_player = ? THEN 'white' ELSE 'black' END as color,
                CASE 
                    WHEN (white_player = ? AND result = '1-0') OR (black_player = ? AND result = '0-1') THEN 'win'
                    WHEN (white_player = ? AND result = '0-1') OR (black_player = ? AND result = '1-0') THEN 'loss'
                    ELSE 'draw'
                END as outcome,
                COUNT(*) as count
            FROM games
            WHERE white_player = ? OR black_player = ?
            GROUP BY color, outcome
        """
        
        df = pd.read_sql_query(query, self.conn, params=[self.player_name]*7)
        
        # Pivot dei dati per il grafico a barre
        pivot_df = df.pivot(index='color', columns='outcome', values='count').fillna(0)
        if 'win' not in pivot_df:
            pivot_df['win'] = 0
        if 'loss' not in pivot_df:
            pivot_df['loss'] = 0
        if 'draw' not in pivot_df:
            pivot_df['draw'] = 0
            
        # Converto in percentuali
        pivot_df['total'] = pivot_df.sum(axis=1)
        pivot_df['win_pct'] = pivot_df['win'] / pivot_df['total'] * 100
        pivot_df['loss_pct'] = pivot_df['loss'] / pivot_df['total'] * 100
        pivot_df['draw_pct'] = pivot_df['draw'] / pivot_df['total'] * 100
        
        # Preparo i dati per il grafico a barre
        colors = [COLORS['white'], COLORS['black']]
        x = ['Bianco', 'Nero']
        win_pct = pivot_df['win_pct'].values
        loss_pct = pivot_df['loss_pct'].values
        draw_pct = pivot_df['draw_pct'].values
        
        ax2.bar(x, win_pct, color=COLORS['win'], label='Vittorie')
        ax2.bar(x, loss_pct, bottom=win_pct, color=COLORS['loss'], label='Sconfitte')
        ax2.bar(x, draw_pct, bottom=win_pct+loss_pct, color=COLORS['draw'], label='Pareggi')
        
        ax2.set_ylim(0, 100)
        ax2.set_title('Risultati per Colore (%)')
        ax2.legend()
        
        plt.tight_layout()
        plt.show()
    
    def analyze_openings(self) -> None:
        """Analizza le aperture più giocate e le performance."""
        # Aperture più giocate
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
            self.conn, 
            params=[self.player_name] * 8
        )
        
        # Migliori aperture (per win rate)
        query_best = """
            SELECT eco, opening, COUNT(*) as games, 
                   SUM(CASE WHEN 
                         (white_player = ? AND result = '1-0') OR
                         (black_player = ? AND result = '0-1')
                       THEN 1 ELSE 0 END) as wins,
                   ROUND(SUM(CASE WHEN 
                         (white_player = ? AND result = '1-0') OR
                         (black_player = ? AND result = '0-1')
                       THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_percentage
            FROM games
            WHERE (white_player = ? OR black_player = ?) AND eco IS NOT NULL AND eco != ''
            GROUP BY eco, opening
            HAVING COUNT(*) >= 2
            ORDER BY win_percentage DESC, games DESC
            LIMIT 10
        """
        
        df_best = pd.read_sql_query(
            query_best, 
            self.conn, 
            params=[self.player_name] * 6
        )
        
        # Peggiori aperture (per win rate)
        query_worst = """
            SELECT eco, opening, COUNT(*) as games, 
                   SUM(CASE WHEN 
                         (white_player = ? AND result = '1-0') OR
                         (black_player = ? AND result = '0-1')
                       THEN 1 ELSE 0 END) as wins,
                   ROUND(SUM(CASE WHEN 
                         (white_player = ? AND result = '1-0') OR
                         (black_player = ? AND result = '0-1')
                       THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_percentage
            FROM games
            WHERE (white_player = ? OR black_player = ?) AND eco IS NOT NULL AND eco != ''
            GROUP BY eco, opening
            HAVING COUNT(*) >= 2
            ORDER BY win_percentage ASC, games DESC
            LIMIT 10
        """
        
        df_worst = pd.read_sql_query(
            query_worst, 
            self.conn, 
            params=[self.player_name] * 6
        )
        
        # Aperture con il bianco
        query_white = """
            SELECT eco, opening, COUNT(*) as games, 
                   SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) as wins,
                   ROUND(SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_percentage
            FROM games
            WHERE white_player = ? AND eco IS NOT NULL AND eco != ''
            GROUP BY eco, opening
            HAVING COUNT(*) >= 2
            ORDER BY win_percentage DESC, games DESC
            LIMIT 10
        """
        
        df_white = pd.read_sql_query(
            query_white, 
            self.conn, 
            params=[self.player_name]
        )
        
        # Aperture con il nero
        query_black = """
            SELECT eco, opening, COUNT(*) as games, 
                   SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) as wins,
                   ROUND(SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_percentage
            FROM games
            WHERE black_player = ? AND eco IS NOT NULL AND eco != ''
            GROUP BY eco, opening
            HAVING COUNT(*) >= 2
            ORDER BY win_percentage DESC, games DESC
            LIMIT 10
        """
        
        df_black = pd.read_sql_query(
            query_black, 
            self.conn, 
            params=[self.player_name]
        )
        
        # Visualizzazione dei risultati
        print("\n===== ANALISI DELLE APERTURE =====")
        
        print("\n--- APERTURE PIÙ GIOCATE ---")
        if not df_most_played.empty:
            print(tabulate(df_most_played, headers='keys', tablefmt='psql', showindex=False))
        else:
            print("Nessun dato disponibile.")
            
        print("\n--- MIGLIORI APERTURE (PER WIN RATE) ---")
        if not df_best.empty:
            print(tabulate(df_best, headers='keys', tablefmt='psql', showindex=False))
        else:
            print("Nessun dato disponibile.")
            
        print("\n--- PEGGIORI APERTURE (PER WIN RATE) ---")
        if not df_worst.empty:
            print(tabulate(df_worst, headers='keys', tablefmt='psql', showindex=False))
        else:
            print("Nessun dato disponibile.")
            
        print("\n--- MIGLIORI APERTURE CON IL BIANCO ---")
        if not df_white.empty:
            print(tabulate(df_white, headers='keys', tablefmt='psql', showindex=False))
        else:
            print("Nessun dato disponibile.")
            
        print("\n--- MIGLIORI APERTURE CON IL NERO ---")
        if not df_black.empty:
            print(tabulate(df_black, headers='keys', tablefmt='psql', showindex=False))
        else:
            print("Nessun dato disponibile.")
        
        # Grafico aperture più giocate
        if not df_most_played.empty:
            plt.figure(figsize=(12, 7))
            
            # Creiamo etichette personalizzate: ECO + Nome apertura
            labels = [f"{eco} - {opening if not pd.isna(opening) else 'N/A'}" 
                      for eco, opening in zip(df_most_played['eco'], df_most_played['opening'])]
            
            # Abbreviamo le etichette se sono troppo lunghe
            labels = [label[:30] + '...' if len(label) > 30 else label for label in labels]
            
            # Creiamo il grafico con i colori per vittorie, pareggi, sconfitte
            bars = plt.barh(labels, df_most_played['games'], color=COLORS['neutral'])
            
            # Aggiungiamo le percentuali di vittoria
            for i, (bar, win_pct) in enumerate(zip(bars, df_most_played['win_percentage'])):
                plt.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2, 
                         f"{win_pct}% win", va='center', fontsize=10)
            
            plt.xlabel('Numero di partite')
            plt.title('Aperture più giocate')
            plt.tight_layout()
            plt.show()
            
            # Grafico con il confronto win rate delle aperture
            plt.figure(figsize=(12, 7))
            
            # Prepariamo i dati per il grafico a barre impilate
            aperture = labels
            totali = df_most_played['games'].values
            vinte = df_most_played['wins'].values
            pareggiate = df_most_played['draws'].values
            perse = df_most_played['losses'].values
            
            # Calcoliamo le percentuali
            win_pct = vinte / totali * 100
            draw_pct = pareggiate / totali * 100
            loss_pct = perse / totali * 100
            
            plt.barh(aperture, win_pct, color=COLORS['win'], label='Vittorie')
            plt.barh(aperture, draw_pct, left=win_pct, color=COLORS['draw'], label='Pareggi')
            plt.barh(aperture, loss_pct, left=win_pct+draw_pct, color=COLORS['loss'], label='Sconfitte')
            
            # Aggiungiamo le etichette per il numero di partite
            for i, (games, apertura) in enumerate(zip(totali, aperture)):
                plt.text(101, i, f"  ({games} partite)", va='center', fontsize=10)
            
            plt.xlim(0, 100)
            plt.xlabel('Percentuale')
            plt.title('Performance per apertura')
            plt.legend(loc='lower right')
            plt.tight_layout()
            plt.show()
    
    def analyze_opponents(self) -> None:
        """Analizza le performance contro diversi avversari."""
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
            self.conn, 
            params=[self.player_name] * 10
        )
        
        print("\n===== ANALISI DEGLI AVVERSARI =====")
        
        if not df.empty:
            print("\n--- STATISTICHE PER AVVERSARIO ---")
            print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            
            # Creiamo un grafico comparativo
            plt.figure(figsize=(12, 8))
            
            # Abbreviamo i nomi se sono troppo lunghi
            opponents = [opp[:15] + '...' if len(opp) > 15 else opp for opp in df['opponent']]
            games = df['games_played'].values
            win_pct = df['win_percent'].values
            
            # Ordiniamo per win rate
            sorted_idx = win_pct.argsort()
            opponents = [opponents[i] for i in sorted_idx]
            games = games[sorted_idx]
            win_pct = win_pct[sorted_idx]
            
            # Coloriamo le barre in base al win rate
            colors = ['#e74c3c' if wp < 40 else '#f39c12' if wp < 60 else '#2ecc71' for wp in win_pct]
            
            plt.barh(opponents, win_pct, color=colors)
            
            # Aggiungiamo il numero di partite come etichetta
            for i, (pct, game) in enumerate(zip(win_pct, games)):
                plt.text(pct + 1, i, f"  ({game} partite)", va='center')
            
            plt.axvline(x=50, color='gray', linestyle='--', alpha=0.7)
            plt.xlabel('Percentuale di vittorie')
            plt.title('Performance contro gli avversari')
            plt.xlim(0, 110)  # Lasciamo spazio per le etichette
            plt.tight_layout()
            plt.show()
        else:
            print("Nessun dato disponibile.")
    
    def analyze_game_phases(self) -> None:
        """Analizza le performance nelle diverse fasi di gioco."""
        # Creiamo un'analisi della lunghezza delle partite
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
            self.conn, 
            params=[self.player_name] * 8
        )
        
        print("\n===== ANALISI DELLE FASI DI GIOCO =====")
        
        if not df.empty:
            # Ordine corretto delle fasi
            correct_order = ['Apertura (≤10)', 'Mediogioco (11-25)', 'Tardo mediogioco (26-40)', 'Finale (>40)']
            df['fase_partita'] = pd.Categorical(df['fase_partita'], categories=correct_order, ordered=True)
            df = df.sort_values('fase_partita')
            
            print("\n--- PERFORMANCE PER FASE DI GIOCO ---")
            print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            
            # Grafico delle performance per fase
            plt.figure(figsize=(12, 6))
            
            # Prepariamo i dati per il grafico
            fasi = df['fase_partita'].tolist()
            totali = df['num_partite'].values
            vinte = df['vittorie'].values
            pareggiate = df['pareggi'].values
            perse = df['sconfitte'].values
            
            # Creiamo un grafico a barre impilate
            bar_width = 0.6
            
            # Prima serie: vittorie
            bars1 = plt.bar(fasi, vinte, bar_width, label='Vittorie', color=COLORS['win'])
            
            # Seconda serie: pareggi
            bars2 = plt.bar(fasi, pareggiate, bar_width, bottom=vinte, label='Pareggi', color=COLORS['draw'])
            
            # Terza serie: sconfitte
            bars3 = plt.bar(fasi, perse, bar_width, bottom=vinte+pareggiate, label='Sconfitte', color=COLORS['loss'])
            
            # Aggiungiamo le etichette con la percentuale di vittoria
            for i, pct in enumerate(df['perc_vittorie']):
                plt.text(i, totali[i] + 0.5, f"{pct}% win", ha='center', fontsize=9, fontweight='bold')
            
            plt.xlabel('Fase della partita')
            plt.ylabel('Numero di partite')
            plt.title('Performance per fase di gioco')
            plt.legend()
            plt.tight_layout()
            plt.show()
            
            # Grafico percentuale vittorie per fase
            plt.figure(figsize=(10, 6))
            
            # Calcoliamo le percentuali
            win_pct = vinte / totali * 100
            draw_pct = pareggiate / totali * 100
            loss_pct = perse / totali * 100
            
            plt.bar(fasi, win_pct, color=COLORS['win'], label='Vittorie')
            plt.bar(fasi, draw_pct, bottom=win_pct, color=COLORS['draw'], label='Pareggi')
            plt.bar(fasi, loss_pct, bottom=win_pct+draw_pct, color=COLORS['loss'], label='Sconfitte')
            
            # Aggiungiamo le etichette con il numero di partite
            for i, tot in enumerate(totali):
                plt.text(i, 103, f"({tot} partite)", ha='center', fontsize=9)
            
            plt.ylim(0, 110)  # Spazio per le etichette
            plt.xlabel('Fase della partita')
            plt.ylabel('Percentuale')
            plt.title('Distribuzione dei risultati per fase di gioco (%)')
            plt.legend()
            plt.tight_layout()
            plt.show()
        else:
            print("Nessun dato disponibile.")
    
    def analyze_elo_progression(self) -> None:
        """Analizza la progressione dell'Elo nel tempo."""
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
            self.conn, 
            params=[self.player_name] * 7
        )
        
        print("\n===== ANALISI DELL'ELO NEL TEMPO =====")
        
        if not df.empty:
            # Convertiamo la data in formato datetime
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])  # Rimuoviamo le date non valide
            
            # Aggiungiamo una colonna per il mese/anno
            df['month_year'] = df['date'].dt.strftime('%Y-%m')
            
            # Calcolo statistiche mensili
            monthly_stats = df.groupby('month_year').agg({
                'elo': ['mean', 'min', 'max', 'count'],
                'result': lambda x: (x == 'win').sum() / len(x) * 100  # win percentage
            })
            
            monthly_stats.columns = ['avg_elo', 'min_elo', 'max_elo', 'games', 'win_percentage']
            monthly_stats = monthly_stats.reset_index()
            
            # Statistiche globali
            print(f"Elo iniziale: {df['elo'].iloc[0]}")
            print(f"Elo finale: {df['elo'].iloc[-1]}")
            print(f"Variazione: {df['elo'].iloc[-1] - df['elo'].iloc[0]}")
            print(f"Elo minimo: {df['elo'].min()}")
            print(f"Elo massimo: {df['elo'].max()}")
            print(f"Media: {df['elo'].mean():.1f}")
            
            # Grafico dell'Elo nel tempo
            plt.figure(figsize=(12, 6))
            
            # Colori dei punti in base al risultato
            colors = {
                'win': COLORS['win'], 
                'loss': COLORS['loss'], 
                'draw': COLORS['draw']
            }
            
            # Grafico a dispersione con colori per i risultati
            for result, color in colors.items():
                mask = df['result'] == result
                plt.scatter(df.loc[mask, 'date'], df.loc[mask, 'elo'], 
                           c=color, label=result, alpha=0.7, s=30)
            
            # Linea di tendenza
            plt.plot(df['date'], df['elo'], color='black', alpha=0.3, linestyle='-')
            
            # Grafico più leggibile
            plt.xlabel('Data')
            plt.ylabel('Elo')
            plt.title('Progressione dell\'Elo nel tempo')
            plt.legend(title='Risultato')
            plt.grid(True, alpha=0.3)
            
            # Formattazione dell'asse x per date
            plt.gcf().autofmt_xdate()
            
            plt.tight_layout()
            plt.show()
            
            # Grafico Elo medio mensile con win rate
            plt.figure(figsize=(12, 6))
            
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            # Convertiamo month_year in datetime per il grafico
            monthly_stats['date'] = pd.to_datetime(monthly_stats['month_year'], format='%Y-%m')
            
            # Primo asse: Elo medio
            color = 'tab:blue'
            ax1.set_xlabel('Data')
            ax1.set_ylabel('Elo medio', color=color)
            ax1.plot(monthly_stats['date'], monthly_stats['avg_elo'], color=color, marker='o')
            ax1.tick_params(axis='y', labelcolor=color)
            
            # Secondo asse: percentuale vittorie
            ax2 = ax1.twinx()
            color = 'tab:red'
            ax2.set_ylabel('Win rate (%)', color=color)
            ax2.plot(monthly_stats['date'], monthly_stats['win_percentage'], color=color, marker='s', linestyle='--')
            ax2.tick_params(axis='y', labelcolor=color)
            
            # Aggiungiamo il numero di partite per mese come etichetta
            for i, row in monthly_stats.iterrows():
                ax1.annotate(f"{int(row['games'])}", 
                             (row['date'], row['avg_elo']),
                             textcoords="offset points",
                             xytext=(0,10),
                             ha='center',
                             fontsize=8)
            
            plt.title('Elo medio mensile e percentuale di vittorie')
            plt.grid(True, alpha=0.3)
            fig.autofmt_xdate()
            fig.tight_layout()
            plt.show()
        else:
            print("Nessun dato disponibile.")
    
    def analyze_frequent_mistakes(self) -> None:
        """Analizza gli errori comuni nelle partite."""
        # Questa è un'analisi avanzata che richiederebbe l'integrazione con un motore di scacchi
        # Come approssimazione, analizziamo le partite perse rapidamente
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
            LIMIT 15
        """
        
        df = pd.read_sql_query(
            query, 
            self.conn, 
            params=[self.player_name] * 4
        )
        
        print("\n===== ANALISI DELLE SCONFITTE RAPIDE =====")
        
        if not df.empty:
            # Aggiungiamo una colonna per il colore
            df['color'] = ['Bianco' if p == self.player_name else 'Nero' for p in df['white_player']]
            
            # Aggiungiamo una colonna per l'avversario
            df['opponent'] = [black if white == self.player_name else white 
                              for white, black in zip(df['white_player'], df['black_player'])]
            
            # Selezioniamo solo le colonne rilevanti
            df_display = df[['color', 'opponent', 'eco', 'opening', 'moves_count']]
            df_display = df_display.rename(columns={
                'color': 'Colore', 
                'opponent': 'Avversario', 
                'eco': 'ECO', 
                'opening': 'Apertura', 
                'moves_count': 'Mosse'
            })
            
            print("\n--- PARTITE PERSE RAPIDAMENTE (<= 25 mosse) ---")
            print(tabulate(df_display, headers='keys', tablefmt='psql', showindex=False))
            
            # Analisi per apertura
            print("\n--- APERTURE PROBLEMATICHE (SCONFITTE RAPIDE) ---")
            eco_counts = df['eco'].value_counts().reset_index()
            eco_counts.columns = ['ECO', 'Frequenza']
            
            # Aggiungiamo il nome dell'apertura
            eco_names = {}
            for eco, opening in zip(df['eco'], df['opening']):
                if eco not in eco_names and not pd.isna(eco):
                    eco_names[eco] = opening
            
            eco_counts['Apertura'] = eco_counts['ECO'].map(lambda x: eco_names.get(x, 'Sconosciuta'))
            
            if not eco_counts.empty:
                print(tabulate(eco_counts.head(10), headers='keys', tablefmt='psql', showindex=False))
            else:
                print("Nessun dato disponibile.")
            
            # Grafico della distribuzione delle mosse nelle sconfitte rapide
            plt.figure(figsize=(10, 6))
            
            plt.hist(df['moves_count'], bins=range(5, 26, 2), color=COLORS['loss'], alpha=0.7, 
                     edgecolor='black', linewidth=1.2)
            
            plt.xlabel('Numero di mosse')
            plt.ylabel('Frequenza')
            plt.title('Distribuzione delle sconfitte rapide per numero di mosse')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
        else:
            print("Nessun dato disponibile.")
    
    def analyze_performance_by_eco(self) -> None:
        """Analizza le performance per categoria ECO."""
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
            self.conn, 
            params=[self.player_name] * 8
        )
        
        print("\n===== ANALISI PER CATEGORIA ECO =====")
        
        if not df.empty:
            # Aggiungiamo una descrizione per ogni categoria ECO
            eco_descriptions = {
                'A': 'Aperture di Fianchetto (1.c4, 1.Nf3, etc.)',
                'B': 'Aperture Semiaperte (1.e4 eccetto 1...e5)',
                'C': 'Aperture Aperte (1.e4 e5)',
                'D': 'Aperture Chiuse (1.d4 d5)',
                'E': 'Difese Indiane (1.d4 Nf6 eccetto 2.c4 e5)'
            }
            
            df['descrizione'] = df['eco_category'].map(lambda x: eco_descriptions.get(x, 'Sconosciuta'))
            
            print("\n--- PERFORMANCE PER CATEGORIA ECO ---")
            print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
            
            # Grafico della performance per categoria ECO
            plt.figure(figsize=(12, 6))
            
            # Dati per il grafico
            categories = df['eco_category'].tolist()
            win_pct = df['win_percentage'].values
            games = df['games'].values
            
            # Creiamo un grafico a barre con colori basati sul win rate
            colors = ['#e74c3c' if wp < 40 else '#f39c12' if wp < 60 else '#2ecc71' for wp in win_pct]
            
            bars = plt.bar(categories, win_pct, color=colors)
            
            # Aggiungiamo le etichette con le descrizioni e il numero di partite
            for i, (cat, desc, game) in enumerate(zip(categories, df['descrizione'], games)):
                plt.text(i, win_pct[i] + 2, f"{desc}", ha='center', fontsize=9, rotation=0)
                plt.text(i, win_pct[i] + 7, f"({game} partite)", ha='center', fontsize=8)
            
            plt.axhline(y=50, color='gray', linestyle='--', alpha=0.7)
            plt.xlabel('Categoria ECO')
            plt.ylabel('Percentuale di vittorie')
            plt.title('Performance per categoria ECO')
            plt.ylim(0, 100)
            plt.tight_layout()
            plt.show()
            
            # Grafico della distribuzione delle partite per categoria ECO
            plt.figure(figsize=(10, 6))
            
            # Creiamo un grafico a torta
            labels = [f"{cat} - {desc} ({game} partite)" 
                     for cat, desc, game in zip(categories, df['descrizione'], games)]
            
            plt.pie(games, labels=labels, autopct='%1.1f%%', startangle=90,
                   colors=plt.cm.tab10.colors, wedgeprops={'linewidth': 1, 'edgecolor': 'white'})
            
            plt.axis('equal')
            plt.title('Distribuzione delle partite per categoria ECO')
            plt.tight_layout()
            plt.show()
        else:
            print("Nessun dato disponibile.")
    
    def export_data(self, query: str, filename: str) -> None:
        """Esporta i dati di una query in un file CSV.
        
        Args:
            query: Query SQL da eseguire
            filename: Nome del file CSV di output
        """
        try:
            df = pd.read_sql_query(query, self.conn)
            df.to_csv(filename, index=False)
            print(f"Dati esportati con successo in '{filename}'")
        except Exception as e:
            print(f"Errore durante l'esportazione dei dati: {e}")
    
    def run_analysis(self) -> None:
        """Esegue tutte le analisi disponibili."""
        self.display_basic_stats()
        self.analyze_openings()
        self.analyze_opponents()
        self.analyze_game_phases()
        self.analyze_elo_progression()
        self.analyze_frequent_mistakes()
        self.analyze_performance_by_eco()


    def export_all_to_csv(self, filename: str = 'chess_analysis.csv') -> None:
        """Esporta tutte le analisi in un unico file CSV strutturato.
        
        Args:
            filename: Nome del file CSV di output
        """
       
        try:
            # Crea la cartella analysis se non esiste
            analysis_dir = os.path.join(os.getcwd(), "analysis")
            if not os.path.exists(analysis_dir):
                os.makedirs(analysis_dir)
                print(f"\nCreata directory 'analysis' per i file di output")
        
            # Costruisci il percorso completo
            if not os.path.isabs(filename):
                filename = os.path.join(analysis_dir, filename)
                print(f"\nEsportazione di tutte le analisi in '{filename}'...")
            
            # Lista per contenere tutti i dataframes da esportare
            all_dfs = []
            
            # ---------- STATISTICHE DI BASE ----------
            stats = self.get_basic_stats()
            basic_df = pd.DataFrame({
                'Metrica': [
                    'Totale partite', 'Partite con il bianco', 'Partite con il nero',
                    'Vittorie', 'Sconfitte', 'Pareggi', 'Percentuale vittorie',
                    'Percentuale sconfitte', 'Percentuale pareggi',
                    'Lunghezza media partite', 'Elo medio giocatore', 'Elo medio avversari'
                ],
                'Valore': [
                    stats['total_games'], stats['white_games'], stats['black_games'],
                    stats['wins'], stats['losses'], stats['draws'],
                    f"{stats['win_percentage']}%", f"{stats['loss_percentage']}%", f"{stats['draw_percentage']}%",
                    f"{stats['avg_game_length']} mosse", stats['avg_player_elo'], stats['avg_opponent_elo']
                ]
            })
            all_dfs.append(('STATISTICHE DI BASE', basic_df))
            
            # ---------- ANALISI APERTURE ----------
            # Aperture più giocate
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
                ORDER BY games DESC
            """
            
            df_most_played = pd.read_sql_query(
                query_most_played, 
                self.conn, 
                params=[self.player_name] * 8
            )
            df_most_played.columns = ['ECO', 'Apertura', 'Partite', 'Vittorie', 'Pareggi', 'Sconfitte', 'Percentuale_Vittorie']
            all_dfs.append(('APERTURE PIÙ GIOCATE', df_most_played))
            
            # Aperture con bianco
            query_white = """
                SELECT eco, opening, COUNT(*) as games, 
                    SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as draws,
                    SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) as losses,
                    ROUND(SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_percentage
                FROM games
                WHERE white_player = ? AND eco IS NOT NULL AND eco != ''
                GROUP BY eco, opening
                ORDER BY win_percentage DESC, games DESC
            """
            
            df_white = pd.read_sql_query(
                query_white, 
                self.conn, 
                params=[self.player_name]
            )
            df_white.columns = ['ECO', 'Apertura', 'Partite', 'Vittorie', 'Pareggi', 'Sconfitte', 'Percentuale_Vittorie']
            all_dfs.append(('APERTURE CON IL BIANCO', df_white))
            
            # Aperture con nero
            query_black = """
                SELECT eco, opening, COUNT(*) as games, 
                    SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as draws,
                    SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) as losses,
                    ROUND(SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_percentage
                FROM games
                WHERE black_player = ? AND eco IS NOT NULL AND eco != ''
                GROUP BY eco, opening
                ORDER BY win_percentage DESC, games DESC
            """
            
            df_black = pd.read_sql_query(
                query_black, 
                self.conn, 
                params=[self.player_name]
            )
            df_black.columns = ['ECO', 'Apertura', 'Partite', 'Vittorie', 'Pareggi', 'Sconfitte', 'Percentuale_Vittorie']
            all_dfs.append(('APERTURE CON IL NERO', df_black))
            
            # ---------- ANALISI AVVERSARI ----------
            query_opponents = """
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
                ORDER BY games_played DESC
            """
            
            df_opponents = pd.read_sql_query(
                query_opponents, 
                self.conn, 
                params=[self.player_name] * 10
            )
            df_opponents.columns = ['Avversario', 'Partite_Giocate', 'Vittorie', 'Pareggi', 'Sconfitte', 'Percentuale_Vittorie', 'Elo_Medio_Avversario']
            all_dfs.append(('ANALISI AVVERSARI', df_opponents))
            
            # ---------- ANALISI FASI DI GIOCO ----------
            query_phases = """
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
            
            df_phases = pd.read_sql_query(
                query_phases, 
                self.conn, 
                params=[self.player_name] * 8
            )
            df_phases.columns = ['Fase_Partita', 'Partite', 'Vittorie', 'Pareggi', 'Sconfitte', 'Percentuale_Vittorie']
            
            # Ordine corretto delle fasi
            correct_order = ['Apertura (≤10)', 'Mediogioco (11-25)', 'Tardo mediogioco (26-40)', 'Finale (>40)']
            df_phases['Fase_Partita'] = pd.Categorical(df_phases['Fase_Partita'], categories=correct_order, ordered=True)
            df_phases = df_phases.sort_values('Fase_Partita')
            
            all_dfs.append(('ANALISI FASI DI GIOCO', df_phases))
            
            # ---------- ANALISI ELO ----------
            query_elo = """
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
            
            df_elo = pd.read_sql_query(
                query_elo, 
                self.conn, 
                params=[self.player_name] * 7
            )
            df_elo.columns = ['Data', 'Elo', 'Risultato']
            
            # Statistiche mensili dell'Elo
            df_elo['Data'] = pd.to_datetime(df_elo['Data'], errors='coerce')
            df_elo = df_elo.dropna(subset=['Data'])
            df_elo['Mese_Anno'] = df_elo['Data'].dt.strftime('%Y-%m')
            
            elo_stats = df_elo.groupby('Mese_Anno').agg({
                'Elo': ['mean', 'min', 'max', 'count'],
                'Risultato': lambda x: (x == 'win').sum() / len(x) * 100
            })
            
            elo_stats.columns = ['Elo_Medio', 'Elo_Minimo', 'Elo_Massimo', 'Partite', 'Percentuale_Vittorie']
            elo_stats = elo_stats.reset_index()
            
            all_dfs.append(('ELO MENSILE', elo_stats))
            
            # ---------- ANALISI CATEGORIE ECO ----------
            query_eco = """
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
            
            df_eco = pd.read_sql_query(
                query_eco, 
                self.conn, 
                params=[self.player_name] * 8
            )
            
            # Aggiungiamo una descrizione per ogni categoria ECO
            eco_descriptions = {
                'A': 'Aperture di Fianchetto (1.c4, 1.Nf3, etc.)',
                'B': 'Aperture Semiaperte (1.e4 eccetto 1...e5)',
                'C': 'Aperture Aperte (1.e4 e5)',
                'D': 'Aperture Chiuse (1.d4 d5)',
                'E': 'Difese Indiane (1.d4 Nf6 eccetto 2.c4 e5)'
            }
            
            df_eco['descrizione'] = df_eco['eco_category'].map(lambda x: eco_descriptions.get(x, 'Sconosciuta'))
            df_eco.columns = ['Categoria_ECO', 'Partite', 'Vittorie', 'Pareggi', 'Sconfitte', 'Percentuale_Vittorie', 'Descrizione']
            
            all_dfs.append(('ANALISI CATEGORIE ECO', df_eco))
            
            # ---------- ESPORTAZIONE IN CSV ----------
            with open(filename, 'w', newline='') as f:
                for title, df in all_dfs:
                    # Scriviamo un'intestazione per ogni sezione
                    f.write(f"\n\n{title}\n")
                    # Scriviamo il dataframe
                    df.to_csv(f, index=False)
                    # Aggiungiamo una riga vuota dopo ogni sezione
                    f.write("\n")
            
            print(f"Analisi esportate con successo in '{filename}'")
            
        except Exception as e:
            print(f"Errore durante l'esportazione: {e}")

    def export_analysis_to_text(self, filename: str = 'chess_analysis.txt') -> None:
        """Esporta tutti i risultati delle analisi in un file di testo formattato.
        
        Questa funzione genera un rapporto di testo formattato con tutte le analisi,
        ottimizzato per essere visualizzato correttamente in qualsiasi editor di testo.
        
        Args:
            filename: Nome del file di testo di output
        """


        try:
            # Crea la cartella analysis se non esiste
            analysis_dir = os.path.join(os.getcwd(), "analysis")
            if not os.path.exists(analysis_dir):
                os.makedirs(analysis_dir)
                print(f"\nCreata directory 'analysis' per i file di output")
            
            # Costruisci il percorso completo
            if not os.path.isabs(filename):
                filename = os.path.join(analysis_dir, filename)
        
            # Impostiamo un formato tabella ottimizzato per il testo
            formato_tabella = 'grid'  # Alternative: 'simple', 'plain', 'github'
            
            # Creiamo un buffer di testo per costruire l'output
            output_testo = []
            
            # Aggiungiamo un'intestazione
            output_testo.append(f"RAPPORTO DI ANALISI SCACCHISTICA PER: {self.player_name}")
            output_testo.append("=" * 50)
            output_testo.append(f"Generato il: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
            output_testo.append("=" * 50)
            output_testo.append("\n")
            
            # Funzione per formattare un dataframe come tabella di testo
            def formatta_dataframe(df, titolo):
                risultato = []
                risultato.append(f"\n{titolo}")
                risultato.append("-" * len(titolo))
                if df.empty:
                    risultato.append("Nessun dato disponibile.")
                else:
                    # Utilizziamo tabulate con un formato adatto ai file di testo
                    risultato.append(tabulate(df, headers='keys', tablefmt=formato_tabella, showindex=False))
                return "\n".join(risultato)
            
            # ----- STATISTICHE DI BASE -----
            output_testo.append("STATISTICHE DI BASE")
            output_testo.append("=" * 30)
            
            stats = self.get_basic_stats()
            testo_stats_base = [
                f"Partite totali: {stats['total_games']}",
                f"Partite con il Bianco: {stats['white_games']} ({round(stats['white_games']/stats['total_games']*100 if stats['total_games'] > 0 else 0, 1)}%)",
                f"Partite con il Nero: {stats['black_games']} ({round(stats['black_games']/stats['total_games']*100 if stats['total_games'] > 0 else 0, 1)}%)",
                f"Vittorie: {stats['wins']} ({stats['win_percentage']}%)",
                f"Sconfitte: {stats['losses']} ({stats['loss_percentage']}%)",
                f"Pareggi: {stats['draws']} ({stats['draw_percentage']}%)",
                f"Lunghezza media partite: {stats['avg_game_length']} mosse",
                f"Elo medio del giocatore: {stats['avg_player_elo']}",
                f"Elo medio degli avversari: {stats['avg_opponent_elo']}"
            ]
            output_testo.append("\n".join(testo_stats_base))
            
            # ----- ANALISI DELLE APERTURE -----
            output_testo.append("\n\nANALISI DELLE APERTURE")
            output_testo.append("=" * 30)
            
            # Aperture più giocate
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
                LIMIT 20
            """
            df_most_played = pd.read_sql_query(query_most_played, self.conn, params=[self.player_name] * 8)
            df_most_played.columns = ['ECO', 'Apertura', 'Partite', 'Vittorie', 'Pareggi', 'Sconfitte', 'Percentuale_Vittorie']
            output_testo.append(formatta_dataframe(df_most_played, "APERTURE PIÙ GIOCATE"))
            
            # Migliori aperture (per tasso di vittoria)
            query_best = """
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
                ORDER BY win_percentage DESC, games DESC
                LIMIT 10
            """
            df_best = pd.read_sql_query(query_best, self.conn, params=[self.player_name] * 8)
            df_best.columns = ['ECO', 'Apertura', 'Partite', 'Vittorie', 'Pareggi', 'Sconfitte', 'Percentuale_Vittorie']
            output_testo.append(formatta_dataframe(df_best, "MIGLIORI APERTURE (PER TASSO DI VITTORIA)"))
            
            # Peggiori aperture (per tasso di vittoria)
            query_worst = """
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
                ORDER BY win_percentage ASC, games DESC
                LIMIT 10
            """
            df_worst = pd.read_sql_query(query_worst, self.conn, params=[self.player_name] * 8)
            df_worst.columns = ['ECO', 'Apertura', 'Partite', 'Vittorie', 'Pareggi', 'Sconfitte', 'Percentuale_Vittorie']
            output_testo.append(formatta_dataframe(df_worst, "PEGGIORI APERTURE (PER TASSO DI VITTORIA)"))
            
            # Aperture con il bianco
            query_white = """
                SELECT eco, opening, COUNT(*) as games, 
                    SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as draws,
                    SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) as losses,
                    ROUND(SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_percentage
                FROM games
                WHERE white_player = ? AND eco IS NOT NULL AND eco != ''
                GROUP BY eco, opening
                HAVING COUNT(*) >= 2
                ORDER BY win_percentage DESC, games DESC
                LIMIT 10
            """
            df_white = pd.read_sql_query(query_white, self.conn, params=[self.player_name])
            df_white.columns = ['ECO', 'Apertura', 'Partite', 'Vittorie', 'Pareggi', 'Sconfitte', 'Percentuale_Vittorie']
            output_testo.append(formatta_dataframe(df_white, "MIGLIORI APERTURE CON IL BIANCO"))
            
            # Aperture con il nero
            query_black = """
                SELECT eco, opening, COUNT(*) as games, 
                    SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as draws,
                    SUM(CASE WHEN result = '1-0' THEN 1 ELSE 0 END) as losses,
                    ROUND(SUM(CASE WHEN result = '0-1' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_percentage
                FROM games
                WHERE black_player = ? AND eco IS NOT NULL AND eco != ''
                GROUP BY eco, opening
                HAVING COUNT(*) >= 2
                ORDER BY win_percentage DESC, games DESC
                LIMIT 10
            """
            df_black = pd.read_sql_query(query_black, self.conn, params=[self.player_name])
            df_black.columns = ['ECO', 'Apertura', 'Partite', 'Vittorie', 'Pareggi', 'Sconfitte', 'Percentuale_Vittorie']
            output_testo.append(formatta_dataframe(df_black, "MIGLIORI APERTURE CON IL NERO"))
            
            # ----- ANALISI DEGLI AVVERSARI -----
            output_testo.append("\n\nANALISI DEGLI AVVERSARI")
            output_testo.append("=" * 30)
            
            query_opponents = """
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
                ORDER BY games_played DESC
                LIMIT 15
            """
            df_opponents = pd.read_sql_query(query_opponents, self.conn, params=[self.player_name] * 10)
            df_opponents.columns = ['Avversario', 'Partite_Giocate', 'Vittorie', 'Pareggi', 'Sconfitte', 'Percentuale_Vittorie', 'Elo_Medio_Avversario']
            output_testo.append(formatta_dataframe(df_opponents, "PERFORMANCE CONTRO GLI AVVERSARI"))
            
            # ----- ANALISI DELLE FASI DI GIOCO -----
            output_testo.append("\n\nANALISI DELLE FASI DI GIOCO")
            output_testo.append("=" * 30)
            
            query_phases = """
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
            df_phases = pd.read_sql_query(query_phases, self.conn, params=[self.player_name] * 8)
            df_phases.columns = ['Fase_Partita', 'Partite', 'Vittorie', 'Pareggi', 'Sconfitte', 'Percentuale_Vittorie']
            
            # Ordine corretto delle fasi
            correct_order = ['Apertura (≤10)', 'Mediogioco (11-25)', 'Tardo mediogioco (26-40)', 'Finale (>40)']
            df_phases['Fase_Partita'] = pd.Categorical(df_phases['Fase_Partita'], categories=correct_order, ordered=True)
            df_phases = df_phases.sort_values('Fase_Partita')
            
            output_testo.append(formatta_dataframe(df_phases, "PERFORMANCE PER FASE DI GIOCO"))
            
            # ----- ANALISI DELL'ELO -----
            output_testo.append("\n\nANALISI DELL'ELO")
            output_testo.append("=" * 30)
            
            query_elo = """
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
            
            df_elo = pd.read_sql_query(query_elo, self.conn, params=[self.player_name] * 7)
            
            if not df_elo.empty:
                # Convertiamo la data in formato datetime
                df_elo['date'] = pd.to_datetime(df_elo['date'], errors='coerce')
                df_elo = df_elo.dropna(subset=['date'])  # Rimuoviamo le date non valide
                
                # Aggiungiamo una colonna per il mese/anno
                df_elo['month_year'] = df_elo['date'].dt.strftime('%Y-%m')
                
                # Calcolo statistiche mensili
                monthly_stats = df_elo.groupby('month_year').agg({
                    'elo': ['mean', 'min', 'max', 'count'],
                    'result': lambda x: (x == 'win').sum() / len(x) * 100  # win percentage
                })
                
                monthly_stats.columns = ['Elo_Medio', 'Elo_Minimo', 'Elo_Massimo', 'Partite', 'Percentuale_Vittorie']
                monthly_stats = monthly_stats.reset_index()
                monthly_stats.rename(columns={'month_year': 'Mese_Anno'}, inplace=True)
                
                output_testo.append("\nSTATISTICHE GENERALI DELL'ELO")
                output_testo.append("-" * 30)
                output_testo.append(f"Elo iniziale: {df_elo['elo'].iloc[0]}")
                output_testo.append(f"Elo finale: {df_elo['elo'].iloc[-1]}")
                output_testo.append(f"Variazione: {df_elo['elo'].iloc[-1] - df_elo['elo'].iloc[0]}")
                output_testo.append(f"Elo minimo: {df_elo['elo'].min()}")
                output_testo.append(f"Elo massimo: {df_elo['elo'].max()}")
                output_testo.append(f"Media: {df_elo['elo'].mean():.1f}")
                
                output_testo.append(formatta_dataframe(monthly_stats, "\nELO MENSILE"))
            else:
                output_testo.append("\nNessun dato Elo disponibile.")
            
            # ----- ANALISI DEGLI ERRORI FREQUENTI -----
            output_testo.append("\n\nANALISI DELLE SCONFITTE RAPIDE")
            output_testo.append("=" * 30)
            
            query_losses = """
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
                LIMIT 15
            """
            
            df_losses = pd.read_sql_query(query_losses, self.conn, params=[self.player_name] * 4)
            
            if not df_losses.empty:
                # Aggiungiamo una colonna per il colore
                df_losses['color'] = ['Bianco' if p == self.player_name else 'Nero' for p in df_losses['white_player']]
                
                # Aggiungiamo una colonna per l'avversario
                df_losses['opponent'] = [black if white == self.player_name else white 
                                for white, black in zip(df_losses['white_player'], df_losses['black_player'])]
                
                # Selezioniamo solo le colonne rilevanti
                df_display = df_losses[['color', 'opponent', 'eco', 'opening', 'moves_count']]
                df_display.columns = ['Colore', 'Avversario', 'ECO', 'Apertura', 'Mosse']
                
                output_testo.append("\nPARTITE PERSE RAPIDAMENTE (<= 25 mosse)")
                output_testo.append("-" * 50)
                output_testo.append(tabulate(df_display, headers='keys', tablefmt=formato_tabella, showindex=False))
                
                # Analisi per apertura
                output_testo.append("\nAPERTURE PROBLEMATICHE (SCONFITTE RAPIDE)")
                output_testo.append("-" * 50)
                
                eco_counts = df_losses['eco'].value_counts().reset_index()
                eco_counts.columns = ['ECO', 'Frequenza']
                
                # Aggiungiamo il nome dell'apertura
                eco_names = {}
                for eco, opening in zip(df_losses['eco'], df_losses['opening']):
                    if eco not in eco_names and not pd.isna(eco):
                        eco_names[eco] = opening
                
                eco_counts['Apertura'] = eco_counts['ECO'].map(lambda x: eco_names.get(x, 'Sconosciuta'))
                
                if not eco_counts.empty:
                    output_testo.append(tabulate(eco_counts.head(10), headers='keys', tablefmt=formato_tabella, showindex=False))
                else:
                    output_testo.append("Nessun dato disponibile.")
            else:
                output_testo.append("Nessuna sconfitta rapida trovata.")
            
            # ----- ANALISI PER CATEGORIA ECO -----
            output_testo.append("\n\nANALISI PER CATEGORIA ECO")
            output_testo.append("=" * 30)
            
            query_eco = """
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
            
            df_eco = pd.read_sql_query(query_eco, self.conn, params=[self.player_name] * 8)
            
            if not df_eco.empty:
                # Aggiungiamo una descrizione per ogni categoria ECO
                eco_descriptions = {
                    'A': 'Aperture di Fianchetto (1.c4, 1.Nf3, etc.)',
                    'B': 'Aperture Semiaperte (1.e4 eccetto 1...e5)',
                    'C': 'Aperture Aperte (1.e4 e5)',
                    'D': 'Aperture Chiuse (1.d4 d5)',
                    'E': 'Difese Indiane (1.d4 Nf6 eccetto 2.c4 e5)'
                }
                
                df_eco['descrizione'] = df_eco['eco_category'].map(lambda x: eco_descriptions.get(x, 'Sconosciuta'))
                df_eco.columns = ['Categoria_ECO', 'Partite', 'Vittorie', 'Pareggi', 'Sconfitte', 'Percentuale_Vittorie', 'Descrizione']
                
                output_testo.append(formatta_dataframe(df_eco, "PERFORMANCE PER CATEGORIA ECO"))
                
                # Spiegazione delle categorie ECO
                output_testo.append("\nSPIEGAZIONE DELLE CATEGORIE ECO:")
                output_testo.append("-" * 30)
                output_testo.append("L'ECO (Encyclopedia of Chess Openings) è un sistema di classificazione standardizzato")
                output_testo.append("per le aperture di scacchi. Le categorie principali sono:")
                output_testo.append("A - Aperture di Fianchetto: Aperture che iniziano con 1.c4, 1.Nf3, etc.")
                output_testo.append("B - Aperture Semiaperte: Iniziano con 1.e4, ma la risposta nera non è 1...e5")
                output_testo.append("C - Aperture Aperte: Iniziano con 1.e4 e5")
                output_testo.append("D - Aperture Chiuse: Principalmente quelle che iniziano con 1.d4 d5")
                output_testo.append("E - Difese Indiane: Principalmente quelle che iniziano con 1.d4 Nf6")
            else:
                output_testo.append("Nessun dato ECO disponibile.")
            
            # ----- CONCLUSIONE -----
            output_testo.append("\n\nANALISI COMPLETATA")
            output_testo.append("=" * 30)
            output_testo.append("Questo rapporto è stato generato automaticamente dal ChessAnalyzer.")
            output_testo.append(f"Utilizza queste informazioni per migliorare il tuo gioco!")
            
            # Scriviamo l'output completo nel file di testo
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("\n".join(output_testo))
                
            print(f"Analisi esportata con successo in '{filename}'")
            
        except Exception as e:
            print(f"Errore durante l'esportazione in testo: {e}")

def show_interactive_menu(args_parser):
    """
    Mostra un menu interattivo per selezionare le operazioni da eseguire.
    
    Args:
        args_parser: L'oggetto parser degli argomenti, usato per costruire il comando finale
        
    Returns:
        argparse.Namespace: Un oggetto contenente gli argomenti come se fossero stati passati da riga di comando
    """
    
    # Funzione di utilità per pulire lo schermo
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')
    
    # Funzione per stampare titoli formattati
    def print_title(title):
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)
    
    # Funzione per stampare menu con opzioni numerate
    def print_menu(options):
        for idx, option in enumerate(options, 1):
            print(f"  {idx}. {option}")
        print("  0. Esci")
    
    # Funzione per ottenere input sicuro
    def get_safe_input(prompt, valid_range=None):
        while True:
            try:
                choice = input(prompt)
                if choice.lower() in ['q', 'quit', 'exit']:
                    return 0
                choice = int(choice)
                
                if valid_range is None or choice in valid_range:
                    return choice
                else:
                    print(f"⚠️  Scelta non valida. Inserisci un numero tra {min(valid_range)} e {max(valid_range)} o 0 per uscire.")
            except ValueError:
                print("⚠️  Inserisci un numero valido.")
    
    # Costruiamo un oggetto per tenere traccia delle scelte dell'utente
    selected_args = {}
    
    # Ciclo principale del menu
    while True:
        clear_screen()
        print_title("ChessMetrics Pro - Menu Interattivo")
        print("\nVersione: 0.2.0-alpha")
        print("❗ Attenzione: Software in fase alpha - Utilizzare a proprio rischio\n")
        
        print("OPERAZIONI DISPONIBILI:")
        operations = [
            "Importa file PGN nel database",
            "Analizza le partite",
            "Esporta analisi in CSV",
            "Esporta analisi in file di testo",
            "Visualizza statistiche rapide",
            "Configura impostazioni"
        ]
        print_menu(operations)
        
        choice = get_safe_input("\nScegli un'operazione (0 per uscire): ", range(len(operations) + 1))
        
        if choice == 0:
            print("\nUscita dal programma...")
            return None  # Indica che l'utente vuole uscire
            
        # Menu per importazione PGN
        elif choice == 1:
            clear_screen()
            print_title("Importazione File PGN")
            
            # Ottieni cartella PGN
            pgn_folder = input("\nInserisci il percorso della cartella PGN [pgn_files]: ").strip()
            if not pgn_folder:
                pgn_folder = "pgn_files"
            selected_args['pgn_folder'] = pgn_folder
            
            # Ottieni percorso database
            db_path = input("\nInserisci il percorso del database [chess_games.db]: ").strip()
            if not db_path:
                db_path = "chess_games.db"
            selected_args['db_path'] = db_path
            
            # Chiedi per la reimportazione
            force_reimport = input("\nForzare la reimportazione dei file già elaborati? [s/N]: ").strip().lower()
            selected_args['force_reimport'] = force_reimport in ['s', 'si', 'sì', 'y', 'yes']
            
            # Chiedi dimensione batch
            batch_size = input("\nDimensione del batch per l'importazione [100]: ").strip()
            if batch_size and batch_size.isdigit():
                selected_args['batch_size'] = int(batch_size)
            else:
                selected_args['batch_size'] = 100
                
            # Esegui l'importazione
            print("\nAvvio importazione...")
            return argparse.Namespace(**selected_args, analysis=None, export_csv=False, export_text=False, stats=True)
            
        # Menu per analisi partite
        elif choice == 2:
            clear_screen()
            print_title("Analisi delle Partite")
            
            # Ottieni il nome del giocatore
            player = input("\nInserisci il nome del giocatore da analizzare [Blackeyes972]: ").strip()
            if not player:
                player = "Blackeyes972"
            selected_args['player'] = player
            
            # Ottieni il tipo di analisi
            print("\nTipi di analisi disponibili:")
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
            print_menu(analysis_types)
            
            analysis_choice = get_safe_input("\nScegli un tipo di analisi (0 per tornare al menu principale): ", 
                                            range(len(analysis_types) + 1))
            
            if analysis_choice == 0:
                continue
                
            analysis_map = {
                1: "all",
                2: "basic",
                3: "openings",
                4: "opponents",
                5: "phases",
                6: "elo",
                7: "mistakes",
                8: "eco"
            }
            
            selected_args['analysis'] = analysis_map[analysis_choice]
            selected_args['export_csv'] = False
            selected_args['export_text'] = False
            
            # Ottieni percorso database
            db_path = input("\nInserisci il percorso del database [chess_games.db]: ").strip()
            if not db_path:
                db_path = "chess_games.db"
            selected_args['db_path'] = db_path
            
            # Esegui l'analisi
            print("\nAvvio analisi...")
            return argparse.Namespace(**selected_args)
            
        # Menu per esportazione CSV
        elif choice == 3:
            clear_screen()
            print_title("Esportazione Analisi in CSV")
            
            # Ottieni il nome del giocatore
            player = input("\nInserisci il nome del giocatore da analizzare [Blackeyes972]: ").strip()
            if not player:
                player = "Blackeyes972"
            selected_args['player'] = player
            
            # Ottieni percorso database
            db_path = input("\nInserisci il percorso del database [chess_games.db]: ").strip()
            if not db_path:
                db_path = "chess_games.db"
            selected_args['db_path'] = db_path
            
            # Ottieni percorso file CSV
            csv_path = input("\nInserisci il percorso del file CSV da generare [analisi_scacchi.csv]: ").strip()
            if not csv_path:
                csv_path = "analisi_scacchi.csv"
            selected_args['csv_path'] = csv_path
            
            # Imposta parametri per CSV export
            selected_args['export_csv'] = True
            selected_args['export_text'] = False
            selected_args['analysis'] = None
            
            # Esegui l'esportazione
            print("\nAvvio esportazione CSV...")
            return argparse.Namespace(**selected_args)

        # Menu per esportazione in file di testo
        elif choice == 4:
            clear_screen()
            print_title("Esportazione Analisi in File di Testo")
            
            # Ottieni il nome del giocatore
            player = input("\nInserisci il nome del giocatore da analizzare [Blackeyes972]: ").strip()
            if not player:
                player = "Blackeyes972"
            selected_args['player'] = player
            
            # Ottieni percorso database
            db_path = input("\nInserisci il percorso del database [chess_games.db]: ").strip()
            if not db_path:
                db_path = "chess_games.db"
            selected_args['db_path'] = db_path
            
            # Ottieni percorso file di testo
            text_path = input("\nInserisci il percorso del file di testo da generare [chess_analysis.txt]: ").strip()
            if not text_path:
                text_path = "chess_analysis.txt"
            selected_args['text_path'] = text_path
            
            # Imposta parametri per text export
            selected_args['export_csv'] = False
            selected_args['export_text'] = True
            selected_args['analysis'] = None
            
            # Esegui l'esportazione
            print("\nAvvio esportazione in file di testo...")
            return argparse.Namespace(**selected_args)
            
        # Menu per visualizzazione rapida statistiche
        elif choice == 5:
            clear_screen()
            print_title("Visualizzazione Statistiche Rapide")
            
            # Ottieni il nome del giocatore
            player = input("\nInserisci il nome del giocatore da analizzare [Blackeyes972]: ").strip()
            if not player:
                player = "Blackeyes972"
            selected_args['player'] = player
            
            # Ottieni percorso database
            db_path = input("\nInserisci il percorso del database [chess_games.db]: ").strip()
            if not db_path:
                db_path = "chess_games.db"
            selected_args['db_path'] = db_path
            
            # Imposta parametri per stats
            selected_args['stats'] = True
            selected_args['analysis'] = "basic"
            selected_args['export_csv'] = False
            selected_args['export_text'] = False
            
            # Esegui visualizzazione statistiche
            print("\nRecupero statistiche...")
            return argparse.Namespace(**selected_args)
            
        # Menu per configurazione
        elif choice == 6:
            clear_screen()
            print_title("Configurazione Impostazioni")
            
            print("\n⚠️ Le impostazioni verranno salvate per sessioni future.")
            
            # Imposta giocatore predefinito
            default_player = input("\nGiocatore predefinito [Blackeyes972]: ").strip()
            if default_player:
                # Salvare questa impostazione in un file di configurazione
                print(f"Giocatore predefinito impostato a: {default_player}")
                
            # Imposta database predefinito
            default_db = input("\nPercorso database predefinito [chess_games.db]: ").strip()
            if default_db:
                # Salvare questa impostazione in un file di configurazione
                print(f"Database predefinito impostato a: {default_db}")
                
            # Altre impostazioni...
            
            input("\nPremi Enter per tornare al menu principale...")
            continue

    # Non dovremmo mai arrivare qui, ma per sicurezza
    return None

def main() -> None:
    """Funzione principale dello script."""
    print("\033[1;33mChessMetrics Pro v0.2.0-alpha\033[0m")
    print("\033[1;33mATTENZIONE: Questo software è in fase alpha. Utilizzare a proprio rischio.\033[0m\n")

    parser = argparse.ArgumentParser(description='Analisi avanzata di partite di scacchi da database SQLite')
    parser.add_argument('--db-path', default='chess_games.db', help='Percorso del database SQLite')
    parser.add_argument('--player', default='Blackeyes972', help='Nome del giocatore da analizzare')
    parser.add_argument('--analysis', choices=['all', 'basic', 'openings', 'opponents', 'phases', 'elo', 'mistakes', 'eco'],
                       help='Tipo di analisi da eseguire')
    parser.add_argument('--export-csv', action='store_true', help='Esporta tutte le analisi in un file CSV')
    parser.add_argument('--csv-path', default='chess_analysis.csv', help='Percorso del file CSV di output')
    parser.add_argument('--export-text', action='store_true', help='Export all analysis to a formatted text file')
    parser.add_argument('--text-path', default='chess_analysis.txt', help='Path for text output file')
    parser.add_argument('--stats', action='store_true', help='Mostra statistiche dopo l\'analisi')
    parser.add_argument('--pgn-folder', help='Cartella contenente i file PGN da importare')
    parser.add_argument('--force-reimport', action='store_true', help='Forza la reimportazione di file già elaborati')
    parser.add_argument('--batch-size', type=int, default=100, help='Dimensione del batch per inserimenti nel database')

   # Primo parsing per controllare se ci sono argomenti
    args, unknown = parser.parse_known_args()
    
    # Determina se mostrare il menu o usare i parametri
    # Se almeno un parametro significativo è stato specificato, usiamo la linea di comando
    has_command_args = any([
        args.analysis is not None,
        args.export_csv,
        args.export_text,
        args.pgn_folder is not None,
        args.force_reimport,
        # Non consideriamo --db-path e --player come significativi da soli,
        # perché potrebbero essere solo sovrascritture dei default
    ])
    
    if not has_command_args:
        # Nessun argomento significativo, mostra il menu interattivo
        menu_args = show_interactive_menu(parser)
        
        # Se l'utente ha scelto di uscire
        if menu_args is None:
            print("Programma terminato.")
            sys.exit(0)
            
        args = menu_args
    else:
        # Rianalizza per ottenere tutti gli argomenti correttamente
        args = parser.parse_args()
    
    # Da qui in poi, procedi con l'esecuzione normale usando args
    analyzer = ChessAnalyzer(args.db_path, args.player)
    
    if not analyzer.connect():
        print(f"Impossibile connettersi al database: {args.db_path}")
        sys.exit(1)
    
    try:
        print(f"\nANALISI DELLE PARTITE DI SCACCHI PER: {args.player}")
        print("=" * 50)
        
        if args.export_csv:
            analyzer.export_all_to_csv(args.csv_path)
        elif args.export_text:
            analyzer.export_analysis_to_text(args.text_path)
        elif args.analysis == 'all' or args.analysis is None:
            analyzer.run_analysis()
        elif args.analysis == 'basic':
            analyzer.display_basic_stats()
        elif args.analysis == 'openings':
            analyzer.analyze_openings()
        elif args.analysis == 'opponents':
            analyzer.analyze_opponents()
        elif args.analysis == 'phases':
            analyzer.analyze_game_phases()
        elif args.analysis == 'elo':
            analyzer.analyze_elo_progression()
        elif args.analysis == 'mistakes':
            analyzer.analyze_frequent_mistakes()
        elif args.analysis == 'eco':
            analyzer.analyze_performance_by_eco()
            
    except Exception as e:
        print(f"Errore durante l'analisi: {e}")
        
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()