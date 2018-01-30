import json
import os
import random
import sys
import stat
import string
import shutil

from urllib.parse import urlparse

from bs4 import BeautifulSoup
import requests

import subprocess
import tempfile

from uuid import uuid4

from smtplib import SMTP_SSL
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

from flask import Flask, request

app = Flask(__name__)


MERCURY_URL = 'https://mercury.postlight.com/parser'
MERCURY_KEY = os.environ.get("MERCURY_KEY")

SMTP_SERVER = "email-smtp.us-east-1.amazonaws.com"
SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
SMTP_FROM_EMAIL = os.environ.get('SMTP_FROM_EMAIL')
SMTP_TO_EMAILS = [os.environ.get('SMTP_TO_EMAIL'), 'brenton@brntn.me']


def rand_str(l):
    return ''.join([random.choice(string.ascii_letters) for _ in range(l)])


@app.route("/")
def url2kindle():
    base_dir = os.path.dirname(os.path.realpath(__file__))

    args = request.args.to_dict()
    if 'url' not in args:
        return "Please provide a URL"

    url = args['url']
    response = requests.get(MERCURY_URL, {'url': url}, headers={'x-api-key': MERCURY_KEY}).json()
    
    if not 'content' in response:
        return json.dumps(response, indent=2)

    content = response['content']

    title_soup = BeautifulSoup(response['title'], 'html.parser')
    title = ' '.join(title_soup.get_text().split())

    if response.get('lead_image_url'):
        content = f"<img src='{response.get('lead_image_url')}'/>" + content

    soup = BeautifulSoup(content, 'html.parser')

    with tempfile.TemporaryDirectory() as work_dir:
        # gather all the images
        for img in soup.find_all('img'):
            src = img.attrs['src']
            path = urlparse(src).path

            if '.' in path:
                ext = path.split('.')[-1]
            else:
                ext = 'jpg'

            fn = f'{uuid4()}.{ext}'

            with open(os.path.join(work_dir, fn), 'wb') as img:
                print('Downloading', src)
                img.write(requests.get(src).content)
                content = content.replace(src, fn)
        
        # load our template and write the content
        with open('template.html', 'r') as t:
            template = t.read()
            template = template.replace('[content]', content)
            template = template.replace('[title]', title)
            with open(os.path.join(work_dir, 'output.html'), 'w') as out:
                out.write(template)

        if sys.platform == 'darwin':
            kindlegen = os.path.join(base_dir, 'bin/kindlegen-macos')
        else:
            kindlegen = os.path.join(base_dir, 'bin/kindlegen-linux')

        out_fn = f'{title}-{rand_str(6)}.mobi'
        subprocess.run([kindlegen, 'output.html', '-o', out_fn], cwd=work_dir, stderr=subprocess.STDOUT)

        if 'copy' in args:
            shutil.copy(os.path.join(work_dir, out_fn), '/Users/brenton/Desktop/')
            return 'Copied to Desktop'

        with SMTP_SSL(SMTP_SERVER) as smtp:
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)

            msg = MIMEMultipart()
            msg['From'] = SMTP_FROM_EMAIL
            msg['To'] = COMMASPACE.join(SMTP_TO_EMAILS)
            msg['Date'] = formatdate(localtime=True)
            msg['Subject'] = title

            msg.attach(MIMEText(''))

            with open(os.path.join(work_dir, out_fn), 'rb') as f:
                part = MIMEApplication(
                    f.read(),
                    Name=out_fn
                )
                part['Content-Disposition'] = f'attachment; filename="{out_fn}"'
                msg.attach(part)

            print('Sending email...')
            smtp.sendmail(SMTP_FROM_EMAIL, SMTP_TO_EMAILS, msg.as_string())

    return title
