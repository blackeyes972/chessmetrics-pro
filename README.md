# ChessMetrics Pro

![ChessMetrics Pro Logo](https://github.com/blackeyyes972/chessmetrics-pro/raw/main/docs/images/logo.png)

## Analisi Avanzata delle Partite di Scacchi

ChessMetrics Pro è un software professionale per l'analisi avanzata delle partite di scacchi. Progettato per giocatori di tutti i livelli, dal principiante all'esperto, permette di analizzare un database di partite per ottenere insights strategici sulla propria performance.

[![Status](https://img.shields.io/badge/status-alpha-red)](https://github.com/blackeyes972/chessmetrics-pro)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![SQLite](https://img.shields.io/badge/database-SQLite-green.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/license-GPL%20v3-orange.svg)](LICENSE)

---

## Stato del Progetto

## Versione Attuale
**0.2.0-alpha**

⚠️ **NOTA: ChessMetrics Pro è attualmente in fase ALPHA** ⚠️

Questo significa che:
- Le funzionalità principali sono implementate ma potrebbero contenere bug
- L'interfaccia utente potrebbe subire modifiche significative
- La documentazione è ancora in sviluppo
- Non consigliamo l'uso in ambienti di produzione critici

Siamo alla ricerca di feedback e segnalazioni per migliorare il software. Se riscontri problemi, 
per favore apri una issue sul repository GitHub.

---

## 📋 Caratteristiche

ChessMetrics Pro offre un'analisi completa delle partite di scacchi attraverso varie lenti analitiche:

### Componenti Principali:

1. **Menu Unificato** (NUOVO!):
   - Interfaccia centralizzata per tutti i componenti
   - Navigazione intuitiva tra le funzionalità
   - Gestione configurazione dell'applicazione
   - Verifica e inizializzazione automatica del database

2. **Importatore PGN**:
   - Importa file PGN in un database SQLite con rilevazione automatica di duplicati
   - Processamento in batch per grandi collezioni di partite
   - Gestione robusta degli errori e supporto multi-encoding

3. **Analizzatore di Partite**:
   - Panoramica generale: Statistiche complessive, distribuzione vittorie/sconfitte/pareggi
   - Analisi delle aperture: Identifica le aperture più efficaci e problematiche
   - Analisi degli avversari: Monitoraggio delle performance contro diversi avversari
   - Analisi delle fasi di gioco: Scopri in quali fasi della partita eccelli o hai difficoltà
   - Evoluzione dell'Elo: Traccia la progressione del tuo rating nel tempo
   - Analisi degli errori: Focus sulle sconfitte rapide per identificare debolezze ricorrenti
   - Analisi per categoria ECO: Performance nelle diverse famiglie di aperture
   - Esportazione dei risultati: Esporta le analisi in formato CSV o file di testo formattato

4. **Visualizzatore di Partite** (NUOVO!):
   - Visualizzazione interattiva delle partite dal database
   - Ricerca avanzata di partite per giocatore, data, evento o ECO
   - Navigazione mossa per mossa con notazione SAN
   - Visualizzazione ASCII della scacchiera nel terminale
   - Opzione per visualizzare la scacchiera in formato SVG nel browser
   - **Generatore di GIF animata** (NUOVO!): Crea GIF delle partite per analisi o condivisione

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
pip install pandas matplotlib seaborn tabulate python-chess pillow cairosvg
```

---

## 📊 Utilizzo

### Menu Principale (Nuovo!)

Il modo più semplice per utilizzare ChessMetrics Pro è attraverso il menu centralizzato:

```bash
# Avvia il menu principale
python chessmetrics_menu.py
```

Questo fornisce un'interfaccia intuitiva per:
- Importare file PGN
- Analizzare partite
- Visualizzare partite
- Configurare l'applicazione

### Componenti individuali

È comunque possibile utilizzare i componenti individuali:

#### Importazione PGN

```bash
# Importazione base con impostazioni predefinite
python chess_import.py 

# Specificare una cartella PGN diversa
python chess_import.py --pgn-folder miei_file_pgn

# Forzare la reimportazione di file già elaborati
python chess_import.py --force-reimport

# Mostrare statistiche dopo l'importazione
python chess_import.py --stats
```

#### Analisi delle partite

```bash
# Esegui tutte le analisi (con grafici interattivi)
python chess_analyzer.py

# Analizza un giocatore specifico
python chess_analyzer.py --player "MagnusCarlsen"

# Esegui solo un tipo di analisi
python chess_analyzer.py --analysis openings
python chess_analyzer.py --analysis elo

# Esporta tutte le analisi in CSV o testo
python chess_analyzer.py --export-csv
python chess_analyzer.py --export-text
```

#### Visualizzatore di partite (Nuovo!)

```bash
# Avvia il visualizzatore interattivo
python chess_game_viewer.py

# Specifica un database alternativo
python chess_game_viewer.py percorso_database.db
```

Il visualizzatore offre un'interfaccia interattiva che permette di:
- Cercare partite per vari criteri
- Navigare mossa per mossa
- Visualizzare la scacchiera in formato ASCII o SVG
- Generare GIF animate delle partite

---

## 🔧 Configurazione

ChessMetrics Pro è altamente configurabile. I principali parametri possono essere impostati tramite:
- Menu delle impostazioni nell'interfaccia principale (consigliato)
- Argomenti della linea di comando
- Modificando direttamente il codice

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

### Generazione di GIF (Nuova funzionalità!)

La nuova funzionalità di generazione GIF:
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
- Heatmap per identificare i punti di forza e debolezza
- **NUOVO!** GIF animate delle partite complete

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

### Visualizzatore di Partite (Nuovo!)

```
==================================================
Partita: Blackeyes972 vs Arti990, 1-0
Data: 2025.04.16, Evento: Live Chess
Luogo: Chess.com
ECO: D02, Apertura: 
==================================================

r n b q k b n r
p p p p p p p p
. . . . . . . .
. . . . . . . .
. . . P . . . .
. . . . . . . .
P P P . P P P P
R N B Q K B N R

Comandi: [n]ext, [p]rev, [g]o to move, [r]estart, [s]ave gif, [q]uit
Comando: 
```

---

## ⚙️ Dipendenze

- [python-chess](https://python-chess.readthedocs.io/): Libreria per manipolazione di partite e file PGN
- [pandas](https://pandas.pydata.org/): Analisi e manipolazione dei dati
- [matplotlib](https://matplotlib.org/): Visualizzazione dei dati
- [seaborn](https://seaborn.pydata.org/): Visualizzazioni statistiche avanzate
- [tabulate](https://pypi.org/project/tabulate/): Formattazione delle tabelle
- [sqlite3](https://docs.python.org/3/library/sqlite3.html): Interfaccia per database SQLite
- [Pillow](https://pillow.readthedocs.io/): Elaborazione immagini per generazione GIF
- [cairosvg](https://cairosvg.org/): Conversione da SVG a PNG (per GIF)
- [svglib](https://github.com/deeplook/svglib): Alternativa per la conversione SVG

---

## 📝 Note Aggiuntive

- **Performance**: Per database di grandi dimensioni (>10.000 partite), l'analisi potrebbe richiedere più tempo
- **Compatibilità**: Testato su Windows 10/11, macOS e Linux (Ubuntu/Debian)
- **Visualizzazione della scacchiera**: Adattamento automatico all'ambiente (terminale o browser)
- **Generazione GIF**: Richiede librerie aggiuntive (Pillow e cairosvg o svglib)
- **Limitazioni**: L'analisi tattica approfondita richiederebbe l'integrazione con un motore di scacchi (funzionalità pianificata per versioni future)

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

---

## 📬 Contatti

Per domande, suggerimenti o segnalazioni di bug, contattare:
- Email: notifiche72@gmail.com
- GitHub: [github.com/blackeyes972](https://github.com/blackeyes972)

---

*ChessMetrics Pro: Trasforma le tue partite in strategie vincenti.*