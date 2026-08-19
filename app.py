import streamlit as st

# --- Configuração básica da página ---
st.set_page_config(
    page_title="Mody — Hoje",
    page_icon="🌿",
    layout="centered",
)


def carregar_css(caminho: str):
    """Lê o arquivo CSS e injeta na página."""
    with open(caminho, "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


carregar_css("styles/style.css")


# --- Dados fictícios (serão substituídos por dados reais nas próximas etapas) ---
tarefa_atual = "Escrever resumo da reunião de ontem"
proximo_compromisso = "Consulta médica às 15h00"


# --- Estado da aplicação (guardado durante a sessão do navegador) ---
if "checkin" not in st.session_state:
    st.session_state.checkin = None

if "mensagem_acao" not in st.session_state:
    st.session_state.mensagem_acao = None


st.title("Hoje")

# --- Check-in: Como você está agora? ---
st.write("**Como você está agora?**")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🟢 Bem", use_container_width=True):
        st.session_state.checkin = "bem"

with col2:
    if st.button("🟡 Sobrecarregada", use_container_width=True):
        st.session_state.checkin = "sobrecarregada"

with col3:
    if st.button("🔴 Preciso me acalmar", use_container_width=True):
        st.session_state.checkin = "acalmar"

if st.session_state.checkin == "bem":
    st.markdown('<div class="resposta-suave">Que bom. Vamos seguir com o seu dia.</div>', unsafe_allow_html=True)
elif st.session_state.checkin == "sobrecarregada":
    st.markdown('<div class="resposta-suave">Entendido. Vamos manter a tela mais simples possível.</div>', unsafe_allow_html=True)
elif st.session_state.checkin == "acalmar":
    st.markdown('<div class="resposta-suave">Tudo bem. O Modo Acalmar ainda será construído — por enquanto, respire.</div>', unsafe_allow_html=True)


st.write("")  # espaçamento

# --- Prioridade / tarefa atual e próximo compromisso ---
st.markdown(
    f"""
    <div class="card">
        <div class="card-label">Tarefa atual</div>
        <div class="card-value">{tarefa_atual}</div>
    </div>
    <div class="card">
        <div class="card-label">Próximo compromisso</div>
        <div class="card-value">{proximo_compromisso}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")  # espaçamento

# --- Ações principais ---
col_a, col_b, col_c = st.columns(3)

with col_a:
    if st.button("▶️ Começar", use_container_width=True):
        st.session_state.mensagem_acao = "comecar"

with col_b:
    if st.button("🚫 Não consigo começar", use_container_width=True):
        st.session_state.mensagem_acao = "nao_consigo"

with col_c:
    if st.button("🌬️ Preciso me acalmar", use_container_width=True):
        st.session_state.mensagem_acao = "modo_acalmar"

if st.session_state.mensagem_acao == "comecar":
    st.markdown('<div class="resposta-suave">Ótimo — a lógica de iniciar a tarefa será construída em uma próxima etapa.</div>', unsafe_allow_html=True)
elif st.session_state.mensagem_acao == "nao_consigo":
    st.markdown('<div class="resposta-suave">Sem problema. O fluxo "Não consigo começar" ainda será construído.</div>', unsafe_allow_html=True)
elif st.session_state.mensagem_acao == "modo_acalmar":
    st.markdown('<div class="resposta-suave">O Modo Acalmar ainda será construído nas próximas etapas.</div>', unsafe_allow_html=True)
