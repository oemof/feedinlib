import era5_processing_weather_data_multi_locations as multi_loc
import era5_with_pvlib_single_location as era5_pvlib
import era5_with_windpowerlib_single_location as era5_windpowerlib
import feedin_with_own_weather_data_set
import matplotlib
import windpowerlib_cluster_and_windfarm

matplotlib.use("Agg")


class TestEra5Examples:
    def test_era5_with_pvlib(self):
        era5_pvlib.era5_with_pvlib_examples()

    def test_era5_with_windpowerlib(self):
        era5_windpowerlib.era5_with_windpowerlib_examples()

    def test_era5_multilocations(self):
        multi_loc.processing_multi_locations()

    def test_farms_and_cluster(self):
        windpowerlib_cluster_and_windfarm.cluster_and_windfarm_examples()

    def test_feedin_with_own_weather_data_set(self):
        feedin_with_own_weather_data_set.run_example()
