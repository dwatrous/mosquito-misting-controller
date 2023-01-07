import constants
from zone import zone
import os
import logging
logging.basicConfig(filename='zone_test.log', encoding='utf-8', level=logging.DEBUG)

# test zone creation and functionality
expected_default_timing = [{'open_at': 500, 'open_for': 700}, {'open_at': 5500, 'open_for': 700}, {'open_at': 10500, 'open_for': 700}, {'open_at': 15500, 'open_for': 700}, {'open_at': 20500, 'open_for': 700}, {'open_at': 25500, 'open_for': 700}, {'open_at': 30500, 'open_for': 700}, {'open_at': 35500, 'open_for': 700}, {'open_at': 40500, 'open_for': 700}]
expected_80nozzle_chemclass4_timing = [{'open_at': 500, 'open_for': 4000}, {'open_at': 5500, 'open_for': 4000}, {'open_at': 10500, 'open_for': 4000}, {'open_at': 15500, 'open_for': 4000}, {'open_at': 20500, 'open_for': 4000}, {'open_at': 25500, 'open_for': 4000}, {'open_at': 30500, 'open_for': 4000}, {'open_at': 35500, 'open_for': 4000}, {'open_at': 40500, 'open_for': 4000}, {'open_at': 45500, 'open_for': 4000}, {'open_at': 50500, 'open_for': 4000}, {'open_at': 55500, 'open_for': 4000}]
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
assert myzone.calculate_valve_openings() == [{'open_at': 7500, 'open_for': 4000}, {'open_at': 22500, 'open_for': 4000}, {'open_at': 37500, 'open_for': 4000}, {'open_at': 52500, 'open_for': 4000}]

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
assert newzone.calculate_valve_openings() == [{'open_at': 7500, 'open_for': 4000}, {'open_at': 22500, 'open_for': 4000}, {'open_at': 37500, 'open_for': 4000}, {'open_at': 52500, 'open_for': 4000}]

if os.path.exists(zonedefinition_filename):
  os.remove(zonedefinition_filename)
else:
  print("The file does not exist")

# assert no error execution
if __name__ == '__main__':
    myzone.execute_spray()
    print(myzone.spraydata)
    newzone.execute_spray()
    print(newzone.spraydata)