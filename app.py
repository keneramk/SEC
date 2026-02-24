"""
Historia Eclesiastica - Juego Educativo tipo "Quien Quiere Ser Millonario"
Seminario Evangelico de Caracas - Version Web (Streamlit)
"""

import streamlit as st
import random
import time
import os
from datetime import datetime
from questions import QUESTIONS

# ── Autorefresh para el temporizador ──
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_OK = True
except ImportError:
    AUTOREFRESH_OK = False

# ── Configuracion de pagina ──
st.set_page_config(
    page_title="Historia Eclesiastica - SEC",
    page_icon="⛪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Constantes ──
LEVELS = [
    {"level": 1,  "amount": 100,     "difficulty": 1, "safe": False},
    {"level": 2,  "amount": 200,     "difficulty": 1, "safe": False},
    {"level": 3,  "amount": 500,     "difficulty": 1, "safe": False},
    {"level": 4,  "amount": 1000,    "difficulty": 1, "safe": False},
    {"level": 5,  "amount": 5000,    "difficulty": 1, "safe": True},
    {"level": 6,  "amount": 10000,   "difficulty": 2, "safe": False},
    {"level": 7,  "amount": 20000,   "difficulty": 2, "safe": False},
    {"level": 8,  "amount": 50000,   "difficulty": 2, "safe": False},
    {"level": 9,  "amount": 75000,   "difficulty": 2, "safe": False},
    {"level": 10, "amount": 100000,  "difficulty": 2, "safe": True},
    {"level": 11, "amount": 150000,  "difficulty": 3, "safe": False},
    {"level": 12, "amount": 300000,  "difficulty": 3, "safe": False},
    {"level": 13, "amount": 500000,  "difficulty": 3, "safe": False},
    {"level": 14, "amount": 750000,  "difficulty": 3, "safe": False},
    {"level": 15, "amount": 1000000, "difficulty": 3, "safe": False},
]

TIME_LIMIT = 30
LETTERS = ["A", "B", "C", "D"]
CAT_NAMES = {
    "eventos": "Eventos", "padres": "Padres de la Iglesia",
    "concilios": "Concilios", "herejias": "Herejias",
    "doctrina": "Doctrina", "emperadores": "Emperadores",
    "monaquismo": "Monaquismo", "escritos": "Escritos"
}


def fmt_money(n):
    return f"${n:,}"


# ══════════════════════════════════════════
# ESTADO DEL JUEGO
# ══════════════════════════════════════════

def init_state():
    defaults = {
        'game_state': 'start',
        'player_name': '',
        'current_level': 0,
        'used_questions': set(),
        'current_question': None,
        'lifelines': {"5050": True, "skip": True, "hint": True},
        'safe_amount': 0,
        'scores': [],
        'answer_idx': None,
        'is_correct': None,
        'is_timeout': False,
        'question_start_time': None,
        'show_hint': False,
        'eliminated_options': [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_next_question():
    lvl = LEVELS[st.session_state.current_level]
    diff = lvl["difficulty"]
    pool = [i for i, q in enumerate(QUESTIONS)
            if q["difficulty"] == diff and i not in st.session_state.used_questions]
    if not pool:
        pool = [i for i, q in enumerate(QUESTIONS)
                if i not in st.session_state.used_questions]
    if not pool:
        return None
    idx = random.choice(pool)
    st.session_state.used_questions.add(idx)
    return QUESTIONS[idx]


def save_score(amount, level):
    entry = {
        "score": amount,
        "level": level,
        "name": st.session_state.player_name or "Anonimo",
        "date": datetime.now().strftime("%d/%m %H:%M"),
    }
    scores = st.session_state.scores + [entry]
    scores.sort(key=lambda s: s["score"], reverse=True)
    st.session_state.scores = scores[:10]


def action_start_game(name):
    st.session_state.player_name = name.strip()
    st.session_state.current_level = 0
    st.session_state.used_questions = set()
    st.session_state.lifelines = {"5050": True, "skip": True, "hint": True}
    st.session_state.safe_amount = 0
    st.session_state.eliminated_options = []
    st.session_state.show_hint = False
    st.session_state.answer_idx = None
    st.session_state.is_correct = None
    st.session_state.is_timeout = False
    st.session_state.current_question = get_next_question()
    st.session_state.question_start_time = time.time()
    st.session_state.game_state = 'game'


def action_answer(idx):
    elapsed = time.time() - (st.session_state.question_start_time or time.time())
    correct = st.session_state.current_question["answer"]
    st.session_state.is_timeout = elapsed > TIME_LIMIT
    st.session_state.is_correct = (not st.session_state.is_timeout) and (idx == correct)
    st.session_state.answer_idx = idx
    lvl = LEVELS[st.session_state.current_level]
    if st.session_state.is_correct and lvl["safe"]:
        st.session_state.safe_amount = lvl["amount"]
    if not st.session_state.is_correct:
        save_score(st.session_state.safe_amount, st.session_state.current_level)
    st.session_state.game_state = 'result'


def action_continue():
    if st.session_state.current_level >= 14:
        save_score(1000000, 15)
        st.session_state.game_state = 'victory'
    else:
        st.session_state.current_level += 1
        st.session_state.current_question = get_next_question()
        st.session_state.question_start_time = time.time()
        st.session_state.eliminated_options = []
        st.session_state.show_hint = False
        st.session_state.answer_idx = None
        st.session_state.is_correct = None
        st.session_state.game_state = 'game'


def action_retire():
    amount = LEVELS[st.session_state.current_level - 1]["amount"] \
        if st.session_state.current_level > 0 else 0
    save_score(amount, st.session_state.current_level)
    st.session_state.safe_amount = amount
    st.session_state.game_state = 'retire'


def action_5050():
    if not st.session_state.lifelines["5050"]:
        return
    st.session_state.lifelines["5050"] = False
    correct = st.session_state.current_question["answer"]
    wrong = [i for i in range(4) if i != correct]
    st.session_state.eliminated_options = random.sample(wrong, 2)


def action_skip():
    if not st.session_state.lifelines["skip"]:
        return
    st.session_state.lifelines["skip"] = False
    nq = get_next_question()
    if nq:
        st.session_state.current_question = nq
    st.session_state.question_start_time = time.time()
    st.session_state.eliminated_options = []
    st.session_state.show_hint = False


def action_hint():
    if not st.session_state.lifelines["hint"]:
        return
    st.session_state.lifelines["hint"] = False
    st.session_state.show_hint = True


# ══════════════════════════════════════════
# CSS
# ══════════════════════════════════════════

CSS = """
<style>
.stApp { background-color: #0f0f1e; }
.block-container { padding-top: 1.2rem !important; padding-bottom: 1rem !important; max-width: 1080px !important; }

/* Question box */
.question-box {
    background: #161630; border: 2px solid #7eb8f0; border-radius: 12px;
    padding: 26px 32px; margin: 10px 0 18px 0; font-size: 1.15rem;
    color: #e8ecf4 !important; text-align: center; line-height: 1.65;
}

/* Result boxes */
.result-ok {
    background: #0a2e18; border: 2px solid #2ecc71; border-radius: 12px;
    padding: 22px; text-align: center; margin-bottom: 14px;
}
.result-fail {
    background: #2e0a0a; border: 2px solid #e74c3c; border-radius: 12px;
    padding: 22px; text-align: center; margin-bottom: 14px;
}

/* Explanation */
.explanation-box {
    background: #161630; border-left: 4px solid #7eb8f0;
    padding: 16px 20px; border-radius: 0 8px 8px 0;
    margin: 12px 0; line-height: 1.7;
}

/* Hint */
.hint-box {
    background: #201500; border: 1px solid #f39c12;
    border-radius: 8px; padding: 12px 16px; margin: 8px 0;
}

/* All streamlit buttons base */
div.stButton > button {
    background-color: #1a1a40 !important; color: #e8ecf4 !important;
    border: 1px solid #3a3a6a !important; border-radius: 8px !important;
    padding: 13px 18px !important; font-size: 0.98rem !important;
    width: 100% !important; text-align: left !important;
    white-space: normal !important; word-wrap: break-word !important;
    height: auto !important; line-height: 1.4 !important;
    transition: all 0.15s !important;
}
div.stButton > button:hover {
    background-color: #2a2a5a !important;
    border-color: #7eb8f0 !important; color: #ffffff !important;
}

/* Play button */
.play-btn div.stButton > button {
    background: linear-gradient(135deg, #ffd700, #e67e00) !important;
    color: #0f0f1e !important; font-size: 1.25rem !important;
    font-weight: bold !important; border: none !important;
    padding: 16px !important; text-align: center !important;
    border-radius: 10px !important; letter-spacing: 3px !important;
}
.play-btn div.stButton > button:hover {
    background: linear-gradient(135deg, #ffe033, #f39c12) !important;
    color: #0f0f1e !important;
}

/* Action buttons (continue, home, play again) */
.action-btn div.stButton > button {
    background: linear-gradient(135deg, #ffd700, #e67e00) !important;
    color: #0f0f1e !important; font-weight: bold !important;
    font-size: 1.05rem !important; border: none !important;
    text-align: center !important; padding: 14px !important;
    letter-spacing: 1px !important;
}

/* Lifeline active */
.ll-on div.stButton > button {
    background-color: #2a1a00 !important; color: #ffd700 !important;
    border-color: #f39c12 !important; font-weight: bold !important;
    text-align: center !important; font-size: 0.88rem !important;
    padding: 9px !important;
}
.ll-on div.stButton > button:hover {
    background-color: #3a2500 !important; color: #ffe55c !important;
}

/* Lifeline used */
.ll-off div.stButton > button {
    background-color: #111120 !important; color: #3a3a5a !important;
    border-color: #1e1e30 !important; text-align: center !important;
    font-size: 0.88rem !important; padding: 9px !important;
    cursor: not-allowed !important;
}

/* Retire button */
.retire-btn div.stButton > button {
    background-color: #1e1e2e !important; color: #7a7a9a !important;
    border-color: #2a2a3a !important; text-align: center !important;
    font-size: 0.82rem !important; padding: 9px !important;
}
.retire-btn div.stButton > button:hover {
    background-color: #2a2a3e !important; color: #a0a0c0 !important;
}

/* Text input */
div.stTextInput > div > input {
    background-color: #1a1a3a !important; color: #ffd700 !important;
    border: 2px solid #3a3a5a !important; border-radius: 8px !important;
    font-size: 1.1rem !important; padding: 10px 16px !important;
    text-align: center !important;
}
div.stTextInput > div > input:focus {
    border-color: #7eb8f0 !important;
    box-shadow: 0 0 0 2px rgba(126,184,240,0.2) !important;
}

/* Progress bar */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #4ec9b0 0%, #f39c12 70%, #e74c3c 100%) !important;
}

/* Divider */
hr { border-color: #2a2a4a !important; margin: 14px 0 !important; }

/* Hide Streamlit chrome */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
div[data-testid="stDecoration"] { display: none !important; }
</style>
"""


# ══════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════

def render_logo(width=130):
    if os.path.exists("logosec.png"):
        cols = st.columns([1, 1, 1])
        with cols[1]:
            st.image("logosec.png", width=width)


def level_ladder_html(current_level):
    rows = ""
    for i in range(14, -1, -1):
        lv = LEVELS[i]
        if i == current_level:
            style = "background:#7eb8f0;color:#0f0f1e;font-weight:bold;border-radius:4px;padding:2px 6px;"
            marker = "▶"
        elif lv["safe"]:
            style = "color:#f5b041;padding:2px 6px;"
            marker = "◆"
        elif i < current_level:
            style = "color:#2ecc71;padding:2px 6px;"
            marker = "✓"
        else:
            style = "color:#3a3a6a;padding:2px 6px;"
            marker = "·"
        rows += (f'<div style="font-family:\'Courier New\',monospace;font-size:0.76rem;{style}">'
                 f'{marker} {lv["level"]:>2}  {fmt_money(lv["amount"]):>10}</div>')
    return rows


def get_remaining():
    if st.session_state.question_start_time is None:
        return TIME_LIMIT
    return max(0.0, TIME_LIMIT - (time.time() - st.session_state.question_start_time))


# ══════════════════════════════════════════
# PANTALLA: INICIO
# ══════════════════════════════════════════

def screen_start():
    render_logo(width=130)

    st.markdown(
        '<p style="text-align:center;color:#7eb8f0;font-size:0.9rem;font-weight:bold;'
        'letter-spacing:2px;margin:6px 0 2px 0;">SEMINARIO EVANGELICO DE CARACAS</p>',
        unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align:center;color:#c8a800;font-size:0.82rem;margin:0 0 8px 0;">'
        'Prof. Ramon Kenayfati  ·  Historia Eclesiastica I</p>',
        unsafe_allow_html=True)

    st.markdown(
        '<h1 style="text-align:center;color:#ffd700;font-size:2.8rem;margin-bottom:0;'
        'text-shadow:0 0 25px rgba(255,215,0,0.45);">HISTORIA</h1>'
        '<h1 style="text-align:center;color:#a0d0ff;font-size:2.8rem;margin-top:0;">ECLESIASTICA</h1>',
        unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align:center;color:#e8ecf4;font-size:1.05rem;margin-bottom:4px;">'
        'Siglos I – X · Trivia de Historia de la Iglesia</p>',
        unsafe_allow_html=True)
    st.markdown(
        f'<p style="text-align:center;color:#4a4a7a;font-size:0.8rem;">'
        f'{len(QUESTIONS)} preguntas · 15 niveles · 3 comodines · 30 seg por pregunta</p>',
        unsafe_allow_html=True)

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name = st.text_input(
            "nombre", placeholder="Escribe tu nombre...",
            key="start_name", label_visibility="collapsed")

        st.markdown('<div class="play-btn">', unsafe_allow_html=True)
        if st.button("⚡  JUGAR  ⚡", key="btn_play", use_container_width=True):
            if name.strip():
                action_start_game(name)
                st.rerun()
            else:
                st.warning("Escribe tu nombre para comenzar.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Mejores puntajes
    scores = st.session_state.scores
    if scores:
        st.markdown("---")
        st.markdown(
            '<p style="text-align:center;color:#7eb8f0;font-weight:bold;'
            'letter-spacing:2px;font-size:0.9rem;">🏆  MEJORES PUNTAJES</p>',
            unsafe_allow_html=True)
        medals = ["🥇", "🥈", "🥉", "4°", "5°"]
        for i, s in enumerate(scores[:5]):
            color = "#ffd700" if i == 0 else "#e8ecf4"
            medal = medals[i] if i < len(medals) else f"{i+1}°"
            pname = (s.get("name") or "---")[:15]
            st.markdown(
                f'<p style="text-align:center;font-family:\'Courier New\';'
                f'font-size:0.88rem;color:{color};margin:2px 0;">'
                f'{medal}  {pname:<15}  {fmt_money(s["score"])}  '
                f'(Nv.{s["level"]})  {s["date"]}</p>',
                unsafe_allow_html=True)


# ══════════════════════════════════════════
# PANTALLA: JUEGO
# ══════════════════════════════════════════

def screen_game():
    if AUTOREFRESH_OK:
        st_autorefresh(interval=1000, key="timer_refresh")

    q = st.session_state.current_question
    if q is None:
        save_score(1000000, 15)
        st.session_state.game_state = 'victory'
        st.rerun()
        return

    remaining = get_remaining()

    # Timeout automático
    if remaining <= 0:
        st.session_state.answer_idx = -1
        st.session_state.is_correct = False
        st.session_state.is_timeout = True
        save_score(st.session_state.safe_amount, st.session_state.current_level)
        st.session_state.game_state = 'result'
        st.rerun()
        return

    lvl = LEVELS[st.session_state.current_level]

    # ── Cabecera ──
    h1, h2, h3 = st.columns([3, 2, 2])
    with h1:
        pname = st.session_state.player_name
        st.markdown(
            f'<p style="color:#7eb8f0;font-weight:bold;margin:0;font-size:0.9rem;">'
            f'HISTORIA ECLESIASTICA'
            f'{"  ·  " + pname if pname else ""}</p>',
            unsafe_allow_html=True)
    with h2:
        st.markdown(
            f'<p style="color:#ffd700;font-weight:bold;text-align:center;margin:0;">'
            f'Nivel {lvl["level"]}  ·  {fmt_money(lvl["amount"])}</p>',
            unsafe_allow_html=True)
    with h3:
        t_color = "#4ec9b0" if remaining > 10 else "#e74c3c"
        st.markdown(
            f'<p style="color:{t_color};font-weight:bold;text-align:right;'
            f'font-size:1.2rem;font-family:\'Courier New\';margin:0;">'
            f'⏱ {int(remaining)} seg</p>',
            unsafe_allow_html=True)

    st.progress(remaining / TIME_LIMIT)

    # ── Panel principal + escalera ──
    main_col, ladder_col = st.columns([3, 1])

    with main_col:
        cat = CAT_NAMES.get(q["category"], q["category"])
        diff_stars = "⭐" * q["difficulty"]
        st.markdown(
            f'<p style="color:#4a4a7a;font-size:0.82rem;margin-bottom:6px;">'
            f'Siglo {q["century"]}  ·  {cat}  ·  {diff_stars}</p>',
            unsafe_allow_html=True)

        st.markdown(f'<div class="question-box">{q["question"]}</div>',
                    unsafe_allow_html=True)

        # Opciones 2×2
        elim = st.session_state.eliminated_options
        opt_c1, opt_c2 = st.columns(2)
        for i, opt_text in enumerate(q["options"]):
            col = opt_c1 if i % 2 == 0 else opt_c2
            with col:
                if i in elim:
                    st.markdown(
                        f'<div style="background:#0a0a18;border:1px solid #1a1a2a;'
                        f'border-radius:8px;padding:13px 18px;margin-bottom:4px;'
                        f'color:#1e1e3a;font-size:0.98rem;">{LETTERS[i]}) —</div>',
                        unsafe_allow_html=True)
                else:
                    if st.button(f"{LETTERS[i]})  {opt_text}", key=f"opt_{i}"):
                        action_answer(i)
                        st.rerun()

        # Pista
        if st.session_state.show_hint:
            exp = q["explanation"]
            hint = exp[:100] + "..." if len(exp) > 100 else exp
            st.markdown(
                f'<div class="hint-box">'
                f'<b style="color:#f39c12;">💡 PISTA: </b>'
                f'<span style="color:#e8ecf4;">{hint}</span></div>',
                unsafe_allow_html=True)

        st.markdown("---")

        # Comodines + retirarse
        ll = st.session_state.lifelines
        bc1, bc2, bc3, bc4 = st.columns(4)

        with bc1:
            cls = "ll-on" if ll["5050"] else "ll-off"
            st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
            if st.button("50 : 50", key="btn_5050",
                         disabled=not ll["5050"], use_container_width=True):
                action_5050()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with bc2:
            cls = "ll-on" if ll["skip"] else "ll-off"
            st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
            if st.button("↪ Saltar", key="btn_skip",
                         disabled=not ll["skip"], use_container_width=True):
                action_skip()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with bc3:
            cls = "ll-on" if ll["hint"] else "ll-off"
            st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
            if st.button("💡 Pista", key="btn_hint",
                         disabled=not ll["hint"], use_container_width=True):
                action_hint()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with bc4:
            retire_amt = LEVELS[st.session_state.current_level - 1]["amount"] \
                if st.session_state.current_level > 0 else 0
            st.markdown('<div class="retire-btn">', unsafe_allow_html=True)
            if st.button(f"🚪 Retirarse\n{fmt_money(retire_amt)}", key="btn_retire",
                         use_container_width=True):
                action_retire()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.safe_amount > 0:
            st.markdown(
                f'<p style="color:#f5b041;font-size:0.82rem;margin-top:6px;">'
                f'🔒 Seguro: {fmt_money(st.session_state.safe_amount)}</p>',
                unsafe_allow_html=True)

    with ladder_col:
        st.markdown(
            '<p style="color:#7eb8f0;font-size:0.78rem;font-weight:bold;'
            'letter-spacing:1px;text-align:center;margin-bottom:6px;">NIVELES</p>',
            unsafe_allow_html=True)
        st.markdown(level_ladder_html(st.session_state.current_level),
                    unsafe_allow_html=True)


# ══════════════════════════════════════════
# PANTALLA: RESULTADO
# ══════════════════════════════════════════

def screen_result():
    q = st.session_state.current_question
    lvl = LEVELS[st.session_state.current_level]
    is_ok = st.session_state.is_correct
    is_to = st.session_state.is_timeout
    a_idx = st.session_state.answer_idx
    c_idx = q["answer"]

    if is_ok:
        st.markdown(
            f'<div class="result-ok">'
            f'<p style="color:#2ecc71;font-size:2rem;font-weight:bold;margin:0;">✅ CORRECTO!</p>'
            f'<p style="color:#ffd700;font-size:1.25rem;margin:8px 0 0 0;">'
            f'Has ganado {fmt_money(lvl["amount"])}</p></div>',
            unsafe_allow_html=True)
    else:
        title = "⏰ TIEMPO AGOTADO" if is_to else "❌ INCORRECTO"
        st.markdown(
            f'<div class="result-fail">'
            f'<p style="color:#e74c3c;font-size:2rem;font-weight:bold;margin:0;">{title}</p>'
            f'<p style="color:#2ecc71;font-size:1rem;margin:8px 0 4px 0;">'
            f'Respuesta correcta: <b>{q["options"][c_idx]}</b></p>'
            f'<p style="color:#ffd700;font-size:1rem;margin:0;">'
            f'Te retiras con: {fmt_money(st.session_state.safe_amount)}</p></div>',
            unsafe_allow_html=True)

    # Dato historico
    st.markdown(
        f'<div class="explanation-box">'
        f'<p style="color:#7eb8f0;font-size:0.83rem;font-weight:bold;margin:0 0 6px 0;">'
        f'📖 DATO HISTORICO</p>'
        f'<p style="color:#e8ecf4;margin:0;line-height:1.7;">{q["explanation"]}</p></div>',
        unsafe_allow_html=True)

    # Opciones con colores
    st.markdown(
        '<p style="color:#4a4a6a;font-size:0.82rem;margin:10px 0 6px 0;">Las opciones:</p>',
        unsafe_allow_html=True)
    oc1, oc2 = st.columns(2)
    for i, opt in enumerate(q["options"]):
        col = oc1 if i % 2 == 0 else oc2
        with col:
            if i == c_idx:
                bg, border, icon = "#0a2e18", "#2ecc71", "✅"
            elif i == a_idx and not is_ok:
                bg, border, icon = "#2e0a0a", "#e74c3c", "❌"
            else:
                bg, border, icon = "#0d0d1e", "#2a2a3a", "  "
            col.markdown(
                f'<div style="background:{bg};border:1px solid {border};border-radius:8px;'
                f'padding:11px 14px;margin-bottom:5px;color:#e8ecf4;font-size:0.95rem;">'
                f'{icon} {LETTERS[i]}) {opt}</div>',
                unsafe_allow_html=True)

    st.markdown("")
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        st.markdown('<div class="action-btn">', unsafe_allow_html=True)
        if is_ok:
            if st.session_state.current_level >= 14:
                if st.button("🏆 VER RESULTADO FINAL", key="btn_win",
                             use_container_width=True):
                    save_score(1000000, 15)
                    st.session_state.game_state = 'victory'
                    st.rerun()
            else:
                next_lvl = LEVELS[st.session_state.current_level + 1]
                st.markdown(
                    f'<p style="text-align:center;color:#7a7a9a;font-size:0.83rem;'
                    f'margin-bottom:8px;">Siguiente: Nivel {next_lvl["level"]} · '
                    f'{fmt_money(next_lvl["amount"])}</p>',
                    unsafe_allow_html=True)
                if st.button("▶  CONTINUAR", key="btn_cont", use_container_width=True):
                    action_continue()
                    st.rerun()
        else:
            if st.button("🏠  VOLVER AL INICIO", key="btn_home_r",
                         use_container_width=True):
                st.session_state.game_state = 'start'
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════
# PANTALLA: RETIRADA
# ══════════════════════════════════════════

def screen_retire():
    render_logo(width=110)
    name = st.session_state.player_name
    amount = st.session_state.safe_amount

    st.markdown(
        f'<h2 style="text-align:center;color:#7eb8f0;margin-bottom:6px;">'
        f'{"" + name.upper() + ", " if name else ""}TE HAS RETIRADO</h2>',
        unsafe_allow_html=True)
    st.markdown(
        f'<h1 style="text-align:center;color:#ffd700;font-size:3.5rem;'
        f'text-shadow:0 0 20px rgba(255,215,0,0.4);">{fmt_money(amount)}</h1>',
        unsafe_allow_html=True)
    st.markdown(
        f'<p style="text-align:center;color:#a0a0c0;">'
        f'Llegaste al nivel {st.session_state.current_level} de 15</p>',
        unsafe_allow_html=True)

    st.markdown("---")
    _, c, _ = st.columns([1, 2, 1])
    with c:
        st.markdown('<div class="action-btn">', unsafe_allow_html=True)
        if st.button("🏠  VOLVER AL INICIO", key="btn_home_ret",
                     use_container_width=True):
            st.session_state.game_state = 'start'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════
# PANTALLA: VICTORIA
# ══════════════════════════════════════════

def screen_victory():
    render_logo(width=120)
    name = st.session_state.player_name

    st.markdown(
        f'<h1 style="text-align:center;color:#ffd700;font-size:3rem;'
        f'text-shadow:0 0 30px rgba(255,215,0,0.6);">'
        f'{"FELICIDADES, " + name.upper() + "!" if name else "FELICIDADES!"}</h1>',
        unsafe_allow_html=True)
    st.markdown(
        '<h2 style="text-align:center;color:#2ecc71;">🏆  HAS GANADO  🏆</h2>',
        unsafe_allow_html=True)
    st.markdown(
        '<h1 style="text-align:center;color:#ffd700;font-size:4.5rem;'
        'text-shadow:0 0 40px rgba(255,215,0,0.5);">$1,000,000</h1>',
        unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align:center;color:#e8ecf4;font-size:1.1rem;">'
        'Has completado las 15 preguntas correctamente.</p>'
        '<p style="text-align:center;color:#7eb8f0;">'
        'Eres un experto en Historia Eclesiastica.</p>'
        '<p style="text-align:center;color:#4a4a6a;margin-top:16px;">'
        'Seminario Evangelico de Caracas</p>',
        unsafe_allow_html=True)

    st.markdown("---")
    _, c, _ = st.columns([1, 2, 1])
    with c:
        st.markdown('<div class="action-btn">', unsafe_allow_html=True)
        if st.button("🔄  JUGAR DE NUEVO", key="btn_again",
                     use_container_width=True):
            st.session_state.game_state = 'start'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════

def main():
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)

    state = st.session_state.game_state
    if state == 'start':
        screen_start()
    elif state == 'game':
        screen_game()
    elif state == 'result':
        screen_result()
    elif state == 'retire':
        screen_retire()
    elif state == 'victory':
        screen_victory()


if __name__ == "__main__":
    main()
