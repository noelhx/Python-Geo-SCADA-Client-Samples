H = connection.set_aggregate( P.id, "Historic", "CHistory")
#Get historic aggregate property
print( "Historic Compress:" + str( connection.get_property( P.id, "Historic.Compress").value) )



#Create Geo Location Aggregate Configuration
G = connection.set_aggregate( P.id, "GISLocationSource", "CGISLocationSrcStatic")
print( "Aggregate: " + connection.get_property( P.id, "GISLocationSource.AggrName").value )
print( G)
#Set Geo location
connection.set_properties( P.id, [
    ("GISLocationSource.Latitude", Variant(VariantType.R8, 30.0)),
    ("GISLocationSource.Longitude", Variant(VariantType.R8, 1.0))
    ] )
    

# Helper function to read the as-selected aggregate type
def get_configured_aggr_class( obj_full_name, aggr_field):
    obj = interface.find_object(obj_full_name)
    aggr_info = next(filter(lambda aggr: aggr.name == aggr_field, obj.aggregates), None)
    if (aggr_info == None or aggr_info.index == 4294967295):
        return None
    return aggr_info.classes[aggr_info.index]
    