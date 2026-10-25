/**
 * Přihořívá Solver - Frontend Logic & Web Audio Controller
 */

// Application State
const state = {
  isSolving: false,
  eventSource: null,
  guesses: [],
  bestGuess: null,
  timerInterval: null,
  startTime: null,
  soundEnabled: true,
  viewMode: 'chronological', // 'chronological' or 'top'
  audioCtx: null,
};

// DOM Elements
const elements = {
  startBtn: document.getElementById('startBtn'),
  stopBtn: document.getElementById('stopBtn'),
  langSelect: document.getElementById('langSelect'),
  gameModeSelect: document.getElementById('gameModeSelect'),
  speedSelect: document.getElementById('speedSelect'),
  maxGuessesInput: document.getElementById('maxGuessesInput'),
  manualWordInput: document.getElementById('manualWordInput'),
  manualGuessBtn: document.getElementById('manualGuessBtn'),
  yesterdayWord: document.getElementById('yesterdayWord'),
  communityWinRate: document.getElementById('communityWinRate'),
  serverStatusText: document.getElementById('serverStatusText'),
  restartServerBtn: document.getElementById('restartServerBtn'),
  soundToggleBtn: document.getElementById('soundToggleBtn'),
  soundIcon: document.getElementById('soundIcon'),
  modeBadge: document.getElementById('modeBadge'),
  phaseIndicator: document.getElementById('phaseIndicator'),
  statGuesses: document.getElementById('statGuesses'),
  statBestScore: document.getElementById('statBestScore'),
  statBestWord: document.getElementById('statBestWord'),
  statTimer: document.getElementById('statTimer'),
  gaugeFill: document.getElementById('gaugeFill'),
  gaugeMarker: document.getElementById('gaugeMarker'),
  victoryBanner: document.getElementById('victoryBanner'),
  victoryWord: document.getElementById('victoryWord'),
  victorySub: document.getElementById('victorySub'),
  domainsBox: document.getElementById('domainsBox'),
  domainTags: document.getElementById('domainTags'),
  guessesTableBody: document.getElementById('guessesTableBody'),
  emptyRow: document.getElementById('emptyRow'),
  guessesCountBadge: document.getElementById('guessesCountBadge'),
  filterAllBtn: document.getElementById('filterAllBtn'),
  filterTopBtn: document.getElementById('filterTopBtn'),
  clearHistoryBtn: document.getElementById('clearHistoryBtn'),
};

// Web Audio API Sound Synthesizer
function playSound(type, score = 0) {
  if (!state.soundEnabled) return;

  try {
    if (!state.audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      state.audioCtx = new AudioContext();
    }
    if (state.audioCtx.state === 'suspended') {
      state.audioCtx.resume();
    }

    const ctx = state.audioCtx;
    const now = ctx.currentTime;

    if (type === 'guess') {
      // Frequency proportional to similarity (from 220Hz cold up to 880Hz hot)
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      const freq = 220 + (score / 100) * 660;
      osc.type = score > 80 ? 'triangle' : 'sine';
      osc.frequency.setValueAtTime(freq, now);

      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.18);
    } else if (type === 'win') {
      // Victory fanfare chord
      const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
      notes.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now + idx * 0.1);

        gain.gain.setValueAtTime(0.12, now + idx * 0.1);
        gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.1 + 0.7);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(now + idx * 0.1);
        osc.stop(now + idx * 0.1 + 0.75);
      });
    }
  } catch (e) {
    // Ignore audio errors
  }
}

// Timer management
function startTimer() {
  state.startTime = Date.now();
  clearInterval(state.timerInterval);
  state.timerInterval = setInterval(() => {
    const elapsedSec = Math.floor((Date.now() - state.startTime) / 1000);
    const m = String(Math.floor(elapsedSec / 60)).padStart(2, '0');
    const s = String(elapsedSec % 60).padStart(2, '0');
    elements.statTimer.textContent = `${m}:${s}`;
  }, 1000);
}

function stopTimer() {
  clearInterval(state.timerInterval);
}

// Fetch Metadata & Community Stats from API
async function loadMetaInfo() {
  try {
    const lang = elements.langSelect.value;
    const mode = elements.gameModeSelect.value;
    const res = await fetch(`/api/meta?lang=${lang}&mode=${mode}`);
    if (res.ok) {
      const data = await res.json();
      const prevWordLabel = document.getElementById('prevWordLabel');
      if (prevWordLabel) {
        prevWordLabel.textContent = mode === 'mega' ? 'Minulé megaslovo:' : 'Včerejší slovo:';
      }
      if (data.yesterdays_word) {
        elements.yesterdayWord.textContent = data.yesterdays_word;
      } else {
        elements.yesterdayWord.textContent = '—';
      }

      if (data.poll) {
        let wr = null;
        if (mode === 'mega' && data.poll.weekly_stats) {
          wr = data.poll.weekly_stats.win_rate;
        } else if (data.poll.stats) {
          wr = data.poll.stats.win_rate;
        }
        elements.communityWinRate.textContent = (wr !== null && wr !== undefined) ? `${wr.toFixed(1)} %` : '—';
      }

      // Obnovení historie z předchozího spuštění dnešní / týdenní hry
      if (data.session && data.session.guesses && data.session.guesses.length > 0) {
        state.guesses = data.session.guesses;
        state.bestGuess = data.session.best;
        elements.statGuesses.textContent = state.guesses.length;
        elements.guessesCountBadge.textContent = `${state.guesses.length} záznamů`;
        if (state.bestGuess) {
          elements.statBestScore.textContent = `${state.bestGuess.score_pct.toFixed(1)} %`;
          elements.statBestWord.textContent = state.bestGuess.word;
          elements.gaugeFill.style.width = `${Math.min(100, state.bestGuess.score_pct)}%`;
          elements.gaugeMarker.style.left = `${Math.min(100, state.bestGuess.score_pct)}%`;
        }
        renderTable();
        if (data.session.is_won && data.session.winning_word) {
          handleVictory(data.session.winning_word, data.session.total);
          elements.phaseIndicator.textContent = 'Vyřešeno v předchozím hádání!';
        } else {
          elements.victoryBanner.classList.remove('active');
          elements.phaseIndicator.textContent = `Načteno ${state.guesses.length} slov z předchozího hádání`;
        }
      } else {
        state.guesses = [];
        state.bestGuess = null;
        elements.statGuesses.textContent = '0';
        elements.statBestScore.textContent = '0.0 %';
        elements.statBestWord.textContent = '—';
        elements.gaugeFill.style.width = '0%';
        elements.gaugeMarker.style.left = '0%';
        elements.victoryBanner.classList.remove('active');
        elements.guessesCountBadge.textContent = '0 záznamů';
        elements.phaseIndicator.textContent = 'Připraven ke startu';
        renderTable();
      }
    }
  } catch (e) {
    console.warn('Failed to load meta info:', e);
  }
}

// Start Solving Process via Server-Sent Events (SSE)
function startSolving() {
  if (state.isSolving) return;

  state.isSolving = true;
  elements.startBtn.disabled = true;
  elements.stopBtn.disabled = false;
  elements.victoryBanner.classList.remove('active');

  const lang = elements.langSelect.value;
  const mode = elements.gameModeSelect.value;
  const speed = elements.speedSelect.value;
  const maxGuesses = parseInt(elements.maxGuessesInput.value, 10) || 100;

  let delaySec = 0.45;
  if (speed === 'fast') delaySec = 0.25;
  if (speed === 'slow') delaySec = 0.9;

  elements.phaseIndicator.textContent = 'Inicializace sémantického průzkumu...';
  startTimer();

  const url = `/api/solve/stream?lang=${lang}&mode=${mode}&delay=${delaySec}&max=${maxGuesses}`;
  state.eventSource = new EventSource(url);

  state.eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleSolverEvent(data);
    } catch (e) {
      console.error('Error parsing SSE event:', e);
    }
  };

  state.eventSource.onerror = (err) => {
    console.warn('SSE stream closed or error:', err);
    stopSolving('Spojení ukončeno');
  };
}

// Stop Solving Process
function stopSolving(reason = 'Zastaveno uživatelem') {
  if (state.eventSource) {
    state.eventSource.close();
    state.eventSource = null;
  }
  state.isSolving = false;
  elements.startBtn.disabled = false;
  elements.stopBtn.disabled = true;
  stopTimer();
  elements.phaseIndicator.textContent = reason;
}

// Handle Incoming Events from Solver Stream
function handleSolverEvent(data) {
  switch (data.type) {
    case 'resumed':
      elements.phaseIndicator.textContent = `Navazuji na předchozí hádání (${data.count} pokusů)`;
      if (data.guesses && state.guesses.length === 0) {
        state.guesses = data.guesses;
        state.bestGuess = data.best;
        elements.statGuesses.textContent = state.guesses.length;
        elements.guessesCountBadge.textContent = `${state.guesses.length} záznamů`;
        if (state.bestGuess) {
          elements.statBestScore.textContent = `${state.bestGuess.score_pct.toFixed(1)} %`;
          elements.statBestWord.textContent = state.bestGuess.word;
          elements.gaugeFill.style.width = `${Math.min(100, state.bestGuess.score_pct)}%`;
          elements.gaugeMarker.style.left = `${Math.min(100, state.bestGuess.score_pct)}%`;
        }
        renderTable();
      }
      break;

    case 'phase':
      elements.phaseIndicator.textContent = `Fáze ${data.phase}: ${data.title}`;
      break;

    case 'clusters_ranked':
      if (data.ranking && data.ranking.length > 0) {
        elements.domainsBox.style.display = 'flex';
        elements.domainTags.innerHTML = data.ranking
          .map(c => `<span class="domain-tag">${c.name} (${c.score}%)</span>`)
          .join('');
      }
      break;

    case 'strategy_pivot':
    case 'hotspot_found':
    case 'lockin':
    case 'scorching':
      elements.phaseIndicator.textContent = data.message;
      break;

    case 'guess':
      addGuess(data.entry, data.best);
      playSound('guess', data.entry.score_pct);
      break;

    case 'win':
      handleVictory(data.word, data.total);
      playSound('win');
      stopSolving('Úspěšně vyřešeno!');
      break;

    case 'done_unsolved':
      stopSolving(data.message || 'Hledání dokončeno');
      break;

    case 'error':
      alert('Chyba: ' + data.message);
      stopSolving('Chyba při komunikaci');
      break;
  }
}

// Add Guess to UI
function addGuess(entry, best) {
  state.guesses.push(entry);
  if (!state.bestGuess || entry.score_pct > state.bestGuess.score_pct) {
    state.bestGuess = entry;
  }

  // Update counters
  elements.statGuesses.textContent = state.guesses.length;
  elements.guessesCountBadge.textContent = `${state.guesses.length} záznamů`;

  if (state.bestGuess) {
    elements.statBestScore.textContent = `${state.bestGuess.score_pct.toFixed(1)} %`;
    elements.statBestWord.textContent = state.bestGuess.word;

    // Update gauge based on highest score
    const pct = Math.min(100, Math.max(0, state.bestGuess.score_pct));
    elements.gaugeFill.style.width = `${pct}%`;
    elements.gaugeMarker.style.left = `${pct}%`;
  }

  renderTable();
}

// Handle Victory
function handleVictory(word, total) {
  elements.victoryWord.textContent = word.toUpperCase();
  elements.victorySub.textContent = `Uhádnuto za ${total} pokusů se 100% shodou! Slovo odesláno do herních statistik.`;
  elements.victoryBanner.classList.add('active');

  elements.gaugeFill.style.width = '100%';
  elements.gaugeMarker.style.left = '100%';
  elements.statBestScore.textContent = '100.0 %';
  elements.statBestWord.textContent = word;
}

// Render Table (Chronological or Sorted by Temperature)
function renderTable() {
  if (state.guesses.length === 0) {
    elements.emptyRow.style.display = 'table-row';
    return;
  }
  elements.emptyRow.style.display = 'none';

  let list = [...state.guesses];
  if (state.viewMode === 'top') {
    list.sort((a, b) => b.score_pct - a.score_pct);
  } else {
    list.reverse(); // Latest guesses first in chronological view
  }

  elements.guessesTableBody.innerHTML = list.map((g) => {
    const isWinner = g.score_pct >= 100.0;
    return `
      <tr class="guess-row ${isWinner ? 'is-winner' : ''}">
        <td class="col-num">${g.number}</td>
        <td class="col-word">${escapeHtml(g.word)}</td>
        <td class="col-score" style="color: ${g.color};">${g.score_pct.toFixed(2)} %</td>
        <td>
          <span class="badge-temp" style="background: ${g.color}22; color: ${g.color}; border: 1px solid ${g.color}44;">
            ${g.emoji} ${g.label}
          </span>
        </td>
        <td>
          <div class="row-bar-track">
            <div class="row-bar-fill" style="width: ${Math.min(100, g.score_pct)}%; background-color: ${g.color};"></div>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

// Manual Guess Submission
async function submitManualWord() {
  const word = elements.manualWordInput.value.trim().toLowerCase();
  if (!word) return;

  elements.manualGuessBtn.disabled = true;
  elements.manualWordInput.value = '';

  const lang = elements.langSelect.value;
  const mode = elements.gameModeSelect.value;

  try {
    const res = await fetch('/api/guess', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ word, lang, mode, guessNumber: state.guesses.length + 1 })
    });

    if (res.ok) {
      const data = await res.json();
      if (data.entry) {
        addGuess(data.entry, data.best);
        playSound('guess', data.entry.score_pct);
        if (data.entry.score_pct >= 100.0) {
          handleVictory(word, state.guesses.length);
          playSound('win');
        }
      }
    } else {
      const err = await res.json();
      alert(err.error || ('Chyba při ověřování slova: ' + res.statusText));
    }
  } catch (e) {
    alert('Chyba při odesílání: ' + e.message);
  } finally {
    elements.manualGuessBtn.disabled = false;
  }
}

// Utility: HTML escaping
function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Event Listeners
elements.startBtn.addEventListener('click', startSolving);
elements.stopBtn.addEventListener('click', () => stopSolving('Zastaveno uživatelem'));

elements.manualGuessBtn.addEventListener('click', submitManualWord);
elements.manualWordInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') submitManualWord();
});

elements.langSelect.addEventListener('change', () => {
  loadMetaInfo();
});

elements.gameModeSelect.addEventListener('change', (e) => {
  elements.modeBadge.textContent = e.target.value === 'mega' ? 'TÝDENNÍ HRA' : 'DENNÍ HRA';
  loadMetaInfo();
});

elements.soundToggleBtn.addEventListener('click', () => {
  state.soundEnabled = !state.soundEnabled;
  elements.soundIcon.textContent = state.soundEnabled ? '🔊' : '🔇';
});

elements.restartServerBtn.addEventListener('click', async () => {
  if (confirm('Opravdu chcete restartovat webový server na pozadí? Hra se přeruší.')) {
    try {
      await fetch('/api/server/restart', { method: 'POST' });
      alert('Server se restartuje. Počkejte sekundu a obnovte stránku.');
      stopSolving('Server se restartuje...');
    } catch (e) {
      alert('Chyba při restartu serveru.');
    }
  }
});

elements.filterAllBtn.addEventListener('click', () => {
  state.viewMode = 'chronological';
  elements.filterAllBtn.classList.add('active');
  elements.filterTopBtn.classList.remove('active');
  renderTable();
});

elements.filterTopBtn.addEventListener('click', () => {
  state.viewMode = 'top';
  elements.filterTopBtn.classList.add('active');
  elements.filterAllBtn.classList.remove('active');
  renderTable();
});

elements.clearHistoryBtn.addEventListener('click', async () => {
  if (confirm('Opravdu chcete vymazat historii z předchozího hádání a začít znovu?')) {
    const lang = elements.langSelect.value;
    const mode = elements.gameModeSelect.value;
    try {
      await fetch('/api/history/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lang, mode }),
      });
    } catch (e) {
      console.warn('Clear history request failed:', e);
    }
    state.guesses = [];
    state.bestGuess = null;
    elements.statGuesses.textContent = '0';
    elements.statBestScore.textContent = '0.0 %';
    elements.statBestWord.textContent = '—';
    elements.gaugeFill.style.width = '0%';
    elements.gaugeMarker.style.left = '0%';
    elements.victoryBanner.classList.remove('active');
    elements.guessesCountBadge.textContent = '0 záznamů';
    elements.phaseIndicator.textContent = 'Historie vymazána, připraven ke startu';
    renderTable();
  }
});

// Initialization
document.addEventListener('DOMContentLoaded', () => {
  loadMetaInfo();
});
