// Клиентская логика переводчика (lab 18).

const $ = (id) => document.getElementById(id);

let currentTargetLang = 'en';

// ---------- языковые пилюли ----------
document.querySelectorAll('.lang-pill').forEach(pill => {
  pill.addEventListener('click', () => setActiveLang(pill.dataset.lang));
});

function setActiveLang(lang) {
  currentTargetLang = lang;
  document.querySelectorAll('.lang-pill').forEach(p => {
    p.classList.toggle('active', p.dataset.lang === lang);
  });
}

// ---------- счётчик символов ----------
$('sourceText').addEventListener('input', () => {
  $('charCount').textContent = $('sourceText').value.length;
});

// ---------- проверка здоровья ----------
async function checkHealth() {
  const dot = $('statusDot');
  try {
    const r = await fetch('/api/health', { cache: 'no-store' });
    const data = await r.json();
    if (!r.ok || data.status !== 'ok') throw new Error();
    dot.className = 'status-dot status-ok';
    dot.title = 'Backend и БД: OK';
  } catch {
    dot.className = 'status-dot status-err';
    dot.title = 'Backend или БД недоступны';
  }
}
checkHealth();
setInterval(checkHealth, 15000);

// ---------- swap ----------
$('swapBtn').addEventListener('click', () => {
  const hasResult = $('result').classList.contains('has-result');
  const resultText = $('resultText').textContent;

  if (hasResult && resultText) {
    $('sourceText').value = resultText;
    $('charCount').textContent = resultText.length;
  }

  setActiveLang(currentTargetLang === 'ru' ? 'en' : 'ru');
  clearResult();
});

function clearResult() {
  $('result').classList.remove('has-result');
  $('resultText').textContent = 'Перевод появится здесь…';
  $('resultMeta').textContent = '';
  $('translateError').classList.add('hidden');
}

// ---------- перевод ----------
$('translateBtn').addEventListener('click', async () => {
  const text = $('sourceText').value.trim();
  const err = $('translateError');
  err.classList.add('hidden');

  if (!text) {
    err.textContent = 'Введите текст для перевода.';
    err.classList.remove('hidden');
    return;
  }

  const btn = $('translateBtn');
  btn.disabled = true;
  btn.textContent = 'Переводим…';

  try {
    const resp = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, target_lang: currentTargetLang }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || ('HTTP ' + resp.status));

    $('resultText').textContent = data.translated_text;
    $('resultMeta').textContent =
      data.source_lang.toUpperCase() + ' → ' + data.target_lang.toUpperCase() +
      '  ·  #' + data.id + '  ·  ' + data.engine;
    $('result').classList.add('has-result');

    loadHistory();
  } catch (e) {
    err.textContent = 'Ошибка перевода: ' + e.message;
    err.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Перевести →';
  }
});

// ---------- словарь ----------
let vocabulary = [];

async function loadVocabulary() {
  const err = $('vocabError');
  const body = $('vocabBody');
  err.classList.add('hidden');

  try {
    const resp = await fetch('/api/vocabulary');
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || ('HTTP ' + resp.status));

    const filter = $('vocabFilter');
    const pairs = Object.entries(data.pairs || {});

    for (const [pairKey, pair] of pairs) {
      for (const item of pair.items) {
        vocabulary.push({
          ...item,
          source_lang: pair.source_lang,
          target_lang: pair.target_lang,
          pair: pairKey,
        });
      }
      const opt = document.createElement('option');
      opt.value = pairKey;
      opt.textContent = pair.source_lang.toUpperCase() + ' → ' + pair.target_lang.toUpperCase();
      filter.appendChild(opt);
    }

    $('vocabCount').textContent =
      'Позиций: ' + data.count + ' · направлений: ' + pairs.length;
    $('statVocab').textContent = data.count;
    renderVocabulary();
  } catch (e) {
    body.innerHTML = '';
    err.textContent = 'Ошибка загрузки словаря: ' + e.message;
    err.classList.remove('hidden');
  }
}

function renderVocabulary() {
  const body = $('vocabBody');
  const pairFilter = $('vocabFilter').value;
  const search = $('vocabSearch').value.trim().toLowerCase();

  const rows = vocabulary.filter(it => {
    if (pairFilter !== 'all' && it.pair !== pairFilter) return false;
    if (search &&
        !it.source.toLowerCase().includes(search) &&
        !it.target.toLowerCase().includes(search)) return false;
    return true;
  });

  body.innerHTML = '';
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="3" class="empty">Ничего не найдено</td></tr>';
    return;
  }

  const limited = rows.slice(0, 100);

  for (const it of limited) {
    const tr = document.createElement('tr');
    tr.className = 'dict-row';
    tr.title = 'Кликните, чтобы подставить';

    const src = document.createElement('td');
    src.className = 'dict-source';
    src.textContent = it.source;

    const tgt = document.createElement('td');
    tgt.className = 'dict-target';
    tgt.textContent = it.target;

    const dir = document.createElement('td');
    dir.className = 'dict-dir';
    dir.textContent = it.source_lang.toUpperCase() + '→' + it.target_lang.toUpperCase();

    tr.addEventListener('click', () => {
      $('sourceText').value = it.source;
      $('charCount').textContent = it.source.length;
      setActiveLang(it.target_lang);
      clearResult();
      $('sourceText').focus();
    });

    tr.append(src, tgt, dir);
    body.appendChild(tr);
  }

  if (rows.length > limited.length) {
    const tr = document.createElement('tr');
    tr.innerHTML =
      '<td colspan="3" class="empty">Показано ' + limited.length +
      ' из ' + rows.length + '. Уточните поиск.</td>';
    body.appendChild(tr);
  }
}

$('vocabFilter').addEventListener('change', renderVocabulary);
$('vocabSearch').addEventListener('input', renderVocabulary);
loadVocabulary();

// ---------- история ----------
async function loadHistory() {
  const err = $('historyError');
  const list = $('historyList');
  err.classList.add('hidden');
  list.innerHTML = '<p class="empty">Загрузка…</p>';

  try {
    const resp = await fetch('/api/history');
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || ('HTTP ' + resp.status));

    $('historyCount').textContent = 'Записей: ' + data.count;
    $('statHistory').textContent = data.count;
    list.innerHTML = '';

    if (!data.items.length) {
      list.innerHTML = '<p class="empty">История пуста</p>';
      return;
    }

    for (const item of data.items) {
      const el = document.createElement('div');
      el.className = 'history-item';
      el.title = 'Кликните, чтобы повторить перевод';

      const marker = document.createElement('div');
      marker.className = 'history-marker';

      const content = document.createElement('div');
      content.className = 'history-content';

      const orig = document.createElement('div');
      orig.className = 'history-original';
      orig.textContent = item.original_text;

      const trans = document.createElement('div');
      trans.className = 'history-translated';
      trans.textContent = item.translated_text;

      const meta = document.createElement('div');
      meta.className = 'history-meta';
      const time = new Date(item.created_at).toLocaleTimeString('ru-RU',
        { hour: '2-digit', minute: '2-digit' });
      meta.textContent = item.source_lang.toUpperCase() + ' → ' +
        item.target_lang.toUpperCase() + ' · ' + time;

      content.append(orig, trans, meta);

      const del = document.createElement('button');
      del.className = 'history-del';
      del.textContent = '×';
      del.title = 'Удалить';
      del.addEventListener('click', async (ev) => {
        ev.stopPropagation();
        await fetch('/api/history?id=' + item.id, { method: 'DELETE' });
        loadHistory();
      });

      el.addEventListener('click', () => {
        $('sourceText').value = item.original_text;
        $('charCount').textContent = item.original_text.length;
        $('resultText').textContent = item.translated_text;
        $('resultMeta').textContent = item.source_lang.toUpperCase() +
          ' → ' + item.target_lang.toUpperCase();
        $('result').classList.add('has-result');
      });

      el.append(marker, content, del);
      list.appendChild(el);
    }
  } catch (e) {
    list.innerHTML = '';
    err.textContent = 'Ошибка загрузки истории: ' + e.message;
    err.classList.remove('hidden');
  }
}

$('historyBtn').addEventListener('click', loadHistory);
loadHistory();