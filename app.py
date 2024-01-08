from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import os
import tempfile
import shutil
from pydub import AudioSegment
import wave
from moviepy.editor import VideoFileClip
from moviepy.editor import AudioFileClip
from texttolab import convert_txt_to_lab
from texttotime import convert_textgrid_to_srt
from docxtolab import convert_docx_to_lab
from convert_label import generate_textgrid_from_lab_and_wav
import os
import time
import subprocess

#app = Flask(__name__)
app = Flask(__name__, template_folder='templates')

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

def convert_mp3_to_wav(audio_path, output_path):
    try:
        audio = AudioFileClip(audio_path)
        
        temp_dir = tempfile.mkdtemp()

        try:
            temp_audio_file = tempfile.NamedTemporaryFile(
                suffix=".wav", dir=temp_dir, delete=False
            )
            temp_audio_filename = temp_audio_file.name
            audio.write_audiofile(temp_audio_filename)

            audio_filename = os.path.splitext(os.path.basename(audio_path))[0]
            output_file_path = os.path.join(output_path, f"{audio_filename}.wav")

            audio.close()
            temp_audio_file.close()
            shutil.move(temp_audio_filename, output_file_path)

            print(f"Audio processed. Output path: {output_file_path}")
            return output_file_path
        finally:
            audio.close()
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Error during audio processing: {str(e)}")
    

def process_video(video_path, output_path):
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        temp_dir = tempfile.mkdtemp()

        try:
            temp_audio_file = tempfile.NamedTemporaryFile(
                suffix=".wav", dir=temp_dir, delete=False
            )
            temp_audio_filename = temp_audio_file.name
            audio.write_audiofile(temp_audio_filename)

            video_filename = os.path.splitext(os.path.basename(video_path))[0]
            output_file_path = os.path.join(output_path, f"{video_filename}.wav")

            audio.close()
            temp_audio_file.close()
            shutil.move(temp_audio_filename, output_file_path)

            print(f"Video processed. Output path: {output_file_path}")
            return output_file_path
        finally:
            video.close()
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Error during video processing: {str(e)}")

'''def generate_textgrid(input_lab_file, output_textgrid_file, audio_file, chooses_mora=False):
    # Read the label file
    label = read_lab(input_lab_file, audio_file)

    # Optionally convert to moras
    if chooses_mora:
        label = label.by_moras()

    # Generate and save the TextGrid file
    label.to_textgrid(output_textgrid_file)'''


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/align', methods=['POST'])
def align():
    output_path = app.config['OUTPUT_FOLDER']

    try:
        if 'videoFile' not in request.files or 'scriptFile' not in request.files:
            return render_template('index.html', error='Please upload both video and script files.')

        video_file = request.files['videoFile']
        script_file = request.files['scriptFile']

        if video_file.filename == '' or script_file.filename == '':
            return render_template('index.html', error='Please select both video and script files.')

        video_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(video_file.filename))
        script_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(script_file.filename))

        video_file.save(video_path)
        script_file.save(script_path)

        print(f"Video Path: {video_path}")
        print(f"Script Path: {script_path}")

        if video_file.filename.lower().endswith('.mp3'):
            convert_mp3_to_wav(video_path, output_path)
        else:
            process_video(video_path, output_path)
        
        if script_file.filename.lower().endswith('.txt'):
            script_output_path = os.path.join(output_path, 'output.lab')
            convert_txt_to_lab(script_path, script_output_path)
        else:
            script_output_path = os.path.join(output_path, 'output.lab') 
            convert_docx_to_lab(script_path, script_output_path)

        if video_file.filename.lower().endswith('.mp3'):
            wav_file_path = os.path.join(output_path, 'output.wav')
            time.sleep(1)  # Introduce a delay after converting MP3 to WAV
        else:
            wav_file_path = os.path.join(output_path, f"{os.path.splitext(os.path.basename(video_path))[0]}.wav")

        print(f"WAV File Path: {wav_file_path}")

        
        #chooses_mora = False
        textgrid_output_path = os.path.join(output_path, 'output.textgrid')
        #generate_textgrid(script_output_path, textgrid_output_path, wav_file_path, chooses_mora)'''
        
        generate_textgrid_from_lab_and_wav(script_output_path, wav_file_path, textgrid_output_path)

        #textgrid_output_path = os.path.join(output_path, 'align.praat')

        srt_output_path = os.path.join(output_path, 'output.srt')
        convert_textgrid_to_srt(textgrid_output_path, output_path, interval_length=1)

        print(f"SRT Output Path: {srt_output_path}")

        response = send_file(srt_output_path, as_attachment=True)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    except Exception as e:
        print(f"Error during alignment: {str(e)}")
        return render_template('index.html', error=f'Error during alignment: {str(e)}')
    
def generate_preview_srt(srt_content, preview_lines=5):
    # Add logic to read the content of the original SRT file and generate the preview
    # For example, you can use the following code assuming srt_content is the file path:
    with open(srt_content, 'r', encoding='utf-8') as file:
        original_srt_content = file.read()

    # Your logic to generate the preview goes here
    preview_content = "\n".join(original_srt_content.splitlines()[:preview_lines])

    return preview_content

@app.route('/Preview', methods=['POST'])
def preview():
    output_path = app.config['OUTPUT_FOLDER']
    srt_content_path = os.path.join(output_path, 'output.srt')

    # Generate the preview content
    preview_content = generate_preview_srt(srt_content_path, preview_lines=5)

    # Render the preview content (you might want to create a specific template for this)
    return render_template('preview_template.html', preview_content=preview_content)


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    app.run(debug=True)
