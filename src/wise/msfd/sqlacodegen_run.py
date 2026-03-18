"""
need python 3.10

pyenv install 3.10.12
pyenv virtualenv 3.10.12 sqlacodegen310
pyenv shell sqlacodegen310
pip install 'sqlacodegen<3'
pip install SQLAlchemy==1.4.46
pip install pymssql

python sqlacodegen_run.py

"""

import subprocess
import os

env = os.environ.get
CRESTEDDUCK_HOST = env('CRESTEDDUCK_HOST', '')
CRESTEDDUCK_DOMAIN = env('CRESTEDDUCK_DOMAIN', '')
CRESTEDDUCK_USER = env('CRESTEDDUCK_USER', '')
CRESTEDDUCK_PASSWORD = env('CRESTEDDUCK_PASSWORD', '')

dsn = ("mssql+pymssql://{}\\{}:{}@{}:1433".format(
    CRESTEDDUCK_DOMAIN,
    CRESTEDDUCK_USER,
    CRESTEDDUCK_PASSWORD,
    CRESTEDDUCK_HOST)
)

# need to run for each scehma separately
cmd = [
    "sqlacodegen",
    "--outfile", "sql2024_NEW.py",
    "--schema=data",
    # "--schema", "data,dbo,spatial",
    "{}/MSFD2024_public".format(dsn),
]


subprocess.run(cmd, check=True)
