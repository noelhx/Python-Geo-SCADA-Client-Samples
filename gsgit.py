# Example showing how to export Geo SCADA configuration as JSON and store updates in GIT
import json
import datetime
import os.path
import zlib
from typing import Optional

from geoscada.client import ConnectionManager, RequestError
from geoscada.comms.misc import ConnectFlags
from geoscada.lib.variant import Variant, VariantType
from geoscada.client.types import PropertyType, ObjectDetails
from git import Repo

# Edit your path here
repo_location = "C:/code/geo-scada/git-repo"


# Custom JSON encoder for the date/time format
class GSEEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        return super().default(o)


# Helper function to read the as-selected aggregate type
def get_configured_aggr_class(obj_full_name, aggr_field):
    obj = interface.find_object(obj_full_name)
    if obj == None:
        return None
    aggr_info = next(filter(lambda aggr: aggr.name == aggr_field, obj.aggregates), None)
    if aggr_info == None or aggr_info.index == 4294967295:
        return None
    return aggr_info.classes[aggr_info.index]


# Get aggregate data separately
def get_agg_properties(
    obj: ObjectDetails, a: str, aggtype: str
) -> Optional[list[tuple[str, list[tuple[str, Variant]]]]]:
    agg_def = interface.get_class(aggtype)
    agg_prop_names = [
        a + "." + p.name
        for p in agg_def.properties
        if p.is_writable and p.property_type == PropertyType.Configuration
    ]
    property_values = []
    this_agg = None
    while len(agg_prop_names) > 0 and len(property_values) == 0:
        try:
            property_values = interface.get_properties(obj.id, agg_prop_names)
        except RequestError as ex:
            if ex.exception_type == "PropertyException":
                for n, v in ex.properties:
                    if n == "PropertyName":
                        print(f"Not including property {v.value}")
                        agg_prop_names.remove(str(v.value))
                        break
    if len(property_values) != 0:
        this_agg = [(aggtype, list(zip(agg_prop_names, property_values)))]

    # Recurse to the base class
    if agg_def.base_class != "CAggregate":
        base_properties = get_agg_properties(obj, a, agg_def.base_class)
        if this_agg != None:
            if base_properties != None:
                return base_properties + this_agg
            else:
                return this_agg
        else:
            return base_properties
    else:
        return this_agg


def get_properties(
    obj: ObjectDetails, class_name: str
) -> list[tuple[str, list[tuple[str, Variant]]]] | None:
    metadata = interface.get_class(class_name)
    property_names = [
        p.name
        for p in metadata.properties
        if p.is_writable and p.property_type == PropertyType.Configuration
    ]

    property_values = []
    this_class = None
    while len(property_names) > 0 and len(property_values) == 0:
        try:
            property_values = interface.get_properties(obj.id, property_names)
        except RequestError as ex:
            if ex.exception_type == "PropertyException":
                for n, v in ex.properties:
                    if n == "PropertyName":
                        print(f"Not including property {v.value}")
                        property_names.remove(str(v.value))
                        break

    # Prepare a list of aggregate information, a list for this class
    agg_details = []
    # Read Aggregate names
    aggregateslist = [a.name for a in metadata.aggregates]
    # Read Aggregate type instantiated
    # Aggregate metadata depends on the type deployed
    this_agg = []
    for a in aggregateslist:
        aggtype = get_configured_aggr_class(obj.full_name, a)
        if aggtype != None:
            # Repeat the get_properties, but on an aggregate
            # Add the aggregate field name and selected class type name to the output - fake a string property
            property_names.append(a)
            property_values.append(Variant(VariantType.BStr, aggtype))
            # Recursively fetch properties
            fetched_agg = get_agg_properties(obj, a, aggtype)
            if fetched_agg != None:
                this_agg = this_agg + fetched_agg

    # Create the property list, including the aggregate setup if needed
    if len(property_values) != 0:
        this_class = [(class_name, list(zip(property_names, property_values)))]

    # Add aggregate fields
    if this_agg != None:
        if this_class != None:
            this_class = this_class + this_agg
        else:
            this_class = this_agg

    # Recurse to the base class
    if metadata.base_class != "":
        base_properties = get_properties(obj, metadata.base_class)
        if this_class != None:
            if base_properties != None:
                return base_properties + this_class
            else:
                return this_class
    else:
        return this_class


def process_object(obj_id: int, is_new_repo: bool):
    constrained, object_list = interface.list_objects_ex(
        obj_id, False, [], "", True, 10000
    )

    for obj in object_list:
        data = {
            "id": obj.id,
            "name": obj.name,
            "class_name": obj.class_name,
            "properties": [],
            "doc_content_crc": 0,
            "doc_content_len": 0,
        }

        properties = get_properties(obj, obj.class_name)
        if properties == None:
            print(
                f"No writable configuration properties for {obj.full_name} of class {obj.class_name}"
            )
            return

        data["properties"] = [
            (class_name, {n: v.value for n, v in props})
            for class_name, props in properties
        ]

        # Document content
        try:
            doc_content = interface.get_document_content(obj.id)
            data["doc_content_len"] = len(doc_content[0])
            data["doc_content_crc"] = zlib.crc32(doc_content[0])
        except RequestError as ex:
            if ex.exception_type == "InvalidObjectException":
                # print("No document content for", obj.full_name)
                pass

        data_path = os.path.join(repo_location, f"{obj.full_name}.json")
        with open(data_path, "w") as f:
            json.dump(data, f, indent=2, cls=GSEEncoder)

        if is_new_repo:
            repo.index.add([data_path])

        if obj.is_group():
            process_object(obj.id, is_new_repo)


new_repo = os.path.exists(repo_location)

if new_repo:
    repo = Repo.init(repo_location)
else:
    os.makedirs(repo_location, exist_ok=True)
    repo = Repo(repo_location)


SERVER = os.environ.get("GEOSCADA_SERVER", "")
USERNAME = os.environ.get("GEOSCADA_USERNAME", "")
PASSWORD = os.environ.get("GEOSCADA_PASSWORD", "")

print(f"Connecting to Geo SCADA Server at {SERVER} with user {USERNAME}")

with ConnectionManager(
    SERVER, 5481, "gsgit", ConnectFlags.IsCompressedLink
) as interface:

    interface.log_on(USERNAME, PASSWORD)

    # Name of group to be scanned for items
    # o = interface.find_object("Example Projects.Oil and Gas")
    o: ObjectDetails | None = interface.find_object("Python Samples")
    if o != None:
        process_object(o.id, new_repo)

if repo.is_dirty():
    repo.index.commit("")
