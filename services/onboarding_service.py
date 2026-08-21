"""
Mody onboarding service.

All reads and writes to `profiles` and
`personalization_preferences` must go through this service.

The UI should never access Supabase tables directly.

All operations use the authenticated Supabase client and respect
Row Level Security (RLS).
"""

from services.supabase_service import get_client


def has_completed_onboarding(user_id: str) -> bool:
    """
    Check whether the user has completed onboarding.

    For the current MVP, onboarding is considered complete when
    the user has a row in the `profiles` table.

    Personalization preferences are optional and therefore are not
    required for onboarding completion.
    """
    client = get_client()

    try:
        response = (
            client.table("profiles")
            .select("user_id")
            .eq("user_id", user_id)
            .execute()
        )

        return len(response.data) > 0

    except Exception:
        return False


def get_existing_data(user_id: str) -> dict:
    """
    Retrieve the user's existing profile and personalization preferences.

    Returns:
        {
            "profile": {...} or None,
            "preferences": {...} or None
        }
    """
    client = get_client()

    profile = None
    preferences = None

    try:
        response = (
            client.table("profiles")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        if response.data:
            profile = response.data[0]

    except Exception:
        pass

    try:
        response = (
            client.table("personalization_preferences")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        if response.data:
            preferences = response.data[0]

    except Exception:
        pass

    return {
        "profile": profile,
        "preferences": preferences,
    }


def save_profile(
    user_id: str,
    display_name: str,
    timezone: str,
) -> dict:
    """
    Create or update the user's basic profile.

    Uses an upsert on `user_id` so running onboarding again updates
    the existing profile instead of creating duplicate records.
    """
    client = get_client()

    payload = {
        "user_id": user_id,
        "display_name": display_name.strip() if display_name else None,
        "timezone": timezone.strip() if timezone else None,
    }

    try:
        (
            client.table("profiles")
            .upsert(
                payload,
                on_conflict="user_id",
            )
            .execute()
        )

        return {
            "success": True
        }

    except Exception:
        return {
            "success": False,
            "error": (
                "Não foi possível salvar seu perfil agora. "
                "Tente novamente."
            ),
        }


def save_preferences(
    user_id: str,
    support_profile: str | None,
    support_needs: list[str] | None,
) -> dict:
    """
    Create or update the user's personalization preferences.

    `support_profile` may contain:

    - adhd
    - anxiety
    - adhd_anxiety
    - none
    - prefer_not_to_say
    - None

    `support_needs` may contain a list of valid support categories
    or None when the user does not select any option.

    Uses an upsert on `user_id` to prevent duplicate records.
    """
    client = get_client()

    payload = {
        "user_id": user_id,
        "support_profile": support_profile,
        "support_needs": support_needs if support_needs else None,
    }

    try:
        (
            client.table("personalization_preferences")
            .upsert(
                payload,
                on_conflict="user_id",
            )
            .execute()
        )

        return {
            "success": True
        }

    except Exception:
        return {
            "success": False,
            "error": (
                "Não foi possível salvar suas preferências agora. "
                "Tente novamente."
            ),
        }