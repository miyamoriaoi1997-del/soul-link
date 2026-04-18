// Soul-Link Dashboard JS
const API = '';

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
    });
});

// ── Emotion State ──
const DIMS = ['affection', 'trust', 'possessiveness', 'patience'];

async function loadEmotion() {
    try {
        const res = await fetch(API + '/api/emotion');
        const data = await res.json();
        if (!data.state) return;
        const s = data.state;
        DIMS.forEach(d => {
            const val = s[d] || 0;
            document.getElementById('bar-' + d).style.width = val + '%';
            document.getElementById('val-' + d).textContent = val + '/100';
            document.getElementById('slider-' + d).value = val;
        });
        document.getElementById('emotion-score').textContent =
            (s.emotion_score >= 0 ? '+' : '') + s.emotion_score.toFixed(2);
    } catch (e) {
        console.error('Failed to load emotion:', e);
    }
}

// Slider sync
DIMS.forEach(d => {
    const slider = document.getElementById('slider-' + d);
    slider.addEventListener('input', () => {
        document.getElementById('val-' + d).textContent = slider.value + '/100';
        document.getElementById('bar-' + d).style.width = slider.value + '%';
    });
});

document.getElementById('btn-save-emotion').addEventListener('click', async () => {
    const body = {};
    DIMS.forEach(d => { body[d] = parseInt(document.getElementById('slider-' + d).value); });
    try {
        const res = await fetch(API + '/api/emotion', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        if (res.ok) await loadEmotion();
    } catch (e) { console.error(e); }
});

document.getElementById('btn-refresh-emotion').addEventListener('click', loadEmotion);

// ── Persona Files ──
let currentFile = 'SOUL.md';

async function loadPersonaFile(filename) {
    currentFile = filename;
    document.getElementById('file-name').textContent = filename;
    document.querySelectorAll('.persona-selector .btn').forEach(b => {
        b.classList.toggle('active', b.dataset.file === filename);
    });
    try {
        const res = await fetch(API + '/api/persona/' + filename);
        const data = await res.json();
        const editor = document.getElementById('persona-editor');
        editor.value = data.content || '';
        editor.readOnly = filename === 'STATE.md' || filename === 'MOMENTS.md';
        document.getElementById('file-size').textContent =
            (data.content || '').length + ' chars';
        document.getElementById('btn-save-persona').disabled = editor.readOnly;
    } catch (e) { console.error(e); }
}

document.querySelectorAll('.persona-selector .btn').forEach(btn => {
    btn.addEventListener('click', () => loadPersonaFile(btn.dataset.file));
});

document.getElementById('btn-save-persona').addEventListener('click', async () => {
    const content = document.getElementById('persona-editor').value;
    const status = document.getElementById('save-status');
    try {
        const res = await fetch(API + '/api/persona/' + currentFile, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ content })
        });
        status.textContent = res.ok ? '✓ 已保存' : '✗ 保存失败';
        status.style.color = res.ok ? '#3fb950' : '#f85149';
        setTimeout(() => { status.textContent = ''; }, 3000);
    } catch (e) { status.textContent = '✗ ' + e.message; }
});

// ── Moments ──
async function loadMoments() {
    const list = document.getElementById('moments-list');
    try {
        const res = await fetch(API + '/api/moments?count=30');
        const data = await res.json();
        if (!data.moments || data.moments.length === 0) {
            list.innerHTML = '<p style="color:var(--text-dim)">暂无记忆</p>';
            return;
        }
        list.innerHTML = data.moments.reverse().map(m => {
            const parts = m.split(' | ');
            const type = parts[1] || 'unknown';
            const typeClass = 'type-' + type;
            return `<div class="moment-entry">
                <span class="moment-type ${typeClass}">${type}</span>
                <span>${m}</span>
            </div>`;
        }).join('');
    } catch (e) { list.innerHTML = '<p>加载失败</p>'; }
}

document.getElementById('btn-refresh-moments').addEventListener('click', loadMoments);

// ── Config ──
async function loadConfig() {
    try {
        const res = await fetch(API + '/api/config');
        const cfg = await res.json();
        if (cfg.llm) {
            document.getElementById('cfg-llm-provider').value = cfg.llm.provider || 'openai';
            document.getElementById('cfg-llm-model').value = cfg.llm.model || '';
            document.getElementById('cfg-llm-baseurl').value = cfg.llm.base_url || '';
        }
        if (cfg.emotion) {
            document.getElementById('cfg-emotion-enabled').checked = cfg.emotion.enabled !== false;
            document.getElementById('cfg-emotion-decay').value = cfg.emotion.decay_rate || 2.0;
            document.getElementById('cfg-neural-enabled').checked = cfg.emotion.neural_enabled === true;
        }
        if (cfg.behavior) {
            document.getElementById('cfg-behavior-enabled').checked = cfg.behavior.enabled !== false;
        }
    } catch (e) { console.error(e); }
}

document.getElementById('btn-save-config').addEventListener('click', async () => {
    const config = {
        llm: {
            provider: document.getElementById('cfg-llm-provider').value,
            model: document.getElementById('cfg-llm-model').value,
            base_url: document.getElementById('cfg-llm-baseurl').value,
        },
        emotion: {
            enabled: document.getElementById('cfg-emotion-enabled').checked,
            decay_rate: parseFloat(document.getElementById('cfg-emotion-decay').value),
            neural_enabled: document.getElementById('cfg-neural-enabled').checked,
        },
        behavior: {
            enabled: document.getElementById('cfg-behavior-enabled').checked,
        }
    };
    const apiKey = document.getElementById('cfg-llm-apikey').value;
    if (apiKey && !apiKey.includes('***')) config.llm.api_key = apiKey;

    const status = document.getElementById('config-status');
    try {
        const res = await fetch(API + '/api/config', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ config })
        });
        status.textContent = res.ok ? '✓ 已保存' : '✗ 保存失败';
        status.style.color = res.ok ? '#3fb950' : '#f85149';
        setTimeout(() => { status.textContent = ''; }, 3000);
    } catch (e) { status.textContent = '✗ ' + e.message; }
});

// ── Chat Test ──
document.getElementById('btn-send').addEventListener('click', sendTestMessage);
document.getElementById('chat-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') sendTestMessage();
});

async function sendTestMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;
    input.value = '';

    const log = document.getElementById('chat-log');
    log.innerHTML += `<div class="chat-msg chat-msg-user">👤 ${msg}</div>`;

    try {
        const res = await fetch(API + '/api/chat', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        const stateStr = data.emotion_state ?
            `好感:${data.emotion_state.affection} 信任:${data.emotion_state.trust} 占有:${data.emotion_state.possessiveness} 耐心:${data.emotion_state.patience}` :
            'N/A';
        log.innerHTML += `<div class="chat-msg chat-msg-system">🔗 情绪: ${stateStr}</div>`;
        await loadEmotion();
    } catch (e) {
        log.innerHTML += `<div class="chat-msg chat-msg-system">❌ ${e.message}</div>`;
    }
    log.scrollTop = log.scrollHeight;
}

// ── Init ──
loadEmotion();
loadPersonaFile('SOUL.md');
loadMoments();
loadConfig();
// Auto-refresh emotion every 30s
setInterval(loadEmotion, 30000);
