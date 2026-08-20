from supabase_auth.errors import AuthApiError

from services.supabase_service import get_client


def sign_up(email: str, password: str) -> dict:
    """
    Cria uma conta nova com e-mail e senha.

    Retorna um dict com:
    - success: bool
    - needs_confirmation: True se o Supabase exige confirmação de
      e-mail antes de liberar uma sessão (não assumimos sessão
      imediata após o cadastro).
    - error: mensagem amigável, presente apenas se success for False.
    """
    client = get_client()
    try:
        response = client.auth.sign_up({"email": email, "password": password})
    except AuthApiError as e:
        return {"success": False, "error": _mensagem_amigavel(e)}
    except Exception:
        return {
            "success": False,
            "error": "Não foi possível criar a conta agora. Tente novamente em instantes.",
        }

    # Se o Supabase exige confirmação de e-mail, sign_up retorna o
    # usuário criado mas SEM sessão. Não podemos tratar isso como
    # "já logado".
    if response.session is None:
        return {"success": True, "needs_confirmation": True}

    return {
        "success": True,
        "needs_confirmation": False,
        "session": response.session,
        "user": response.user,
    }


def sign_in(email: str, password: str) -> dict:
    """
    Autentica um usuário existente com e-mail e senha.

    Retorna um dict com success, e em caso de sucesso, session e user.
    Em caso de falha, error com uma mensagem adequada para exibir.
    """
    client = get_client()
    try:
        response = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
    except AuthApiError as e:
        return {"success": False, "error": _mensagem_amigavel(e)}
    except Exception:
        return {
            "success": False,
            "error": "Não foi possível entrar agora. Tente novamente em instantes.",
        }

    if response.session is None or response.user is None:
        return {"success": False, "error": "Não foi possível iniciar a sessão."}

    return {"success": True, "session": response.session, "user": response.user}


def sign_out() -> None:
    """Encerra a sessão no Supabase. Falhas aqui não impedem o logout
    local (o app limpa o session_state de qualquer forma, em app.py)."""
    client = get_client()
    try:
        client.auth.sign_out()
    except Exception:
        pass


def restore_session(access_token: str, refresh_token: str) -> bool:
    """
    Restaura/sincroniza no cliente Supabase a sessão que mantemos em
    st.session_state entre reruns do Streamlit.

    Contexto: o Streamlit reexecuta o script inteiro a cada interação
    do usuário (clique em botão, envio de formulário etc.). Variáveis
    locais e o estado interno do cliente Supabase seriam recriados do
    zero a cada execução — por isso guardamos access_token e
    refresh_token em st.session_state, que sobrevive entre reruns na
    mesma sessão de navegador (nunca a senha).

    Esta função pega esses tokens salvos e os aplica ao cliente
    Supabase da sessão atual (reaproveitado entre reruns via
    st.session_state — ver services/supabase_service.py) através de
    client.auth.set_session(...). Isso garante que toda chamada
    seguinte ao banco carregue o JWT correto no cabeçalho da
    requisição, permitindo que auth.uid() — usado pelas policies de
    Row Level Security — identifique corretamente o usuário
    autenticado.

    Retorna True se a sessão foi restaurada com sucesso, False se o
    token estiver inválido/expirado (nesse caso o chamador deve
    tratar como "sessão perdida" e voltar para o login).
    """
    client = get_client()
    try:
        client.auth.set_session(access_token, refresh_token)
        return True
    except Exception:
        return False


def _mensagem_amigavel(erro: AuthApiError) -> str:
    """Traduz erros comuns do Supabase Auth em mensagens claras,
    sem expor detalhes técnicos ao usuário final."""
    texto = (erro.message or "").lower()

    if "invalid login credentials" in texto:
        return "E-mail ou senha incorretos."
    if "user already registered" in texto:
        return "Já existe uma conta com este e-mail."
    if "password" in texto and (
        "at least" in texto or "should be" in texto or "characters" in texto
    ):
        return "A senha não atende aos requisitos mínimos do Supabase."
    if "email" in texto and "invalid" in texto:
        return "Informe um e-mail válido."
    if "rate limit" in texto:
        return "Muitas tentativas em pouco tempo. Aguarde um momento e tente novamente."

    return "Não foi possível completar a operação. Verifique os dados e tente novamente."
