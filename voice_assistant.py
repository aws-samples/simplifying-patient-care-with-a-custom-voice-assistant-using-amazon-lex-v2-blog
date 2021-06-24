# SPDX-FileCopyrightText: Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# SPDX-License-Identifier: MIT-0

from sys import byteorder
from array import array
import base64
import os
import pyaudio
import pocketsphinx as ps
import boto3
import uuid
import zlib
import json
from pocketsphinx.pocketsphinx import *

#Change to reflect the bot and alias you created
bot_id = '##CHANGE##'
bot_alias_id='##CHANGE##'

#Change the KEY_PHRASE and DICT path if you have trained your own custom wake word.
KEY_PHRASE = "HEY PATIENT HEALTH BOT" 
DICT = "pocketsphinx-model/default-model/default.dic"

MODELDIR = "pocketsphinx-model/pocketsphinx"

THRESHOLD = 500
CHUNK_SIZE = 2048
FORMAT = pyaudio.paInt16
RATE = 16000
VOICE_ID = None

polly = boto3.client('polly')
lexv2 = boto3.client('lexv2-runtime')

def is_silent(data):
    return max(data) < THRESHOLD

def record_phrase():
    num_silent = 0
    start = False
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)
    stream.start_stream()
    recording = array('h')
    while True:
        data = array('h', stream.read(CHUNK_SIZE))
        if byteorder == 'big':
            data.byteswap()
        recording.extend(data)
        silent = is_silent(data)
        if silent and start:
            num_silent += 1
        elif not silent and not start:
            start = True
            num_silent = 0
        if start and num_silent > 5:
            break
    stream.stop_stream()
    stream.close()
    p.terminate()
    return recording

def play_audio(audio):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE, output=True)
    stream.write(audio.read())
    stream.stop_stream()
    stream.close()

def set_pocketsphinx_config():
    config = Decoder.default_config()
    config.set_string('-hmm', MODELDIR)
    config.set_string('-logfn','nul')
    config.set_string('-dict', DICT)
    config.set_string('-keyphrase', KEY_PHRASE)
    config.set_float('-kws_threshold', 1e-20)
    return config

def detect_wakeword():
    config = set_pocketsphinx_config()
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)
    stream.start_stream()
    decoder = Decoder(config)
    decoder.start_utt()
    print("Listening for keyword: " + KEY_PHRASE)
    while True:
        frames = []
        buf = stream.read(2048)
        frames.append(buf)
        if buf:
            decoder.process_raw(buf, False, False)
        else:
            return
        if decoder.hyp() is not None:
            if KEY_PHRASE in decoder.hyp().hypstr:
                print("Detected keyword. Please say the appropriate utterance to activate the intent.")
                decoder.end_utt()
                stream.stop_stream()
                stream.close()
                p.terminate()
                return

def synthesize_speech(message):
    global VOICE_ID
    if VOICE_ID is None:
        VOICE_ID = get_voiceid()
    response = polly.synthesize_speech(
        Engine='standard',
        OutputFormat = 'pcm',
        Text = message,
        VoiceId = VOICE_ID
    )
    audio = response['AudioStream']
    play_audio(audio)

def call_lexv2(session_id, recording):
    response = lexv2.recognize_utterance(
        botId=bot_id,
        botAliasId=bot_alias_id,
        localeId='en_US',
        sessionId=session_id,
        requestContentType='audio/l16; rate=16000; channels=1',
        responseContentType='audio/pcm',
        inputStream=recording
    )
    return response

def decode(data):
    decoded_data = base64.b64decode(data)
    decompressed_data = zlib.decompress(decoded_data, 16+zlib.MAX_WBITS)
    return json.loads(decompressed_data)

def get_voiceid():
    lexv2_model = boto3.client('lexv2-models')
    bot_alias = lexv2_model.describe_bot_alias(
        botAliasId = bot_alias_id,
        botId = bot_id
    )
    bot_locale = lexv2_model.describe_bot_locale(
        botId = bot_id,
        botVersion = bot_alias['botVersion'],
        localeId = 'en_US'
    )
    return bot_locale['voiceSettings']['voiceId']

def main():
    detect_wakeword()
    session_id = str(uuid.uuid4())
    while 1:
        try:
            recording = record_phrase()
            response = call_lexv2(session_id, bytes(recording))
            play_audio(response['audioStream'])
            session_state = decode(response['sessionState'])
            dialog_action = session_state['dialogAction']['type']
            state = session_state['intent']['state']
            if dialog_action == 'Close' and state == 'Fulfilled':
                break
        except Exception as e:
            print(e)

if __name__ == "__main__":
    bot = True
    while bot:
        main()
        synthesize_speech("Would you like to try again? Please input y or n.")
        while 1:
            key = input("Please input y/n: ")
            if key == 'y':
                break
            elif key == 'n':
                bot = False
                break
            else:
                synthesize_speech("Please input y or n.")
    synthesize_speech("Thank you. Have a nice day!")








            