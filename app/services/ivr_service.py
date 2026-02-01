"""
IVR (Interactive Voice Response) service using Twilio for the AI-Driven Agri-Civic Intelligence Platform.
"""

import logging
from typing import Dict, Any, Optional
from twilio.rest import Client
from twilio.twiml import VoiceResponse
from twilio.base.exceptions import TwilioException

from app.config import get_settings
from app.core.logging import get_logger
from app.services.translation import TranslationService
from app.services.llm_service import LLMService

settings = get_settings()
logger = get_logger(__name__)


class IVRService:
    """Service for handling IVR operations using Twilio."""

    def __init__(self):
        """Initialize IVR service with Twilio client."""
        self.client = None
        self.translation_service = TranslationService()
        self.llm_service = LLMService()
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Twilio client."""
        try:
            if settings.twilio_account_sid and settings.twilio_auth_token:
                self.client = Client(
                    settings.twilio_account_sid, settings.twilio_auth_token
                )
                logger.info("Twilio IVR client initialized successfully")
            else:
                logger.warning("Twilio credentials not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            raise

    def generate_welcome_response(self, language: str = "hi") -> str:
        """Generate welcome IVR response."""
        response = VoiceResponse()

        # Welcome messages in different languages
        welcome_messages = {
            "hi": "नमस्ते! कृषि सहायता केंद्र में आपका स्वागत है। भाषा चुनने के लिए: हिंदी के लिए 1, अंग्रेजी के लिए 2 दबाएं।",
            "en": "Welcome to the Agricultural Assistance Center. To select language: Press 1 for Hindi, 2 for English.",
            "bn": "নমস্কার! কৃষি সহায়তা কেন্দ্রে আপনাকে স্বাগতম। ভাষা নির্বাচনের জন্য: বাংলার জন্য 3, হিন্দির জন্য 1 চাপুন।",
            "te": "నమస్కారం! వ్যవసాయ సహాయ కేంద్రానికి స్వాগతం। భాష ఎంచుకోవడానికి: తెలుగు కోసం 4, హిందీ కోసం 1 నొక్కండి।",
            "ta": "வணக்கம்! விவசாய உதவி மையத்திற்கு வரவேற்கிறோம்। மொழி தேர்வுக்கு: தமிழுக்கு 5, ஹிந்திக்கு 1 அழுத்தவும்।",
        }

        # Use Hindi as default
        message = welcome_messages.get(language, welcome_messages["hi"])

        response.say(
            message,
            language=f"{language}-IN" if language != "en" else "en-IN",
            voice="Polly.Aditi" if language == "hi" else "Polly.Raveena",
        )

        # Gather language selection
        gather = response.gather(
            num_digits=1,
            action="/api/v1/ivr/language-selection",
            method="POST",
            timeout=10,
        )

        # Fallback if no input
        response.say("कोई जवाब नहीं मिला। कॉल समाप्त की जा रही है।", language="hi-IN")
        response.hangup()

        return str(response)

    def handle_language_selection(self, digit: str) -> str:
        """Handle language selection from user input."""
        response = VoiceResponse()

        language_map = {
            "1": "hi",  # Hindi
            "2": "en",  # English
            "3": "bn",  # Bengali
            "4": "te",  # Telugu
            "5": "ta",  # Tamil
            "6": "mr",  # Marathi
            "7": "gu",  # Gujarati
            "8": "kn",  # Kannada
            "9": "ml",  # Malayalam
        }

        selected_language = language_map.get(digit, "hi")

        # Store language in session (you'd implement session storage)
        # session.language = selected_language

        return self.generate_main_menu(selected_language)

    def generate_main_menu(self, language: str = "hi") -> str:
        """Generate main menu IVR response."""
        response = VoiceResponse()

        menu_messages = {
            "hi": "मुख्य मेनू: मौसम की जानकारी के लिए 1, फसल की बीमारी के लिए 2, सरकारी योजनाओं के लिए 3, बाजार की कीमतों के लिए 4 दबाएं।",
            "en": "Main Menu: Press 1 for weather information, 2 for crop diseases, 3 for government schemes, 4 for market prices.",
            "bn": "প্রধান মেনু: আবহাওয়ার তথ্যের জন্য 1, ফসলের রোগের জন্য 2, সরকারি প্রকল্পের জন্য 3, বাজার দামের জন্য 4 চাপুন।",
            "te": "ప్రధాన మెనూ: వాతావరణ సమాచారం కోసం 1, పంట వ్యాధుల కోసం 2, ప్రభుత్వ పథకాల కోసం 3, మార్కెట్ ధరల కోసం 4 నొక్కండి।",
            "ta": "முதன்மை மெனு: வானிலை தகவலுக்கு 1, பயிர் நோய்களுக்கு 2, அரசு திட்டங்களுக்கு 3, சந்தை விலைகளுக்கு 4 அழுத்தவும்।",
        }

        message = menu_messages.get(language, menu_messages["hi"])

        response.say(
            message,
            language=f"{language}-IN" if language != "en" else "en-IN",
            voice=self._get_voice_for_language(language),
        )

        # Gather menu selection
        gather = response.gather(
            num_digits=1,
            action=f"/api/v1/ivr/menu-selection?lang={language}",
            method="POST",
            timeout=10,
        )

        # Fallback
        response.redirect(f"/api/v1/ivr/main-menu?lang={language}")

        return str(response)

    def handle_menu_selection(self, digit: str, language: str = "hi") -> str:
        """Handle main menu selection."""
        response = VoiceResponse()

        menu_actions = {
            "1": self._handle_weather_request,
            "2": self._handle_disease_request,
            "3": self._handle_schemes_request,
            "4": self._handle_market_request,
        }

        if digit in menu_actions:
            return menu_actions[digit](language)
        else:
            # Invalid selection
            error_messages = {
                "hi": "गलत विकल्प। कृपया फिर से कोशिश करें।",
                "en": "Invalid option. Please try again.",
                "bn": "ভুল বিকল্প। অনুগ্রহ করে আবার চেষ্টা করুন।",
                "te": "తప్పు ఎంపిక. దయచేసి మళ్లీ ప్రయత్నించండి।",
                "ta": "தவறான விருப்பம். தயவுசெய்து மீண்டும் முயற்சிக்கவும்।",
            }

            message = error_messages.get(language, error_messages["hi"])
            response.say(message, language=f"{language}-IN")
            response.redirect(f"/api/v1/ivr/main-menu?lang={language}")

            return str(response)

    def _handle_weather_request(self, language: str) -> str:
        """Handle weather information request."""
        response = VoiceResponse()

        prompts = {
            "hi": "मौसम की जानकारी के लिए अपना जिला बोलें। बोलना शुरू करने के लिए बीप की आवाज़ का इंतज़ार करें।",
            "en": "For weather information, please speak your district name. Wait for the beep to start speaking.",
            "bn": "আবহাওয়ার তথ্যের জন্য আপনার জেলার নাম বলুন। কথা বলা শুরু করতে বিপের জন্য অপেক্ষা করুন।",
            "te": "వాతావరణ సమాచారం కోసం మీ జిల్లా పేరు చెప్పండి. మాట్లాడటం ప్రారంభించడానికి బీప్ కోసం వేచి ఉండండి।",
            "ta": "வானிலை தகவலுக்கு உங்கள் மாவட்டத்தின் பெயரைச் சொல்லுங்கள். பேசத் தொடங்க பீப்பிற்காகக் காத்திருங்கள்.",
        }

        message = prompts.get(language, prompts["hi"])
        response.say(message, language=f"{language}-IN")

        # Record user input
        response.record(
            action=f"/api/v1/ivr/process-weather?lang={language}",
            method="POST",
            max_length=10,
            transcribe=True,
            transcribe_callback=f"/api/v1/ivr/weather-transcription?lang={language}",
        )

        return str(response)

    def _handle_disease_request(self, language: str) -> str:
        """Handle crop disease request."""
        response = VoiceResponse()

        prompts = {
            "hi": "फसल की बीमारी के बारे में बताने के लिए, अपनी फसल का नाम और समस्या बोलें।",
            "en": "To report crop disease, please speak your crop name and the problem you're facing.",
            "bn": "ফসলের রোগ সম্পর্কে জানাতে, আপনার ফসলের নাম এবং সমস্যা বলুন।",
            "te": "పంట వ్యాధి గురించి తెలియజేయడానికి, మీ పంట పేరు మరియు సమస్యను చెప్పండి।",
            "ta": "பயிர் நோய் பற்றி தெரிவிக்க, உங்கள் பயிரின் பெயரையும் பிரச்சனையையும் சொல்லுங்கள்.",
        }

        message = prompts.get(language, prompts["hi"])
        response.say(message, language=f"{language}-IN")

        response.record(
            action=f"/api/v1/ivr/process-disease?lang={language}",
            method="POST",
            max_length=20,
            transcribe=True,
            transcribe_callback=f"/api/v1/ivr/disease-transcription?lang={language}",
        )

        return str(response)

    def _handle_schemes_request(self, language: str) -> str:
        """Handle government schemes request."""
        response = VoiceResponse()

        prompts = {
            "hi": "सरकारी योजनाओं की जानकारी के लिए अपना राज्य और फसल का प्रकार बोलें।",
            "en": "For government schemes information, please speak your state and crop type.",
            "bn": "সরকারি প্রকল্পের তথ্যের জন্য আপনার রাজ্য এবং ফসলের ধরন বলুন।",
            "te": "ప్రభుత్వ పథకాల సమాచారం కోసం మీ రాష్ట్రం మరియు పంట రకాన్ని చెప్పండి।",
            "ta": "அரசு திட்டங்களின் தகவலுக்கு உங்கள் மாநிலம் மற்றும் பயிர் வகையைச் சொல்லுங்கள்.",
        }

        message = prompts.get(language, prompts["hi"])
        response.say(message, language=f"{language}-IN")

        response.record(
            action=f"/api/v1/ivr/process-schemes?lang={language}",
            method="POST",
            max_length=15,
            transcribe=True,
            transcribe_callback=f"/api/v1/ivr/schemes-transcription?lang={language}",
        )

        return str(response)

    def _handle_market_request(self, language: str) -> str:
        """Handle market prices request."""
        response = VoiceResponse()

        prompts = {
            "hi": "बाजार की कीमतों के लिए अपनी फसल का नाम और मंडी का स्थान बोलें।",
            "en": "For market prices, please speak your crop name and mandi location.",
            "bn": "বাজার দামের জন্য আপনার ফসলের নাম এবং মান্ডির অবস্থান বলুন।",
            "te": "మార్కెట్ ధరల కోసం మీ పంట పేరు మరియు మండి స్థానాన్ని చెప్పండి।",
            "ta": "சந்தை விலைகளுக்கு உங்கள் பயிரின் பெயரையும் மண்டி இடத்தையும் சொல்லுங்கள்.",
        }

        message = prompts.get(language, prompts["hi"])
        response.say(message, language=f"{language}-IN")

        response.record(
            action=f"/api/v1/ivr/process-market?lang={language}",
            method="POST",
            max_length=15,
            transcribe=True,
            transcribe_callback=f"/api/v1/ivr/market-transcription?lang={language}",
        )

        return str(response)

    def process_transcription(
        self, transcription: str, request_type: str, language: str
    ) -> str:
        """Process transcribed user input and generate AI response."""
        try:
            # Translate to English if needed
            if language != "en":
                english_text = self.translation_service.translate(
                    transcription, source_lang=language, target_lang="en"
                )
            else:
                english_text = transcription

            # Get AI response based on request type
            ai_response = self._get_ai_response(english_text, request_type)

            # Translate response back to user's language
            if language != "en":
                localized_response = self.translation_service.translate(
                    ai_response, source_lang="en", target_lang=language
                )
            else:
                localized_response = ai_response

            # Generate TTS response
            return self._generate_tts_response(localized_response, language)

        except Exception as e:
            logger.error(f"Error processing transcription: {e}")
            return self._generate_error_response(language)

    def _get_ai_response(self, query: str, request_type: str) -> str:
        """Get AI response based on query and request type."""
        context_prompts = {
            "weather": "Provide weather information and agricultural advice for: ",
            "disease": "Provide crop disease diagnosis and treatment for: ",
            "schemes": "Provide information about relevant government schemes for: ",
            "market": "Provide market price information and selling advice for: ",
        }

        prompt = context_prompts.get(request_type, "") + query
        return self.llm_service.generate_response(prompt)

    def _generate_tts_response(self, text: str, language: str) -> str:
        """Generate TTS response for the user."""
        response = VoiceResponse()

        # Limit response length for voice
        if len(text) > 500:
            text = text[:500] + "..."

        response.say(
            text,
            language=f"{language}-IN" if language != "en" else "en-IN",
            voice=self._get_voice_for_language(language),
        )

        # Offer to repeat or go back to main menu
        repeat_prompts = {
            "hi": "दोहराने के लिए 1, मुख्य मेनू के लिए 2, कॉल समाप्त करने के लिए 9 दबाएं।",
            "en": "Press 1 to repeat, 2 for main menu, 9 to end call.",
            "bn": "পুনরাবৃত্তির জন্য 1, প্রধান মেনুর জন্য 2, কল শেষ করতে 9 চাপুন।",
            "te": "పునరావృతం చేయడానికి 1, ప్రధాన మెనూ కోసం 2, కాల్ ముగించడానికి 9 నొక్కండి।",
            "ta": "மீண்டும் கேட்க 1, முதன்மை மெனுவிற்கு 2, அழைப்பை முடிக்க 9 அழுத்தவும்.",
        }

        repeat_message = repeat_prompts.get(language, repeat_prompts["hi"])
        response.say(repeat_message, language=f"{language}-IN")

        gather = response.gather(
            num_digits=1,
            action=f"/api/v1/ivr/post-response?lang={language}",
            method="POST",
            timeout=10,
        )

        # Default action
        response.hangup()

        return str(response)

    def _generate_error_response(self, language: str) -> str:
        """Generate error response."""
        response = VoiceResponse()

        error_messages = {
            "hi": "क्षमा करें, कुछ तकनीकी समस्या है। कृपया बाद में कॉल करें।",
            "en": "Sorry, there's a technical issue. Please call back later.",
            "bn": "দুঃখিত, একটি প্রযুক্তিগত সমস্যা আছে। অনুগ্রহ করে পরে কল করুন।",
            "te": "క్షమించండి, సాంకేతిక సమస్య ఉంది. దయచేసి తర్వాత కాల్ చేయండి।",
            "ta": "மன்னிக்கவும், தொழில்நுட்ப சிக்கல் உள்ளது. தயவுசெய்து பின்னர் அழைக்கவும்.",
        }

        message = error_messages.get(language, error_messages["hi"])
        response.say(message, language=f"{language}-IN")
        response.hangup()

        return str(response)

    def _get_voice_for_language(self, language: str) -> str:
        """Get appropriate Twilio voice for language."""
        voice_map = {
            "hi": "Polly.Aditi",
            "en": "Polly.Raveena",
            "bn": "Polly.Aditi",  # Use Hindi voice for Bengali
            "te": "Polly.Aditi",  # Use Hindi voice for Telugu
            "ta": "Polly.Aditi",  # Use Hindi voice for Tamil
            "mr": "Polly.Aditi",  # Use Hindi voice for Marathi
            "gu": "Polly.Aditi",  # Use Hindi voice for Gujarati
            "kn": "Polly.Aditi",  # Use Hindi voice for Kannada
            "ml": "Polly.Aditi",  # Use Hindi voice for Malayalam
        }

        return voice_map.get(language, "Polly.Aditi")

    def make_outbound_call(
        self, to_number: str, message: str, language: str = "hi"
    ) -> Optional[str]:
        """Make an outbound call for notifications."""
        try:
            if not self.client:
                logger.error("Twilio client not initialized")
                return None

            # Create TwiML for the message
            response = VoiceResponse()
            response.say(
                message,
                language=f"{language}-IN" if language != "en" else "en-IN",
                voice=self._get_voice_for_language(language),
            )

            call = self.client.calls.create(
                twiml=str(response), to=to_number, from_=settings.twilio_phone_number
            )

            logger.info(f"Outbound call initiated: {call.sid}")
            return call.sid

        except TwilioException as e:
            logger.error(f"Twilio error making outbound call: {e}")
            return None
        except Exception as e:
            logger.error(f"Error making outbound call: {e}")
            return None


# Global instance
ivr_service = IVRService()
