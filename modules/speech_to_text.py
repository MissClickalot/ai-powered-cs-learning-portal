import os
import queue
import sounddevice as sd
import vosk
import json

def load_stt_model():
    # Path to the Vosk model
    model_path = "static/vosk_model"

    # Check if the model exists
    if not os.path.exists(model_path):
        raise FileNotFoundError("Speech recognition model not found. Please use the text box instead.")

    # Load Vosk model
    return vosk.Model(model_path)

# Callback function to process audio
def stt_callback(indata, frames, time, status, audio_queue):
    if status:
        print(status, flush=True)
    audio_queue.put(bytes(indata))

def stt_recognise_speech(model, audio_queue):
    # Set up the microphone input
    with sd.RawInputStream(samplerate=16000,  # Set sample rate to 16kHz as required by vosk
                           blocksize=8000,  # Block size determines the amount of audio processed at a time
                           dtype="int16",  # Data type for raw audio (16-bit PCM)
                           channels=1,  # Mono audio input (single channel)
                           callback=lambda indata, frames, time, status: stt_callback(indata, frames, time, status, audio_queue)):  # Function to process incoming audio

        # Initialise the Vosk speech recogniser with the model
        recognizer = vosk.KaldiRecognizer(model, 16000)

        print("Listening...")

        while True:
            # Get the next chunk of audio data from the queue
            data = audio_queue.get()
            # Check if the recogniser detects a speech segment
            if recognizer.AcceptWaveform(data):
                # Convert the result from JSON format to a Python dictionary
                result = json.loads(recognizer.Result())
                # return the output
                return result["text"]

if __name__ == '__main__':
    # Create a queue to store audio data
    audio_queue = queue.Queue()
    # Load the Vosk model
    model = load_stt_model()
    # Start speech recognition
    result = stt_recognise_speech(model, audio_queue)
    print(result)