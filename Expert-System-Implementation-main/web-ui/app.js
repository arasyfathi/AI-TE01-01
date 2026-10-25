/**
 * CardioExpert CDSS — app.js  v2
 * Expert System Logic (Backward Chaining + Forward Chaining)
 * Ported from C++ source: Project1-A05071238
 *
 * NEW IN v2:
 * - 2-Column layout: Live Working Memory + Live Hypothesis Tracker
 * - Clickable log entries (toggle YA <-> TIDAK without reset)
 * - Log filter tabs (Semua / YA / TIDAK)
 * - Demo Preset Cases (Quick Load)
 * - Differential Diagnosis (partial rule matching ≥40%)
 * - localStorage patient history
 * - Formal print-friendly report
 */

// ============================================================
//  KNOWLEDGE BASE — BACKWARD CHAINING
// ============================================================

const SYMPTOMS = [
  "Detak Jantung Cepat/Tidak Teratur atau Berdebar-debar (Palpitasi)", // 0
  "Nyeri Dada",                                                          // 1
  "Sesak Napas Terus-Menerus",                                          // 2
  "Kelelahan Ekstrem / Mudah Lelah",                                    // 3
  "Pusing (Dizziness)",                                                 // 4
  "Kepala Terasa Ringan / Melayang",                                    // 5
  "Tubuh Lemas / Tidak Bertenaga",                                      // 6
  "Keringat Dingin Berlebih Tanpa Sebab Jelas",                        // 7
  "Pingsan / Kehilangan Kesadaran",                                     // 8
  "Kenaikan Berat Badan Mendadak (Penumpukan Cairan)",                 // 9
  "Edema (Pembengkakan Kaki/Pergelangan Kaki)",                        // 10
  "Perut Kembung / Membengkak (Asites)",                               // 11
  "Kebingungan / Linglung",                                             // 12
  "Rasa Tertekan / Sesak di Dada",                                     // 13
  "Muntah",                                                             // 14
  "Gelisah / Tidak Tenang",                                            // 15
  "Riwayat Serangan Jantung",                                          // 16
  "Mual",                                                              // 17
  "Rasa Tertekan atau Nyeri Menjalar ke Leher",                       // 18
  "Riwayat Henti Jantung Mendadak",                                   // 19
  "Kongesti / Penumpukan Cairan di Paru-paru",                        // 20
];

const DIAGNOSES = [
  "Gagal Jantung (Heart Failure)",
  "Kardiomiopati (Cardiomyopathy)",
  "Angina Pectoris (Angina)",
  "Penyakit Jantung Koroner (Coronary Artery Disease)",
  "Takikardia (Tachycardia)",
  "Takikardia Ventrikel (Ventricular Tachycardia)",
];

const ICD10 = {
  "Gagal Jantung (Heart Failure)": "I50",
  "Kardiomiopati (Cardiomyopathy)": "I42",
  "Angina Pectoris (Angina)": "I20",
  "Penyakit Jantung Koroner (Coronary Artery Disease)": "I25",
  "Takikardia (Tachycardia)": "I47.1",
  "Takikardia Ventrikel (Ventricular Tachycardia)": "I47.2",
};

const URGENCY = {
  "Gagal Jantung (Heart Failure)":                      { level: "KRITIS", cls: "urgency-critical" },
  "Kardiomiopati (Cardiomyopathy)":                     { level: "TINGGI", cls: "urgency-high" },
  "Angina Pectoris (Angina)":                           { level: "TINGGI", cls: "urgency-high" },
  "Penyakit Jantung Koroner (Coronary Artery Disease)": { level: "KRITIS", cls: "urgency-critical" },
  "Takikardia (Tachycardia)":                           { level: "SEDANG", cls: "urgency-moderate" },
  "Takikardia Ventrikel (Ventricular Tachycardia)":     { level: "KRITIS", cls: "urgency-critical" },
};

const BACKWARD_RULES = [
  { ruleNum: 10,  symptoms: [0,1,6],   diagIdx: 0 },
  { ruleNum: 20,  symptoms: [0,12],    diagIdx: 0 },
  { ruleNum: 30,  symptoms: [0,20],    diagIdx: 0 },
  { ruleNum: 40,  symptoms: [0,10],    diagIdx: 1 },
  { ruleNum: 50,  symptoms: [0,11],    diagIdx: 1 },
  { ruleNum: 60,  symptoms: [0,18],    diagIdx: 5 },
  { ruleNum: 70,  symptoms: [0,19],    diagIdx: 5 },
  { ruleNum: 80,  symptoms: [1,2,6],   diagIdx: 2 },
  { ruleNum: 90,  symptoms: [1,2,7],   diagIdx: 2 },
  { ruleNum: 100, symptoms: [1,2,8],   diagIdx: 5 },
  { ruleNum: 110, symptoms: [1,2,9],   diagIdx: 1 },
  { ruleNum: 120, symptoms: [1,10],    diagIdx: 1 },
  { ruleNum: 130, symptoms: [1,11],    diagIdx: 1 },
  { ruleNum: 140, symptoms: [1,13],    diagIdx: 2 },
  { ruleNum: 150, symptoms: [1,14],    diagIdx: 2 },
  { ruleNum: 160, symptoms: [1,15],    diagIdx: 2 },
  { ruleNum: 170, symptoms: [1,18],    diagIdx: 5 },
  { ruleNum: 180, symptoms: [1,19],    diagIdx: 5 },
  { ruleNum: 190, symptoms: [1,3,7],   diagIdx: 2 },
  { ruleNum: 200, symptoms: [1,3,8],   diagIdx: 0 },
  { ruleNum: 210, symptoms: [1,20],    diagIdx: 0 },
  { ruleNum: 220, symptoms: [1,5,6],   diagIdx: 2 },
  { ruleNum: 230, symptoms: [1,5,7],   diagIdx: 2 },
  { ruleNum: 240, symptoms: [1,5,9],   diagIdx: 1 },
  { ruleNum: 250, symptoms: [1,12],    diagIdx: 0 },
  { ruleNum: 260, symptoms: [1,6,9],   diagIdx: 0 },
  { ruleNum: 270, symptoms: [1,6,7],   diagIdx: 2 },
  { ruleNum: 280, symptoms: [1,6,8],   diagIdx: 0 },
  { ruleNum: 290, symptoms: [1,7],     diagIdx: 2 },
  { ruleNum: 300, symptoms: [1,8,9],   diagIdx: 0 },
  { ruleNum: 310, symptoms: [0,16],    diagIdx: 3 },
  { ruleNum: 320, symptoms: [0,17],    diagIdx: 3 },
  { ruleNum: 330, symptoms: [0,7],     diagIdx: 3 },
  { ruleNum: 340, symptoms: [0,8,9],   diagIdx: 3 },
  { ruleNum: 350, symptoms: [1,4,7],   diagIdx: 2 },
  { ruleNum: 360, symptoms: [1,4,9],   diagIdx: 0 },
];

// ============================================================
//  KNOWLEDGE BASE — FORWARD CHAINING
// ============================================================

const FORWARD_CLAUSE_VARIABLES = [
  "Tekanan darah tinggi dan perkembangan penyakit",
  "Penumpukan cairan tubuh",
  "Peradangan / Inflamasi",
  "Sirkulasi darah buruk",
  "Penyempitan pembuluh darah dan nyeri dada",
  "Kadar kolesterol tinggi",
  "Pembekuan / Gumpalan darah",
  "Peningkatan denyut jantung abnormal",
  "Penyumbatan pembuluh darah",
];

const DIAGNOSIS_AILMENT = {
  0: [0,1], 1: [2,3], 2: [4,5,6], 3: [0,6], 4: [6,7], 5: [7,8],
};

const AILMENT_CONDITION = {
  0: ["TINGGI","MENUMPUK"],
  1: ["INFLAMASI","BERKURANG"],
  2: ["MENYEMPIT","MENINGKAT","BEKU"],
  3: ["TINGGI","BEKU"],
  4: ["MENINGKAT","BEKU"],
  5: ["MENINGKAT","TERSUMBAT"],
};

const FORWARD_TREATMENT_RULES = [
  { clauseVarIdx: 0, condition: "TINGGI",    treatment: "OBAT ACE INHIBITOR / ARB BLOCKERS" },
  { clauseVarIdx: 1, condition: "MENUMPUK",  treatment: "OBAT DIURETIK / ANTAGONIS ALDOSTERON" },
  { clauseVarIdx: 2, condition: "INFLAMASI", treatment: "KORTIKOSTEROID" },
  { clauseVarIdx: 3, condition: "BERKURANG", treatment: "OBAT ACE INHIBITOR / ANGIOTENSIN II RECEPTOR BLOCKERS" },
  { clauseVarIdx: 4, condition: "MENYEMPIT", treatment: "NITRAT" },
  { clauseVarIdx: 5, condition: "MENINGKAT", treatment: "STATIN (PENURUN KOLESTEROL)" },
  { clauseVarIdx: 6, condition: "BEKU",      treatment: "OBAT PENCEGAH PENGGUMPALAN DARAH (CLOPIDOGREL, TICAGRELOR) / ASPIRIN" },
  { clauseVarIdx: 7, condition: "MENINGKAT", treatment: "MANUVER VAGAL" },
];

const FURTHER_EXAMS = {
  "Gagal Jantung (Heart Failure)":                      ["Echocardiography (USG Jantung)", "BNP/NT-proBNP Test", "Rontgen Dada (CXR)", "EKG 12 Lead", "Tes Fungsi Ginjal"],
  "Kardiomiopati (Cardiomyopathy)":                     ["MRI Jantung (Cardiac MRI)", "Biopsi Miokardium", "Echocardiography", "EKG Holter 24 Jam", "Tes Genetik"],
  "Angina Pectoris (Angina)":                           ["Stress Test (Treadmill)", "Angiografi Koroner", "EKG saat istirahat dan saat nyeri", "CT Angiography", "Troponin T & I"],
  "Penyakit Jantung Koroner (Coronary Artery Disease)": ["Kateterisasi Jantung", "CT Angiography Koroner", "Lipid Panel Lengkap", "Gula Darah & HbA1c", "Stress Test Nuklir"],
  "Takikardia (Tachycardia)":                           ["EKG 12 Lead", "Holter Monitor 24-48 Jam", "Elektrofisiologi (EPS)", "TSH & Hormon Tiroid", "Elektrolit Darah"],
  "Takikardia Ventrikel (Ventricular Tachycardia)":     ["EKG 12 Lead (SEGERA)", "Echocardiography Darurat", "Troponin & CK-MB", "Elektrolit Darah Cito", "ICD Assessment"],
};

const DIAG_STYLES = {
  "Gagal Jantung (Heart Failure)":                      { card:"diag-card-heart-failure",  icon:"diag-icon-heart-failure",  lucide:"heart-crack",    hypoColor:"#ef4444", hypoText:"text-red-400" },
  "Kardiomiopati (Cardiomyopathy)":                     { card:"diag-card-cardiomyopathy", icon:"diag-icon-cardiomyopathy", lucide:"heart",          hypoColor:"#f59e0b", hypoText:"text-amber-400" },
  "Angina Pectoris (Angina)":                           { card:"diag-card-angina",         icon:"diag-icon-angina",         lucide:"zap",            hypoColor:"#fbbf24", hypoText:"text-yellow-400" },
  "Penyakit Jantung Koroner (Coronary Artery Disease)": { card:"diag-card-coronary",       icon:"diag-icon-coronary",       lucide:"shield-alert",   hypoColor:"#ef4444", hypoText:"text-red-400" },
  "Takikardia (Tachycardia)":                           { card:"diag-card-tachycardia",    icon:"diag-icon-tachycardia",    lucide:"activity",       hypoColor:"#8b5cf6", hypoText:"text-violet-400" },
  "Takikardia Ventrikel (Ventricular Tachycardia)":     { card:"diag-card-ventricular",    icon:"diag-icon-ventricular",    lucide:"alert-triangle", hypoColor:"#f43f5e", hypoText:"text-rose-400" },
};

// ============================================================
//  DEMO PRESET CASES
// ============================================================

const DEMO_PRESETS = [
  {
    name: "Gagal Jantung — Kasus Berat",
    color: "#ef4444",
    description: "Palpitasi + nyeri dada + lemas + pingsan + penumpukan cairan",
    symptoms: [true, true, false, false, false, false, true, false, true, true, false, false, false, false, false, false, false, false, false, false, false],
    patient: { name: "Ahmad Santoso", id: "RM-2024001", age: "58", gender: "Laki-laki" },
  },
  {
    name: "Gagal Jantung — Palpitasi & Linglung",
    color: "#ef4444",
    description: "Palpitasi + kebingungan",
    symptoms: [true, false, false, false, false, false, false, false, false, false, false, false, true, false, false, false, false, false, false, false, false],
    patient: { name: "Siti Rahayu", id: "RM-2024002", age: "65", gender: "Perempuan" },
  },
  {
    name: "Kardiomiopati — Kasus Sedang",
    color: "#f59e0b",
    description: "Palpitasi + nyeri dada + sesak + penumpukan",
    symptoms: [true, true, true, false, false, false, false, false, false, true, false, false, false, false, false, false, false, false, false, false, false],
    patient: { name: "Budi Hartono", id: "RM-2024003", age: "47", gender: "Laki-laki" },
  },
  {
    name: "Angina Pectoris — Nyeri Dada Khas",
    color: "#fbbf24",
    description: "Nyeri dada + sesak + lemas",
    symptoms: [false, true, true, false, false, false, true, false, false, false, false, false, false, false, false, false, false, false, false, false, false],
    patient: { name: "Dewi Lestari", id: "RM-2024004", age: "52", gender: "Perempuan" },
  },
  {
    name: "Coronary Artery Disease — Riwayat Serangan",
    color: "#ef4444",
    description: "Palpitasi + riwayat serangan jantung",
    symptoms: [true, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, true, false, false, false, false],
    patient: { name: "Hendra Gunawan", id: "RM-2024005", age: "60", gender: "Laki-laki" },
  },
  {
    name: "Takikardia Ventrikel — Kasus Kritis",
    color: "#f43f5e",
    description: "Palpitasi + nyeri dada + nyeri menjalar ke leher",
    symptoms: [true, true, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, true, false, false],
    patient: { name: "Rini Wulandari", id: "RM-2024006", age: "43", gender: "Perempuan" },
  },
];

// ============================================================
//  APP STATE
// ============================================================

const state = {
  mode: 'wizard',
  wizardIndex: 0,
  symptoms: Array(21).fill(null),  // null=unasked, true=yes, false=no
  logFilter: 'all',
  diagnosisResult: null,
  treatmentResult: null,
  inferenceTrace: null,
  terminalLines: [],
};

// ============================================================
//  NAVIGATION
// ============================================================

function showSection(id) {
  document.querySelectorAll('.section-page').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  const navMap = { 'sec-anamnesis':'nav-anamnesis','sec-diagnosis':'nav-diagnosis','sec-treatment':'nav-treatment','sec-inference':'nav-inference','sec-knowledge':'nav-knowledge','sec-terminal':'nav-terminal' };
  const titleMap = { 'sec-anamnesis':'Anamnesis Gejala','sec-diagnosis':'Hasil Diagnosis','sec-treatment':'Rekomendasi Pengobatan','sec-inference':'Inference Trace','sec-knowledge':'Rule Explorer','sec-terminal':'Terminal CLI Simulator' };
  if (navMap[id]) document.getElementById(navMap[id]).classList.add('active');
  document.getElementById('header-section-title').textContent = titleMap[id] || '';
}

// ============================================================
//  ANAMNESIS MODE TOGGLE
// ============================================================

function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll('.mode-content').forEach(m => m.classList.add('hidden'));
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('mode-' + mode).classList.remove('hidden');
  document.getElementById('btn-mode-' + mode).classList.add('active');
  if (mode === 'matrix') syncMatrixFromState();
  updateRunButtonState();
}

// ============================================================
//  LIVE WORKING MEMORY LOG
// ============================================================

function renderWorkingMemoryLog() {
  const container = document.getElementById('wm-log');
  if (!container) return;
  container.innerHTML = '';

  const filter = state.logFilter;
  let countYes = 0, countNo = 0, countAll = 0;

  SYMPTOMS.forEach((symptom, idx) => {
    const val = state.symptoms[idx];
    const stateStr = val === null ? 'null' : val ? 'true' : 'false';
    if (val === true) countYes++;
    if (val === false) countNo++;
    countAll++;

    if (filter === 'yes' && val !== true) return;
    if (filter === 'no' && val !== false) return;

    const entry = document.createElement('div');
    entry.className = 'wm-entry';
    entry.dataset.state = stateStr;
    entry.dataset.idx = idx;
    entry.title = val === null ? 'Klik untuk menandai YA' : val ? 'YA — klik untuk ubah ke TIDAK' : 'TIDAK — klik untuk ubah ke YA';

    const badgeText = val === null ? '—' : val ? 'YA' : 'TIDAK';
    entry.innerHTML = `
      <div class="wm-dot"></div>
      <span class="flex-1 leading-snug">${symptom}</span>
      <span class="wm-badge">${badgeText}</span>
    `;
    entry.addEventListener('click', () => toggleSymptomFromLog(idx));
    container.appendChild(entry);
  });

  // Update filter counts
  const countAllEl = document.getElementById('log-count-all');
  const countYesEl = document.getElementById('log-count-yes');
  const countNoEl  = document.getElementById('log-count-no');
  if (countAllEl) countAllEl.textContent = countAll;
  if (countYesEl) countYesEl.textContent = countYes;
  if (countNoEl)  countNoEl.textContent  = countNo;
}

function toggleSymptomFromLog(idx) {
  const current = state.symptoms[idx];
  // null → true → false → null cycle, but simpler: null/false → true, true → false
  if (current === true) {
    state.symptoms[idx] = false;
  } else {
    state.symptoms[idx] = true;
  }
  renderWorkingMemoryLog();
  updateHypothesisTracker();
  updateRunButtonState();
  if (state.mode === 'matrix') syncMatrixFromState();
  // If we're past this symptom in wizard, update matrix
  if (idx < state.wizardIndex) {
    // Already past this — just sync
  }
}

function setLogFilter(filter) {
  state.logFilter = filter;
  document.querySelectorAll('.log-filter').forEach(b => b.classList.remove('active'));
  document.getElementById('log-filter-' + filter).classList.add('active');
  renderWorkingMemoryLog();
}

// ============================================================
//  LIVE HYPOTHESIS TRACKER
// ============================================================

const HYPO_COLORS = [
  { bg: 'rgba(239,68,68,0.8)',   track: 'rgba(239,68,68,0.15)'  },
  { bg: 'rgba(245,158,11,0.8)',  track: 'rgba(245,158,11,0.15)' },
  { bg: 'rgba(251,191,36,0.8)',  track: 'rgba(251,191,36,0.15)' },
  { bg: 'rgba(239,68,68,0.7)',   track: 'rgba(239,68,68,0.12)'  },
  { bg: 'rgba(139,92,246,0.8)',  track: 'rgba(139,92,246,0.15)' },
  { bg: 'rgba(244,63,94,0.8)',   track: 'rgba(244,63,94,0.15)'  },
];

function computeHypothesisScores() {
  // For each diagnosis, find the best matching rule and compute percentage
  const diagScores = DIAGNOSES.map((diagName, diagIdx) => {
    const rulesForDiag = BACKWARD_RULES.filter(r => r.diagIdx === diagIdx);
    let bestScore = 0;
    let bestRule = null;
    rulesForDiag.forEach(rule => {
      const matched = rule.symptoms.filter(s => state.symptoms[s] === true).length;
      const score = matched / rule.symptoms.length;
      if (score > bestScore) {
        bestScore = score;
        bestRule = rule;
      }
    });
    return { diagIdx, diagName, score: bestScore, bestRule };
  });
  // Sort by score descending
  diagScores.sort((a, b) => b.score - a.score);
  return diagScores;
}

function updateHypothesisTracker() {
  const container = document.getElementById('hypothesis-tracker');
  if (!container) return;
  const scores = computeHypothesisScores();

  container.innerHTML = '';
  scores.forEach((item, i) => {
    const pct = Math.round(item.score * 100);
    const color = HYPO_COLORS[item.diagIdx] || HYPO_COLORS[0];
    const el = document.createElement('div');
    el.className = 'hypo-item';
    el.innerHTML = `
      <div class="flex items-center justify-between gap-2">
        <span class="text-[11px] font-medium text-slate-300 truncate leading-tight">${item.diagName}</span>
        <span class="font-mono text-[11px] font-bold flex-shrink-0" style="color:${color.bg}">${pct}%</span>
      </div>
      <div class="hypo-bar-track" style="background:${color.track}">
        <div class="hypo-bar-fill" style="width:${pct}%; background:${color.bg}"></div>
      </div>
      ${item.bestRule && pct > 0 ? `<p class="text-[10px] text-slate-600 truncate">Best rule: R-${item.bestRule.ruleNum} (${item.bestRule.symptoms.length} gejala)</p>` : ''}
    `;
    container.appendChild(el);
  });
}

// ============================================================
//  WIZARD MODE
// ============================================================

function updateWizardUI() {
  const idx = state.wizardIndex;
  const qEl = document.getElementById('wiz-question');
  const codeEl = document.getElementById('wiz-symptom-code');
  const barEl = document.getElementById('wiz-progress-bar');
  const labelEl = document.getElementById('wiz-progress-label');
  if (!qEl) return;
  if (idx >= SYMPTOMS.length) return;
  qEl.textContent = SYMPTOMS[idx] + '?';
  if (codeEl) codeEl.textContent = `S-${String(idx + 1).padStart(3, '0')}`;
  const pct = (idx / SYMPTOMS.length) * 100;
  if (barEl) barEl.style.width = pct + '%';
  if (labelEl) labelEl.textContent = `Gejala ${idx + 1} / ${SYMPTOMS.length}`;
}

function wizardAnswer(isYes) {
  const idx = state.wizardIndex;
  if (idx >= SYMPTOMS.length) return;
  state.symptoms[idx] = isYes;
  state.wizardIndex++;
  renderWorkingMemoryLog();
  updateHypothesisTracker();

  if (state.wizardIndex >= SYMPTOMS.length) {
    const card = document.getElementById('wiz-card');
    if (card) {
      card.innerHTML = `
        <div class="px-5 py-10 text-center">
          <div class="w-12 h-12 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center mx-auto mb-3">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
          </div>
          <h3 class="text-white font-semibold mb-1.5">Semua gejala telah direkam</h3>
          <p class="text-xs text-slate-500">Klik "Jalankan Expert System" untuk analisis.</p>
        </div>
      `;
    }
    const barEl = document.getElementById('wiz-progress-bar');
    const labelEl = document.getElementById('wiz-progress-label');
    if (barEl) barEl.style.width = '100%';
    if (labelEl) labelEl.textContent = 'Selesai — 21 / 21';
  } else {
    updateWizardUI();
  }
  updateRunButtonState();
}

// ============================================================
//  RUN BUTTON STATE
// ============================================================

function updateRunButtonState() {
  const hasAny = state.symptoms.some(s => s !== null);
  ['wiz-run-btn', 'matrix-run-btn'].forEach(id => {
    const btn = document.getElementById(id);
    if (!btn) return;
    if (hasAny) {
      btn.disabled = false;
      btn.classList.remove('opacity-40', 'cursor-not-allowed');
    } else {
      btn.disabled = true;
      btn.classList.add('opacity-40', 'cursor-not-allowed');
    }
  });
}

// ============================================================
//  RAPID MATRIX MODE
// ============================================================

function buildMatrix() {
  const grid = document.getElementById('matrix-grid');
  if (!grid) return;
  grid.innerHTML = '';
  SYMPTOMS.forEach((symptom, idx) => {
    const item = document.createElement('label');
    item.className = 'matrix-item' + (state.symptoms[idx] === true ? ' selected' : '');
    item.id = `matrix-item-${idx}`;
    item.innerHTML = `
      <div class="check-box">
        <svg class="check-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
      </div>
      <span class="symptom-text">${symptom}</span>
    `;
    item.addEventListener('click', () => toggleMatrixItem(idx));
    grid.appendChild(item);
  });
  updateMatrixCount();
}

function toggleMatrixItem(idx) {
  state.symptoms[idx] = state.symptoms[idx] === true ? false : true;
  const item = document.getElementById(`matrix-item-${idx}`);
  if (item) item.classList.toggle('selected', state.symptoms[idx]);
  updateMatrixCount();
  updateRunButtonState();
  renderWorkingMemoryLog();
  updateHypothesisTracker();
}

function syncMatrixFromState() {
  SYMPTOMS.forEach((_, idx) => {
    const item = document.getElementById(`matrix-item-${idx}`);
    if (!item) return;
    item.classList.toggle('selected', state.symptoms[idx] === true);
  });
  updateMatrixCount();
}

function updateMatrixCount() {
  const count = state.symptoms.filter(s => s === true).length;
  const el = document.getElementById('matrix-count');
  if (el) el.textContent = `${count} dipilih`;
}

// ============================================================
//  DEMO PRESETS
// ============================================================

function buildPresetMenu() {
  const list = document.getElementById('preset-list');
  if (!list) return;
  list.innerHTML = '';
  DEMO_PRESETS.forEach((preset, i) => {
    const btn = document.createElement('button');
    btn.className = 'preset-option';
    btn.innerHTML = `
      <div class="preset-dot" style="background:${preset.color}"></div>
      <div class="text-left">
        <p class="text-[12px] font-semibold text-slate-200 leading-tight">${preset.name}</p>
        <p class="text-[10px] text-slate-500 leading-tight mt-0.5">${preset.description}</p>
      </div>
    `;
    btn.addEventListener('click', () => loadPreset(i));
    list.appendChild(btn);
  });
}

function loadPreset(idx) {
  const preset = DEMO_PRESETS[idx];
  if (!preset) return;

  // Load symptoms
  state.symptoms = [...preset.symptoms];
  state.wizardIndex = SYMPTOMS.length; // mark wizard as complete

  // Load patient data
  const nameEl = document.getElementById('inp-name');
  const idEl   = document.getElementById('inp-id');
  const ageEl  = document.getElementById('inp-age');
  const genderEl = document.getElementById('inp-gender');
  if (nameEl)   nameEl.value   = preset.patient.name;
  if (idEl)     idEl.value     = preset.patient.id;
  if (ageEl)    ageEl.value    = preset.patient.age;
  if (genderEl) genderEl.value = preset.patient.gender;

  updatePatientBadge();

  // Reset wizard card to "complete" state
  const card = document.getElementById('wiz-card');
  if (card) {
    card.innerHTML = `
      <div class="px-5 py-10 text-center">
        <div class="w-12 h-12 rounded-2xl bg-violet-500/15 border border-violet-500/30 flex items-center justify-center mx-auto mb-3">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-violet-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
        </div>
        <h3 class="text-white font-semibold mb-1.5">Preset: ${preset.name}</h3>
        <p class="text-xs text-slate-500">${preset.symptoms.filter(Boolean).length} gejala positif dimuat. Klik "Jalankan Expert System" untuk analisis.</p>
      </div>
    `;
  }

  const barEl = document.getElementById('wiz-progress-bar');
  const labelEl = document.getElementById('wiz-progress-label');
  if (barEl) barEl.style.width = '100%';
  if (labelEl) labelEl.textContent = `Preset — ${preset.symptoms.filter(Boolean).length} gejala aktif`;

  // Sync all UI
  if (state.mode === 'matrix') syncMatrixFromState();
  renderWorkingMemoryLog();
  updateHypothesisTracker();
  updateRunButtonState();

  // Close menu
  document.getElementById('preset-menu').classList.add('hidden');
}

function togglePresetMenu() {
  const menu = document.getElementById('preset-menu');
  menu.classList.toggle('hidden');
}

// Close preset menu on outside click
document.addEventListener('click', (e) => {
  const wrapper = document.getElementById('preset-wrapper');
  if (wrapper && !wrapper.contains(e.target)) {
    const menu = document.getElementById('preset-menu');
    if (menu) menu.classList.add('hidden');
  }
});

// ============================================================
//  EXPERT SYSTEM — BACKWARD CHAINING
// ============================================================

function runBackwardChaining(symptomsArray) {
  const traceSteps = [];
  for (const rule of BACKWARD_RULES) {
    const allMatch = rule.symptoms.every(s => symptomsArray[s]);
    const partial  = rule.symptoms.some(s => symptomsArray[s]);
    traceSteps.push({ ruleNum: rule.ruleNum, symptoms: rule.symptoms, diagIdx: rule.diagIdx, matched: allMatch, partial });
    if (allMatch) return { matched: rule, trace: traceSteps };
  }
  return { matched: null, trace: traceSteps };
}

// ============================================================
//  EXPERT SYSTEM — FORWARD CHAINING
// ============================================================

function runForwardChaining(diagnosisIndex) {
  const ailmentIndices = DIAGNOSIS_AILMENT[diagnosisIndex] || [];
  const conditions = ailmentIndices.map((varIdx, localIdx) => ({
    varIdx, name: FORWARD_CLAUSE_VARIABLES[varIdx],
    condition: (AILMENT_CONDITION[diagnosisIndex] || [])[localIdx] || '—',
  }));
  const forwardTrace = [];
  const treatments = new Set();
  conditions.forEach(cond => {
    for (const rule of FORWARD_TREATMENT_RULES) {
      if (rule.clauseVarIdx === cond.varIdx && rule.condition === cond.condition) {
        treatments.add(rule.treatment);
        forwardTrace.push({ condition: cond.name, state: cond.condition, treatment: rule.treatment });
        break;
      }
    }
  });
  return { conditions, treatments: [...treatments], forwardTrace };
}

// ============================================================
//  DIFFERENTIAL DIAGNOSIS
// ============================================================

function computeDifferentialDiagnosis(symptomsArray, matchedRuleNum) {
  const diagBestScores = {};
  const diagBestRules  = {};

  BACKWARD_RULES.forEach(rule => {
    if (rule.ruleNum === matchedRuleNum) return; // skip primary
    const matchedCount = rule.symptoms.filter(s => symptomsArray[s]).length;
    const pct = matchedCount / rule.symptoms.length;
    const diagName = DIAGNOSES[rule.diagIdx];
    if (pct > (diagBestScores[diagName] || 0)) {
      diagBestScores[diagName] = pct;
      diagBestRules[diagName]  = rule;
    }
  });

  return Object.entries(diagBestScores)
    .filter(([_, pct]) => pct >= 0.4)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([diagName, pct]) => {
      const rule = diagBestRules[diagName];
      const missing = rule.symptoms.filter(s => !symptomsArray[s]).map(s => SYMPTOMS[s]);
      return { diagName, pct, rule, missing };
    });
}

// ============================================================
//  RUN EXPERT SYSTEM (ENTRY POINT)
// ============================================================

function runExpertSystem() {
  const normalized = state.symptoms.map(s => s === true);
  const bcResult = runBackwardChaining(normalized);

  if (!bcResult.matched) {
    showSection('sec-diagnosis');
    document.getElementById('diag-empty').classList.remove('hidden');
    document.getElementById('diag-result').classList.add('hidden');
    const el = document.getElementById('diag-empty');
    el.querySelector('h3').textContent = 'Diagnosis Tidak Dapat Ditentukan';
    el.querySelector('p').textContent = 'Gejala yang diinputkan tidak memenuhi aturan apapun secara penuh. Silakan rujuk ke dokter spesialis jantung (Sp.JP).';
    return;
  }

  const matchedRule = bcResult.matched;
  const diagnosisName = DIAGNOSES[matchedRule.diagIdx];
  const fcResult = runForwardChaining(matchedRule.diagIdx);
  const differential = computeDifferentialDiagnosis(normalized, matchedRule.ruleNum);

  state.diagnosisResult = { rule: matchedRule, name: diagnosisName };
  state.treatmentResult = fcResult;
  state.inferenceTrace = {
    backward: bcResult.trace,
    forward: fcResult.forwardTrace,
    workingMemory: normalized,
  };

  updatePatientBadge();
  saveToHistory(diagnosisName);
  renderDiagnosis(diagnosisName, matchedRule, normalized, differential);
  renderTreatment(diagnosisName, fcResult);
  renderInferenceTrace(state.inferenceTrace, diagnosisName);
  buildTerminalOutput(diagnosisName, matchedRule, normalized, fcResult);
  showSection('sec-diagnosis');
}

// ============================================================
//  RENDER — DIAGNOSIS
// ============================================================

function renderDiagnosis(diagnosisName, rule, normalized, differential) {
  document.getElementById('diag-empty').classList.add('hidden');
  const resultEl = document.getElementById('diag-result');
  resultEl.classList.remove('hidden');

  const style   = DIAG_STYLES[diagnosisName] || {};
  const icd     = ICD10[diagnosisName] || '—';
  const urgency = URGENCY[diagnosisName] || { level: 'SEDANG', cls: 'urgency-moderate' };

  const card = document.getElementById('diag-main-card');
  card.className = `rounded-2xl border p-5 ${style.card || ''}`;

  const iconRing = document.getElementById('diag-icon-ring');
  iconRing.className = `w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 ${style.icon || ''}`;
  iconRing.innerHTML = `<i data-lucide="${style.lucide || 'stethoscope'}" class="w-7 h-7"></i>`;

  document.getElementById('diag-name').textContent = diagnosisName;
  document.getElementById('diag-icd').textContent = `ICD-10: ${icd}`;

  const ubadge = document.getElementById('diag-urgency-badge');
  ubadge.textContent = `Urgensi: ${urgency.level}`;
  ubadge.className = `rounded-full px-3 py-1 text-xs font-bold ${urgency.cls}`;

  const symList = document.getElementById('diag-symptoms-list');
  symList.innerHTML = '';
  rule.symptoms.forEach(sIdx => {
    const chip = document.createElement('div');
    chip.className = 'flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/25 rounded-full px-3 py-1 text-xs text-emerald-400';
    chip.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>${SYMPTOMS[sIdx]}`;
    symList.appendChild(chip);
  });

  document.getElementById('diag-rule-detail').textContent =
    `RULE-${rule.ruleNum}:\nIF\n${rule.symptoms.map(s => `  S${s}: ${SYMPTOMS[s]}`).join('\n')}\nTHEN\n  DIAGNOSIS: ${diagnosisName}`;

  // Differential Diagnosis
  const diffEl = document.getElementById('diag-differential');
  diffEl.innerHTML = '';
  if (differential.length === 0) {
    diffEl.innerHTML = '<p class="text-xs text-slate-600 italic">Tidak ada kandidat diagnosis banding yang memiliki kecocokan ≥ 40%.</p>';
  } else {
    differential.forEach(item => {
      const pct = Math.round(item.pct * 100);
      const dStyle = DIAG_STYLES[item.diagName] || {};
      const icdCode = ICD10[item.diagName] || '—';
      const el = document.createElement('div');
      el.className = 'diff-item';
      el.innerHTML = `
        <div class="w-9 h-9 rounded-xl flex-shrink-0 flex items-center justify-center ${dStyle.icon || 'bg-slate-700/50'}">
          <i data-lucide="${dStyle.lucide || 'circle'}" class="w-4 h-4"></i>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-sm font-semibold text-white truncate">${item.diagName}</span>
            <span class="font-mono text-[10px] text-slate-500">${icdCode}</span>
          </div>
          <div class="w-full bg-surface-900/60 rounded-full h-1.5 mb-1.5">
            <div class="h-full rounded-full transition-all duration-700" style="width:${pct}%; background:${dStyle.hypoColor || '#38bdf8'}"></div>
          </div>
          ${item.missing.length > 0 ? `<p class="text-[10px] text-slate-600">Gejala kurang: <span class="text-slate-500">${item.missing.slice(0,2).join(', ')}${item.missing.length > 2 ? ` +${item.missing.length-2} lainnya` : ''}</span></p>` : ''}
        </div>
        <div class="flex-shrink-0 text-right">
          <span class="font-mono font-bold text-sm" style="color:${dStyle.hypoColor || '#38bdf8'}">${pct}%</span>
          <p class="text-[10px] text-slate-600">match</p>
        </div>
      `;
      diffEl.appendChild(el);
    });
  }

  // Patient Summary
  const summaryEl = document.getElementById('diag-patient-summary');
  summaryEl.innerHTML = '';
  [
    { label: 'Nama',          value: document.getElementById('inp-name').value || '—' },
    { label: 'ID Rekam Medis',value: document.getElementById('inp-id').value || '—' },
    { label: 'Usia',          value: document.getElementById('inp-age').value ? document.getElementById('inp-age').value + ' thn' : '—' },
    { label: 'Jenis Kelamin', value: document.getElementById('inp-gender').value || '—' },
  ].forEach(f => {
    const el = document.createElement('div');
    el.className = 'bg-surface-900/50 rounded-xl p-3';
    el.innerHTML = `<p class="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">${f.label}</p><p class="text-sm font-semibold text-white">${f.value}</p>`;
    summaryEl.appendChild(el);
  });

  lucide.createIcons();
}

// ============================================================
//  RENDER — TREATMENT
// ============================================================

function renderTreatment(diagnosisName, fcResult) {
  document.getElementById('treat-empty').classList.add('hidden');
  document.getElementById('treat-result').classList.remove('hidden');

  const condEl = document.getElementById('treat-conditions');
  condEl.innerHTML = '';
  fcResult.conditions.forEach(cond => {
    const el = document.createElement('div');
    el.className = 'flex items-center gap-3 p-3 bg-surface-900/50 rounded-xl border border-slate-700/30';
    el.innerHTML = `
      <div class="w-8 h-8 rounded-lg bg-amber-500/15 border border-amber-500/25 flex items-center justify-center flex-shrink-0">
        <i data-lucide="activity" class="w-4 h-4 text-amber-400"></i>
      </div>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-white truncate">${cond.name}</p>
        <p class="text-xs text-slate-500">Status: <span class="text-amber-400 font-mono font-semibold">${cond.condition}</span></p>
      </div>
    `;
    condEl.appendChild(el);
  });

  const treatColors = [
    'from-brand-900/50 to-brand-800/30 border-brand-700/40',
    'from-violet-900/50 to-violet-800/30 border-violet-700/40',
    'from-emerald-900/50 to-emerald-800/30 border-emerald-700/40',
    'from-amber-900/50 to-amber-800/30 border-amber-700/40',
  ];
  const cardsEl = document.getElementById('treat-cards');
  cardsEl.innerHTML = '';
  fcResult.treatments.forEach((treatment, i) => {
    const el = document.createElement('div');
    el.className = `treat-card bg-gradient-to-br ${treatColors[i % treatColors.length]}`;
    el.innerHTML = `
      <div class="flex items-start gap-3">
        <div class="w-9 h-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center flex-shrink-0 mt-0.5">
          <i data-lucide="pill" class="w-4 h-4 text-brand-300"></i>
        </div>
        <div>
          <p class="text-[10px] text-slate-500 uppercase tracking-widest mb-0.5">Rekomendasi ${i+1}</p>
          <p class="text-sm font-bold text-white leading-snug">${treatment}</p>
        </div>
      </div>
    `;
    cardsEl.appendChild(el);
  });

  const examsEl = document.getElementById('treat-exams');
  examsEl.innerHTML = '';
  (FURTHER_EXAMS[diagnosisName] || []).forEach((exam, i) => {
    const el = document.createElement('div');
    el.className = 'flex items-center gap-2.5 p-3 bg-surface-900/50 rounded-xl border border-slate-700/30';
    el.innerHTML = `<span class="font-mono text-[10px] text-brand-400 bg-brand-500/10 border border-brand-500/20 rounded px-1.5 py-0.5">${String(i+1).padStart(2,'0')}</span><span class="text-sm text-slate-300">${exam}</span>`;
    examsEl.appendChild(el);
  });

  lucide.createIcons();
}

// ============================================================
//  RENDER — INFERENCE TRACE
// ============================================================

function renderInferenceTrace(trace, diagnosisName) {
  document.getElementById('inf-empty').classList.add('hidden');
  document.getElementById('inf-result').classList.remove('hidden');

  // Working Memory
  const wmEl = document.getElementById('inf-working-memory');
  wmEl.innerHTML = '';
  trace.workingMemory.forEach((val, idx) => {
    const el = document.createElement('div');
    el.className = `flex items-center gap-2 p-2.5 rounded-lg text-xs ${val ? 'bg-emerald-500/08 border border-emerald-500/20' : 'bg-surface-900/40 border border-slate-700/20'}`;
    el.innerHTML = `
      <div class="w-4 h-4 rounded flex items-center justify-center flex-shrink-0 ${val ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700/30 text-slate-600'}">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-2.5 h-2.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">${val ? '<polyline points="20 6 9 17 4 12"></polyline>' : '<line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line>'}</svg>
      </div>
      <span class="${val ? 'text-slate-300' : 'text-slate-600'} leading-tight">${SYMPTOMS[idx]}</span>
      <span class="ml-auto font-mono text-[10px] ${val ? 'text-emerald-400' : 'text-slate-700'}">${val ? 'TRUE' : 'FALSE'}</span>
    `;
    wmEl.appendChild(el);
  });

  // Backward trace
  const bcEl = document.getElementById('inf-backward-trace');
  bcEl.innerHTML = '';
  trace.backward.forEach(step => {
    const el = document.createElement('div');
    el.className = `trace-step ${step.matched ? 'success' : (step.partial ? 'active' : 'fail')}`;
    el.innerHTML = `
      <div class="w-5 h-5 rounded flex items-center justify-center flex-shrink-0 text-[10px] font-mono ${step.matched ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700/30 text-slate-500'}">${step.matched ? '✓' : '✗'}</div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-0.5">
          <span class="font-mono text-[10px] text-slate-500">R-${step.ruleNum}</span>
          ${step.matched ? '<span class="text-[10px] text-emerald-400 font-semibold">MATCHED</span>' : ''}
        </div>
        <p class="text-xs text-slate-400 truncate">IF <span class="font-mono text-slate-300">${step.symptoms.map(s=>`S${s}`).join(' ∧ ')}</span> → <span class="${step.matched?'text-emerald-300':'text-slate-500'}">${DIAGNOSES[step.diagIdx]}</span></p>
      </div>
    `;
    bcEl.appendChild(el);
  });

  // Forward trace
  const fcEl = document.getElementById('inf-forward-trace');
  fcEl.innerHTML = '';
  trace.forward.forEach(step => {
    const el = document.createElement('div');
    el.className = 'trace-step success';
    el.innerHTML = `
      <div class="w-5 h-5 rounded bg-emerald-500/20 text-emerald-400 flex items-center justify-center flex-shrink-0 text-[10px]">⚡</div>
      <div>
        <p class="text-xs text-slate-400">IF <span class="font-mono text-amber-300">${step.condition}</span> = <span class="font-mono text-amber-400 font-semibold">${step.state}</span></p>
        <p class="text-xs text-emerald-300 font-medium mt-0.5">THEN → ${step.treatment}</p>
      </div>
    `;
    fcEl.appendChild(el);
  });

  const trigger = document.createElement('div');
  trigger.className = 'trace-step active mt-2';
  trigger.innerHTML = `<div class="w-5 h-5 rounded bg-brand-500/20 text-brand-400 flex items-center justify-center flex-shrink-0 text-[10px]">→</div><p class="text-xs text-slate-300">Diagnosis <span class="text-brand-300 font-semibold">${diagnosisName}</span> memicu ${trace.forward.length} kondisi klinis → ${state.treatmentResult.treatments.length} rekomendasi terapi.</p>`;
  fcEl.appendChild(trigger);
}

// ============================================================
//  KNOWLEDGE BASE TABLES
// ============================================================

function buildKnowledgeTables() {
  const bTbody = document.getElementById('kb-backward-tbody');
  if (bTbody) {
    bTbody.innerHTML = '';
    BACKWARD_RULES.forEach(rule => {
      const diagName = DIAGNOSES[rule.diagIdx];
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="px-4 py-2.5 font-mono text-xs text-slate-500">R-${rule.ruleNum}</td>
        <td class="px-4 py-2.5">
          <div class="flex flex-wrap gap-1 mb-1">
            ${rule.symptoms.map(s => `<span class="text-[10px] bg-brand-500/10 border border-brand-500/20 text-brand-400 rounded px-1.5 py-0.5 font-mono">S${s}</span>`).join('')}
          </div>
          <p class="text-[11px] text-slate-500">${rule.symptoms.map(s=>SYMPTOMS[s]).join(' ∧ ')}</p>
        </td>
        <td class="px-4 py-2.5 text-xs font-semibold text-white">${diagName}</td>
      `;
      bTbody.appendChild(tr);
    });
  }

  const fTbody = document.getElementById('kb-forward-tbody');
  if (fTbody) {
    fTbody.innerHTML = '';
    Object.entries(DIAGNOSIS_AILMENT).forEach(([diagIdx, ailmentIndices]) => {
      const diagName = DIAGNOSES[parseInt(diagIdx)];
      const conditions = AILMENT_CONDITION[parseInt(diagIdx)] || [];
      ailmentIndices.forEach((varIdx, localIdx) => {
        const condition = conditions[localIdx] || '—';
        const match = FORWARD_TREATMENT_RULES.find(r => r.clauseVarIdx === varIdx && r.condition === condition);
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td class="px-4 py-2.5 text-xs font-semibold text-white">${diagName}</td>
          <td class="px-4 py-2.5"><span class="text-xs text-slate-300">${FORWARD_CLAUSE_VARIABLES[varIdx]}</span> <span class="font-mono text-[10px] text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded px-1.5 py-0.5">${condition}</span></td>
          <td class="px-4 py-2.5 text-xs text-emerald-300 font-medium">${match ? match.treatment : '—'}</td>
        `;
        fTbody.appendChild(tr);
      });
    });
  }
}

function showKnowledgeTab(tabId) {
  document.querySelectorAll('.kb-tab-content').forEach(t => t.classList.add('hidden'));
  document.querySelectorAll('.kb-tab').forEach(t => t.classList.remove('active'));
  document.getElementById(tabId).classList.remove('hidden');
  document.getElementById(tabId === 'tab-backward' ? 'kn-tab-backward' : 'kn-tab-forward').classList.add('active');
}

// ============================================================
//  TERMINAL SIMULATOR
// ============================================================

function buildTerminalOutput(diagnosisName, rule, normalized, fcResult) {
  const positiveSymptoms = rule.symptoms.map(s => SYMPTOMS[s]);
  const lines = [
    '=======================================================================',
    '  SISTEM PAKAR: DIAGNOSIS & REKOMENDASI PENGOBATAN PENYAKIT JANTUNG    ',
    '=======================================================================',
    '',
    'Silakan jawab pertanyaan gejala berikut untuk mendiagnosis pasien.',
    '',
    ...SYMPTOMS.map((s, i) => `Apakah pasien mengalami: ${s}?\n[Ketik Y untuk Ya / T untuk Tidak]: ${normalized[i] ? 'y' : 't'}`),
    '',
    '=======================================================================',
    '                       HASIL DIAGNOSIS SISTEM PAKAR                    ',
    '=======================================================================',
    '',
    'Pasien teridentifikasi memiliki gejala-gejala berikut:',
    ...positiveSymptoms.map(s => `  * ${s}`),
    '',
    '>>> KESIMPULAN DIAGNOSIS:',
    `    Pasien kemungkinan menderita: ${diagnosisName}`,
    '    (Disarankan melakukan tes medis lanjutan untuk konfirmasi kondisi).',
    '',
    '-----------------------------------------------------------------------',
    '            REKOMENDASI PENGOBATAN & TINDAKAN KLINIS (FORWARD CHAIN)   ',
    '-----------------------------------------------------------------------',
    '',
    ...fcResult.conditions.map((c, i) => [`- Kondisi Klinis Terkait : ${c.name}`, `  -> Terapi / Rekomendasi : ${fcResult.treatments[i] || '—'}`, '']).flat(),
    '=======================================================================',
    '  Terima kasih telah menggunakan Sistem Pakar Diagnosis Jantung!',
    '=======================================================================',
    '',
  ];
  state.terminalLines = lines;
}

function simulateTerminal() {
  const el = document.getElementById('terminal-output');
  el.innerHTML = '';
  const sample = [
    '=======================================================================',
    '  SISTEM PAKAR: DIAGNOSIS & REKOMENDASI PENGOBATAN PENYAKIT JANTUNG    ',
    '=======================================================================','',
    'Silakan jawab pertanyaan gejala berikut untuk mendiagnosis pasien.','',
    'Apakah pasien mengalami: Detak Jantung Cepat/Tidak Teratur atau Berdebar-debar (Palpitasi)?',
    '[Ketik Y untuk Ya / T untuk Tidak]: y',
    'Apakah pasien mengalami: Nyeri Dada?',
    '[Ketik Y untuk Ya / T untuk Tidak]: t',
    'Apakah pasien mengalami: Kebingungan / Linglung?',
    '[Ketik Y untuk Ya / T untuk Tidak]: y','',
    '=======================================================================',
    '                       HASIL DIAGNOSIS SISTEM PAKAR                    ',
    '=======================================================================','',
    'Pasien teridentifikasi memiliki gejala-gejala berikut:',
    '  * Detak Jantung Cepat/Tidak Teratur atau Berdebar-debar (Palpitasi)',
    '  * Kebingungan / Linglung','',
    '>>> KESIMPULAN DIAGNOSIS:',
    '    Pasien kemungkinan menderita: Gagal Jantung (Heart Failure)',
    '    (Disarankan melakukan tes medis lanjutan untuk konfirmasi kondisi).','',
    '-----------------------------------------------------------------------',
    '            REKOMENDASI PENGOBATAN & TINDAKAN KLINIS (FORWARD CHAIN)   ',
    '-----------------------------------------------------------------------','',
    '- Kondisi Klinis Terkait : Tekanan darah tinggi dan perkembangan penyakit',
    '  -> Terapi / Rekomendasi : OBAT ACE INHIBITOR / ARB BLOCKERS','',
    '- Kondisi Klinis Terkait : Penumpukan cairan tubuh',
    '  -> Terapi / Rekomendasi : OBAT DIURETIK / ANTAGONIS ALDOSTERON','',
    '=======================================================================',
    '  Terima kasih telah menggunakan Sistem Pakar Diagnosis Jantung!',
    '=======================================================================','',
  ];
  typewriterEffect(el, sample, 0, 16);
}

function typeCurrentSession() {
  const el = document.getElementById('terminal-output');
  el.innerHTML = '';
  if (!state.terminalLines.length) {
    el.textContent = '-- Belum ada sesi aktif. Jalankan Expert System terlebih dahulu. --';
    return;
  }
  typewriterEffect(el, state.terminalLines, 0, 10);
}

function typewriterEffect(el, lines, idx, speed) {
  if (idx >= lines.length) {
    const cur = document.createElement('span');
    cur.className = 'terminal-cursor';
    el.appendChild(cur);
    return;
  }
  el.textContent += lines[idx] + '\n';
  el.scrollTop = el.scrollHeight;
  setTimeout(() => typewriterEffect(el, lines, idx + 1, speed), speed);
}

function clearTerminal() {
  document.getElementById('terminal-output').innerHTML = '';
}

// ============================================================
//  PATIENT HISTORY — localStorage
// ============================================================

const HISTORY_KEY = 'cardioexpert_history';

function saveToHistory(diagnosisName) {
  const history = getHistory();
  const entry = {
    id: Date.now(),
    timestamp: new Date().toISOString(),
    name:   document.getElementById('inp-name').value || '—',
    rmId:   document.getElementById('inp-id').value || '—',
    age:    document.getElementById('inp-age').value || '—',
    gender: document.getElementById('inp-gender').value || '—',
    diagnosis: diagnosisName,
    icd: ICD10[diagnosisName] || '—',
    urgency: (URGENCY[diagnosisName] || {}).level || '—',
  };
  history.unshift(entry);
  // Keep last 50
  const trimmed = history.slice(0, 50);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(trimmed));
  updateHistoryBadge();
}

function getHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
  } catch {
    return [];
  }
}

function updateHistoryBadge() {
  const count = getHistory().length;
  const badge = document.getElementById('history-count-badge');
  if (!badge) return;
  if (count > 0) {
    badge.textContent = count;
    badge.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
  }
}

function showHistoryModal() {
  const modal = document.getElementById('history-modal');
  const list  = document.getElementById('history-list');
  const history = getHistory();
  list.innerHTML = '';

  if (history.length === 0) {
    list.innerHTML = '<div class="flex flex-col items-center py-12 text-center"><p class="text-slate-400 font-medium mb-1">Belum ada riwayat</p><p class="text-xs text-slate-600">Jalankan diagnosis untuk menyimpan riwayat pasien.</p></div>';
  } else {
    history.forEach(entry => {
      const dt = new Date(entry.timestamp);
      const dtStr = dt.toLocaleDateString('id-ID', { day:'numeric', month:'short', year:'numeric' }) + ' ' + dt.toLocaleTimeString('id-ID', { hour:'2-digit', minute:'2-digit' });
      const urgencyClass = entry.urgency === 'KRITIS' ? 'text-red-400 bg-red-500/10 border-red-500/25' : entry.urgency === 'TINGGI' ? 'text-amber-400 bg-amber-500/10 border-amber-500/25' : 'text-brand-400 bg-brand-500/10 border-brand-500/25';
      const el = document.createElement('div');
      el.className = 'history-item';
      el.innerHTML = `
        <div class="flex items-start justify-between gap-3 mb-2">
          <div>
            <p class="text-sm font-semibold text-white">${entry.name}</p>
            <p class="text-xs text-slate-500">${entry.rmId} · ${entry.age === '—' ? '—' : entry.age + ' thn'} · ${entry.gender}</p>
          </div>
          <span class="text-[10px] text-slate-600 font-mono flex-shrink-0 mt-0.5">${dtStr}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-semibold text-white truncate">${entry.diagnosis}</span>
          <span class="text-[10px] font-mono text-slate-500">${entry.icd}</span>
          <span class="ml-auto text-[10px] font-bold px-2 py-0.5 rounded-full border ${urgencyClass}">${entry.urgency}</span>
        </div>
      `;
      list.appendChild(el);
    });
  }

  modal.classList.remove('hidden');
  lucide.createIcons();
}

function hideHistoryModal(e) {
  if (!e || e.target === document.getElementById('history-modal')) {
    document.getElementById('history-modal').classList.add('hidden');
  }
}

function clearHistory() {
  localStorage.removeItem(HISTORY_KEY);
  updateHistoryBadge();
  showHistoryModal();
}

// ============================================================
//  PRINT REPORT (formal white paper)
// ============================================================

function printReport() {
  const diagName    = state.diagnosisResult ? state.diagnosisResult.name : null;
  const patName     = document.getElementById('inp-name').value || '—';
  const patId       = document.getElementById('inp-id').value || '—';
  const patAge      = document.getElementById('inp-age').value || '—';
  const patGender   = document.getElementById('inp-gender').value || '—';
  const now         = new Date().toLocaleString('id-ID', { dateStyle: 'full', timeStyle: 'short' });
  const icd         = diagName ? (ICD10[diagName] || '—') : '—';
  const urg         = diagName ? ((URGENCY[diagName] || {}).level || '—') : '—';
  const urgColor    = urg === 'KRITIS' ? '#dc2626' : urg === 'TINGGI' ? '#d97706' : '#0284c7';

  const symptomRows = diagName && state.diagnosisResult
    ? state.diagnosisResult.rule.symptoms.map(s => `<tr><td style="padding:5px 12px; border:1px solid #e2e8f0; font-size:12px; color:#374151;">• ${SYMPTOMS[s]}</td></tr>`).join('')
    : '';

  const treatRows = state.treatmentResult
    ? state.treatmentResult.treatments.map((t, i) =>
        `<tr><td style="padding:6px 12px; border:1px solid #e2e8f0; font-size:11px; color:#166534; background:#f0fdf4; font-weight:700;">${i+1}. ${t}</td></tr>`
      ).join('')
    : '<tr><td style="padding:6px; color:#6b7280; font-style:italic; font-size:12px;">—</td></tr>';

  const examRows = diagName
    ? (FURTHER_EXAMS[diagName] || []).map((e, i) => `<tr><td style="padding:5px 12px; border:1px solid #e2e8f0; font-size:12px; color:#374151;">${i+1}. ${e}</td></tr>`).join('')
    : '';

  const diffRows = state.inferenceTrace && diagName
    ? computeDifferentialDiagnosis(state.inferenceTrace.workingMemory, state.diagnosisResult.rule.ruleNum)
        .map(d => `<tr><td style="padding:5px 12px; border:1px solid #e2e8f0; font-size:12px; color:#374151;">${d.diagName}</td><td style="padding:5px 12px; border:1px solid #e2e8f0; font-size:12px; font-weight:700; color:#374151; text-align:center;">${Math.round(d.pct*100)}%</td></tr>`)
        .join('')
    : '';

  const content = `
    <div style="font-family:'Plus Jakarta Sans',sans-serif; color:#1e293b;">
      <!-- Header -->
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; padding-bottom:16px; border-bottom:3px solid #0369a1;">
        <div>
          <h1 style="font-size:20px; font-weight:800; color:#0c4a6e; margin:0 0 3px;">CardioExpert CDSS</h1>
          <p style="font-size:11px; color:#64748b; margin:0;">Clinical Decision Support System — Laporan Medis Klinis</p>
        </div>
        <div style="text-align:right;">
          <p style="font-size:10px; color:#94a3b8; margin:0;">Dicetak: ${now}</p>
          <p style="font-size:10px; color:#94a3b8; margin:2px 0 0;">AI-TE01 · S1 Teknik Elektro · A05071238</p>
        </div>
      </div>

      <!-- Patient Data -->
      <table style="width:100%; border-collapse:collapse; margin-bottom:18px;">
        <thead><tr><th colspan="2" style="padding:8px 12px; background:#0369a1; color:white; font-size:12px; text-align:left; border-radius:6px 6px 0 0;">Data Pasien</th></tr></thead>
        <tbody>
          <tr><td style="padding:5px 12px; border:1px solid #e2e8f0; width:30%; font-size:12px; font-weight:600; background:#f8fafc;">Nama</td><td style="padding:5px 12px; border:1px solid #e2e8f0; font-size:12px;">${patName}</td></tr>
          <tr><td style="padding:5px 12px; border:1px solid #e2e8f0; font-size:12px; font-weight:600; background:#f8fafc;">ID Rekam Medis</td><td style="padding:5px 12px; border:1px solid #e2e8f0; font-size:12px;">${patId}</td></tr>
          <tr><td style="padding:5px 12px; border:1px solid #e2e8f0; font-size:12px; font-weight:600; background:#f8fafc;">Usia</td><td style="padding:5px 12px; border:1px solid #e2e8f0; font-size:12px;">${patAge === '—' ? '—' : patAge + ' tahun'}</td></tr>
          <tr><td style="padding:5px 12px; border:1px solid #e2e8f0; font-size:12px; font-weight:600; background:#f8fafc;">Jenis Kelamin</td><td style="padding:5px 12px; border:1px solid #e2e8f0; font-size:12px;">${patGender}</td></tr>
        </tbody>
      </table>

      ${diagName ? `
      <!-- Diagnosis -->
      <table style="width:100%; border-collapse:collapse; margin-bottom:18px;">
        <thead><tr><th colspan="2" style="padding:8px 12px; background:#dc2626; color:white; font-size:12px; text-align:left;">Hasil Diagnosis — Backward Chaining</th></tr></thead>
        <tbody>
          <tr>
            <td colspan="2" style="padding:14px 12px; border:1px solid #e2e8f0; background:#fef2f2;">
              <p style="font-size:11px; color:#6b7280; margin:0 0 4px; text-transform:uppercase; letter-spacing:0.05em;">Kesimpulan Diagnosis Utama</p>
              <p style="font-size:18px; font-weight:800; color:#991b1b; margin:0 0 6px;">${diagName}</p>
              <div style="display:flex; gap:12px; flex-wrap:wrap;">
                <span style="font-size:11px; background:#fee2e2; color:#991b1b; padding:2px 8px; border-radius:4px; font-weight:600;">ICD-10: ${icd}</span>
                <span style="font-size:11px; background:${urg==='KRITIS'?'#fee2e2':urg==='TINGGI'?'#fef3c7':'#e0f2fe'}; color:${urgColor}; padding:2px 8px; border-radius:4px; font-weight:700;">Urgensi: ${urg}</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Positive Symptoms -->
      <table style="width:100%; border-collapse:collapse; margin-bottom:18px;">
        <thead><tr><th style="padding:8px 12px; background:#0f766e; color:white; font-size:12px; text-align:left;">Gejala Positif Teridentifikasi</th></tr></thead>
        <tbody>${symptomRows}</tbody>
      </table>

      <!-- Differential Diagnosis -->
      ${diffRows ? `
      <table style="width:100%; border-collapse:collapse; margin-bottom:18px;">
        <thead><tr>
          <th style="padding:8px 12px; background:#92400e; color:white; font-size:12px; text-align:left; width:75%;">Diagnosis Banding (Differential Diagnosis)</th>
          <th style="padding:8px 12px; background:#92400e; color:white; font-size:12px; text-align:center;">Match %</th>
        </tr></thead>
        <tbody>${diffRows}</tbody>
      </table>` : ''}

      <!-- Treatment -->
      <table style="width:100%; border-collapse:collapse; margin-bottom:18px;">
        <thead><tr><th style="padding:8px 12px; background:#166534; color:white; font-size:12px; text-align:left;">Rekomendasi Pengobatan — Forward Chaining</th></tr></thead>
        <tbody>${treatRows}</tbody>
      </table>

      <!-- Further Exams -->
      ${examRows ? `
      <table style="width:100%; border-collapse:collapse; margin-bottom:18px;">
        <thead><tr><th style="padding:8px 12px; background:#075985; color:white; font-size:12px; text-align:left;">Pemeriksaan Lanjutan yang Direkomendasikan</th></tr></thead>
        <tbody>${examRows}</tbody>
      </table>` : ''}

      <!-- Rule Used -->
      <div style="margin-bottom:18px; padding:12px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px;">
        <p style="font-size:11px; font-weight:600; color:#374151; margin:0 0 6px; text-transform:uppercase; letter-spacing:0.05em;">Aturan Backward Chaining yang Dipicu</p>
        <pre style="font-family:'JetBrains Mono',monospace; font-size:10px; color:#475569; white-space:pre-wrap; margin:0;">RULE-${state.diagnosisResult.rule.ruleNum}:
IF
${state.diagnosisResult.rule.symptoms.map(s=>`  S${s}: ${SYMPTOMS[s]}`).join('\n')}
THEN
  DIAGNOSIS: ${diagName}</pre>
      </div>
      ` : '<p style="color:#6b7280; font-style:italic; padding:20px 0;">Belum ada hasil diagnosis. Jalankan anamnesis terlebih dahulu.</p>'}

      <!-- Footer -->
      <div style="margin-top:20px; padding-top:12px; border-top:1px solid #e2e8f0; font-size:9px; color:#94a3b8; text-align:center; line-height:1.8;">
        <p>Dokumen ini dihasilkan oleh <strong>CardioExpert CDSS</strong> — Sistem Pakar Diagnosis &amp; Rekomendasi Pengobatan Penyakit Jantung</p>
        <p style="color:#dc2626; font-weight:700; font-size:10px;">⚠ PERHATIAN: Dokumen ini hanya untuk keperluan akademik. BUKAN pengganti diagnosis dan rekomendasi dokter profesional bersertifikat.</p>
      </div>
    </div>
  `;

  document.getElementById('print-content').innerHTML = content;
  document.getElementById('print-overlay').classList.remove('hidden');
  lucide.createIcons();
}

// ============================================================
//  PATIENT BADGE
// ============================================================

function updatePatientBadge() {
  const name = document.getElementById('inp-name').value;
  const badge = document.getElementById('patient-badge');
  const text  = document.getElementById('patient-badge-text');
  if (name) {
    badge.classList.remove('hidden'); badge.classList.add('flex');
    text.textContent = name;
  } else {
    badge.classList.add('hidden'); badge.classList.remove('flex');
  }
}

// ============================================================
//  RESET
// ============================================================

function resetAll() {
  state.wizardIndex = 0;
  state.symptoms    = Array(21).fill(null);
  state.diagnosisResult = null;
  state.treatmentResult = null;
  state.inferenceTrace  = null;
  state.terminalLines   = [];

  // Rebuild wizard card
  const wc = document.getElementById('wiz-card');
  if (wc) {
    wc.innerHTML = `
      <div class="bg-gradient-to-r from-surface-700 to-surface-600 px-5 py-3 flex items-center justify-between border-b border-slate-700/30">
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 rounded-lg bg-brand-500/20 border border-brand-500/30 flex items-center justify-center">
            <i data-lucide="help-circle" class="w-3.5 h-3.5 text-brand-400"></i>
          </div>
          <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Pertanyaan Klinis</span>
        </div>
        <span id="wiz-symptom-code" class="font-mono text-[11px] text-slate-500">S-001</span>
      </div>
      <div class="px-5 py-6">
        <p class="text-slate-400 text-xs mb-1.5">Apakah pasien mengalami:</p>
        <h2 id="wiz-question" class="text-lg font-semibold text-white leading-relaxed mb-6">${SYMPTOMS[0]}?</h2>
        <div class="flex gap-3">
          <button id="wiz-btn-yes" onclick="wizardAnswer(true)" class="flex-1 flex items-center justify-center gap-2 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 hover:border-emerald-500/60 text-emerald-400 font-semibold rounded-xl py-3.5 transition-all duration-150 group">
            <i data-lucide="check-circle-2" class="w-5 h-5 group-hover:scale-110 transition-transform"></i>
            <span>Ya</span><span class="text-[11px] text-emerald-400/60 font-mono">[Y]</span>
          </button>
          <button id="wiz-btn-no" onclick="wizardAnswer(false)" class="flex-1 flex items-center justify-center gap-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 hover:border-red-500/60 text-red-400 font-semibold rounded-xl py-3.5 transition-all duration-150 group">
            <i data-lucide="x-circle" class="w-5 h-5 group-hover:scale-110 transition-transform"></i>
            <span>Tidak</span><span class="text-[11px] text-red-400/60 font-mono">[T]</span>
          </button>
        </div>
        <p class="text-center text-[11px] text-slate-600 mt-3">Keyboard: <kbd class="kbd-key">Y</kbd> = Ya &nbsp;·&nbsp; <kbd class="kbd-key">T</kbd> = Tidak</p>
      </div>
    `;
  }

  const barEl = document.getElementById('wiz-progress-bar');
  const labelEl = document.getElementById('wiz-progress-label');
  if (barEl)   barEl.style.width = '0%';
  if (labelEl) labelEl.textContent = 'Gejala 1 / 21';

  buildMatrix();
  renderWorkingMemoryLog();
  updateHypothesisTracker();

  // Hide results
  ['diag-empty','diag-result'].forEach((id, i) => {
    const el = document.getElementById(id);
    if (el) { if (i === 0) el.classList.remove('hidden'); else el.classList.add('hidden'); }
  });
  document.getElementById('treat-empty')?.classList.remove('hidden');
  document.getElementById('treat-result')?.classList.add('hidden');
  document.getElementById('inf-empty')?.classList.remove('hidden');
  document.getElementById('inf-result')?.classList.add('hidden');

  updatePatientBadge();
  updateRunButtonState();
  lucide.createIcons();
  showSection('sec-anamnesis');
}

// ============================================================
//  KEYBOARD SHORTCUTS
// ============================================================

document.addEventListener('keydown', (e) => {
  if (['INPUT','SELECT','TEXTAREA'].includes(document.activeElement.tagName)) return;
  const section = document.querySelector('.section-page.active');
  if (!section || section.id !== 'sec-anamnesis') return;
  if (state.mode !== 'wizard') return;
  if (state.wizardIndex >= SYMPTOMS.length) return;
  if (e.key === 'y' || e.key === 'Y') wizardAnswer(true);
  else if (e.key === 't' || e.key === 'T' || e.key === 'n' || e.key === 'N') wizardAnswer(false);
});

// ============================================================
//  INIT
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();
  buildMatrix();
  buildKnowledgeTables();
  buildPresetMenu();
  renderWorkingMemoryLog();
  updateHypothesisTracker();
  updateRunButtonState();
  updateHistoryBadge();

  document.getElementById('inp-name').addEventListener('input', updatePatientBadge);
});
