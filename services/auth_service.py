from supabase_auth.errors import AuthApiError

from services.supabase_service import get_client


def sign_up(email: str, password: str) -> dict:
    """
    Cria uma conta nova com e-mail e senha.
    """
    client = get_client()

    try:
        response = client.auth.sign_up(
            {
                "email": email,
                "password": password,
            }
        )

    except AuthApiError as e:
        return {
            "success": False,
            "error": _mensagem_amigavel(e),
        }

    except Exception:
        return {
            "success": False,
            "error": (
                "Não foi possível criar a conta agora. "
                "Tente novamente em instantes."
            ),
        }

    if response.session is None:
        return {
            "success": True,
            "needs_confirmation": True,
        }

    return {
        "success": True,
        "needs_confirmation": False,
        "session": response.session,
        "user": response.user,
    }


def sign_in(email: str, password: str) -> dict:
    """
    Autentica um usuário existente com e-mail e senha.
    """
    client = get_client()

    try:
        response = client.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )

    except AuthApiError as e:
        return {
            "success": False,
            "error": _mensagem_amigavel(e),
        }

    except Exception:
        return {
            "success": False,
            "error": (
                "Não foi possível entrar agora. "
                "Tente novamente em instantes."
            ),
        }

    if response.session is None or response.user is None:
        return {
            "success": False,
            "error": "Não foi possível iniciar a sessão.",
        }

    return {
        "success": True,
        "session": response.session,
        "user": response.user,
    }


def request_password_reset(email: str, redirect_url: str) -> dict:
    """
    Solicita ao Supabase o envio de um e-mail de recuperação de senha.

    A mensagem retornada é neutra para evitar revelar
    se determinado e-mail possui ou não uma conta.
    """
    client = get_client()

    try:
        client.auth.reset_password_for_email(
            email,
            {
                "redirect_to": redirect_url,
            },
        )

        return {
            "success": True,
            "message": (
                "Se existir uma conta associada a este e-mail, "
                "você receberá instruções para redefinir sua senha."
            ),
        }

    except AuthApiError:
        return {
            "success": True,
            "message": (
                "Se existir uma conta associada a este e-mail, "
                "você receberá instruções para redefinir sua senha."
            ),
        }

    except Exception:
        return {
            "success": False,
            "error": (
                "Não foi possível solicitar a recuperação agora. "
                "Tente novamente em instantes."
            ),
        }


def verify_recovery_otp(email: str, token: str) -> dict:
    """
    Valida o código OTP de recuperação recebido por e-mail.

    Quando o código é válido, o Supabase cria uma sessão
    autenticada temporária que será usada para alterar a senha.
    """
    client = get_client()

    try:
        response = client.auth.verify_otp(
            {
                "email": email,
                "token": token,
                "type": "recovery",
            }
        )

        if response.session is None or response.user is None:
            return {
                "success": False,
                "error": (
                    "O código de recuperação não é válido ou expirou."
                ),
            }

        return {
            "success": True,
            "session": response.session,
            "user": response.user,
        }

    except AuthApiError:
        return {
            "success": False,
            "error": (
                "O código de recuperação não é válido ou expirou."
            ),
        }

    except Exception:
        return {
            "success": False,
            "error": (
                "Não foi possível validar o código de recuperação. "
                "Solicite um novo código e tente novamente."
            ),
        }


def update_password(new_password: str) -> dict:
    """
    Atualiza a senha do usuário autenticado.

    No fluxo de recuperação, esta função é chamada depois
    da validação do código OTP.
    """
    client = get_client()

    try:
        response = client.auth.update_user(
            {
                "password": new_password,
            }
        )

        if response.user is None:
            return {
                "success": False,
                "error": "Não foi possível atualizar a senha.",
            }

        return {
            "success": True,
            "message": "Senha atualizada com sucesso.",
        }

    except AuthApiError as e:
        return {
            "success": False,
            "error": _mensagem_amigavel(e),
        }

    except Exception:
        return {
            "success": False,
            "error": (
                "Não foi possível atualizar a senha agora. "
                "Tente novamente em instantes."
            ),
        }


def delete_account() -> dict:
    """
    Exclui permanentemente a conta do usuário autenticado.

    A exclusão é feita pela função RPC `delete_my_account`
    criada no Supabase.

    A função no banco usa auth.uid(), portanto o usuário
    só consegue excluir a própria conta.

    Os registros relacionados nas tabelas públicas são
    removidos automaticamente pelas foreign keys configuradas
    com ON DELETE CASCADE.
    """
    client = get_client()

    try:
        client.rpc("delete_my_account").execute()

        return {
            "success": True,
            "message": "Conta excluída com sucesso.",
        }

    except Exception:
        return {
            "success": False,
            "error": (
                "Não foi possível excluir sua conta agora. "
                "Tente novamente em instantes."
            ),
        }


def sign_out() -> None:
    """
    Encerra a sessão no Supabase.

    Falhas aqui não impedem o logout local,
    pois o app também limpa o session_state.
    """
    client = get_client()

    try:
        client.auth.sign_out()

    except Exception:
        pass


def restore_session(
    access_token: str,
    refresh_token: str,
) -> bool:
    """
    Restaura a sessão Supabase armazenada no session_state.
    """
    client = get_client()

    try:
        client.auth.set_session(
            access_token,
            refresh_token,
        )

        return True

    except Exception:
        return False


def _mensagem_amigavel(erro: AuthApiError) -> str:
    """
    Traduz erros comuns do Supabase Auth em mensagens claras,
    sem expor detalhes técnicos ao usuário final.
    """
    texto = (erro.message or "").lower()

    if "invalid login credentials" in texto:
        return "E-mail ou senha incorretos."

    if "user already registered" in texto:
        return "Já existe uma conta com este e-mail."

    if "password" in texto and (
        "at least" in texto
        or "should be" in texto
        or "characters" in texto
    ):
        return (
            "A senha não atende aos requisitos mínimos do Supabase."
        )

    if "email" in texto and "invalid" in texto:
        return "Informe um e-mail válido."

    if "rate limit" in texto:
        return (
            "Muitas tentativas em pouco tempo. "
            "Aguarde um momento e tente novamente."
        )

    return (
        "Não foi possível completar a operação. "
        "Verifique os dados e tente novamente."
    )