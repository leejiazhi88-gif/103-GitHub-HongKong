"""Minimal Feishu Sheets API client. Credentials never appear in command arguments."""
import argparse
import json
import os
import subprocess
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]


def load_env(path):
    if not path or not Path(path).exists():
        return
    for line in Path(path).read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key, value = line.split('=', 1)
            if key.strip() in ('FEISHU_APP_ID', 'FEISHU_APP_SECRET'):
                os.environ.setdefault(key.strip(), value.strip().strip('\"\''))


def arguments(description):
    p = argparse.ArgumentParser(description=description)
    p.add_argument('--env-file', type=Path, default=ROOT / '.env')
    return p


def request(method, path, token=None, body=None):
    # Headers/body are supplied via stdin rather than exposed in process arguments.
    cfg = ['silent', 'show-error', 'max-time = 60',
           'url = ' + json.dumps('https://open.feishu.cn/open-apis/' + path),
           'request = ' + json.dumps(method),
           'header = "Content-Type: application/json"']
    if token:
        cfg.append('header = ' + json.dumps('Authorization: Bearer ' + token))
    if body is not None:
        cfg.append('data = ' + json.dumps(json.dumps(body, ensure_ascii=False)))
    proc = subprocess.run(['curl', '--config', '-'], input='\n'.join(cfg),
                          text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError('HTTPS transport failure, curl code ' + str(proc.returncode))
    result = json.loads(proc.stdout)
    if result.get('code') != 0:
        raise RuntimeError(f'Feishu API {result.get("code")}: {result.get("msg")}')
    return result


class Sheet:
    def __init__(self, env_file=None):
        load_env(env_file or ROOT / '.env')
        self.config = json.loads((ROOT / 'config/project.json').read_text())
        names = ('FEISHU_APP_ID', 'FEISHU_APP_SECRET')
        if any(not os.environ.get(n) for n in names):
            raise RuntimeError('Configure FEISHU_APP_ID and FEISHU_APP_SECRET locally.')
        self.token = request('POST', 'auth/v3/tenant_access_token/internal', body={
            'app_id': os.environ[names[0]], 'app_secret': os.environ[names[1]]
        })['tenant_access_token']
        node = request('GET', 'wiki/v2/spaces/get_node?' + urlencode({
            'token': self.config['wiki_token']}), self.token)['data']['node']
        if node['obj_type'] != 'sheet':
            raise RuntimeError('Configured wiki node is not a spreadsheet.')
        self.spreadsheet = node['obj_token']
        self.sid = self.config['sheet_id']
        self.base = f'sheets/v2/spreadsheets/{self.spreadsheet}'

    def call(self, method, suffix, body=None):
        return request(method, self.base + suffix, self.token, body)

    def metadata(self):
        sheets = request('GET', f'sheets/v3/spreadsheets/{self.spreadsheet}/sheets/query',
                         self.token)['data']['sheets']
        return next(s for s in sheets if s['sheet_id'] == self.sid)

    def read(self, address):
        return self.call('GET', f'/values/{self.sid}!{address}?valueRenderOption=ToString')[
            'data']['valueRange']['values']
