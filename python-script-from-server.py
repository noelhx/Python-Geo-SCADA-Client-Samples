import geo_scada_types
##from geoscada.client import ConnectionManager

# Commonly used imports
from geoscada.lib.variant import *
from geoscada.client.interface_scx import InterfaceScx
from geoscada.client.types import QueryStatus, ImportOptions
from typing import Optional
from datetime import datetime, timezone, timedelta
import sys
import time

# Use next line if you are running from Geo SCADA, and comment out the 'with' 3 lines
def execute(program_path: str, program_name: str, trigger_type: geo_scada_types.ProgramTrigger, geo_scada_args: dict, connection: Optional[InterfaceScx], *args, **kwargs):
##def execute():
##  with ConnectionManager('localhost', 5481, 'ConnectionManager example') as connection:
##    user, passw = '', '' # Add your code to retrieve credentials here
##    connection.log_on(user, passw)

    # Your code goes here

#execute()