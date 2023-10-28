import constants
from zone import zone
import os
import logging
logging.basicConfig(filename='zone_test.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s', force=True)
import unittest.mock as mock

# test zone creation and functionality
expected_default_timing = [{'open_at_ms': 500, 'open_for_ms': 700}, {'open_at_ms': 5500, 'open_for_ms': 700}, {'open_at_ms': 10500, 'open_for_ms': 700}, {'open_at_ms': 15500, 'open_for_ms': 700}, {'open_at_ms': 20500, 'open_for_ms': 700}, {'open_at_ms': 25500, 'open_for_ms': 700}, {'open_at_ms': 30500, 'open_for_ms': 700}, {'open_at_ms': 35500, 'open_for_ms': 700}, {'open_at_ms': 40500, 'open_for_ms': 700}]
expected_80nozzle_chemclass4_timing = [{'open_at_ms': 500, 'open_for_ms': 4000}, {'open_at_ms': 5500, 'open_for_ms': 4000}, {'open_at_ms': 10500, 'open_for_ms': 4000}, {'open_at_ms': 15500, 'open_for_ms': 4000}, {'open_at_ms': 20500, 'open_for_ms': 4000}, {'open_at_ms': 25500, 'open_for_ms': 4000}, {'open_at_ms': 30500, 'open_for_ms': 4000}, {'open_at_ms': 35500, 'open_for_ms': 4000}, {'open_at_ms': 40500, 'open_for_ms': 4000}, {'open_at_ms': 45500, 'open_for_ms': 4000}, {'open_at_ms': 50500, 'open_for_ms': 4000}, {'open_at_ms': 55500, 'open_for_ms': 4000}]
zonedefinition_filename = "zonedefinition.json"

# assert no error execution
if __name__ == '__main__':

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
  assert myzone.remove_sprayoccurrence({'dayofweek': 0, 'timeofday': {'type': 'fixedtime', 'value': {"hour": 23, "minutes": 0}}}) == {'dayofweek': 0, 'timeofday': {'type': 'fixedtime', 'value': {"hour": 23, "minutes": 0}}}
  assert len(myzone.sprayoccurrences) == len(default_sprayoccurrences)-1
  assert myzone.sprayoccurrences == [{'dayofweek': 0, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'sunrise', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 0, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'dusk', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 1, 'timeofday': {'type': 'fixedtime', 'value': {"hour": 23, "minutes": 0}}}, {'dayofweek': 1, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'sunrise', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 1, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'dusk', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 2, 'timeofday': {'type': 'fixedtime', 'value': {"hour": 23, "minutes": 0}}}, {'dayofweek': 2, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'sunrise', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 2, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'dusk', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 3, 'timeofday': {'type': 'fixedtime', 'value': {"hour": 23, "minutes": 0}}}, {'dayofweek': 3, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'sunrise', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 3, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'dusk', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 4, 'timeofday': {'type': 'fixedtime', 'value': {"hour": 23, "minutes": 0}}}, {'dayofweek': 4, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'sunrise', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 4, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'dusk', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 5, 'timeofday': {'type': 'fixedtime', 'value': {"hour": 23, "minutes": 0}}}, {'dayofweek': 5, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'sunrise', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 5, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'dusk', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 6, 'timeofday': {'type': 'fixedtime', 'value': {"hour": 23, "minutes": 0}}}, {'dayofweek': 6, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'sunrise', 'sunposition': 'before', 'deltaminutes': 5}}}, {'dayofweek': 6, 'timeofday': {'type': 'relativetime', 'value': {'sunevent': 'dusk', 'sunposition': 'before', 'deltaminutes': 5}}}]

  # test new timing
  myzone.valve_first_open_offset_ms = 7500
  myzone.valve_activation_interval_ms = 15000
  assert myzone.calculate_valve_openings() == [{'open_at_ms': 7500, 'open_for_ms': 4000}, {'open_at_ms': 22500, 'open_for_ms': 4000}, {'open_at_ms': 37500, 'open_for_ms': 4000}, {'open_at_ms': 52500, 'open_for_ms': 4000}]

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
  assert newzone.calculate_valve_openings() == [{'open_at_ms': 7500, 'open_for_ms': 4000}, {'open_at_ms': 22500, 'open_for_ms': 4000}, {'open_at_ms': 37500, 'open_for_ms': 4000}, {'open_at_ms': 52500, 'open_for_ms': 4000}]

  if os.path.exists(zonedefinition_filename):
      os.remove(zonedefinition_filename)
  else:
      print("The file does not exist")

  myzone.env.get_low_temp_last_24hr = mock.MagicMock(return_value=75)
  myzone.env.get_low_temp_last_24hr.__reduce__ = lambda self: (mock.MagicMock, ())
  myzone.env.get_low_temp_next_24hr = mock.MagicMock(return_value=76)
  myzone.env.get_low_temp_next_24hr.__reduce__ = lambda self: (mock.MagicMock, ())
  myzone.env.get_rain_prediction_next_24hr = mock.MagicMock(return_value={"inches": 0.1})
  myzone.env.get_rain_prediction_next_24hr.__reduce__ = lambda self: (mock.MagicMock, ())
  myzone.execute_spray()
  # print(myzone.spraydata)

  newzone.execute_spray()
  # print(newzone.spraydata)