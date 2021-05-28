import os
from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename
from pydub.playback import play
from pydub import AudioSegment
import wave
import json
import time
import vosk
from vosk import Model, KaldiRecognizer, SetLogLevel
from flask import send_from_directory


model = vosk.Model("vosk-model-fr-0.6-linto-2.0.0")
SetLogLevel(0)  # To control how much output we want

app=Flask(__name__)

app.secret_key = "secret key"
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

path = os.getcwd()
# file Upload
UPLOAD_FOLDER = os.path.join(path, 'uploads')

if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


ALLOWED_EXTENSIONS = set(['m4a'])

def transcribe(file_path, buffer_size=32000, nb_sec = 720):
    start_time = time.time()  # To check the time of transciption
    wf = wave.open(file_path)
    rec = KaldiRecognizer(model, wf.getframerate())
    nb_buffers = wf.getframerate() * nb_sec // buffer_size
    for i in range(nb_buffers):
        # For each iteration readframes() removes the frames already read.
        buffer = wf.readframes(buffer_size)
        rec.AcceptWaveform(buffer)
    result_json_str = rec.FinalResult()
    result = json.loads(result_json_str)
    wf.close()
    end_time = time.time()
    delta_time = end_time - start_time
    return result, delta_time


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def upload_form():
    return render_template('upload.html')


@app.route('/', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            print('File uploading please wait')  
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File successfully uploaded')
            
            print('File successfully uploaded')                                                  
            src = f"uploads/{filename}"   
            dst = f"uploads/{filename}.wav"
                                                                        
            sound = AudioSegment.from_file(src, format="m4a")
            sound.set_channels(1) # (in mono)
            sound.export(dst, format="wav")
            
            nb_sec = 720
            
            file_path = f"uploads/{filename}.wav"
            
            print('Beginning transcription')   
            result, delta_time = transcribe(file_path)
                
            print("Transcription time " + filename + ": " + str(delta_time) + " s")
                
            # We save the output of the vosk model in a json file.
            #with open("Transcripts/vosk_result_" + filename + ".json", "w") as outfile:  
            #    json.dump(result, outfile, indent=4, sort_keys=True)

            # We save the text of the transcript in a seperate .txt file
            with open("Transcripts/vosk_" + filename + ".txt", "w") as outfile:  
                outfile.write(result["text"])
            
            outputfilename= f"vosk_{filename}.txt"
            print('sending file')   
            
            return send_from_directory(directory='./Transcripts', filename=outputfilename, as_attachment = True)
        else:
            flash('Allowed file type is m4a for now')
            return redirect(request.url)


if __name__ == "__main__":
    app.run(host = '127.0.0.1',port = 5000, debug = False)