import constants
import zone

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

# assert reset to defaults
myzone.reset_to_defaults()
assert myzone.nozzlecount == constants.default_nozzlecount
assert myzone.chemicalclass == constants.CHEMICALCLASS2
assert myzone.calculate_valve_openings() == expected_default_timing

# test new timing
myzone.valve_first_open_offset_ms = 7500
myzone.valve_activation_interval_ms = 15000
myzone.calculate_valve_openings()

# assert no error execution
myzone.execute_spray()