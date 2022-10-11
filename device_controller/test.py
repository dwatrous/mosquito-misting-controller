import constants
import zone
import datetime

# test zone creation and functionality
expected_default_timing = [(500, 700), (5500, 700), (10500, 700), (15500, 700), (20500, 700), (25500, 700), (30500, 700), (35500, 700), (40500, 700)]
expected_80nozzle_chemclass4_timing = [(500, 4000), (5500, 4000), (10500, 4000), (15500, 4000), (20500, 4000), (25500, 4000), (30500, 4000), (35500, 4000), (40500, 4000), (45500, 4000), (50500, 4000), (55500, 4000)]

# create zone instance
myzone = zone.zone()

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
assert myzone.remove_sprayoccurrence({'dayofweek': 0, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(18, 0)}}) == {'dayofweek': 0, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(18, 0)}}
assert len(myzone.sprayoccurrences) == len(default_sprayoccurrences)-1
assert myzone.sprayoccurrences == [{'dayofweek': 0, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(0, 0)}}, {'dayofweek': 0, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(6, 0)}}, {'dayofweek': 0, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(20, 0)}}, {'dayofweek': 1, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(0, 0)}}, {'dayofweek': 1, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(6, 0)}}, {'dayofweek': 1, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(18, 0)}}, {'dayofweek': 1, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(20, 0)}}, {'dayofweek': 2, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(0, 0)}}, {'dayofweek': 2, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(6, 0)}}, {'dayofweek': 2, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(18, 0)}}, {'dayofweek': 2, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(20, 0)}}, {'dayofweek': 3, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(0, 0)}}, {'dayofweek': 3, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(6, 0)}}, {'dayofweek': 3, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(18, 0)}}, {'dayofweek': 3, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(20, 0)}}, {'dayofweek': 4, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(0, 0)}}, {'dayofweek': 4, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(6, 0)}}, {'dayofweek': 4, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(18, 0)}}, {'dayofweek': 4, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(20, 0)}}, {'dayofweek': 5, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(0, 0)}}, {'dayofweek': 5, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(6, 0)}}, {'dayofweek': 5, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(18, 0)}}, {'dayofweek': 5, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(20, 0)}}, {'dayofweek': 6, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(0, 0)}}, {'dayofweek': 6, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(6, 0)}}, {'dayofweek': 6, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(18, 0)}}, {'dayofweek': 6, 'timeofday': {'type': 'fixedtime', 'value': datetime.time(20, 0)}}]


# assert reset to defaults
myzone.reset_to_defaults()
assert myzone.nozzlecount == constants.default_nozzlecount
assert myzone.chemicalclass == constants.CHEMICALCLASS2
assert myzone.calculate_valve_openings() == expected_default_timing

# test new timing
myzone.valve_first_open_offset_ms = 7500
myzone.valve_activation_interval_ms = 15000
assert myzone.calculate_valve_openings() == [(7500, 700), (22500, 700), (37500, 700)]

# assert no error execution
if __name__ == '__main__':
    myzone.execute_spray()