"""Tests for services/appointment_service.py.

Mocks services.appointment_service.get_client for every test that would
otherwise hit Supabase, so this suite never depends on external state
or credentials. Validation-only tests (blank title, missing required
fields) don't need a client at all, since the service returns before
ever calling it.
"""

import datetime
from unittest.mock import MagicMock, patch

from services import appointment_service


def _mock_response(data):
    """Builds a stand-in for the object returned by .execute(), which
    the real Supabase/PostgREST client exposes as response.data."""
    response = MagicMock()
    response.data = data
    return response


def _mock_select_chain(mock_client, rows):
    """Wires up client.table(...).select(...).eq(...).order(...).order(...).execute()
    to return `rows`, matching the chain used by get_appointments()."""
    (
        mock_client.table.return_value.select.return_value.eq.return_value
        .order.return_value.order.return_value.execute.return_value
    ) = _mock_response(rows)


class TestCreateAppointmentValidation:
    def test_title_cannot_be_blank(self):
        result = appointment_service.create_appointment(
            user_id="user-1",
            title="   ",
            event_date=datetime.date(2026, 9, 1),
            event_time=datetime.time(10, 0),
        )
        assert result["success"] is False
        assert "Título" in result["error"]

    def test_user_id_is_required(self):
        result = appointment_service.create_appointment(
            user_id=None,
            title="Consulta",
            event_date=datetime.date(2026, 9, 1),
            event_time=datetime.time(10, 0),
        )
        assert result["success"] is False
        assert result["data"] is None

    def test_event_date_is_required(self):
        result = appointment_service.create_appointment(
            user_id="user-1",
            title="Consulta",
            event_date=None,
            event_time=datetime.time(10, 0),
        )
        assert result["success"] is False
        assert "Data" in result["error"]

    def test_event_time_is_required(self):
        result = appointment_service.create_appointment(
            user_id="user-1",
            title="Consulta",
            event_date=datetime.date(2026, 9, 1),
            event_time=None,
        )
        assert result["success"] is False
        assert "Hora" in result["error"]


class TestCreateAppointmentSuccess:
    @patch("services.appointment_service.get_client")
    def test_successful_create_returns_expected_structure(self, mock_get_client):
        inserted_row = {
            "id": "appt-1",
            "user_id": "user-1",
            "title": "Consulta",
            "event_date": "2026-09-01",
            "event_time": "10:00:00",
            "notes": None,
            "created_at": "2026-08-29T00:00:00Z",
        }
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value = _mock_response(
            [inserted_row]
        )
        mock_get_client.return_value = mock_client

        result = appointment_service.create_appointment(
            user_id="user-1",
            title="  Consulta  ",
            event_date=datetime.date(2026, 9, 1),
            event_time=datetime.time(10, 0),
        )

        assert result == {"success": True, "data": inserted_row, "error": None}

    @patch("services.appointment_service.get_client")
    def test_title_and_notes_are_trimmed_before_saving(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value = _mock_response(
            [{"id": "appt-1"}]
        )
        mock_get_client.return_value = mock_client

        appointment_service.create_appointment(
            user_id="user-1",
            title="  Consulta  ",
            event_date=datetime.date(2026, 9, 1),
            event_time=datetime.time(10, 0),
            notes="  Levar documentos  ",
        )

        payload = mock_client.table.return_value.insert.call_args[0][0]
        assert payload["title"] == "Consulta"
        assert payload["notes"] == "Levar documentos"
        assert payload["user_id"] == "user-1"

    @patch("services.appointment_service.get_client")
    def test_database_error_is_normalized(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.side_effect = Exception(
            "raw supabase failure"
        )
        mock_get_client.return_value = mock_client

        result = appointment_service.create_appointment(
            user_id="user-1",
            title="Consulta",
            event_date=datetime.date(2026, 9, 1),
            event_time=datetime.time(10, 0),
        )

        assert result["success"] is False
        assert "raw supabase failure" not in result["error"]


class TestGetAppointments:
    @patch("services.appointment_service.get_client")
    def test_appointments_returned_in_chronological_order(self, mock_get_client):
        rows = [
            {
                "id": "1",
                "user_id": "user-1",
                "title": "A",
                "event_date": "2026-09-01",
                "event_time": "09:00:00",
                "notes": None,
            },
            {
                "id": "2",
                "user_id": "user-1",
                "title": "B",
                "event_date": "2026-09-02",
                "event_time": "10:00:00",
                "notes": None,
            },
        ]
        mock_client = MagicMock()
        _mock_select_chain(mock_client, rows)
        mock_get_client.return_value = mock_client

        result = appointment_service.get_appointments("user-1", upcoming_only=False)

        assert result["success"] is True
        assert [a["id"] for a in result["data"]] == ["1", "2"]
        mock_client.table.return_value.select.return_value.eq.return_value.order.assert_called_with(
            "event_date", desc=False
        )

    @patch("services.appointment_service.get_client")
    def test_upcoming_only_filters_out_past_appointments(self, mock_get_client):
        past_date = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        future_date = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        rows = [
            {"id": "past", "user_id": "user-1", "title": "Past", "event_date": past_date, "event_time": "09:00:00", "notes": None},
            {"id": "future", "user_id": "user-1", "title": "Future", "event_date": future_date, "event_time": "09:00:00", "notes": None},
        ]
        mock_client = MagicMock()
        _mock_select_chain(mock_client, rows)
        mock_get_client.return_value = mock_client

        result = appointment_service.get_appointments("user-1", upcoming_only=True)

        assert result["success"] is True
        assert [a["id"] for a in result["data"]] == ["future"]

    @patch("services.appointment_service.get_client")
    def test_database_error_is_normalized(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.order.return_value.execute.side_effect = Exception(
            "raw supabase failure"
        )
        mock_get_client.return_value = mock_client

        result = appointment_service.get_appointments("user-1")

        assert result["success"] is False
        assert "raw supabase failure" not in result["error"]

    def test_user_id_is_required(self):
        result = appointment_service.get_appointments(None)
        assert result["success"] is False


class TestGetNextAppointment:
    @patch("services.appointment_service.get_client")
    def test_returns_earliest_upcoming_appointment(self, mock_get_client):
        earlier = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
        later = (datetime.date.today() + datetime.timedelta(days=10)).isoformat()
        rows = [
            {"id": "earlier", "user_id": "user-1", "title": "Earlier", "event_date": earlier, "event_time": "09:00:00", "notes": None},
            {"id": "later", "user_id": "user-1", "title": "Later", "event_date": later, "event_time": "09:00:00", "notes": None},
        ]
        mock_client = MagicMock()
        _mock_select_chain(mock_client, rows)
        mock_get_client.return_value = mock_client

        result = appointment_service.get_next_appointment("user-1")

        assert result["success"] is True
        assert result["data"]["id"] == "earlier"

    @patch("services.appointment_service.get_client")
    def test_returns_none_when_no_upcoming_appointments(self, mock_get_client):
        past_date = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        rows = [
            {"id": "past", "user_id": "user-1", "title": "Past", "event_date": past_date, "event_time": "09:00:00", "notes": None},
        ]
        mock_client = MagicMock()
        _mock_select_chain(mock_client, rows)
        mock_get_client.return_value = mock_client

        result = appointment_service.get_next_appointment("user-1")

        assert result["success"] is True
        assert result["data"] is None

    @patch("services.appointment_service.get_client")
    def test_returns_none_when_there_are_no_appointments_at_all(self, mock_get_client):
        mock_client = MagicMock()
        _mock_select_chain(mock_client, [])
        mock_get_client.return_value = mock_client

        result = appointment_service.get_next_appointment("user-1")

        assert result["success"] is True
        assert result["data"] is None


class TestDeleteAppointment:
    def test_delete_requires_appointment_id(self):
        result = appointment_service.delete_appointment(user_id="user-1", appointment_id=None)
        assert result["success"] is False
        assert "obrigatório" in result["error"]

    def test_delete_requires_user_id(self):
        result = appointment_service.delete_appointment(user_id=None, appointment_id="appt-1")
        assert result["success"] is False

    @patch("services.appointment_service.get_client")
    def test_delete_uses_both_user_id_and_appointment_id(self, mock_get_client):
        mock_client = MagicMock()
        mock_delete = mock_client.table.return_value.delete.return_value
        mock_eq_id = mock_delete.eq.return_value
        mock_eq_id.eq.return_value.execute.return_value = _mock_response([{"id": "appt-1"}])
        mock_get_client.return_value = mock_client

        result = appointment_service.delete_appointment(user_id="user-1", appointment_id="appt-1")

        assert result["success"] is True
        mock_delete.eq.assert_called_once_with("id", "appt-1")
        mock_eq_id.eq.assert_called_once_with("user_id", "user-1")

    @patch("services.appointment_service.get_client")
    def test_database_error_is_normalized(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception(
            "raw supabase failure"
        )
        mock_get_client.return_value = mock_client

        result = appointment_service.delete_appointment(user_id="user-1", appointment_id="appt-1")

        assert result["success"] is False
        assert "raw supabase failure" not in result["error"]


class TestResultShape:
    def test_validation_error_has_standard_result_shape(self):
        result = appointment_service.create_appointment(
            user_id=None,
            title="Consulta",
            event_date=datetime.date.today(),
            event_time=datetime.time(9, 0),
        )
        assert set(result.keys()) == {"success", "data", "error"}

    @patch("services.appointment_service.get_client")
    def test_get_appointments_result_has_standard_shape(self, mock_get_client):
        mock_client = MagicMock()
        _mock_select_chain(mock_client, [])
        mock_get_client.return_value = mock_client

        result = appointment_service.get_appointments("user-1")
        assert set(result.keys()) == {"success", "data", "error"}