# ChessMetrics Pro

![ChessMetrics Pro Logo](https://github.com/username/chessmetrics-pro/raw/main/docs/images/logo.png)

## Analisi Avanzata delle Partite di Scacchi

ChessMetrics Pro è un software professionale per l'analisi avanzata delle partite di scacchi. Progettato per giocatori di tutti i livelli, dal principiante all'esperto, permette di analizzare un database di partite per ottenere insights strategici sulla propria performance.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![SQLite](https://img.shields.io/badge/database-SQLite-green.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/license-GPL%20v3-orange.svg)](LICENSE)

---

## 📋 Caratteristiche

ChessMetrics Pro offre un'analisi completa delle partite di scacchi attraverso varie lenti analitiche:

- **Importazione PGN**: Importa file PGN in un database SQLite con rilevazione automatica di duplicati
- **Panoramica generale**: Statistiche complessive, distribuzione vittorie/sconfitte/pareggi, bianco vs nero
- **Analisi delle aperture**: Identifica le tue aperture più efficaci e quelle più problematiche
- **Analisi degli avversari**: Monitoraggio delle performance contro diversi avversari
- **Analisi delle fasi di gioco**: Scopri in quali fasi della partita eccelli o hai difficoltà
- **Evoluzione dell'Elo**: Traccia la progressione del tuo rating nel tempo
- **Analisi degli errori**: Focus sulle partite perse rapidamente per identificare debolezze ricorrenti
- **Analisi per categoria ECO**: Performance nelle diverse famiglie di aperture
- **Visualizzazioni grafiche**: Rappresentazione grafica dei dati per una comprensione immediata
- **Esportazione dei risultati**: Esporta le analisi in formato CSV o file di testo formattato

---

## 🚀 Installazione

### Prerequisiti

- Python 3.8 o superiore
- pip (gestore pacchetti Python)

### Installazione dei pacchetti richiesti

```bash
# Clona il repository
git clone https://github.com/username/chessmetrics-pro.git
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
pip install pandas matplotlib seaborn tabulate python-chess
```

---

## 📊 Utilizzo

ChessMetrics Pro è composto da due script principali:

1. `chess_importer.py` - Per importare file PGN nel database
2. `chess_analyzer.py` - Per analizzare le partite nel database

### Importazione PGN

```bash
# Importazione base con impostazioni predefinite
python chess_importer.py 

# Specificare una cartella PGN diversa
python chess_importer.py --pgn-folder miei_file_pgn

# Forzare la reimportazione di file già elaborati
python chess_importer.py --force-reimport

# Mostrare statistiche dopo l'importazione
python chess_importer.py --stats
```

### Analisi delle partite

```bash
# Esegui tutte le analisi (con grafici interattivi)
python chess_analyzer.py

# Analizza un giocatore specifico
python chess_analyzer.py --player "MagnusCarlsen"

# Esegui solo un tipo di analisi
python chess_analyzer.py --analysis openings
python chess_analyzer.py --analysis elo
python chess_analyzer.py --analysis opponents

# Esporta tutte le analisi in CSV
python chess_analyzer.py --export-csv

# Esporta tutte le analisi in un file di testo formattato
python chess_analyzer.py --export-text
```

### Tipi di analisi disponibili

- `basic` - Statistiche di base
- `openings` - Analisi delle aperture
- `opponents` - Analisi degli avversari
- `phases` - Analisi delle fasi di gioco
- `elo` - Evoluzione dell'Elo nel tempo
- `mistakes` - Analisi degli errori e sconfitte rapide
- `eco` - Analisi per categoria ECO
- `all` - Esegue tutte le analisi (predefinito)

---

## 🔧 Configurazione

ChessMetrics Pro è altamente configurabile. I principali parametri possono essere impostati tramite argomenti della linea di comando o modificando il codice.

### File e Posizioni

- `--pgn-folder`: Cartella contenente i file PGN (default: `pgn_files`)
- `--db-path`: Percorso del database SQLite (default: `chess_games.db`)
- `--csv-path`: Percorso del file CSV di output (default: `analisi_scacchi.csv`)
- `--text-path`: Percorso del file di testo di output (default: `analisi_scacchi.txt`)

### Performance

- `--batch-size`: Dimensione del batch per inserimenti nel database (default: `100`)

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
- Heatmap per identificare i punti di forza e debolezza

---

## 🔍 Esempio di Output

### Statistiche di Base

```
===== PANORAMICA GENERALE =====
Giocatore: Blackeyes972
Totale partite: 156
Partite con il bianco: 78 (50.0%)
Partite con il nero: 78 (50.0%)
Vittorie: 62 (39.7%)
Sconfitte: 86 (55.1%)
Pareggi: 8 (5.1%)
Lunghezza media partite: 37.3 mosse
Elo medio del giocatore: 528
Elo medio degli avversari: 531
```

### Migliori Aperture

```
--- MIGLIORI APERTURE (PER TASSO DI VITTORIA) ---
+-----+--------------------------+-------+----------+---------+-----------+----------------------+
| ECO | Apertura                 | Partite | Vittorie | Pareggi | Sconfitte | Percentuale_Vittorie |
+-----+--------------------------+-------+----------+---------+-----------+----------------------+
| C47 | Four Knights Game        |     5 |        4 |       0 |         1 |                80.00 |
| B07 | Pirc Defense            |    12 |        7 |       1 |         4 |                58.33 |
| C50 | Italian Game             |     8 |        4 |       1 |         3 |                50.00 |
| C45 | Scotch Game              |     6 |        3 |       0 |         3 |                50.00 |
| C67 | Ruy Lopez                |     4 |        1 |       0 |         3 |                25.00 |
+-----+--------------------------+-------+----------+---------+-----------+----------------------+
```

---

## ⚙️ Dipendenze

- [python-chess](https://python-chess.readthedocs.io/): Libreria per manipolazione di partite e file PGN
- [pandas](https://pandas.pydata.org/): Analisi e manipolazione dei dati
- [matplotlib](https://matplotlib.org/): Visualizzazione dei dati
- [seaborn](https://seaborn.pydata.org/): Visualizzazioni statistiche avanzate
- [tabulate](https://pypi.org/project/tabulate/): Formattazione delle tabelle
- [sqlite3](https://docs.python.org/3/library/sqlite3.html): Interfaccia per database SQLite (inclusa in Python)

---

## 📝 Note Aggiuntive

- **Performance**: Per database di grandi dimensioni (>10.000 partite), l'analisi potrebbe richiedere più tempo
- **Compatibilità**: Testato su Windows 10/11, macOS e Linux (Ubuntu/Debian)
- **Limitazioni**: L'analisi tattica approfondita richiederebbe l'integrazione con un motore di scacchi (funzionalità pianificata per versioni future)

---

## 📜 Licenza

Questo progetto è rilasciato sotto la licenza MIT. Vedi il file [LICENSE](LICENSE) per i dettagli.

---

## 👥 Autori

- **Alessandro Marone** - *Sviluppo iniziale*

## 🙏 Ringraziamenti

- La community di [Python-Chess](https://github.com/niklasf/python-chess)
- [Chess.com](https://www.chess.com/) per il formato PGN standard
- Tutti i contributori della documentazione ECO

---

## 📬 Contatti

Per domande, suggerimenti o segnalazioni di bug, contattare:
- Email: alessandro.marone@example.com
- GitHub: [github.com/alessandro-marone](https://github.com/alessandro-marone)

---

*ChessMetrics Pro: Trasforma le tue partite in strategie vincenti.*