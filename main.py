import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Start, Stream, Pause
from dotenv import load_dotenv
import openai
import datetime

# Cargar variables
load_dotenv()
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TARGET_PHONE = os.getenv("TARGET_PHONE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client_twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
openai.api_key = OPENAI_API_KEY

app = FastAPI()


@app.post("/call/start")
def start_call():
    call = client_twilio.calls.create(
        to=TARGET_PHONE,
        from_=TWILIO_PHONE_NUMBER,
        url="https://<tu-dominio>.railway.app/call/handler"  # <- cambiar al final
    )
    return {"message": "Llamada iniciada", "sid": call.sid}


@app.post("/call/handler")
def call_handler():
    response = VoiceResponse()

    # Activa transcripción vía Twilio <Stream>
    start = Start()
    start.stream(url="wss://handler.yourdomain.com/audio-stream")
    response.append(start)

    response.say("Hola, soy Andrés de Tony Superpapelerías. ¿En qué puedo ayudarte?", voice="man", language="es-MX")
    response.pause(length=10)
    response.say("No escuché ninguna respuesta. Terminando la llamada.", voice="man", language="es-MX")

    return PlainTextResponse(str(response), media_type="application/xml")


@app.post("/call/process")
async def call_process(request: Request):
    body = await request.body()
    transcription = "Texto transcrito..."  # aquí va whisper

    # Procesamiento con GPT
    gpt_response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Actúa como un vendedor profesional y empático."},
            {"role": "user", "content": transcription}
        ]
    )
    response_text = gpt_response.choices[0].message.content

    # Texto a voz con tts-1
    audio_response = openai.audio.speech.create(
        model="tts-1",
        voice="onyx",  # o alloy / echo / nova
        input=response_text
    )
    audio_path = "static/response.mp3"
    with open(audio_path, "wb") as f:
        f.write(await audio_response.read())

    # Respuesta de audio
    response = VoiceResponse()
    response.play(f"https://<tu-dominio>.railway.app/static/response.mp3")
    return PlainTextResponse(str(response), media_type="application/xml")
