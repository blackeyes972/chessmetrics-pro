#!/usr/bin/env python3
"""
Chess Game Viewer - Visualizzatore di partite dal database di scacchi
"""

import os
import sqlite3
import chess
import chess.pgn
import chess.svg
from IPython.display import SVG, display
import tempfile
import webbrowser

class ChessGameViewer:
    """Visualizzatore di partite di scacchi dal database."""
    
    def __init__(self, db_path):
        """Inizializza il visualizzatore.
        
        Args:
            db_path: Percorso al database SQLite
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.game_id = None
        self.moves = []
        self.current_move_index = -1
        self.board = chess.Board()
        
    def connect(self):
        """Connette al database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            print(f"Errore di connessione al database: {e}")
            return False
    
    def search_games(self, criteria=None):
        """Cerca partite nel database in base ai criteri forniti.
        
        Args:
            criteria: Dizionario con criteri di ricerca (giocatore, evento, data, ecc.)
        
        Returns:
            Lista di partite corrispondenti ai criteri
        """
        query = """
            SELECT id, white_player, black_player, result, date, event, site
            FROM games
            WHERE 1=1
        """
        params = []
        
        if criteria:
            if 'player' in criteria:
                query += " AND (white_player LIKE ? OR black_player LIKE ?)"
                params.extend([f"%{criteria['player']}%", f"%{criteria['player']}%"])
            
            if 'date' in criteria:
                query += " AND date LIKE ?"
                params.append(f"%{criteria['date']}%")
            
            if 'event' in criteria:
                query += " AND event LIKE ?"
                params.append(f"%{criteria['event']}%")
                
            if 'eco' in criteria:
                query += " AND eco LIKE ?"
                params.append(f"%{criteria['eco']}%")
        
        query += " ORDER BY date DESC LIMIT 50"
        
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def load_game(self, game_id):
        """Carica una partita dal database.
        
        Args:
            game_id: ID della partita nel database
            
        Returns:
            True se la partita è stata caricata con successo, False altrimenti
        """
        try:
            # Carica i dettagli della partita
            self.cursor.execute("""
                SELECT white_player, black_player, result, date, event, site, eco, opening
                FROM games
                WHERE id = ?
            """, (game_id,))
            
            game_details = self.cursor.fetchone()
            if not game_details:
                print(f"Partita con ID {game_id} non trovata.")
                return False
            
            # Carica le mosse della partita
            self.cursor.execute("""
                SELECT ply_number, san, uci, comment
                FROM moves
                WHERE game_id = ?
                ORDER BY ply_number
            """, (game_id,))
            
            self.moves = self.cursor.fetchall()
            if not self.moves:
                print(f"Nessuna mossa trovata per la partita con ID {game_id}.")
                return False
            
            self.game_id = game_id
            self.current_move_index = -1
            self.board = chess.Board()
            
            # Stampa i dettagli della partita
            white, black, result, date, event, site, eco, opening = game_details
            print(f"\n{'=' * 50}")
            print(f"Partita: {white} vs {black}, {result}")
            print(f"Data: {date}, Evento: {event}")
            print(f"Luogo: {site}")
            print(f"ECO: {eco}, Apertura: {opening}")
            print(f"{'=' * 50}\n")
            
            # Mostra la posizione iniziale
            self.display_board()
            
            return True
            
        except sqlite3.Error as e:
            print(f"Errore nel caricamento della partita: {e}")
            return False
    
    def next_move(self):
        """Avanza alla mossa successiva."""
        if self.current_move_index + 1 < len(self.moves):
            self.current_move_index += 1
            ply, san, uci, comment = self.moves[self.current_move_index]
            
            # Esegui la mossa
            move = chess.Move.from_uci(uci)
            self.board.push(move)
            
            # Mostra informazioni sulla mossa
            move_number = (ply // 2) + 1
            color = "Bianco" if ply % 2 == 0 else "Nero"
            print(f"Mossa {move_number}. {color}: {san}")
            if comment:
                print(f"Commento: {comment}")
                
            # Mostra la scacchiera aggiornata
            self.display_board()
            return True
        else:
            print("Fine della partita.")
            return False
    
    def prev_move(self):
        """Torna alla mossa precedente."""
        if self.current_move_index >= 0:
            self.board.pop()
            self.current_move_index -= 1
            
            if self.current_move_index >= 0:
                ply, san, uci, comment = self.moves[self.current_move_index]
                move_number = (ply // 2) + 1
                color = "Bianco" if ply % 2 == 0 else "Nero"
                print(f"Mossa {move_number}. {color}: {san}")
            else:
                print("Posizione iniziale.")
                
            # Mostra la scacchiera aggiornata
            self.display_board()
            return True
        else:
            print("Già alla posizione iniziale.")
            return False
    
    def display_board(self):
        """Visualizza la scacchiera nella posizione corrente."""
        # Mostra sempre la rappresentazione testuale
        print(self.board)
        
        # Controlla se siamo in un ambiente che può realmente mostrare SVG
        can_display_svg = False
        try:
            # Verifica se get_ipython() esiste E se siamo in un notebook
            shell = get_ipython().__class__.__name__
            if shell == 'ZMQInteractiveShell':  # Jupyter notebook/lab
                can_display_svg = True
            else:
                can_display_svg = False
        except (NameError, ImportError):
            can_display_svg = False
        
        if can_display_svg:
            # Solo se siamo sicuri di poter mostrare SVG
            svg_data = chess.svg.board(self.board, size=400)
            display(SVG(svg_data))
        else:
            # In ambiente terminale, offriamo l'opzione di aprire nel browser
            print("\nVuoi visualizzare la scacchiera nel browser? (s/n, Invio per solo testo): ", end="")
            choice = input().lower()
            if choice.startswith('s'):
                svg_data = chess.svg.board(self.board, size=400)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
                    html = f"<html><body>{svg_data}</body></html>"
                    f.write(html.encode('utf-8'))
                    browser_file = f.name
                
                webbrowser.open('file://' + browser_file)
                print("Scacchiera aperta nel browser")

    def create_game_gif(self, output_path=None, delay=500):
        """
        Crea una GIF animata dell'intera partita di scacchi.
        
        Args:
            output_path: Percorso dove salvare la GIF. Se None, usa il nome della partita.
            delay: Ritardo tra i frame in millisecondi (default 500ms).
            
        Returns:
            Il percorso del file GIF generato o None in caso di errore.
        """
        if not self.game_id:
            print("Nessuna partita caricata.")
            return None
        
        try:
            # Importa le librerie necessarie
            from PIL import Image
            import io
            import os
            
            # Se non è specificato un percorso di output, crea uno basato sui dati della partita
            if output_path is None:
                self.cursor.execute("""
                    SELECT white_player, black_player, date
                    FROM games
                    WHERE id = ?
                """, (self.game_id,))
                white, black, date = self.cursor.fetchone()
                filename = f"{white}_vs_{black}_{date}.gif".replace(" ", "_").replace(".", "-")
                output_path = os.path.join(os.getcwd(), filename)
            
            print(f"Generazione GIF della partita in corso...")
            
            # Salva la posizione corrente per ripristinarla alla fine
            current_position = self.current_move_index
            
            # Torna alla posizione iniziale
            self.board = chess.Board()
            self.current_move_index = -1
            
            # Lista per memorizzare le immagini
            images = []
            
            # Funzione per convertire SVG in immagine PIL
            def svg_to_pil(svg_data):
                """Converte SVG in un'immagine PIL usando vari metodi disponibili."""
                try:
                    # Prova prima con cairosvg
                    import cairosvg
                    png_data = io.BytesIO()
                    cairosvg.svg2png(bytestring=svg_data.encode('utf-8'), write_to=png_data)
                    png_data.seek(0)
                    return Image.open(png_data)
                except ImportError:
                    try:
                        # Prova con svglib se cairosvg non è disponibile
                        from svglib.svglib import svg2rlg
                        from reportlab.graphics import renderPM
                        drawing = svg2rlg(io.StringIO(svg_data))
                        png_data = io.BytesIO()
                        renderPM.drawToFile(drawing, png_data, fmt="PNG")
                        png_data.seek(0)
                        return Image.open(png_data)
                    except ImportError:
                        # Se nessuna delle librerie è disponibile, informiamo l'utente
                        print("È necessario installare cairosvg o svglib per creare GIF.")
                        print("pip install cairosvg")
                        print("oppure")
                        print("pip install svglib reportlab")
                        return None
            
            # Aggiungi la posizione iniziale
            svg_data = chess.svg.board(self.board, size=400)
            initial_img = svg_to_pil(svg_data)
            if initial_img is None:
                # Se la conversione fallisce, usciamo
                return None
            images.append(initial_img)
            
            # Esegui tutte le mosse e cattura le immagini
            for i in range(len(self.moves)):
                ply, san, uci, comment = self.moves[i]
                move = chess.Move.from_uci(uci)
                self.board.push(move)
                
                # Genera SVG e converti in immagine PIL
                svg_data = chess.svg.board(self.board, size=400)
                img = svg_to_pil(svg_data)
                if img is None:
                    # Se la conversione fallisce, usciamo
                    return None
                images.append(img)
                
                # Mostra progresso
                if (i+1) % 10 == 0 or i+1 == len(self.moves):
                    print(f"Processate {i+1}/{len(self.moves)} mosse...")
            
            # Crea la GIF
            if images:
                images[0].save(
                    output_path,
                    save_all=True,
                    append_images=images[1:],
                    duration=delay,
                    loop=0  # 0 significa loop infinito
                )
                print(f"GIF creata con successo: {output_path}")
            
            # Ripristina la posizione originale
            self.board = chess.Board()
            for i in range(current_position + 1):
                if i >= 0 and i < len(self.moves):
                    ply, san, uci, comment = self.moves[i]
                    move = chess.Move.from_uci(uci)
                    self.board.push(move)
            self.current_move_index = current_position
            
            return output_path
        
        except Exception as e:
            print(f"Errore durante la creazione della GIF: {e}")
            return None

    def run_interactive(self):
        """Esegue l'interfaccia interattiva per navigare tra le partite."""
        if not self.connect():
            return
            
        while True:
            print("\nCHESS GAME VIEWER - Menu Principale")
            print("1. Cerca partite")
            print("2. Carica partita per ID")
            print("3. Esci")
            
            choice = input("Scelta: ")
            
            if choice == '1':
                self.search_interactive()
            elif choice == '2':
                game_id = input("Inserisci ID partita: ")
                try:
                    game_id = int(game_id)
                    if self.load_game(game_id):
                        self.navigate_game()
                except ValueError:
                    print("ID partita non valido.")
            elif choice == '3':
                break
            else:
                print("Scelta non valida.")
    
    def search_interactive(self):
        """Interfaccia interattiva per la ricerca di partite."""
        criteria = {}
        
        print("\nRicerca Partite - Inserisci i criteri (lascia vuoto per ignorare)")
        player = input("Giocatore: ")
        if player:
            criteria['player'] = player
            
        date = input("Data (YYYY.MM.DD): ")
        if date:
            criteria['date'] = date
            
        event = input("Evento: ")
        if event:
            criteria['event'] = event
            
        eco = input("Codice ECO: ")
        if eco:
            criteria['eco'] = eco
        
        games = self.search_games(criteria)
        
        if not games:
            print("Nessuna partita trovata con questi criteri.")
            return
            
        print(f"\nTrovate {len(games)} partite:")
        for i, (id, white, black, result, date, event, site) in enumerate(games, 1):
            print(f"{i}. [{id}] {white} vs {black}, {result}, {date}")
            
        choice = input("\nScegli una partita (numero o ID) o premi Invio per tornare: ")
        if not choice:
            return
            
        try:
            choice_int = int(choice)
            if 1 <= choice_int <= len(games):
                game_id = games[choice_int - 1][0]
            else:
                game_id = choice_int
                
            if self.load_game(game_id):
                self.navigate_game()
        except ValueError:
            print("Scelta non valida.")
    
    def navigate_game(self):
        """Interfaccia per navigare attraverso le mosse di una partita."""
        while True:
            print("\nComandi: [n]ext, [p]rev, [g]o to move, [r]estart, [q]uit")
            command = input("Comando: ").lower()
            
            if command.startswith('n'):
                self.next_move()
            elif command.startswith('p'):
                self.prev_move()
            elif command.startswith('g'):
                try:
                    move_num = int(input("Numero mossa: "))
                    target_ply = (move_num * 2) - 2  # Calcola il ply corrispondente
                    
                    # Resetta alla posizione iniziale
                    self.board = chess.Board()
                    self.current_move_index = -1
                    
                    # Avanza fino alla mossa desiderata
                    for i in range(min(target_ply + 1, len(self.moves))):
                        ply, san, uci, comment = self.moves[i]
                        move = chess.Move.from_uci(uci)
                        self.board.push(move)
                        self.current_move_index = i
                    
                    # Mostra la posizione
                    if self.current_move_index >= 0:
                        ply, san, uci, comment = self.moves[self.current_move_index]
                        move_number = (ply // 2) + 1
                        color = "Bianco" if ply % 2 == 0 else "Nero"
                        print(f"Mossa {move_number}. {color}: {san}")
                    
                    self.display_board()
                    
                except ValueError:
                    print("Numero mossa non valido.")
            elif command.startswith('r'):
                self.board = chess.Board()
                self.current_move_index = -1
                print("Partita riavviata alla posizione iniziale.")
                self.display_board()
            elif command.startswith('q'):
                break
            else:
                print("Comando non valido.")

    def close(self):
        """Chiude la connessione al database."""
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    import sys
    
    # Percorso predefinito del database
    db_path = "chess_games.db"
    
    # Se viene fornito un percorso come argomento, lo usa
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    viewer = ChessGameViewer(db_path)
    viewer.run_interactive()
    viewer.close()