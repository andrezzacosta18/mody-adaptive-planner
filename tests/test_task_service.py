"""
Temporary manual test page for services/task_service.py.

Goal: exercise create/list/update/complete/reopen/delete and repeat
the user-isolation (RLS) check with two different users, without
touching app.py yet.

How to run:
    streamlit run tests/test_task_service.py
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

from services.auth_service import restore_session, sign_in, sign_out, sign_up
from services.task_service import (
    complete_task,
    create_task,
    delete_task,
    get_task_by_id,
    get_tasks,
    reopen_task,
    update_task,
)

st.set_page_config(page_title="Mody — Teste de Tarefas", page_icon="🧪")


# =========================================================
# Authentication (minimal copy, same pattern as
# tests/test_onboarding.py, just so this page can run in
# isolation)
# =========================================================
if "auth" not in st.session_state:
    st.session_state.auth = None


def is_authenticated() -> bool:
    auth = st.session_state.auth
    if auth is None:
        return False
    ok = restore_session(auth["access_token"], auth["refresh_token"])
    if not ok:
        st.session_state.auth = None
        return False
    return True


def show_login() -> None:
    st.title("🧪 Teste de Tarefas — login")
    st.caption("Use uma conta já existente, ou crie duas para testar o isolamento entre usuários (A e B).")

    login_tab, signup_tab = st.tabs(["Entrar", "Criar conta"])

    with login_tab:
        with st.form("login_form_tasks"):
            email = st.text_input("E-mail", key="login_email_tasks")
            password = st.text_input("Senha", type="password", key="login_password_tasks")
            submitted = st.form_submit_button("Entrar")

        if submitted:
            if not email or not password:
                st.warning("Preencha e-mail e senha.")
            else:
                result = sign_in(email, password)
                if not result["success"]:
                    st.error(result["error"])
                else:
                    session = result["session"]
                    st.session_state.auth = {
                        "access_token": session.access_token,
                        "refresh_token": session.refresh_token,
                        "user_id": session.user.id,
                        "email": session.user.email,
                    }
                    st.rerun()

    with signup_tab:
        with st.form("signup_form_tasks"):
            email = st.text_input("E-mail", key="signup_email_tasks")
            password = st.text_input("Senha", type="password", key="signup_password_tasks")
            submitted = st.form_submit_button("Criar conta")

        if submitted:
            if not email or not password:
                st.warning("Preencha e-mail e senha.")
            else:
                result = sign_up(email, password)
                if not result["success"]:
                    st.error(result["error"])
                elif result["needs_confirmation"]:
                    st.success("Conta criada. Confirme o e-mail e depois volte para fazer login.")
                else:
                    session = result["session"]
                    st.session_state.auth = {
                        "access_token": session.access_token,
                        "refresh_token": session.refresh_token,
                        "user_id": session.user.id,
                        "email": session.user.email,
                    }
                    st.rerun()


STATUS_LABELS_PT = {
    "pending": "Pendente",
    "in_progress": "Em andamento",
    "completed": "Concluída",
    "blocked": "Bloqueada",
}

PRIORITY_LABELS_PT = {
    "low": "Baixa",
    "medium": "Média",
    "high": "Alta",
    None: "Sem prioridade",
}


def show_task_tests() -> None:
    auth = st.session_state.auth
    user_id = auth["user_id"]  # always from the authenticated session

    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.title("🧪 Teste de Tarefas")
    with col_logout:
        st.write("")
        if st.button("Sair"):
            sign_out()
            st.session_state.clear()
            st.rerun()

    st.caption(f"Conectado como {auth['email']} · user_id: {user_id}")

    st.divider()

    # ---- Create ----
    st.subheader("Criar tarefa")
    with st.form("create_task_form"):
        title = st.text_input("Título (obrigatório)", placeholder="Ex: Comprar shampoo")
        description = st.text_area("Descrição (opcional)", value="")
        col1, col2, col3 = st.columns(3)
        with col1:
            priority_label = st.selectbox("Prioridade (opcional)", ["", "Baixa", "Média", "Alta"])
        with col2:
            estimated_minutes = st.number_input(
                "Minutos estimados (opcional)", min_value=0, step=5, value=0
            )
        with col3:
            due_date = st.date_input("Data limite (opcional)", value=None)

        submitted = st.form_submit_button("Criar", type="primary")

    if submitted:
        priority_map = {"": None, "Baixa": "low", "Média": "medium", "Alta": "high"}
        result = create_task(
            user_id=user_id,
            title=title,
            description=description or None,
            priority=priority_map[priority_label],
            estimated_minutes=int(estimated_minutes) if estimated_minutes else None,
            due_date=due_date.isoformat() if due_date else None,
        )
        if result["success"]:
            st.success("Tarefa criada.")
        else:
            st.error(result["error"])

    st.divider()

    # ---- List ----
    st.subheader("Suas tarefas")
    status_filter_label = st.selectbox(
        "Filtrar por status",
        ["Todos", "Pendente", "Em andamento", "Concluída", "Bloqueada"],
        key="status_filter",
    )
    status_filter_map = {
        "Todos": None,
        "Pendente": "pending",
        "Em andamento": "in_progress",
        "Concluída": "completed",
        "Bloqueada": "blocked",
    }
    result = get_tasks(user_id, status=status_filter_map[status_filter_label])

    if not result["success"]:
        st.error(result["error"])
    else:
        tasks = result["data"]
        if not tasks:
            st.info("Nenhuma tarefa encontrada.")
        for task in tasks:
            with st.expander(f"{task['title']} — {STATUS_LABELS_PT.get(task['status'], task['status'])}"):
                st.write(f"**id:** `{task['id']}`")
                st.write(f"**Descrição:** {task.get('description') or '—'}")
                st.write(f"**Prioridade:** {PRIORITY_LABELS_PT.get(task.get('priority'))}")
                st.write(f"**Minutos estimados:** {task.get('estimated_minutes') or '—'}")
                st.write(f"**Data limite:** {task.get('due_date') or '—'}")
                st.write(f"**Criada em:** {task.get('created_at')}")
                st.write(f"**Concluída em:** {task.get('completed_at') or '—'}")

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if task["status"] != "completed":
                        if st.button("Concluir", key=f"complete_{task['id']}"):
                            r = complete_task(user_id, task["id"])
                            if r["success"]:
                                st.rerun()
                            else:
                                st.error(r["error"])
                    else:
                        if st.button("Reabrir", key=f"reopen_{task['id']}"):
                            r = reopen_task(user_id, task["id"])
                            if r["success"]:
                                st.rerun()
                            else:
                                st.error(r["error"])
                with col_b:
                    new_title = st.text_input(
                        "Novo título", value=task["title"], key=f"edit_title_{task['id']}"
                    )
                    if st.button("Salvar título", key=f"save_title_{task['id']}"):
                        r = update_task(user_id, task["id"], title=new_title)
                        if r["success"]:
                            st.rerun()
                        else:
                            st.error(r["error"])
                with col_c:
                    if st.button("Excluir", key=f"delete_{task['id']}"):
                        r = delete_task(user_id, task["id"])
                        if r["success"]:
                            st.rerun()
                        else:
                            st.error(r["error"])

    st.divider()

    # ---- Get by id (manual isolation check) ----
    st.subheader("Buscar tarefa por id")
    st.caption(
        "Útil para o teste de isolamento: copie o id de uma tarefa criada "
        "pelo Usuário A, faça login como Usuário B, e tente buscar esse "
        "mesmo id aqui — o resultado deve vir vazio (não encontrado)."
    )
    task_id_input = st.text_input("Task id")
    if st.button("Buscar"):
        if not task_id_input:
            st.warning("Informe um id.")
        else:
            result = get_task_by_id(user_id, task_id_input)
            if not result["success"]:
                st.error(result["error"])
            elif result["data"] is None:
                st.info("Não encontrada (ou não pertence a este usuário).")
            else:
                st.json(result["data"])


# =========================================================
# Routing
# =========================================================
if is_authenticated():
    show_task_tests()
else:
    show_login()