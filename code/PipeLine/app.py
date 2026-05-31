import os
from io import BytesIO

from flask import Flask, abort, request, render_template_string, redirect, send_file, url_for

from core import get_download_payload, list_files, save_and_compress

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Local Drive</title>
    <style>
        body { font-family: Arial; background:#f1f3f4; padding:20px; }
        .container { max-width:800px; margin:auto; background:white; padding:20px; border-radius:10px; }
        .file { display:flex; justify-content:space-between; padding:10px; border-bottom:1px solid #ddd; }
        a { color:#1a73e8; text-decoration:none; }
        button { background:#1a73e8; color:white; border:none; padding:6px 10px; border-radius:5px; }
    </style>
</head>
<body>

<div class="container">
<h1>📁 Local Drive</h1>

<form action="/upload" method="post" enctype="multipart/form-data">
    <input type="file" name="file">
    <button type="submit">Enviar</button>
</form>

<h3>Arquivos</h3>

{% for file in files %}
<div class="file">
    <span>📄 {{ file.display }}</span>
    <a href="/download/{{ file.storage }}">Baixar</a>
</div>
{% endfor %}

</div>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML, files=list_files())


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return redirect(url_for("index"))

    file = request.files["file"]
    if not file.filename:
        return redirect(url_for("index"))

    save_and_compress(file)
    return redirect(url_for("index"))


@app.route("/download/<filename>")
def download(filename):
    payload = get_download_payload(filename)
    if payload is None:
        abort(404)

    download_name, content = payload
    return send_file(
        BytesIO(content),
        as_attachment=True,
        download_name=download_name,
    )


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))

    app.run(host=host, port=port, debug=True)
