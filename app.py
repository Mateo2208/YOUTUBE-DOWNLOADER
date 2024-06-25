from flask import Flask, request, render_template
from pytube import YouTube
import os
import subprocess
import re

app = Flask(__name__)

def clean_filename(filename):
    # Eliminar caracteres no válidos para nombres de archivos en Windows
    return re.sub(r'[\\/*?:"<>|]', "", filename)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/descargar', methods=['POST'])
def descargar():
    url = request.form['url']
    try:
        yt = YouTube(url)
        
        # Obtener el stream de video de mayor resolución
        video_stream = yt.streams.filter(progressive=False, file_extension='mp4').order_by('resolution').desc().first()
        
        # Obtener el stream de audio de mayor calidad
        audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
        
        # Especificar la carpeta de destino
        download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        
        # Crear la carpeta si no existe
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        
        # Descargar los streams
        video_file = video_stream.download(output_path=download_path, filename='video.mp4')
        audio_file = audio_stream.download(output_path=download_path, filename='audio.mp4')
        
        # Limpiar el nombre del archivo de salida
        output_filename = clean_filename(yt.title) + ".mp4"
        output_path = os.path.join(download_path, output_filename)
        
        # Usar ffmpeg para combinar los streams de video y audio
        ffmpeg_command = [
            'ffmpeg', '-i', video_file, '-i', audio_file, '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental', output_path
        ]
        
        # Ejecutar el comando ffmpeg y capturar la salida en bytes
        result = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Decodificar la salida
        stdout = result.stdout.decode('utf-8', errors='replace')
        stderr = result.stderr.decode('utf-8', errors='replace')
        
        # Verificar si ffmpeg tuvo éxito
        if result.returncode != 0:
            error_message = f"ffmpeg error: {stderr}"
            return f'Ha ocurrido un error: {error_message}'
        
        # Eliminar los archivos temporales
        os.remove(video_file)
        os.remove(audio_file)
        
        return f'Video descargado: {yt.title} en {download_path}'
    except Exception as e:
        return f'Ha ocurrido un error: {e}'

if __name__ == "__main__":
    app.run(debug=True)
