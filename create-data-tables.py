import os
import traceback
import datetime
import math
import time

from geoscada.client import ConnectionManager
from geoscada.base.gs_logging import LogLevel
from geoscada.lib.variant import Variant, VariantType

def CreateTable(connection):
    folder = connection.find_object("SQL_DATA_TABLES.TestTables")
    if folder is None:
        SQL_DATA_Tables  = connection.create_object("CGroup", 0, "SQL_DATA_TABLES")
        TestTables       = connection.create_object("CGroup", SQL_DATA_Tables.id, "TestTables")
    folder = connection.find_object("SQL_DATA_TABLES")
    table = connection.create_object("CDataTable", folder.id, "MainTable")
    connection.set_property(table.id, "TableName", Variant(var_type = VariantType.BStr, value = "MainTable"))
    connection.set_property(table.id, "Title", Variant(var_type = VariantType.BStr, value ="MainTable"))
    # Add a time field
    connection.invoke_method(table.id, "AddField", [Variant(VariantType.BStr, "TimeStamp"), Variant(VariantType.I4, 2)])
    # The string of the created column only has length=1
    connection.invoke_method(table.id, "AddField", [Variant(VariantType.BStr, "TestName"), Variant(VariantType.I4, 6)])
    # Adjust the column size
    connection.invoke_method(table.id, "SetFieldSize", [Variant(VariantType.BStr, "TestName"), Variant(VariantType.I4, 16)])

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 5481
CLIENT_NAME = 'Python Test' 
USERNAME = "" # Your credentials
PASSWORD = ""

# Main function uses ConnectionManager
if __name__ == "__main__":
    print(f"Connecting to GeoSCADA Server at {SERVER_ADDRESS}:{SERVER_PORT}...")
    try:
        with ConnectionManager(SERVER_ADDRESS, SERVER_PORT, CLIENT_NAME) as connection:
            print("Connection successful. Logging on...")
            connection.log_on(USERNAME, PASSWORD) # Log on using credentials
            CreateTable(connection)

    except Exception as e:
        print(f"\n*** An error occurred: {e} ***")
        traceback.print_exc()
        print(f"--- Script Finished with Errors ---")