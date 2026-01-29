""" run sqlacodegen only works with python <3.11 
need python 3.10
pip install 'sqlacodegen<3'
pip install SQLAlchemy==1.4.46
pip install pymssql
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

cmd = [
    "sqlacodegen",
    "--outfile", "sql2024_NEW.py",
    "--schema=spatial",
    # "--schema", "data,dbo,spatial",
    "{}/MSFD2024_public".format(dsn),
]


subprocess.run(cmd, check=True)

# from sqlacodegen.main import main
# import sys

# sys.argv = [
#     "sqlacodegen",
#     "--outfile", "sql2024_NEW.py",
#     "--schema", "data,dbo",
#     "{}/MSFD2024_public".format(dsn),
# ]

# main()
