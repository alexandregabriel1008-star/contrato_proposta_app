import openai
import os
import math
from pydub import AudioSegment

def dividir_audio(caminho_audio, minutos=10):
    audio = AudioSegment.from_file(caminho_audio)
    duracao_ms = minutos * 60 * 1000
    partes = []

    total = math.ceil(len(audio) / duracao_ms)

    for i in range(total):
        inicio = i * duracao_ms
        fim = inicio + duracao_ms
        trecho = audio[inicio:fim]

        nome = f"{caminho_audio}_parte_{i}.wav"
        trecho.export(nome, format="wav")
        partes.append(nome)

    return partes


def transcrever_audio_grande(caminho_audio):
    partes = dividir_audio(caminho_audio)
    texto_final = ""

    for parte in partes:
        with open(parte, "rb") as audio:
            resposta = openai.audio.transcriptions.create(
                file=audio,
                model="gpt-4o-transcribe"
            )
            texto_final += resposta.text + "\n\n"

        os.remove(parte)

    return texto_final
