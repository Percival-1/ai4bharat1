"""
IVR API endpoints for the AI-Driven Agri-Civic Intelligence Platform.
"""

from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import Response
from typing import Optional
import logging

from app.services.ivr_service import ivr_service
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/welcome")
async def ivr_welcome(request: Request):
    """Handle incoming IVR calls with welcome message."""
    try:
        # Get caller information
        caller_number = request.form.get("From", "")
        call_sid = request.form.get("CallSid", "")

        logger.info(f"Incoming IVR call from {caller_number}, CallSid: {call_sid}")

        # Generate welcome response
        twiml_response = ivr_service.generate_welcome_response()

        return Response(content=twiml_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error in IVR welcome: {e}")
        # Return error response
        error_response = ivr_service._generate_error_response("hi")
        return Response(content=error_response, media_type="application/xml")


@router.post("/language-selection")
async def handle_language_selection(request: Request, Digits: str = Form(...)):
    """Handle language selection from user."""
    try:
        call_sid = request.form.get("CallSid", "")
        logger.info(f"Language selection: {Digits} for call {call_sid}")

        twiml_response = ivr_service.handle_language_selection(Digits)

        return Response(content=twiml_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error in language selection: {e}")
        error_response = ivr_service._generate_error_response("hi")
        return Response(content=error_response, media_type="application/xml")


@router.post("/main-menu")
async def main_menu(request: Request, lang: str = Query(default="hi")):
    """Display main menu options."""
    try:
        call_sid = request.form.get("CallSid", "")
        logger.info(f"Main menu requested for call {call_sid}, language: {lang}")

        twiml_response = ivr_service.generate_main_menu(lang)

        return Response(content=twiml_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error in main menu: {e}")
        error_response = ivr_service._generate_error_response(lang)
        return Response(content=error_response, media_type="application/xml")


@router.post("/menu-selection")
async def handle_menu_selection(
    request: Request, Digits: str = Form(...), lang: str = Query(default="hi")
):
    """Handle main menu selection."""
    try:
        call_sid = request.form.get("CallSid", "")
        logger.info(f"Menu selection: {Digits} for call {call_sid}, language: {lang}")

        twiml_response = ivr_service.handle_menu_selection(Digits, lang)

        return Response(content=twiml_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error in menu selection: {e}")
        error_response = ivr_service._generate_error_response(lang)
        return Response(content=error_response, media_type="application/xml")


@router.post("/process-weather")
async def process_weather_request(
    request: Request,
    lang: str = Query(default="hi"),
    RecordingUrl: Optional[str] = Form(None),
    TranscriptionText: Optional[str] = Form(None),
):
    """Process weather information request."""
    try:
        call_sid = request.form.get("CallSid", "")
        logger.info(f"Processing weather request for call {call_sid}")

        if TranscriptionText:
            logger.info(f"Weather transcription: {TranscriptionText}")
            twiml_response = ivr_service.process_transcription(
                TranscriptionText, "weather", lang
            )
        else:
            # Fallback if transcription not available
            twiml_response = ivr_service._generate_error_response(lang)

        return Response(content=twiml_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error processing weather request: {e}")
        error_response = ivr_service._generate_error_response(lang)
        return Response(content=error_response, media_type="application/xml")


@router.post("/weather-transcription")
async def weather_transcription_callback(
    request: Request,
    lang: str = Query(default="hi"),
    TranscriptionText: str = Form(...),
    TranscriptionStatus: str = Form(...),
):
    """Handle weather transcription callback."""
    try:
        call_sid = request.form.get("CallSid", "")
        logger.info(
            f"Weather transcription callback for call {call_sid}: {TranscriptionText}"
        )

        if TranscriptionStatus == "completed":
            twiml_response = ivr_service.process_transcription(
                TranscriptionText, "weather", lang
            )
        else:
            twiml_response = ivr_service._generate_error_response(lang)

        return Response(content=twiml_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error in weather transcription callback: {e}")
        error_response = ivr_service._generate_error_response(lang)
        return Response(content=error_response, media_type="application/xml")


@router.post("/process-disease")
async def process_disease_request(
    request: Request,
    lang: str = Query(default="hi"),
    RecordingUrl: Optional[str] = Form(None),
    TranscriptionText: Optional[str] = Form(None),
):
    """Process crop disease request."""
    try:
        call_sid = request.form.get("CallSid", "")
        logger.info(f"Processing disease request for call {call_sid}")

        if TranscriptionText:
            logger.info(f"Disease transcription: {TranscriptionText}")
            twiml_response = ivr_service.process_transcription(
                TranscriptionText, "disease", lang
            )
        else:
            twiml_response = ivr_service._generate_error_response(lang)

        return Response(content=twiml_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error processing disease request: {e}")
        error_response = ivr_service._generate_error_response(lang)
        return Response(content=error_response, media_type="application/xml")


@router.post("/disease-transcription")
async def disease_transcription_callback(
    request: Request,
    lang: str = Query(default="hi"),
    TranscriptionText: str = Form(...),
    TranscriptionStatus: str = Form(...),
):
    """Handle disease transcription callback."""
    try:
        call_sid = request.form.get("CallSid", "")
        logger.info(
            f"Disease transcription callback for call {call_sid}: {TranscriptionText}"
        )

        if TranscriptionStatus == "completed":
            twiml_response = ivr_service.process_transcription(
                TranscriptionText, "disease", lang
            )
        else:
            twiml_response = ivr_service._generate_error_response(lang)

        return Response(content=twiml_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error in disease transcription callback: {e}")
        error_response = ivr_service._generate_error_response(lang)
        return Response(content=error_response, media_type="application/xml")


@router.post("/process-schemes")
async def process_schemes_request(
    request: Request,
    lang: str = Query(default="hi"),
    RecordingUrl: Optional[str] = Form(None),
    TranscriptionText: Optional[str] = Form(None),
):
    """Process government schemes request."""
    try:
        call_sid = request.form.get("CallSid", "")
        logger.info(f"Processing schemes request for call {call_sid}")

        if TranscriptionText:
            logger.info(f"Schemes transcription: {TranscriptionText}")
            twiml_response = ivr_service.process_transcription(
                TranscriptionText, "schemes", lang
            )
        else:
            twiml_response = ivr_service._generate_error_response(lang)

        return Response(content=twiml_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error processing schemes request: {e}")
        error_response = ivr_service._generate_error_response(lang)
        return Response(content=error_response, media_type="application/xml")


@router.post("/schemes-transcription")
async def schemes_transcription_callback(
    request: Request,
    lang: str = Query(default="hi"),
    TranscriptionText: str = Form(...),
    TranscriptionStatus: str = Form(...),
):
    """Handle schemes transcription callback."""
    try:
        call_sid = request.form.get("CallSid", "")
        logger.info(
            f"Schemes transcription callback for call {call_sid}: {TranscriptionText}"
        )

        if TranscriptionStatus == "completed":
            twiml_response = ivr_service.process_transcription(
                TranscriptionText, "schemes", lang
            )
        else:
            twiml_response = ivr_service._generate_error_response(lang)

        return Response(content=twiml_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error in schemes transcription callback: {e}")
        error_response = ivr_service._generate_error_response(lang)
        return Response(content=error_response, media_type="application/xml")


@router.post("/process-market")
async def process_market_request(
    request: Request,
    lang: str = Query(default="hi"),
    RecordingUrl: Optional[str] = Form(None),
    TranscriptionText: Optional[str] = Form(None),
):
    """Process market prices request."""
    try:
        call_sid = request.form.get("CallSid", "")
        logger.info(f"Processing market request for call {call_sid}")

        if TranscriptionText:
            logger.info(f"Market transcription: {TranscriptionText}")
            twiml_response = ivr_service.process_transcription(
                TranscriptionText, "market", lang
            )
        else:
            twiml_response = ivr_service._generate_error_response(lang)

        return Response(content=twiml_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error processing market request: {e}")
        error_response = ivr_service._generate_error_response(lang)
        return Response(content=error_response, media_type="application/xml")


@router.post("/market-transcription")
async def market_transcription_callback(
    request: Request,
    lang: str = Query(default="hi"),
    TranscriptionText: str = Form(...),
    TranscriptionStatus: str = Form(...),
):
    """Handle market transcription callback."""
    try:
        call_sid = request.form.get("CallSid", "")
        logger.info(
            f"Market transcription callback for call {call_sid}: {TranscriptionText}"
        )

        if TranscriptionStatus == "completed":
            twiml_response = ivr_service.process_transcription(
                TranscriptionText, "market", lang
            )
        else:
            twiml_response = ivr_service._generate_error_response(lang)

        return Response(content=twiml_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error in market transcription callback: {e}")
        error_response = ivr_service._generate_error_response(lang)
        return Response(content=error_response, media_type="application/xml")


@router.post("/post-response")
async def handle_post_response(
    request: Request, Digits: str = Form(...), lang: str = Query(default="hi")
):
    """Handle user action after receiving AI response."""
    try:
        call_sid = request.form.get("CallSid", "")
        logger.info(f"Post-response action: {Digits} for call {call_sid}")

        if Digits == "1":
            # Repeat last response (would need session storage)
            twiml_response = ivr_service.generate_main_menu(lang)
        elif Digits == "2":
            # Go to main menu
            twiml_response = ivr_service.generate_main_menu(lang)
        elif Digits == "9":
            # End call
            from twilio.twiml import VoiceResponse

            response = VoiceResponse()
            goodbye_messages = {
                "hi": "धन्यवाद! कृषि सहायता केंद्र से संपर्क करने के लिए धन्यवाद।",
                "en": "Thank you for contacting Agricultural Assistance Center.",
                "bn": "কৃষি সহায়তা কেন্দ্রে যোগাযোগের জন্য ধন্যবাদ।",
                "te": "వ్యవసాయ సహాయ కేంద్రాన్ని సంప్రదించినందుకు ధన్యవాదాలు।",
                "ta": "விவசாய உதவி மையத்தைத் தொடர்பு கொண்டதற்கு நன்றி।",
            }
            message = goodbye_messages.get(lang, goodbye_messages["hi"])
            response.say(message, language=f"{lang}-IN")
            response.hangup()
            twiml_response = str(response)
        else:
            # Invalid option, go to main menu
            twiml_response = ivr_service.generate_main_menu(lang)

        return Response(content=twiml_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error in post-response handling: {e}")
        error_response = ivr_service._generate_error_response(lang)
        return Response(content=error_response, media_type="application/xml")


@router.get("/status")
async def ivr_status():
    """Get IVR service status."""
    try:
        status = {
            "service": "IVR",
            "status": "healthy" if ivr_service.client else "unhealthy",
            "twilio_configured": bool(ivr_service.client),
            "supported_languages": [
                "hi",
                "en",
                "bn",
                "te",
                "ta",
                "mr",
                "gu",
                "kn",
                "ml",
            ],
        }
        return status
    except Exception as e:
        logger.error(f"Error getting IVR status: {e}")
        return {"service": "IVR", "status": "error", "error": str(e)}
