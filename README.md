# ChessMetrics Pro

![ChessMetrics Pro Logo](https://github.com/blackeyes972/chessmetrics-pro/raw/main/docs/images/logo.png)

## Analisi Avanzata delle Partite di Scacchi

ChessMetrics Pro è un software professionale per l'analisi avanzata delle partite di scacchi. Progettato per giocatori di tutti i livelli, dal principiante all'esperto, permette di analizzare un database di partite per ottenere insights strategici sulla propria performance.

[![Status](https://img.shields.io/badge/status-beta-blue)](https://github.com/blackeyes972/chessmetrics-pro)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![SQLite](https://img.shields.io/badge/database-SQLite-green.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/license-GPL%20v3-orange.svg)](LICENSE)

---

## Stato del Progetto

## Versione Attuale
**0.3.0-beta**

ChessMetrics Pro è ora in fase **BETA**, con tutte le funzionalità principali implementate e un'interfaccia grafica completa. Il software è pronto per essere utilizzato da un pubblico più ampio, pur continuando a ricevere miglioramenti e ottimizzazioni.

---

## 📋 Caratteristiche

ChessMetrics Pro offre un'analisi completa delle partite di scacchi attraverso varie lenti analitiche:

### Componenti Principali:

1. **Interfaccia Grafica PyQt6** (NUOVO!):
   - Interfaccia grafica moderna e intuitiva
   - Visualizzazione integrata dei grafici
   - Navigazione fluida tra le funzionalità
   - Supporto per toolbar interattive nei grafici
   - Salvataggio diretto delle immagini dei grafici

2. **Menu a Riga di Comando** (Alternativa):
   - Interfaccia centralizzata per tutti i componenti
   - Navigazione intuitiva tra le funzionalità
   - Gestione configurazione dell'applicazione
   - Verifica e inizializzazione automatica del database

3. **Importatore PGN**:
   - Importa file PGN in un database SQLite con rilevazione automatica di duplicati
   - Processamento in batch per grandi collezioni di partite
   - Visualizzazione del progresso in tempo reale
   - Gestione robusta degli errori e supporto multi-encoding

4. **Analizzatore di Partite**:
   - Panoramica generale: Statistiche complessive, distribuzione vittorie/sconfitte/pareggi
   - Analisi delle aperture: Identifica le aperture più efficaci e problematiche
   - Analisi degli avversari: Monitoraggio delle performance contro diversi avversari
   - Analisi delle fasi di gioco: Scopri in quali fasi della partita eccelli o hai difficoltà
   - Evoluzione dell'Elo: Traccia la progressione del tuo rating nel tempo
   - Analisi degli errori: Focus sulle sconfitte rapide per identificare debolezze ricorrenti
   - Analisi per categoria ECO: Performance nelle diverse famiglie di aperture
   - Esportazione organizzata dei risultati in cartella dedicata "analysis"

5. **Visualizzatore di Partite**:
   - Visualizzazione interattiva delle partite dal database
   - Ricerca avanzata di partite per giocatore, data, evento o ECO
   - Navigazione mossa per mossa con notazione SAN
   - Visualizzazione grafica SVG della scacchiera direttamente nell'interfaccia
   - **Generatore di GIF animata**: Crea GIF delle partite per analisi o condivisione

---

## 🚀 Installazione

### Prerequisiti

- Python 3.8 o superiore
- pip (gestore pacchetti Python)

### Installazione dei pacchetti richiesti

```bash
# Clona il repository
git clone https://github.com/blackeyes972/chessmetrics-pro.git
cd chessmetrics-pro

# Crea un ambiente virtuale (consigliato)
python -m venv chess_env
source chess_env/bin/activate  # Linux/macOS
# oppure
chess_env\Scripts\activate     # Windows

# Installa le dipendenze
pip install -r requirements.txt
```

Oppure, se preferisci installare singolarmente i pacchetti:

```bash
# Pacchetti principali
pip install pandas matplotlib seaborn tabulate python-chess

# Per la generazione di GIF
pip install pillow cairosvg

# Per l'interfaccia grafica PyQt6
pip install PyQt6
```

---

## 📊 Utilizzo

### Interfaccia Grafica (Raccomandata)

Il modo più semplice per utilizzare ChessMetrics Pro è attraverso l'interfaccia grafica:

```bash
# Avvia l'interfaccia grafica
python chessmetrics_gui.py
```

L'interfaccia grafica offre:
- **Importazione PGN** con feedback visivo in tempo reale
- **Analisi partite** con grafici interattivi integrati
- **Visualizzazione partite** con scacchiera SVG integrata
- **Configurazione** semplice dell'applicazione

### Menu a Riga di Comando (Alternativa)

È ancora possibile utilizzare il menu a riga di comando:

```bash
# Avvia il menu a riga di comando
python chessmetrics_menu.py
```

### Componenti individuali

È inoltre possibile utilizzare i componenti individuali:

#### Importazione PGN

```bash
# Importazione con impostazioni predefinite
python chess_import.py 

# Opzioni aggiuntive
python chess_import.py --pgn-folder miei_file_pgn --force-reimport --stats
```

#### Analisi delle partite

```bash
# Analisi completa
python chess_analyzer.py

# Analisi specifica
python chess_analyzer.py --player "MagnusCarlsen" --analysis elo

# Esportazione
python chess_analyzer.py --export-csv --export-text
```

#### Visualizzatore di partite

```bash
# Visualizzatore interattivo
python chess_game_viewer.py
```

---

## 🔧 Organizzazione File

ChessMetrics Pro organizza i file di output in modo strutturato:

- **pgn_files/**: Directory predefinita per i file PGN da importare
- **analysis/**: Directory per i file di analisi esportati (CSV, TXT)
- **gif_files/**: Directory per le GIF animate delle partite
- **chess_games.db**: Database SQLite per l'archiviazione delle partite

Questa struttura mantiene il progetto organizzato e facilita la gestione dei dati.

---

## 📚 Dettagli Tecnici

### Struttura del database

ChessMetrics Pro utilizza un database SQLite con le seguenti tabelle principali:

- `games`: Informazioni generali sulle partite (giocatori, risultato, data, ECO, ecc.)
- `moves`: Mosse di ogni partita in formato SAN e UCI
- `import_metadata`: Metadati sull'importazione dei file PGN

```sql
# Schema della tabella principale
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
```

### Interfaccia grafica PyQt6

La nuova interfaccia grafica sfrutta PyQt6 per offrire:
- Visualizzazione integrata mediante schede per tutte le funzionalità
- Multithreading per mantenere l'interfaccia reattiva durante operazioni lunghe
- Grafici matplotlib integrati con toolbar interattive
- Visualizzazione SVG della scacchiera direttamente nell'interfaccia

### Generazione di GIF

La funzionalità di generazione GIF:
- Crea animazioni delle partite con posizioni fotogramma per fotogramma
- Consente di impostare la velocità dell'animazione regolando il ritardo dei frame
- Supporta convertitori SVG diversi (cairosvg o svglib)
- Salva i file GIF in una directory organizzata (`gif_files`)
- Fornisce feedback dettagliato durante il processo di generazione

### Il Sistema ECO

L'ECO (Encyclopedia of Chess Openings) è un sistema standardizzato di classificazione delle aperture di scacchi:

- **A**: Aperture di fianchetto (1.c4, 1.Nf3, etc.)
- **B**: Aperture semiaperte (1.e4 eccetto 1...e5)
- **C**: Aperture aperte (1.e4 e5)
- **D**: Aperture chiuse (1.d4 d5)
- **E**: Difese indiane (1.d4 Nf6 eccetto 2.c4 e5)

Ogni categoria è ulteriormente suddivisa con codici numerici (es. B22, C45) per identificare varianti specifiche.

---

## 📈 Esempi di Visualizzazioni

ChessMetrics Pro genera diverse visualizzazioni grafiche durante l'analisi interattiva, inclusi:

- Grafici a torta per la distribuzione dei risultati
- Grafici a barre per le performance con aperture specifiche
- Grafici temporali per l'evoluzione dell'Elo
- Grafici comparativi per le prestazioni nelle diverse fasi di gioco
- Grafici interattivi con funzionalità di zoom, pan e salvataggio
- GIF animate delle partite complete

---

## ⚙️ Dipendenze

- [python-chess](https://python-chess.readthedocs.io/): Manipolazione di partite e file PGN
- [pandas](https://pandas.pydata.org/): Analisi e manipolazione dei dati
- [matplotlib](https://matplotlib.org/): Visualizzazione dei dati
- [seaborn](https://seaborn.pydata.org/): Visualizzazioni statistiche avanzate
- [tabulate](https://pypi.org/project/tabulate/): Formattazione delle tabelle
- [sqlite3](https://docs.python.org/3/library/sqlite3.html): Interfaccia per database SQLite
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/): Interfaccia grafica
- [Pillow](https://pillow.readthedocs.io/): Elaborazione immagini per generazione GIF
- [cairosvg](https://cairosvg.org/): Conversione da SVG a PNG (per GIF)

---

## 🔍 Roadmap

Per la versione 1.0 sono previste le seguenti funzionalità:

- **Integrazione con motori di scacchi** per analisi tattiche avanzate
- **Filtri avanzati** per la ricerca di partite
- **Analisi comparativa** tra diversi giocatori
- **Supporto multilingua** per l'interfaccia utente
- **Installer** per un'installazione semplificata

---

## 📜 Licenza

Questo progetto è rilasciato sotto la licenza GPL v3. Vedi il file [LICENSE](LICENSE) per i dettagli.

---

## 👥 Autori

- **Alessandro Castaldi** - *Sviluppo iniziale*

## 🙏 Ringraziamenti

- La community di [Python-Chess](https://github.com/niklasf/python-chess)
- [Chess.com](https://www.chess.com/) per il formato PGN standard
- Tutti i contributori della documentazione ECO
- La community di [PyQt](https://www.riverbankcomputing.com/software/pyqt/) per l'eccellente toolkit GUI

---

## 📬 Contatti

Per domande, suggerimenti o segnalazioni di bug, contattare:
- Email: notifiche72@gmail.com
- GitHub: [github.com/blackeyes972](https://github.com/blackeyes972)

---

*ChessMetrics Pro: Trasforma le tue partite in strategie vincenti.*