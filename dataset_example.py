import datetime
import socket
import os
import subprocess

import dataset

try:
  import pwd
except ImportError:
  import getpass
  pwd = None

def current_user():
  if pwd:
    return pwd.getpwuid(os.geteuid()).pw_name
  else:
    return getpass.getuser()

db = dataset.connect('sqlite:///example.db')

metadata = {
    'host': socket.gethostname(),
    'user': current_user(),
    'start_time': datetime.datetime.now(),
    'end_time': datetime.datetime.now(),
    'git_commit': subprocess.getoutput('git rev-parse HEAD'),
    'git_status': subprocess.getoutput('git status -z')
}

echild = {
    'grammar_id': 611,
    'sentences_consumed': 500000
}

grammar = {
    'p_AH': 0.0
}

table = db['echildren']
table.insert(dict(**metadata, **echild, **grammar))

import pandas as pd

df = pd.read_sql_table('echildren', 'sqlite:///example.db')
