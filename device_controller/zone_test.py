import constants
from zone import zone
import os

# test zone creation and functionality
expected_default_timing = [(500, 700), (5500, 700), (10500, 700), (15500, 700), (20500, 700), (25500, 700), (30500, 700), (35500, 700), (40500, 700)]
expected_80nozzle_chemclass4_timing = [(500, 4000), (5500, 4000), (10500, 4000), (15500, 4000), (20500, 4000), (25500, 4000), (30500, 4000), (35500, 4000), (40500, 4000), (45500, 4000), (50500, 4000), (55500, 4000)]
zonedefinition_filename = "zonedefinition.json"

# create zone instance
myzone = zone()

# assert timing
assert myzone.calculate_valve_openings() == expected_default_timing
# change timing and assert
myzone.nozzlecount = 80
myzone.sprayduration_ms = 60000
myzone.chemicalclass = constants.CHEMICALCLASS4
assert myzone.calculate_valve_openings() == expected_80nozzle_chemclass4_timing

# assert sprayoccurrences functionality
default_sprayoccurrences = constants.generate_default_sprayoccurrences()
assert len(myzone.sprayoccurrences) == len(default_sprayoccurrences)
assert myzone.sprayoccurrences == default_sprayoccurrences
assert myzone.remove_sprayoccurrence({}) == None
assert myzone.remove_sprayoccurrence({'dayofweek': 0, 'timeofday': {'type': 'fixedtime', 'value': [23,0]}}) == {'dayofweek': 0, 'timeofday': {'type': 'fixedtime', 'value': [23,0]}}
assert len(myzone.sprayoccurrences) == len(default_sprayoccurrences)-1
assert myzone.sprayoccurrences == [{'dayofweek': 0, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'sunrise', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 0, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'dusk', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 1, 'timeofday': {'type': 'fixedtime', 'value': [23, 0]}}, {'dayofweek': 1, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'sunrise', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 1, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'dusk', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 2, 'timeofday': {'type': 'fixedtime', 'value': [23, 0]}}, {'dayofweek': 2, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'sunrise', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 2, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'dusk', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 3, 'timeofday': {'type': 'fixedtime', 'value': [23, 0]}}, {'dayofweek': 3, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'sunrise', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 3, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'dusk', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 4, 'timeofday': {'type': 'fixedtime', 'value': [23, 0]}}, {'dayofweek': 4, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'sunrise', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 4, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'dusk', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 5, 'timeofday': {'type': 'fixedtime', 'value': [23, 0]}}, {'dayofweek': 5, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'sunrise', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 5, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'dusk', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 6, 'timeofday': {'type': 'fixedtime', 'value': [23, 0]}}, {'dayofweek': 6, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'sunrise', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 6, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'dusk', 'sunposition': 'before', 'deltaminutes': 5}}}]

# test new timing
myzone.valve_first_open_offset_ms = 7500
myzone.valve_activation_interval_ms = 15000
assert myzone.calculate_valve_openings() == [(7500, 4000), (22500, 4000), (37500, 4000), (52500, 4000)]

# test save zonedefinition
with open(zonedefinition_filename, "w") as savedfile:
    savedfile.write(myzone.get_zonedefinition_json())

# assert reset to defaults
myzone.reset_to_defaults()
assert myzone.nozzlecount == constants.default_nozzlecount
assert myzone.chemicalclass == constants.CHEMICALCLASS2
assert myzone.calculate_valve_openings() == expected_default_timing

# load from zonedefinition
with open(zonedefinition_filename, "r") as savedfile:
    new_zonedefinition_json = savedfile.read()
newzone = zone(zonedefinition=new_zonedefinition_json)
assert newzone.valve_first_open_offset_ms == 7500
assert newzone.valve_activation_interval_ms == 15000
assert newzone.calculate_valve_openings() == [(7500, 4000), (22500, 4000), (37500, 4000), (52500, 4000)]

if os.path.exists(zonedefinition_filename):
  os.remove(zonedefinition_filename)
else:
  print("The file does not exist")

# assert no error execution
if __name__ == '__main__':
    myzone.execute_spray()
    newzone.execute_spray()