"""
Tests for IVR service and endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.services.ivr_service import IVRService

client = TestClient(app)


@pytest.fixture
def mock_ivr_service():
    """Create a mock IVR service for testing."""
    with patch("app.services.ivr_service.ivr_service") as mock_service:
        mock_service.client = Mock()
        mock_service.generate_welcome_response.return_value = '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Welcome</Say></Response>'
        mock_service.handle_language_selection.return_value = '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Language selected</Say></Response>'
        mock_service.generate_main_menu.return_value = '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Main menu</Say></Response>'
        mock_service.handle_menu_selection.return_value = '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Menu selected</Say></Response>'
        mock_service.process_transcription.return_value = '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Response</Say></Response>'
        mock_service._generate_error_response.return_value = '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Error</Say></Response>'
        yield mock_service


def test_ivr_welcome_endpoint(mock_ivr_service):
    """Test IVR welcome endpoint."""
    response = client.post(
        "/api/v1/ivr/welcome",
        data={"From": "+919876543210", "CallSid": "test_call_sid"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml; charset=utf-8"
    assert "Welcome" in response.text
    mock_ivr_service.generate_welcome_response.assert_called_once()


def test_language_selection_endpoint(mock_ivr_service):
    """Test language selection endpoint."""
    response = client.post(
        "/api/v1/ivr/language-selection",
        data={"Digits": "1", "CallSid": "test_call_sid"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml; charset=utf-8"
    mock_ivr_service.handle_language_selection.assert_called_once_with("1")


def test_main_menu_endpoint(mock_ivr_service):
    """Test main menu endpoint."""
    response = client.post(
        "/api/v1/ivr/main-menu?lang=hi", data={"CallSid": "test_call_sid"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml; charset=utf-8"
    mock_ivr_service.generate_main_menu.assert_called_once_with("hi")


def test_menu_selection_endpoint(mock_ivr_service):
    """Test menu selection endpoint."""
    response = client.post(
        "/api/v1/ivr/menu-selection?lang=hi",
        data={"Digits": "1", "CallSid": "test_call_sid"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml; charset=utf-8"
    mock_ivr_service.handle_menu_selection.assert_called_once_with("1", "hi")


def test_weather_transcription_endpoint(mock_ivr_service):
    """Test weather transcription callback endpoint."""
    response = client.post(
        "/api/v1/ivr/weather-transcription?lang=hi",
        data={
            "TranscriptionText": "Delhi weather",
            "TranscriptionStatus": "completed",
            "CallSid": "test_call_sid",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml; charset=utf-8"
    mock_ivr_service.process_transcription.assert_called_once_with(
        "Delhi weather", "weather", "hi"
    )


def test_ivr_status_endpoint():
    """Test IVR status endpoint."""
    response = client.get("/api/v1/ivr/status")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "IVR"
    assert "status" in data
    assert "supported_languages" in data


def test_ivr_service_initialization():
    """Test IVR service initialization."""
    with patch("app.services.ivr_service.settings") as mock_settings:
        mock_settings.twilio_account_sid = "test_sid"
        mock_settings.twilio_auth_token = "test_token"

        with patch("twilio.rest.Client") as mock_client:
            service = IVRService()
            assert service.client is not None
            mock_client.assert_called_once_with("test_sid", "test_token")


def test_generate_welcome_response():
    """Test welcome response generation."""
    service = IVRService()
    service.client = Mock()  # Mock the client

    response = service.generate_welcome_response("hi")

    assert "<?xml" in response
    assert "Response" in response
    assert "Say" in response


def test_handle_language_selection():
    """Test language selection handling."""
    service = IVRService()
    service.client = Mock()

    with patch.object(service, "generate_main_menu") as mock_menu:
        mock_menu.return_value = "menu_response"

        response = service.handle_language_selection("1")

        assert response == "menu_response"
        mock_menu.assert_called_once_with("hi")


def test_get_voice_for_language():
    """Test voice selection for different languages."""
    service = IVRService()

    assert service._get_voice_for_language("hi") == "Polly.Aditi"
    assert service._get_voice_for_language("en") == "Polly.Raveena"
    assert service._get_voice_for_language("bn") == "Polly.Aditi"
    assert service._get_voice_for_language("unknown") == "Polly.Aditi"


def test_make_outbound_call():
    """Test making outbound calls."""
    service = IVRService()
    mock_client = Mock()
    mock_call = Mock()
    mock_call.sid = "test_call_sid"
    mock_client.calls.create.return_value = mock_call
    service.client = mock_client

    with patch("app.services.ivr_service.settings") as mock_settings:
        mock_settings.twilio_phone_number = "+919876543210"

        call_sid = service.make_outbound_call("+919876543211", "Test message", "hi")

        assert call_sid == "test_call_sid"
        mock_client.calls.create.assert_called_once()


def test_error_handling_in_endpoints(mock_ivr_service):
    """Test error handling in IVR endpoints."""
    # Make the mock service raise an exception
    mock_ivr_service.generate_welcome_response.side_effect = Exception("Test error")

    response = client.post(
        "/api/v1/ivr/welcome",
        data={"From": "+919876543210", "CallSid": "test_call_sid"},
    )

    assert response.status_code == 200  # Should still return 200 with error TwiML
    assert "Error" in response.text
    mock_ivr_service._generate_error_response.assert_called_once()


def test_post_response_handling(mock_ivr_service):
    """Test post-response handling."""
    # Test repeat option
    response = client.post(
        "/api/v1/ivr/post-response?lang=hi",
        data={"Digits": "1", "CallSid": "test_call_sid"},
    )

    assert response.status_code == 200
    mock_ivr_service.generate_main_menu.assert_called_with("hi")

    # Test main menu option
    response = client.post(
        "/api/v1/ivr/post-response?lang=hi",
        data={"Digits": "2", "CallSid": "test_call_sid"},
    )

    assert response.status_code == 200

    # Test end call option
    response = client.post(
        "/api/v1/ivr/post-response?lang=hi",
        data={"Digits": "9", "CallSid": "test_call_sid"},
    )

    assert response.status_code == 200
    assert "धन्यवाद" in response.text or "Thank you" in response.text
