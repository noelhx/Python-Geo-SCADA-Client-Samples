# Example: Get Earthquake Map Data
import geo_scada_types
from geoscada.lib.variant import *
from datetime import datetime, timedelta
from geoscada.client.interface_scx import InterfaceScx
from geoscada.client.types import QueryStatus
from typing import Optional
import unicodedata
# Allow program to write to its StdErr property
import sys

################################################################
# Web request library - needs you to run "pip install requests"
################################################################
import requests

def execute(program_path: str, program_name: str, trigger_type: geo_scada_types.ProgramTrigger, geo_scada_args: dict, connection: Optional[InterfaceScx], *args, **kwargs):
    # Find this program item
    ppath = connection.find_object(program_path)

    #############################################################
    # RUN SECTION - READ FROM WEB WRITE TO GEO SCADA
    #############################################################

    # Make the web request
    starttime = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d%%20%H:%M:%S")
    endtime = datetime.now().strftime("%Y-%m-%d%%20%H:%M:%S")
    minmagnitude = 4.5
    base_url = f"https://earthquake.usgs.gov/fdsnws/event/1/query.geojson"
    # Parameters
    final_url = base_url + f"?starttime={starttime}&endtime={endtime}&minmagnitude={minmagnitude}&orderby=time"
    # Constrain by bounding box, e.g. this is the USA
    # &maxlatitude=50&minlatitude=24.6&maxlongitude=-65&minlongitude=-125
    
    # Get data in JSON
    earthquake_response = requests.get(final_url)
    earthquake_data = earthquake_response.json()

    # The following would be more efficient to keep existing records, purge old and insert new

    # Remove all previous records
    sqltext = f"DELETE FROM Earthquakes"
    print(sqltext)
    q = connection.prepare_query(sqltext, False)
    result = q.execute_sync()
    if result.status == QueryStatus.Succeeded:
        print(result.rows_affected)
    else:
        print(result.status, file=sys.stderr)

    # Get all records and insert each one
    index = 0
    while (index < len(earthquake_data["features"])):
        # Get parameters
        time = earthquake_data["features"][index]["properties"]["time"] #milliseconds
        timevalue = datetime.fromtimestamp(time/1000.0)
        mag = earthquake_data["features"][index]["properties"]["mag"]
        title = earthquake_data["features"][index]["properties"]["title"]
        title = unicodedata.normalize('NFC', title).encode('ascii', 'ignore')
        title = title.decode()
        lat = earthquake_data["features"][index]["geometry"]["coordinates"][1]
        long = earthquake_data["features"][index]["geometry"]["coordinates"][0]
        print(f"{mag}, {timevalue.strftime('%Y-%m-%d %H:%M:%S')}, {title}, {lat}, {long}")
    
        sqltext = f"INSERT INTO Earthquakes (timevalue, mag, title, lat, long) VALUES (TIMESTAMP('{timevalue.strftime("%Y-%m-%d %H:%M:%S")}'), {mag}, '{title}', {lat}, {long})"
        print(sqltext)
        q = connection.prepare_query(sqltext, False)
        result = q.execute_sync()
        if result.status == QueryStatus.Succeeded:
            print(result.rows_affected)
        else:
            print(result.status, file=sys.stderr)
        index += 1

    print("Success")