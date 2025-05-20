# Manuale d'Uso Completo - ChessMetrics Pro

## Indice
1. [Introduzione a ChessMetrics Pro](#1-introduzione-a-chessmetrics-pro)
2. [Requisiti di sistema e installazione](#2-requisiti-di-sistema-e-installazione)
3. [Panoramica delle componenti](#3-panoramica-delle-componenti)
4. [Interfaccia a linea di comando (chessmetrics_menu.py)](#4-interfaccia-a-linea-di-comando-chessmetrics_menupy)
5. [Interfaccia grafica principale (chessmetrics_gui.py)](#5-interfaccia-grafica-principale-chessmetrics_guipy)
6. [Analisi con motore scacchistico (chess_engine_analysis.py)](#6-analisi-con-motore-scacchistico-chess_engine_analysispy)
7. [Interfaccia grafica dell'analizzatore (chess_engine_analysis_gui.py)](#7-interfaccia-grafica-dellanalizzatore-chess_engine_analysis_guipy)
8. [Verifica del corretto funzionamento](#8-verifica-del-corretto-funzionamento)
9. [Funzionalità avanzate](#9-funzionalità-avanzate)
10. [Risoluzione dei problemi](#10-risoluzione-dei-problemi)

## 1. Introduzione a ChessMetrics Pro

ChessMetrics Pro è una suite completa per l'analisi delle partite di scacchi, progettata per aiutare giocatori di tutti i livelli a migliorare le proprie capacità attraverso un'analisi dettagliata delle partite. La suite combina diversi strumenti potenti in un'unica piattaforma integrata, offrendo funzionalità per l'importazione, l'analisi, la visualizzazione e l'esportazione di dati scacchistici.

### Caratteristiche principali

- **Importazione di file PGN**: Importa facilmente le tue partite da file PGN nel database
- **Analisi statistica avanzata**: Valuta le tue prestazioni, individua punti di forza e debolezze
- **Analisi con motore scacchistico**: Usa motori come Stockfish per analizzare posizioni e identificare errori
- **Visualizzatore interattivo**: Naviga attraverso le tue partite con una scacchiera interattiva
- **Analisi delle aperture**: Valuta le tue prestazioni con diverse aperture
- **Interfacce multiple**: Scegli tra interfaccia console o grafica in base alle tue preferenze
- **Esportazione dati**: Esporta analisi in formato PGN, HTML o CSV

ChessMetrics Pro è pensato per utenti di diversi livelli:
- **Principianti**: Identifica errori comuni e migliora le conoscenze di base
- **Giocatori intermedi**: Analizza sistematicamente le proprie partite e migliora specifiche aree di gioco
- **Giocatori avanzati**: Esegui analisi dettagliate con motori di scacchi e studia tendenze statistiche
- **Allenatori**: Analizza le partite dei propri studenti e prepara materiale di coaching

## 2. Requisiti di sistema e installazione

### Requisiti di sistema

- **Sistema operativo**: Windows, macOS o Linux
- **Python**: Versione 3.6 o superiore
- **Librerie Python necessarie**:
  - PyQt6 (per le interfacce grafiche)
  - python-chess
  - matplotlib
  - pandas
  - numpy
  - sqlite3 (generalmente incluso in Python)
- **Motore di scacchi**: Stockfish (o altro motore compatibile con UCI)
- **Spazio su disco**: Almeno 100MB per l'installazione base, più spazio per il database
- **Memoria RAM**: Almeno 4GB consigliati per analisi complesse

### Procedura di installazione

1. **Installazione di Python**:
   - Scarica e installa Python 3.6+ dal sito ufficiale: https://www.python.org/downloads/
   - Assicurati di selezionare "Add Python to PATH" durante l'installazione

2. **Installazione delle dipendenze Python**:
   ```
   pip install PyQt6 python-chess matplotlib pandas numpy
   ```

3. **Installazione di Stockfish**:
   - Scarica Stockfish dal sito ufficiale: https://stockfishchess.org/download/
   - Estrai l'eseguibile in una cartella a tua scelta
   - Nota: L'applicazione può cercare automaticamente Stockfish, ma è consigliabile specificare manualmente il percorso nelle impostazioni

4. **Download di ChessMetrics Pro**:
   - Scarica o clona il repository in una cartella locale
   - Assicurati che tutti i file Python siano nella stessa cartella

5. **Inizializzazione dell'ambiente**:
   - Avvia l'applicazione per la prima volta usando uno dei seguenti comandi:
     ```
     python chessmetrics_menu.py    # Per l'interfaccia a linea di comando
     ```
     oppure
     ```
     python chessmetrics_gui.py     # Per l'interfaccia grafica
     ```
   - Al primo avvio, l'applicazione creerà tutte le cartelle necessarie e ti chiederà di inizializzare il database

### Struttura delle directory

ChessMetrics Pro crea automaticamente le seguenti directory:
- `data/`: Contiene il database SQLite
- `logs/`: Contiene i file di log dell'applicazione
- `pgn_files/`: Directory predefinita per i file PGN da importare
- `export/`: Directory per le esportazioni (PGN, HTML, CSV)

## 3. Panoramica delle componenti

ChessMetrics Pro è composto da diverse componenti che lavorano insieme. Ecco una panoramica:

### Database SQLite

Il cuore del sistema è un database SQLite che memorizza:
- Dati delle partite importate (giocatori, evento, data, risultato)
- Mosse individuali di ogni partita
- Analisi del motore
- Statistiche dei giocatori
- Metadati sull'importazione

### Moduli principali

1. **ChessDBManager** (chess_import.py)
   - Gestisce l'importazione di file PGN nel database
   - Crea e mantiene la struttura del database
   - Fornisce statistiche di base sui dati importati

2. **ChessAnalyzer** (chess_analyzer.py)
   - Esegue analisi statistiche sulle partite
   - Genera rapporti e visualizzazioni
   - Esporta i risultati dell'analisi

3. **ChessGameViewer** (chess_game_viewer.py)
   - Visualizza le partite mossa per mossa
   - Permette di cercare partite nel database
   - Genera GIF animate dalle partite

4. **ChessEngineAnalyzer** (chess_engine_analysis.py)
   - Analizza le partite usando motori di scacchi (es. Stockfish)
   - Identifica errori e posizioni critiche
   - Salva analisi dettagliate nel database

### Interfacce utente

1. **Interfaccia a linea di comando** (chessmetrics_menu.py)
   - Menu interattivo basato su testo
   - Accesso a tutte le funzionalità tramite comandi numerici
   - Ideale per script e utilizzo su server

2. **Interfaccia grafica principale** (chessmetrics_gui.py)
   - Interfaccia grafica completa basata su PyQt6
   - Visualizzazione grafica dei dati
   - Esperienza utente moderna e intuitiva

3. **Interfaccia grafica dell'analizzatore** (chess_engine_analysis_gui.py)
   - Interfaccia dedicata all'analisi con motore scacchistico
   - Visualizzazione avanzata delle analisi
   - Integrazione con il resto della suite

## 4. Interfaccia a linea di comando (chessmetrics_menu.py)

L'interfaccia a linea di comando offre accesso a tutte le funzionalità della suite in un'interfaccia basata su testo, ideale per utenti esperti o per l'utilizzo su server remoti.

### Avvio dell'interfaccia

```
python chessmetrics_menu.py
```

Opzionalmente, puoi specificare un percorso del database diverso:
```
python chessmetrics_menu.py --db-path percorso/al/database.db
```

### Menu principale

All'avvio, vedrai il menu principale con le seguenti opzioni:
1. Importa file PGN
2. Analizza partite
3. Visualizza partite
4. Impostazioni
5. Informazioni

Seleziona un'opzione digitando il numero corrispondente.

### Importazione file PGN

1. Seleziona "Importa file PGN" dal menu principale
2. Specifica la cartella contenente i file PGN (predefinito: pgn_files)
3. Imposta la dimensione del batch (quante partite processare alla volta)
4. Scegli se reimportare file già elaborati
5. Conferma per avviare l'importazione

Durante l'importazione, verranno mostrati messaggi di avanzamento. Al termine, verranno visualizzate statistiche di base sui dati importati.

### Analisi delle partite

1. Seleziona "Analizza partite" dal menu principale
2. Scegli il tipo di analisi:
   - Statistiche di base
   - Analisi delle aperture
   - Analisi degli avversari
   - Analisi delle fasi di gioco
   - Evoluzione dell'Elo
   - Analisi degli errori
   - Analisi per categoria ECO
   - Esegui tutte le analisi
   - Esporta analisi in CSV/testo
3. Specifica il nome del giocatore da analizzare
4. Visualizza i risultati dell'analisi

I risultati verranno mostrati in formato testuale e, se richiesto, puoi esportarli in file CSV o di testo.

### Visualizzatore di partite

1. Seleziona "Visualizza partite" dal menu principale
2. Usa il visualizzatore interattivo per esplorare le partite
3. Cerca partite per giocatore, data, evento o apertura
4. Naviga nelle partite mossa per mossa

Il visualizzatore a linea di comando mostra la scacchiera usando caratteri ASCII e permette di navigare con comandi semplici.

### Impostazioni

1. Seleziona "Impostazioni" dal menu principale
2. Modifica i seguenti parametri:
   - Giocatore predefinito
   - Cartella PGN
   - Percorso del database
   - Dimensione batch
   - Formato di esportazione predefinito
3. Salva le impostazioni o reinizializza il database

## 5. Interfaccia grafica principale (chessmetrics_gui.py)

L'interfaccia grafica principale offre un'esperienza utente moderna e intuitiva con grafici interattivi e visualizzazioni avanzate.

### Avvio dell'interfaccia grafica

```
python chessmetrics_gui.py
```

### Scheda "Importa PGN"

Questa scheda permette di importare file PGN nel database:

1. Specifica la cartella contenente i file PGN (usa "Sfoglia..." per selezionarla)
2. Imposta la dimensione del batch (quante partite processare alla volta)
3. Seleziona se reimportare file già elaborati
4. Clicca "Importa File PGN" per avviare l'importazione

Durante l'importazione, la barra di progresso e l'area di log mostrano l'avanzamento. Al termine, viene visualizzato un riepilogo dell'operazione.

### Scheda "Analizza"

Questa scheda offre potenti strumenti di analisi statistica:

1. Specifica il nome del giocatore da analizzare
2. Seleziona il tipo di analisi dal menu a tendina
3. Scegli se visualizzare i risultati o esportarli in CSV/testo
4. Clicca "Analizza" per avviare l'analisi

I risultati dell'analisi vengono visualizzati in forma di grafici interattivi:
- Grafici a torta per la distribuzione dei risultati
- Grafici a barre per le aperture più giocate
- Grafici temporali per l'evoluzione dell'Elo
- Grafici comparativi per la performance contro diversi avversari

Puoi interagire con i grafici (zoom, pan) e salvarli come immagini.

### Scheda "Visualizza"

Questa scheda offre un visualizzatore interattivo di partite:

1. Usa il pannello di ricerca a sinistra per trovare partite
   - Cerca per giocatore, data, evento o codice ECO
   - Clicca "Cerca" per visualizzare i risultati
2. Seleziona una partita dalla lista dei risultati
3. Usa i pulsanti di navigazione (|<, <, >, >|) per muoverti nella partita
4. Visualizza le informazioni sulla mossa corrente
5. Opzionalmente, genera una GIF animata della partita

La scacchiera mostra la posizione corrente e si aggiorna automaticamente durante la navigazione.

### Scheda "Impostazioni"

Questa scheda permette di configurare l'applicazione:

1. Specifica il percorso del database
2. Imposta il giocatore predefinito
3. Clicca "Salva Impostazioni" per applicare le modifiche
4. Usa "Reinizializza Database" per creare un nuovo database vuoto

La sezione "Informazioni" mostra dettagli sulla versione dell'applicazione e sulle sue componenti.

## 6. Analisi con motore scacchistico (chess_engine_analysis.py)

Il modulo di analisi con motore scacchistico è un potente strumento che usa motori come Stockfish per analizzare partite e identificare errori.

### Funzionalità del modulo

- **Analisi completa**: Analizza ogni posizione di una partita
- **Analisi posizioni critiche**: Identifica e analizza solo i punti di svolta
- **Identificazione degli errori**: Classifica errori in diverse categorie (blunder, mistake, inaccuracy)
- **Riconoscimento mosse eccellenti**: Identifica mosse particolarmente buone (good move, excellent move)
- **Varianti alternative**: Suggerisce linee di gioco alternative
- **Esportazione dell'analisi**: Esporta in PGN o HTML interattivo
- **Statistiche giocatore**: Calcola statistiche sugli errori commessi

### Utilizzo da linea di comando

Puoi usare lo script direttamente da linea di comando:

```
# Elencare le partite disponibili
python chess_engine_analysis.py --list-games

# Analizzare una partita completa
python chess_engine_analysis.py --game-id 123

# Analizzare solo le posizioni critiche
python chess_engine_analysis.py --game-id 123 --critical-only

# Esportare in PGN
python chess_engine_analysis.py --game-id 123 --export-pgn partita.pgn

# Esportare in HTML
python chess_engine_analysis.py --game-id 123 --export-html

# Visualizzare statistiche giocatore
python chess_engine_analysis.py --player-stats "NomeGiocatore"
```

### Parametri di configurazione

- `--db-path`: Percorso del database SQLite
- `--engine-path`: Percorso dell'eseguibile del motore di scacchi
- `--depth`: Profondità di analisi (default: 18)
- `--multipv`: Numero di varianti da analizzare (default: 3)
- `--critical-only`: Analizza solo le posizioni critiche
- `--verbose`: Abilita log dettagliati

### Classificazione degli errori

Il modulo classifica gli errori in base alla variazione della valutazione:
- **Blunder (??)**:  Errore grave (≥ 300 centipawns)
- **Mistake (?)**:  Errore significativo (≥ 150 centipawns)
- **Inaccuracy (?!)**:  Imprecisione minore (≥ 50 centipawns)
- **Good move (!)**:  Buona mossa che migliora significativamente la posizione
- **Excellent move (!!)**:  Mossa eccellente che cambia drasticamente la valutazione a favore

### Esportazione dell'analisi

#### Esportazione PGN

Il formato PGN è standardizzato e compatibile con la maggior parte dei software di scacchi. L'analisi viene integrata come commenti alle mosse, mantenendo la struttura originale della partita.

#### Esportazione HTML

Il formato HTML crea una pagina interattiva con:
- Diagrammi delle posizioni critiche
- Commenti sull'analisi
- Indice delle posizioni chiave
- Suggerimenti di varianti alternative

## 7. Interfaccia grafica dell'analizzatore (chess_engine_analysis_gui.py)

L'interfaccia grafica dell'analizzatore offre tutte le funzionalità del modulo di analisi in un'interfaccia user-friendly.

### Avvio dell'interfaccia

```
python chess_engine_analysis_gui.py
```

### Scheda "Analisi"

1. Seleziona una partita dalla tabella
2. Configura i parametri dell'analisi:
   - Profondità: Determina quanto in profondità analizzare (15-25 è un buon valore)
   - Varianti (MultiPV): Quante linee alternative valutare (1-5)
   - Tempo per posizione: Quanto tempo dedicare a ogni posizione (in secondi)
   - Tipo di analisi: Completa o solo posizioni critiche
   - Soglia critica: Per l'analisi delle sole posizioni critiche
3. Configura il motore di scacchi:
   - Lascia vuoto per rilevamento automatico o specifica il percorso
4. Opzioni di esportazione:
   - Seleziona se esportare in PGN o HTML
5. Clicca "Avvia Analisi" per iniziare

Durante l'analisi, l'area di testo mostra i progressi. Al termine, vengono visualizzati i commenti generati e ti viene chiesto se caricare la partita nel visualizzatore.

### Scheda "Visualizzatore"

1. Seleziona una partita analizzata dall'elenco sulla sinistra
2. Usa i controlli di navigazione per esplorare la partita:
   - |< : Prima posizione
   - < : Posizione precedente
   - > : Posizione successiva
   - >| : Ultima posizione
3. Visualizza il grafico della valutazione:
   - L'asse Y mostra la valutazione in pedoni (positivo = vantaggio Bianco)
   - I punti rossi indicano posizioni critiche (errori o mosse eccellenti)
4. Consulta l'analisi dettagliata sotto la scacchiera:
   - Valutazione numerica della posizione
   - Varianti suggerite dal motore
   - Commenti sugli errori o sulle buone mosse
5. Usa il pulsante "Capovolgi scacchiera" per cambiare prospettiva

### Scheda "Statistiche"

1. Seleziona un giocatore dal menu a tendina
2. Clicca "Calcola Statistiche" per analizzare le prestazioni del giocatore
3. Visualizza i grafici delle statistiche:
   - Distribuzione dei risultati (vittorie/pareggi/sconfitte)
   - Media di errori per partita
4. Consulta l'elenco delle partite del giocatore
5. Clicca "Esporta Statistiche CSV" per salvare i dati

### Scheda "Impostazioni"

1. Configura il percorso del database
2. Imposta il percorso predefinito del motore
3. Personalizza le opzioni di visualizzazione:
   - Evidenziazione degli errori
   - Capovolgimento automatico della scacchiera
4. Clicca "Salva Impostazioni" per applicare le modifiche

## 8. Verifica del corretto funzionamento

Per assicurarti che ChessMetrics Pro funzioni correttamente, segui questa procedura di verifica per ogni componente:

### Verifica del database

1. **Controllo della connessione**:
   - Avvia una delle interfacce (grafica o testuale)
   - Se il database non esiste, l'applicazione dovrebbe offrire di crearlo
   - Verifica che non ci siano errori di connessione

2. **Verifica della struttura**:
   - Importa almeno un file PGN
   - Verifica che la partita sia visibile nella lista delle partite
   - Se necessario, esegui `python chessmetrics_menu.py --list-games` per vedere l'elenco da console

### Verifica dell'importazione PGN

1. **Preparazione file di test**:
   - Crea una cartella "pgn_files" se non esiste
   - Inserisci alcuni file PGN di test (puoi trovarli online o esportarli da piattaforme come chess.com o lichess.org)

2. **Test di importazione**:
   - Avvia l'interfaccia grafica (`python chessmetrics_gui.py`)
   - Vai alla scheda "Importa PGN"
   - Configura la cartella PGN e avvia l'importazione
   - Verifica che il processo si completi senza errori
   - Controlla che le partite siano state importate correttamente

### Verifica dell'analisi statistica

1. **Test di analisi base**:
   - Vai alla scheda "Analizza" (in chessmetrics_gui.py)
   - Inserisci il nome di un giocatore presente nel database
   - Seleziona "Statistiche di base" e avvia l'analisi
   - Verifica che vengano generati grafici e dati corretti

2. **Test di esportazione**:
   - Esegui un'analisi e seleziona l'opzione di esportazione in CSV
   - Verifica che il file venga creato e contenga i dati corretti

### Verifica dell'analisi con motore

1. **Configurazione motore**:
   - Assicurati che Stockfish sia installato
   - Avvia l'interfaccia dell'analizzatore (`python chess_engine_analysis_gui.py`)
   - Verifica che il motore venga rilevato automaticamente o specifica il percorso

2. **Test di analisi base**:
   - Seleziona una partita e configura un'analisi rapida (profondità 15, tempo 0.2s)
   - Avvia l'analisi e verifica che venga completata senza errori
   - Controlla i commenti generati per assicurarti che siano sensati

3. **Test di analisi posizioni critiche**:
   - Seleziona l'opzione "Solo posizioni critiche"
   - Imposta una soglia (es. 100)
   - Avvia l'analisi e verifica che vengano identificate posizioni critiche

4. **Test di esportazione**:
   - Esporta l'analisi in formato PGN e verifica che il file sia correttamente formattato
   - Esporta l'analisi in formato HTML e verifica che la pagina si apra correttamente nel browser

### Verifica del visualizzatore

1. **Caricamento partita**:
   - Vai alla scheda "Visualizza" (in chessmetrics_gui.py) o avvia il visualizzatore nell'analizzatore
   - Cerca e seleziona una partita
   - Verifica che le informazioni della partita vengano visualizzate correttamente

2. **Navigazione**:
   - Usa i pulsanti di navigazione per muoverti nella partita
   - Verifica che la scacchiera si aggiorni correttamente
   - Controlla che le informazioni sulla mossa siano accurate

3. **Test del grafico** (solo nell'analizzatore):
   - Carica una partita analizzata
   - Verifica che il grafico della valutazione venga visualizzato
   - Controlla che i punti critici siano evidenziati

### Test integrato completo

1. **Flusso di lavoro completo**:
   - Importa un file PGN con alcune partite
   - Esegui un'analisi statistica di un giocatore
   - Analizza una partita con il motore
   - Visualizza la partita analizzata
   - Esporta l'analisi in diversi formati

2. **Verifica dei log**:
   - Controlla i file di log in logs/chessmetrics.log e logs/chess_engine_analysis.log
   - Verifica che non ci siano errori critici

## 9. Funzionalità avanzate

### Analisi delle posizioni critiche

L'analisi delle posizioni critiche è una delle funzionalità più potenti di ChessMetrics Pro. Invece di analizzare ogni singola posizione (che può richiedere molto tempo), si concentra solo sui punti di svolta della partita.

Una posizione è considerata "critica" quando la valutazione cambia significativamente rispetto alla posizione precedente, indicando che è stata giocata una mossa particolarmente buona o cattiva.

Per ottimizzare l'analisi delle posizioni critiche:

1. **Regolazione della soglia**:
   - Soglia bassa (50-70): Identifica anche piccole imprecisioni
   - Soglia media (100-150): Evidenzia errori significativi ma ignora piccole imprecisioni
   - Soglia alta (200+): Identifica solo errori gravi

2. **Interpretazione dei risultati**:
   - Gli errori vengono classificati per gravità (blunder, mistake, inaccuracy)
   - Le buone mosse vengono riconosciute (good move, excellent move)
   - I commenti spiegano il cambiamento nella valutazione

Questa modalità di analisi è particolarmente utile per:
- Analisi rapida di molte partite
- Identificazione dei punti chiave della partita
- Focus sui principali errori da correggere

### Valutazione del motore

Le valutazioni dei motori di scacchi sono generalmente espresse in centesimi di pedone (centipawns):

- Un valore di +1.00 significa che il Bianco ha un vantaggio equivalente a un pedone
- Un valore di -2.00 significa che il Nero ha un vantaggio equivalente a due pedoni
- "M5" indica scacco matto in 5 mosse

Per interpretare le valutazioni:
- 0.00 a ±0.20: Posizione equilibrata
- ±0.30 a ±0.80: Leggero vantaggio
- ±0.90 a ±1.50: Vantaggio chiaro
- ±1.60 a ±2.50: Vantaggio decisivo
- Oltre ±2.50: Posizione probabilmente vinta

### Generazione di GIF animate

ChessMetrics Pro può generare GIF animate delle partite, utili per condividere o studiare le partite:

1. Apri una partita nel visualizzatore
2. Clicca su "Genera GIF"
3. Scegli un nome file e imposta il ritardo tra i frame
4. Attendi il completamento della generazione

Le GIF create possono essere condivise facilmente sui social media o su siti web.

### Analisi avanzata per categoria ECO

ChessMetrics Pro offre un'analisi dettagliata delle prestazioni per categoria ECO (Encyclopaedia of Chess Openings):

- **Categoria A**: Aperture di Fianchetto (1.c4, 1.Nf3, etc.)
- **Categoria B**: Aperture Semiaperte (1.e4 eccetto 1...e5)
- **Categoria C**: Aperture Aperte (1.e4 e5)
- **Categoria D**: Aperture Chiuse (1.d4 d5)
- **Categoria E**: Difese Indiane (1.d4 Nf6 eccetto 2.c4 e5)

Questa analisi ti permette di:
- Identificare le aperture con cui hai maggior successo
- Scoprire quali aperture evitare
- Migliorare la tua preparazione in apertura

## 10. Risoluzione dei problemi

### Problemi di database

**Problema**: "Impossibile connettersi al database" o "Database non trovato"

**Soluzioni**:
1. Verifica che il percorso del database specificato sia corretto
2. Assicurati che la directory contenente il database esista
3. Verifica i permessi di lettura/scrittura sulla directory e sul file
4. Prova a reinizializzare il database dalle impostazioni

**Problema**: "Errore durante l'esecuzione di una query"

**Soluzioni**:
1. Controlla che il database non sia corrotto
2. Verifica che la struttura del database sia aggiornata
3. Prova a reinizializzare il database
4. Controlla i log per dettagli sull'errore esatto

### Problemi con motore di scacchi

**Problema**: "Impossibile avviare il motore di scacchi"

**Soluzioni**:
1. Verifica che Stockfish sia installato correttamente
2. Controlla il percorso dell'eseguibile nelle impostazioni
3. Assicurati che l'eseguibile abbia i permessi di esecuzione
4. Prova con un'altra versione di Stockfish

**Problema**: "L'analisi è troppo lenta"

**Soluzioni**:
1. Riduci la profondità di analisi (usa valori 15-18)
2. Riduci il tempo per posizione (0.2-0.3 secondi)
3. Usa l'opzione "Solo posizioni critiche"
4. Riduci il numero di varianti (MultiPV)

### Problemi di importazione PGN

**Problema**: "Errore durante l'importazione dei file PGN"

**Soluzioni**:
1. Verifica che i file PGN siano formattati correttamente
2. Controlla che non ci siano caratteri speciali nei nomi file
3. Prova a importare i file uno alla volta
4. Controlla lo spazio disponibile sul disco

**Problema**: "Nessun file PGN trovato"

**Soluzioni**:
1. Verifica che i file abbiano estensione .pgn
2. Controlla che la cartella PGN specificata sia corretta
3. Assicurati che la cartella non sia vuota

### Problemi di interfaccia grafica

**Problema**: "L'interfaccia si blocca durante l'analisi"

**Soluzioni**:
1. Riduci i parametri di analisi (profondità, tempo)
2. Attendi il completamento dell'operazione in corso
3. Chiudi e riavvia l'applicazione
4. Verifica le risorse di sistema disponibili

**Problema**: "I grafici non vengono visualizzati correttamente"

**Soluzioni**:
1. Verifica che matplotlib sia installato correttamente
2. Assicurati che ci siano dati sufficienti per generare i grafici
3. Ridimensiona la finestra dell'applicazione
4. Aggiorna PyQt e matplotlib alle versioni più recenti

### Segnalazione di bug

Se riscontri problemi non trattati in questa sezione:
1. Controlla i file di log in logs/
2. Prendi nota dei passaggi esatti per riprodurre il problema
3. Segnala il bug fornendo:
   - Versione di ChessMetrics Pro
   - Sistema operativo
   - Versione di Python e delle librerie
   - File di log pertinenti
   - Passaggi per riprodurre il problema

---

Questo manuale d'uso completo dovrebbe aiutarti a sfruttare al meglio tutte le potenti funzionalità di ChessMetrics Pro. La suite è progettata per essere flessibile e adattarsi alle tue esigenze, che tu sia un principiante che vuole migliorare o un giocatore esperto che cerca analisi dettagliate.

Buona analisi e buon gioco!
