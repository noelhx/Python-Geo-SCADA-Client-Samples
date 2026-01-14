###################################################################################################
#      This program shows how to query the database and then modify selected configuration
# It will find points in Example Projects and add a historic export link to the Sp Publisher.
###################################################################################################
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

# Use next line if you are running from Geo SCADA, and comment out the 'with' 3 lines, plus exchange comments at the top line and uncomment the final execute() line.
def execute(program_path: str, program_name: str, trigger_type: geo_scada_types.ProgramTrigger, geo_scada_args: dict, connection: Optional[InterfaceScx], *args, **kwargs):
##def execute():
##  with ConnectionManager('localhost', 5481, 'ConnectionManager example') as connection:
##    user, passw = '', '' # Add your code to retrieve credentials here
##    connection.log_on(user, passw)

    # Query all objects with historic data
    q = connection.prepare_query("SELECT WITH TEMPLATES H.ID, P.FULLNAME, H.HISTORICEXPORTIDS FROM CHISTORY AS H LEFT JOIN CDBOBJECT AS P USING ( ID ) WHERE P.FULLNAME LIKE 'Example Projects.%'", False)
    result = q.execute_sync()
    print(result.status == QueryStatus.Succeeded)
    if result.status == QueryStatus.Succeeded:
        print(result.rows_affected)
    else:
        print(f"Failed query {result.status}", file=sys.stderr)

    # Get the export object - EDIT YOUR REFERENCE HERE
    exportobj = connection.find_object( "Sparkplug Publisher")
    exportid = exportobj.id
    
    for queryrow in result.rows:
        id = queryrow.data[0].value
        # Get current export ids
        exportidsvar = connection.get_property( id, "Historic.HistoricExportIDs")
        # Does it contain ours?
        if ( exportid not in [int(id) for id in exportidsvar.value]):
            exportidsvar.value.append( exportid)
            # If creating the variant: = Variant(CombinedVariantType(VariantType.I4, VariantFlags.Array), exportids)
            try:
                connection.set_property( id, "Historic.HistoricExportIDs", exportidsvar)
                print(f"OK {queryrow.data[1].value}")
            except Exception as e:
                print(f"Fail {queryrow.data[1].value} {e.args[0]}", file=sys.stderr)

#execute()