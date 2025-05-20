# Manuale d'uso di ChessEngine Analysis GUI

## Indice
1. [Introduzione](#1-introduzione)
2. [Requisiti e installazione](#2-requisiti-e-installazione)
3. [Interfaccia e funzionalità principali](#3-interfaccia-e-funzionalità-principali)
4. [Guida dettagliata all'utilizzo](#4-guida-dettagliata-allutilizzo)
5. [Verifica del corretto funzionamento](#5-verifica-del-corretto-funzionamento)
6. [Risoluzione dei problemi comuni](#6-risoluzione-dei-problemi-comuni)
7. [Funzionalità avanzate](#7-funzionalità-avanzate)
8. [Riferimenti tecnici](#8-riferimenti-tecnici)

## 1. Introduzione

ChessEngine Analysis GUI è un'applicazione completa dedicata all'analisi delle partite di scacchi che integra un motore di valutazione (come Stockfish) per valutare posizioni, identificare errori e fornire statistiche dettagliate sui giocatori. Questo software è progettato per essere utile sia a giocatori amatoriali che vogliono migliorare il loro gioco che ad analisti e allenatori che necessitano di strumenti professionali.

### 1.1 Caratteristiche principali

- **Analisi completa o selettiva delle partite di scacchi**: Esamina ogni mossa o concentrati solo sulle posizioni critiche
- **Identificazione automatica degli errori**: Rileva blunders, mistakes e inaccuracies con soglie personalizzabili
- **Visualizzazione interattiva**: Naviga attraverso la partita con una scacchiera interattiva
- **Grafico della valutazione**: Visualizza l'andamento della valutazione durante la partita
- **Esportazione delle analisi**: Salva le analisi in formato PGN standard o HTML interattivo con diagrammi
- **Statistiche dei giocatori**: Esplora le prestazioni dei giocatori con grafici dettagliati
- **Integrazione database**: Memorizza e recupera le analisi per riferimenti futuri
- **Interfaccia multilingue**: Completamente in italiano per una migliore esperienza utente

## 2. Requisiti e installazione

### 2.1 Requisiti di sistema

- Python 3.6 o superiore
- Librerie Python: PyQt6, python-chess, matplotlib, sqlite3
- Motore di scacchi UCI (preferibilmente Stockfish)
- 100MB di spazio libero su disco
- Sistema operativo: Windows, macOS o Linux

### 2.2 Installazione

1. **Installazione delle dipendenze Python**:
   ```bash
   pip install PyQt6 python-chess matplotlib
   ```

2. **Installazione di Stockfish**:
   - Scarica Stockfish dal sito ufficiale: [stockfishchess.org](https://stockfishchess.org/download/)
   - Estrai l'eseguibile in una cartella a tua scelta
   - L'applicazione cercherà automaticamente Stockfish nei percorsi comuni, ma è consigliato specificare manualmente il percorso nelle impostazioni

3. **Download e configurazione dell'applicazione**:
   - Scarica i file `chess_engine_analysis.py`, `chess_engine_analysis_gui.py` e `data_utils.py`
   - Assicurati che i file siano nella stessa cartella

4. **Configurazione del database**:
   - Di default, l'applicazione creerà un database SQLite nella cartella predefinita
   - Per utilizzare un database esistente, puoi specificare il percorso nelle impostazioni

### 2.3 Avvio dell'applicazione

Esegui il programma con il comando:
```bash
python chess_engine_analysis_gui.py
```

## 3. Interfaccia e funzionalità principali

L'interfaccia di ChessEngine Analysis GUI è organizzata in quattro schede principali, ciascuna dedicata a una funzionalità specifica:

### 3.1 Scheda "Analisi"

Questa scheda permette di:
- Selezionare una partita dal database
- Configurare le opzioni di analisi (profondità, varianti, tempo)
- Scegliere tra analisi completa o solo delle posizioni critiche
- Esportare i risultati in formato PGN o HTML
- Visualizzare i commenti generati dall'analisi

### 3.2 Scheda "Visualizzatore"

Permette di:
- Visualizzare la scacchiera con le posizioni analizzate
- Navigare tra le mosse della partita
- Visualizzare il grafico dell'andamento della valutazione
- Esplorare i commenti e le varianti suggerite dal motore
- Esportare l'analisi visualizzata

### 3.3 Scheda "Statistiche"

Offre:
- Selezione di un giocatore dal database
- Calcolo delle statistiche di gioco (vittorie, sconfitte, pareggi)
- Visualizzazione grafica delle prestazioni
- Analisi degli errori commessi dal giocatore
- Elenco delle partite giocate con possibilità di caricamento diretto nel visualizzatore

### 3.4 Scheda "Impostazioni"

Consente di configurare:
- Percorso del database
- Percorso del motore di scacchi
- Opzioni di visualizzazione
- Preferenze generali dell'applicazione

## 4. Guida dettagliata all'utilizzo

### 4.1 Analisi di una partita

#### 4.1.1 Selezione della partita
1. Vai alla scheda "Analisi"
2. La tabella mostrerà l'elenco delle partite disponibili nel database
3. Seleziona una partita cliccando sulla riga corrispondente
4. Se non vedi partite, clicca su "Aggiorna Lista"

#### 4.1.2 Configurazione dell'analisi
1. **Profondità**: Determina quanto in profondità il motore analizzerà ogni posizione (valori più alti = analisi più accurate ma più lente)
2. **Varianti (MultiPV)**: Imposta quante linee di gioco alternative verranno analizzate
3. **Tempo per posizione**: Specifica quanto tempo (in secondi) dedicare all'analisi di ogni posizione
4. **Tipo di analisi**:
   - "Analisi completa": analizza ogni posizione della partita
   - "Solo posizioni critiche": analizza solo le posizioni dove si verificano cambi significativi nella valutazione
   - "Soglia": se è selezionata l'opzione "Solo posizioni critiche", determina quanto deve variare la valutazione (in centipawn) per considerare una posizione come critica

#### 4.1.3 Avvio dell'analisi
1. Clicca sul pulsante "Avvia Analisi"
2. Attendi il completamento dell'analisi (la barra di progresso mostra l'avanzamento)
3. I risultati verranno visualizzati nell'area di testo sotto forma di commenti
4. Al termine, ti verrà chiesto se desideri caricare la partita nel visualizzatore

#### 4.1.4 Esportazione dell'analisi
1. Seleziona "Esporta analisi in PGN" per salvare l'analisi in formato PGN standard
2. Seleziona "Esporta analisi in HTML" per creare una pagina web interattiva con diagrammi
3. Specifica il percorso di salvataggio o utilizza quello predefinito

### 4.2 Utilizzo del visualizzatore

#### 4.2.1 Caricamento di una partita analizzata
1. Vai alla scheda "Visualizzatore"
2. Seleziona una partita già analizzata dall'elenco
3. La scacchiera e il grafico si aggiorneranno automaticamente

#### 4.2.2 Navigazione nella partita
1. Utilizza i pulsanti di navigazione sotto la scacchiera:
   - "|<" - Prima posizione (posizione iniziale)
   - "<" - Posizione precedente
   - ">" - Posizione successiva
   - ">|" - Ultima posizione
2. La scacchiera si aggiornerà per mostrare la posizione corrente
3. L'area di testo mostrerà i dettagli dell'analisi per la mossa selezionata

#### 4.2.3 Interpretazione del grafico
1. Il grafico mostra l'andamento della valutazione durante la partita
2. L'asse X rappresenta le mosse, l'asse Y la valutazione in pedoni
3. Valori positivi indicano vantaggio per il Bianco, negativi per il Nero
4. I punti rossi evidenziano le posizioni critiche (errori o mosse eccellenti)

#### 4.2.4 Personalizzazione della visualizzazione
1. Clicca su "Capovolgi scacchiera" per cambiare la prospettiva
2. Nelle impostazioni, puoi attivare l'opzione "Capovolgi automaticamente scacchiera in base al turno"

### 4.3 Analisi delle statistiche dei giocatori

#### 4.3.1 Selezione del giocatore
1. Vai alla scheda "Statistiche"
2. Seleziona un giocatore dal menu a discesa
3. Clicca su "Calcola Statistiche"

#### 4.3.2 Interpretazione dei dati
I dati visualizzati includono:
- Numero totale di partite giocate
- Vittorie, pareggi e sconfitte (percentuali)
- Media di errori gravi e imprecisioni per partita
- Grafici a torta che mostrano la distribuzione dei risultati
- Grafici a barre che mostrano la distribuzione degli errori

#### 4.3.3 Esportazione delle statistiche
1. Clicca su "Esporta Statistiche CSV"
2. Scegli il percorso di salvataggio
3. Il file CSV conterrà tutte le statistiche del giocatore selezionato

### 4.4 Configurazione delle impostazioni

#### 4.4.1 Impostazioni database
1. Vai alla scheda "Impostazioni"
2. Specifica il percorso del database SQLite
3. Per cambiare database, sarà necessario riavviare l'applicazione

#### 4.4.2 Impostazioni motore
1. Specifica il percorso dell'eseguibile Stockfish o altro motore UCI
2. Il percorso verrà utilizzato come predefinito nella scheda Analisi

#### 4.4.3 Opzioni di visualizzazione
1. Attiva/disattiva "Evidenzia errori gravi"
2. Attiva/disattiva "Capovolgi automaticamente scacchiera"

## 5. Verifica del corretto funzionamento

Per assicurarti che l'applicazione funzioni correttamente, esegui i seguenti test:

### 5.1 Verifica del database

1. **Test di connessione database**:
   - Vai alla scheda "Analisi" e verifica che la lista delle partite venga caricata
   - Se non vedi partite, controlla se il percorso del database è corretto nella scheda "Impostazioni"
   - Assicurati che il database contenga le tabelle necessarie (games, moves, ecc.)

2. **Test di struttura del database**:
   - Se il programma si avvia senza errori, la struttura del database dovrebbe essere corretta
   - In caso di errori, verifica che il database non sia danneggiato

### 5.2 Verifica del motore di scacchi

1. **Test di connessione al motore**:
   - Seleziona una partita nella scheda "Analisi"
   - Imposta una profondità bassa (es. 10) e un tempo di analisi breve (es. 0.2s)
   - Clicca su "Avvia Analisi" e verifica che non ci siano errori

2. **Test dell'output del motore**:
   - Se l'analisi inizia correttamente, il motore è configurato correttamente
   - Verifica che vengano prodotti risultati di analisi con valutazioni numeriche

### 5.3 Verifica dell'interfaccia utente

1. **Test di navigazione**:
   - Passa tra le diverse schede e verifica che tutte si carichino correttamente
   - Prova tutte le funzioni di navigazione nel visualizzatore

2. **Test di visualizzazione**:
   - Carica una partita analizzata e verifica che la scacchiera mostri correttamente le posizioni
   - Controlla che il grafico di valutazione venga visualizzato

### 5.4 Verifica delle funzionalità complete

Per un test completo, esegui questa procedura:

1. Seleziona una partita nella scheda "Analisi"
2. Configura l'analisi con l'opzione "Solo posizioni critiche" e una soglia di 100
3. Avvia l'analisi e attendi il completamento
4. Carica la partita nel visualizzatore
5. Naviga tra le posizioni e verifica che le valutazioni e i commenti siano coerenti
6. Esporta l'analisi in PGN e HTML
7. Vai alla scheda "Statistiche" e calcola le statistiche per un giocatore
8. Esporta le statistiche in CSV

Se tutte queste operazioni funzionano senza errori, l'applicazione è configurata correttamente.

## 6. Risoluzione dei problemi comuni

### 6.1 Problemi di database

**Problema**: "Impossibile connettersi al database"
- **Soluzione**: Verifica che il percorso del database sia corretto
- **Soluzione**: Controlla che il database esista e sia accessibile in lettura/scrittura
- **Soluzione**: Assicurati che il database non sia bloccato da un'altra applicazione

**Problema**: "Database danneggiato o tabelle mancanti"
- **Soluzione**: L'applicazione dovrebbe creare automaticamente le tabelle necessarie
- **Soluzione**: Se il problema persiste, crea un nuovo database vuoto

### 6.2 Problemi con il motore di scacchi

**Problema**: "Impossibile avviare il motore di scacchi"
- **Soluzione**: Verifica che il percorso dell'eseguibile sia corretto
- **Soluzione**: Assicurati che l'eseguibile abbia i permessi di esecuzione
- **Soluzione**: Prova a installare Stockfish in una posizione standard

**Problema**: "Analisi troppo lenta"
- **Soluzione**: Riduci la profondità di analisi
- **Soluzione**: Riduci il tempo di analisi per posizione
- **Soluzione**: Utilizza l'analisi delle sole posizioni critiche

### 6.3 Problemi di interfaccia

**Problema**: "L'interfaccia si blocca durante l'analisi"
- **Soluzione**: L'analisi viene eseguita in un thread separato, quindi l'interfaccia dovrebbe rimanere reattiva
- **Soluzione**: In caso di blocco persistente, riavvia l'applicazione

**Problema**: "La scacchiera non si aggiorna correttamente"
- **Soluzione**: Fai clic su un'altra scheda e poi torna alla scheda "Visualizzatore"
- **Soluzione**: Ricarica la partita selezionandola nuovamente

### 6.4 Problemi di esportazione

**Problema**: "Errore durante l'esportazione in PGN/HTML"
- **Soluzione**: Verifica che la cartella di destinazione esista e sia accessibile in scrittura
- **Soluzione**: Assicurati che il file non sia aperto in un'altra applicazione
- **Soluzione**: Controlla che ci sia spazio sufficiente sul disco

## 7. Funzionalità avanzate

### 7.1 Analisi delle posizioni critiche

L'analisi delle posizioni critiche è particolarmente utile per partite lunghe o quando si desidera un'analisi rapida. Ecco come ottimizzare questa funzione:

1. **Regolazione della soglia**: 
   - Soglia bassa (50-100): Identifica anche piccole imprecisioni
   - Soglia media (100-200): Evidenzia errori significativi
   - Soglia alta (>200): Rileva solo errori gravi

2. **Interpretazione dei risultati**:
   - Blunder (??): Errore grave che cambia drasticamente la valutazione (≥300 centipawns)
   - Mistake (?): Errore significativo (≥150 centipawns)
   - Inaccuracy (?!): Imprecisione minore (≥50 centipawns)
   - Good move (!): Buona mossa che migliora significativamente la posizione
   - Excellent move (!!): Mossa eccellente che cambia drasticamente la valutazione a favore

### 7.2 Comprendere la valutazione del motore

Le valutazioni sono espresse in centesimi di pedone (centipawns):
- +1.00 significa che il Bianco ha un vantaggio equivalente a un pedone
- -2.00 significa che il Nero ha un vantaggio equivalente a due pedoni
- "M5" significa scacco matto in 5 mosse

Il grafico della valutazione mostra l'andamento di questi valori durante la partita, permettendo di identificare visivamente il momento in cui si verificano errori significativi.

### 7.3 Esportazione HTML interattiva

L'esportazione HTML crea una pagina web interattiva con:
- Informazioni sulla partita e sui giocatori
- Indice delle posizioni critiche con link diretti
- Diagrammi delle posizioni chiave
- Commenti generati dal motore
- Varianti alternative suggerite

Questa rappresentazione è ideale per:
- Condividere l'analisi con altri giocatori
- Pubblicare l'analisi su siti web o blog
- Stampare l'analisi con diagrammi

### 7.4 Analisi statistica avanzata

Le statistiche dei giocatori permettono di:
- Identificare pattern ricorrenti negli errori
- Riconoscere debolezze specifiche per tipo di apertura
- Monitorare i progressi nel tempo
- Confrontare le prestazioni con altri giocatori

## 8. Riferimenti tecnici

### 8.1 Struttura del database

Il database utilizza le seguenti tabelle principali:
- `games`: Informazioni generali sulle partite
- `moves`: Mosse individuali per ogni partita
- `engine_analysis`: Risultati dell'analisi del motore
- `engine_variations`: Varianti calcolate dal motore
- `engine_comments`: Commenti generati in base all'analisi
- `player_stats`: Statistiche aggregate per giocatore

### 8.2 Parametri di configurazione avanzati

Oltre alle opzioni disponibili nell'interfaccia, è possibile modificare parametri avanzati direttamente nel file Python:
- `DEFAULT_DB_PATH`: Percorso predefinito del database
- `DEFAULT_PGN_FOLDER`: Cartella per i file PGN
- `EXPORT_FOLDER`: Cartella per le esportazioni
- `VERSION`: Versione corrente del software

### 8.3 Utilizzo da riga di comando

Il modulo `chess_engine_analysis.py` può essere utilizzato anche direttamente da riga di comando:

```bash
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
python chess_engine_analysis.py --player-stats "Blackeyes972"
```

Questo permette di automatizzare l'analisi attraverso script o di integrare il modulo in altri progetti.

---

Questo manuale d'uso dovrebbe fornirti tutte le informazioni necessarie per utilizzare al meglio ChessEngine Analysis GUI. Per qualsiasi problema non trattato in questa guida, controlla i file di log nella cartella "logs" o contatta il supporto.