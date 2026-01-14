connection.set_aggregate(object_id, aggregate_name, aggregate_class)
# example
o = connection.find_object("Example Projects.Oil and Gas.Transportation.Pig running.Simulation Logic.CurrentPath")
connection.set_aggregate(o.id, "Historic", "CHistory")
# to remove, set aggregate to empty string or null
connection.set_aggregate(o.id, "Historic", "")
