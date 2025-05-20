# Manuale d'uso di ChessEngine Analysis GUI

## Indice
1. Introduzione
2. Requisiti e installazione
3. Panoramica dell'interfaccia
4. Guida all'uso
   - 4.1 Analisi delle partite
   - 4.2 Visualizzazione e navigazione
   - 4.3 Statistiche dei giocatori
   - 4.4 Configurazione
5. Funzionalità avanzate
6. Risoluzione dei problemi
7. Verifiche di funzionamento

---

## 1. Introduzione

ChessEngine Analysis GUI è un'applicazione completa per l'analisi delle partite di scacchi che integra un motore di analisi (come Stockfish) per valutare posizioni, identificare errori e fornire statistiche dettagliate sui giocatori. Il software permette di visualizzare l'andamento della valutazione delle partite, esportare le analisi in diversi formati ed esplorare le statistiche delle prestazioni dei giocatori.

**Caratteristiche principali:**
- Analisi completa o selettiva delle partite di scacchi
- Identificazione automatica delle posizioni critiche
- Visualizzazione interattiva con grafico della valutazione
- Esportazione delle analisi in formato PGN e HTML interattivo
- Statistiche dettagliate dei giocatori
- Interfaccia intuitiva multilingue (italiano)

## 2. Requisiti e installazione

### Requisiti di sistema:
- Python 3.6 o superiore
- PyQt6
- python-chess
- matplotlib
- Un motore di scacchi UCI (preferibilmente Stockfish)
- Circa 100MB di spazio su disco

### Procedura di installazione:

1. **Installazione delle dipendenze Python:**
   ```
   pip install PyQt6 python-chess matplotlib
   ```

2. **Installazione del motore di scacchi:**
   - Scarica Stockfish dal sito ufficiale [stockfishchess.org](https://stockfishchess.org/download/)
   - Estrai l'eseguibile in una cartella a tua scelta
   - Il software può rilevare automaticamente Stockfish nei percorsi più comuni, ma è consigliabile specificare manualmente il percorso nella scheda Impostazioni

3. **Avvio dell'applicazione:**
   ```
   python chess_engine_analysis_gui.py
   ```

## 3. Panoramica dell'interfaccia

L'interfaccia è organizzata in quattro schede principali:

### 3.1. Scheda "Analisi"
Dedicata all'analisi delle partite, consente di selezionare una partita dal database e avviare l'analisi con varie opzioni di configurazione.

### 3.2. Scheda "Visualizzatore"
Permette di visualizzare e navigare attraverso l'analisi di una partita, con scacchiera interattiva, grafico della valutazione e dettagli su ogni posizione.

### 3.3. Scheda "Statistiche"
Fornisce statistiche dettagliate sui giocatori, tra cui percentuale di vittorie, media di errori per partita e grafici riassuntivi.

### 3.4. Scheda "Impostazioni"
Consente di configurare i parametri del software, come il percorso del database e del motore di scacchi.

## 4. Guida all'uso

### 4.1 Analisi delle partite

#### 4.1.1 Selezionare una partita
1. Nella scheda "Analisi", verrà visualizzata una tabella con le partite disponibili nel database.
2. Fai clic sul pulsante "Aggiorna Lista" per visualizzare le partite più recenti.
3. Seleziona una partita dalla tabella facendo clic sulla riga corrispondente.

#### 4.1.2 Configurare le opzioni di analisi
1. **Profondità**: Determina quanto in profondità il motore analizzerà ogni posizione. Valori maggiori offrono analisi più accurate ma richiedono più tempo.
2. **Varianti (MultiPV)**: Imposta il numero di varianti alternative da analizzare per ogni posizione.
3. **Tempo per posizione**: Specifica il tempo (in secondi) da dedicare all'analisi di ogni posizione.
4. **Tipo di analisi**:
   - **Analisi completa**: Analizza ogni posizione della partita.
   - **Solo posizioni critiche**: Analizza solo le posizioni in cui si verificano variazioni significative della valutazione.
   - **Soglia (centipawns)**: Se è selezionata l'opzione "Solo posizioni critiche", questa impostazione determina quanto deve variare la valutazione per considerare una posizione come critica.
5. **Motore**: Specifica il percorso dell'eseguibile del motore di scacchi. Se lasciato vuoto, il software tenterà di rilevare automaticamente Stockfish.

#### 4.1.3 Opzioni di esportazione
1. **Esporta analisi in PGN**: Salva l'analisi in formato PGN standard, con commenti e varianti incorporate.
2. **Esporta analisi in HTML**: Crea una pagina HTML interattiva con diagrammi delle posizioni critiche.

#### 4.1.4 Avviare l'analisi
1. Fai clic sul pulsante "Avvia Analisi".
2. Il progresso dell'analisi verrà visualizzato nell'area di testo sottostante e nella barra di progresso.
3. Al termine dell'analisi, verranno visualizzati i commenti generati e ti verrà chiesto se desideri caricare la partita nel visualizzatore.

#### 4.1.5 Visualizzare un'analisi esistente
1. Se una partita è già stata analizzata, puoi visualizzare i risultati esistenti facendo clic sul pulsante "Mostra Analisi Esistente".
2. I commenti dell'analisi verranno visualizzati nell'area di testo sottostante.

### 4.2 Visualizzazione e navigazione

#### 4.2.1 Caricare una partita analizzata
1. Nella scheda "Visualizzatore", verrà visualizzata una tabella con le partite analizzate.
2. Seleziona una partita dalla tabella per caricarla nel visualizzatore.

#### 4.2.2 Navigare tra le posizioni
1. Utilizza i pulsanti di navigazione sotto la scacchiera:
   - **|<** : Prima posizione (posizione iniziale)
   - **<** : Posizione precedente
   - **>** : Posizione successiva
   - **>|** : Ultima posizione

#### 4.2.3 Analizzare la posizione corrente
1. La scacchiera mostra la posizione corrente.
2. L'area di testo sotto la scacchiera mostra:
   - La mossa che ha portato alla posizione corrente
   - La valutazione del motore
   - Le principali varianti calcolate
   - Eventuali commenti sulla qualità della mossa

#### 4.2.4 Interpretare il grafico della valutazione
1. Il grafico mostra l'andamento della valutazione durante la partita.
2. L'asse X rappresenta il numero di mosse, l'asse Y la valutazione in pedoni.
3. Valori positivi indicano vantaggio per il Bianco, valori negativi per il Nero.
4. I punti rossi evidenziano le posizioni critiche (errori gravi o mosse eccellenti).

#### 4.2.5 Personalizzare la visualizzazione
1. Fai clic sul pulsante "Capovolgi scacchiera" per cambiare prospettiva.
2. Nella scheda "Impostazioni", puoi attivare l'opzione "Capovolgi automaticamente scacchiera in base al turno" per visualizzare la scacchiera sempre dal punto di vista del giocatore che deve muovere.

#### 4.2.6 Esportare l'analisi
1. Fai clic su "Esporta PGN" per salvare l'analisi in formato PGN.
2. Fai clic su "Esporta HTML" per creare una pagina HTML interattiva con l'analisi e i diagrammi delle posizioni critiche.

### 4.3 Statistiche dei giocatori

#### 4.3.1 Selezionare un giocatore
1. Nella scheda "Statistiche", seleziona un giocatore dal menu a discesa.
2. Fai clic su "Calcola Statistiche" per analizzare le prestazioni del giocatore.

#### 4.3.2 Interpretare le statistiche
Le statistiche del giocatore includono:
- Numero totale di partite giocate
- Numero di vittorie, pareggi e sconfitte
- Percentuale di vittorie
- Media di errori gravi (blunder) per partita
- Media di errori (mistake) per partita
- Data dell'ultimo aggiornamento

#### 4.3.3 Analizzare i grafici
1. **Grafico a torta**: Mostra la distribuzione di vittorie, pareggi e sconfitte.
2. **Grafico a barre**: Illustra la media di errori gravi e errori per partita.

#### 4.3.4 Esplorare le partite del giocatore
1. La tabella nella parte inferiore della scheda mostra le partite giocate dal giocatore selezionato.
2. Seleziona una partita e fai clic su "Carica Partita Selezionata nel Visualizzatore" per analizzarla in dettaglio.

#### 4.3.5 Esportare le statistiche
1. Fai clic su "Esporta Statistiche CSV" per salvare le statistiche del giocatore in un file CSV.
2. Il file CSV include le statistiche generali e un'analisi degli errori per tipo di apertura.

### 4.4 Configurazione

#### 4.4.1 Impostazioni database
1. Nella scheda "Impostazioni", puoi specificare il percorso del database SQLite.
2. Fai clic su "Sfoglia..." per selezionare un file di database esistente.

#### 4.4.2 Impostazioni motore
1. Specifica il percorso predefinito del motore di scacchi (Stockfish).
2. Questo percorso verrà utilizzato come predefinito nella scheda "Analisi".

#### 4.4.3 Opzioni di visualizzazione
1. **Evidenzia errori gravi**: Attiva o disattiva l'evidenziazione degli errori gravi nel visualizzatore.
2. **Capovolgi automaticamente scacchiera**: Attiva o disattiva il capovolgimento automatico della scacchiera in base al turno.

#### 4.4.4 Salvare le impostazioni
1. Fai clic su "Salva Impostazioni" per applicare le modifiche.
2. Se modifichi il percorso del database, ti verrà chiesto di riavviare l'applicazione.

## 5. Funzionalità avanzate

### 5.1 Analisi delle posizioni critiche
L'analisi delle posizioni critiche è particolarmente utile per partite lunghe o quando si desidera un'analisi rapida. Il software analizza l'intera partita ma commenta solo le posizioni in cui si verifica una variazione significativa della valutazione (determinata dalla soglia in centipawns).

### 5.2 Analisi della valutazione
La valutazione è espressa in centesimi di pedone (centipawns). Un valore di +1.00 indica che il Bianco ha un vantaggio equivalente a un pedone. Valori positivi indicano vantaggio per il Bianco, valori negativi per il Nero.

### 5.3 Tipi di errori
Il software classifica gli errori in diverse categorie:
- **Blunder (??)**:  Errore grave che cambia drasticamente la valutazione (≥ 300 centipawns)
- **Mistake (?)**:  Errore significativo (≥ 150 centipawns)
- **Inaccuracy (?!)**:  Imprecisione minore (≥ 50 centipawns)
- **Good move (!)**:  Buona mossa che migliora significativamente la posizione
- **Excellent move (!!)**:  Mossa eccellente che cambia drasticamente la valutazione a favore

### 5.4 Filtri personalizzati
È possibile filtrare le partite per giocatore, evento o data utilizzando le funzionalità di ricerca incorporate nelle tabelle. Fai clic con il tasto destro sull'intestazione di una colonna per accedere alle opzioni di filtro.

## 6. Risoluzione dei problemi

### 6.1 Il motore non viene rilevato automaticamente
1. Verifica che Stockfish sia installato correttamente.
2. Specifica manualmente il percorso completo dell'eseguibile di Stockfish nella scheda "Impostazioni".
3. Assicurati che l'eseguibile abbia i permessi di esecuzione adeguati.

### 6.2 Errori di connessione al database
1. Verifica che il percorso del database sia corretto.
2. Assicurati che il database esista e sia accessibile.
3. Controlla che il database non sia bloccato da un'altra applicazione.

### 6.3 L'analisi è troppo lenta
1. Riduci la profondità di analisi.
2. Utilizza l'opzione "Solo posizioni critiche" con una soglia più alta.
3. Riduci il numero di varianti (MultiPV).
4. Riduci il tempo di analisi per posizione.

### 6.4 La GUI si blocca durante l'analisi
1. L'analisi viene eseguita in un thread separato, quindi l'interfaccia dovrebbe rimanere reattiva.
2. Se si verifica un blocco, attendi il completamento dell'operazione corrente o riavvia l'applicazione.

### 6.5 Errori durante l'esportazione
1. Verifica che la cartella di destinazione esista e sia accessibile in scrittura.
2. Assicurati che il file di destinazione non sia aperto in un'altra applicazione.

## 7. Verifiche di funzionamento

Per verificare che tutto funzioni correttamente, segui questi passaggi:

### 7.1 Verifica del database
1. Apri la scheda "Analisi" e controlla che vengano visualizzate le partite nella tabella.
2. Se non vengono visualizzate partite, verifica il percorso del database nella scheda "Impostazioni".
3. Controlla che il database contenga le tabelle necessarie (games, moves, ecc.).

### 7.2 Verifica del motore
1. Seleziona una partita nella scheda "Analisi".
2. Imposta una profondità bassa (es. 10) e un breve tempo di analisi (es. 0.2s).
3. Avvia l'analisi cliccando su "Avvia Analisi".
4. Se l'analisi non si avvia o si verificano errori, verifica il percorso del motore nella scheda "Impostazioni".

### 7.3 Verifica della visualizzazione
1. Nella scheda "Visualizzatore", seleziona una partita analizzata.
2. Verifica che la scacchiera mostri correttamente la posizione.
3. Prova a navigare tra le mosse utilizzando i pulsanti di navigazione.
4. Controlla che il grafico della valutazione venga visualizzato correttamente.

### 7.4 Verifica delle statistiche
1. Nella scheda "Statistiche", seleziona un giocatore e fai clic su "Calcola Statistiche".
2. Verifica che vengano visualizzate le statistiche e i grafici.
3. Controlla che la tabella delle partite del giocatore venga popolata correttamente.

### 7.5 Verifica dell'esportazione
1. Nella scheda "Visualizzatore", carica una partita analizzata.
2. Fai clic su "Esporta PGN" e verifica che il file venga creato correttamente.
3. Fai clic su "Esporta HTML" e verifica che il file HTML venga creato e visualizzato correttamente nel browser.

### 7.6 Test completo
Un test completo consiste nell'eseguire queste operazioni in sequenza:
1. Seleziona una partita nella scheda "Analisi".
2. Avvia l'analisi con l'opzione "Solo posizioni critiche".
3. Al termine, carica la partita nel visualizzatore.
4. Naviga tra le posizioni e verifica che le valutazioni e i commenti siano coerenti.
5. Esporta l'analisi in formato PGN e HTML.
6. Seleziona il giocatore nella scheda "Statistiche" e calcola le statistiche.
7. Verifica che le statistiche riflettano correttamente le prestazioni del giocatore.

Se tutte queste verifiche hanno esito positivo, il software funziona correttamente.

---

Questo manuale d'uso completo ti aiuterà a sfruttare al meglio tutte le funzionalità di ChessEngine Analysis GUI. Il software è progettato per essere intuitivo ma potente, adatto sia agli analisti esperti che ai giocatori che desiderano migliorare le proprie capacità attraverso l'analisi delle partite.