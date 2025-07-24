""" run sqlacodegen only works with python <3.11 """

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

cmd = [
    "sqlacodegen",
    "--outfile", "sql2024.py",
    "--schema=data",
    "{}/MSFD2024_public".format(dsn),
]


subprocess.run(cmd, check=True)
