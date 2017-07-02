from __future__ import print_function 
import os
from flask import *
from PIL import Image
import StringIO
from picamera import PiCamera
from flask_apscheduler import APScheduler
from time import strftime
import sys

app = Flask(__name__)

camera = PiCamera()
#camera.brightness = 70
#camera.exposure_mode = 'night'

lastfile = ""

WIDTH = 1000
HEIGHT = 800

TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title></title>
    <meta charset="utf-8" />
    <style>
body {
    margin: 0;
    background-color: #333;
}
.image {
    display: block;
    margin: 2em auto;
    background-color: #444;
    box-shadow: 0 0 10px rgba(0,0,0,0.3);
}
img {
    display: block;
}
    </style>
    <script src="https://code.jquery.com/jquery-1.10.2.min.js" charset="utf-8"></script>
    <script src="http://luis-almeida.github.io/unveil/jquery.unveil.min.js" charset="utf-8"></script>
    <script>
$(document).ready(function() {
    $('img').unveil(1000);
});
    </script>
</head>
<body>
    {% for image in images %}
        <a class="image" href="{{ image.src }}" style="width: {{ image.width }}px; height: {{ image.height }}px">
            <img src="{{ image.src }}" width="{{ image.width }}" height="{{ image.height }}" />
        </a>
    {% endfor %}
</body>
'''



def save_image():
    global lastfile
    timestr = strftime("%Y%m%d-%H%M%S")
    lastfile = '/media/pi/AC0F-7391/' + timestr + '.jpg'

#    print(lastfile, file=sys.stderr)
    camera.capture(lastfile, resize=(640, 480))


class Config(object):
    JOBS = [
        {
            'id': 'job1',
            'func': save_image,
#            'args': (1, 2),
            'trigger': 'interval',
            'seconds': 10
        }
    ]

    SCHEDULER_API_ENABLED = True


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/image.jpg")
def getImage():
#     camera.capture("/home/pi/web/image.jpg")
#     camera.close()
#     return send_file("/home/pi/web/image.jpg")
#      print(lastfile, file=sys.stderr)

      return send_file(lastfile)

@app.route('/<path:filename>')
def image(filename):
    try:
        w = int(request.args['w'])
        h = int(request.args['h'])
    except (KeyError, ValueError):
        return send_from_directory('/media/pi/AC0F-7391/', filename)

    try:
        im = Image.open(filename)
        im.thumbnail((w, h), Image.ANTIALIAS)
        io = StringIO.StringIO()
        im.save(io, format='JPEG')
        return Response(io.getvalue(), mimetype='image/jpeg')

    except IOError:
        abort(404)

    return send_from_directory('/media/pi/AC0F-7391/', filename)

@app.route('/list')
def list():
    images = []
    for root, dirs, files in os.walk('/media/pi/AC0F-7391/'):
        for filename in [os.path.join(root, name) for name in files]:
#            print(filename[-19:], file=sys.stderr)
            if not filename.endswith('.jpg'):
                continue
            im = Image.open(filename)
            w, h = im.size
            aspect = 1.0*w/h
            if aspect > 1.0*WIDTH/HEIGHT:
                width = min(w, WIDTH)
                height = width/aspect
            else:
                height = min(h, HEIGHT)
                width = height*aspect
            images.append({
                'width': int(width),
                'height': int(height),
                'src': filename[-19:]
            })

    return render_template_string(TEMPLATE, **{
        'images': images
})

#@app.route("/script.js")
#def getTheScript():
#     return render_template("script.js")

if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0")
#     app = Flask(__name__)
     app.config.from_object(Config())
#     app.run(host='0.0.0.0', port=8000, debug=False)

     scheduler = APScheduler()
    # it is also possible to enable the API directly
    # scheduler.api_enabled = True
     scheduler.init_app(app)
     scheduler.start()

     app.run(host='0.0.0.0', port=8000, debug=False)

