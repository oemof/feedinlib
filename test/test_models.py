import pytest
from pandas.util.testing import assert_frame_equal
import pandas as pd
from copy import deepcopy

from feedinlib import WindPowerPlant, Photovoltaic
from feedinlib.models import WindpowerlibTurbine, Pvlib, \
    WindpowerlibTurbineCluster
from windpowerlib import WindTurbine as WindpowerlibWindTurbine


class Fixtures:
    """
    Class providing all fixtures for model tests.
    """

    @pytest.fixture
    def pvlib_weather(self):
        """
        Returns a test weather dataframe to use in tests for pvlib model.
        """
        return pd.DataFrame(data={'wind_speed': [5.0],
                                  'temp_air': [10.0],
                                  'dhi': [150.0],
                                  'ghi': [300]},
                            index=pd.date_range('1/1/1970 12:00',
                                                periods=1, tz='UTC'))

    @pytest.fixture
    def windpowerlib_weather(self):
        """
        Returns a test weather dataframe to use in tests for windpowerlib
        model.
        """
        return pd.DataFrame(data={('wind_speed', 10): [5.0],
                                  ('temperature', 2): [270.0],
                                  ('roughness_length', 0): [0.15],
                                  ('pressure', 0): [98400.0]},
                            index=pd.date_range('1/1/1970 12:00',
                                                periods=1, tz='UTC'))

    @pytest.fixture
    def pvlib_pv_system(self):
        """
        Returns a test PV system setup to use in tests for pvlib model.
        """
        return {'module_name': 'Yingli_YL210__2008__E__',
                'inverter_name':
                    'ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_',
                'azimuth': 180,
                'tilt': 30,
                'albedo': 0.2}

    @pytest.fixture
    def windpowerlib_turbine(self):
        """
        Returns a test wind power plant to use in tests for windpowerlib model.
        """
        return {'turbine_type': 'E-82/3000',
                'hub_height': 135}

    @pytest.fixture
    def windpowerlib_turbine_2(self):
        """
        Returns a test wind power plant to use in tests for windpowerlib model.
        """
        return {'turbine_type': 'V90/2000',
                'hub_height': 120,
                'rotor_diameter': 80}

    @pytest.fixture
    def windpowerlib_farm(self, windpowerlib_turbine, windpowerlib_turbine_2):
        """
        Returns a test wind farm to use in tests for windpowerlib model.
        """
        return {'wind_turbine_fleet': pd.DataFrame(
            {'wind_turbine': [windpowerlib_turbine, windpowerlib_turbine_2],
             'number_of_turbines': [6, None],
             'total_capacity': [None, 3 * 2e6]})}

    @pytest.fixture
    def windpowerlib_farm_2(self, windpowerlib_turbine):
        """
        Returns a test wind farm to use in tests for windpowerlib model.
        """
        return {'wind_turbine_fleet': [WindpowerlibWindTurbine(
            **windpowerlib_turbine).to_group(1)]}

    @pytest.fixture
    def windpowerlib_farm_3(
            self, windpowerlib_turbine, windpowerlib_turbine_2):
        """
        Returns a test wind farm to use in tests for windpowerlib model.
        """

        return {'wind_turbine_fleet': pd.DataFrame(
            {'wind_turbine': [WindPowerPlant(**windpowerlib_turbine),
                              WindPowerPlant(**windpowerlib_turbine_2)],
             'number_of_turbines': [6, 3]})}

    @pytest.fixture
    def windpowerlib_turbine_cluster(self, windpowerlib_farm,
                                     windpowerlib_farm_2):
        """
        Returns a test wind turbine cluster to use in tests for windpowerlib
        model.
        """
        return {'wind_farms': [windpowerlib_farm, windpowerlib_farm_2]}


class TestPowerplants(Fixtures):
    """
    Class to test some basic functionalities of the power plant classes.
    """

    def test_powerplant_requirements(self, pvlib_pv_system, pvlib_weather):
        """
        Test that attribute error is not raised in case a valid model is
        specified when calling feedin method.
        """
        test_module = Photovoltaic(**pvlib_pv_system)
        feedin = test_module.feedin(weather=pvlib_weather,
                                    model=Pvlib, location=(52, 13))
        assert 143.28844 == pytest.approx(feedin.values[0], 1e-5)

    def test_powerplant_requirements_2(self, pvlib_pv_system, pvlib_weather):
        """
        Test that attribute error is raised in case required power plant
        parameters are missing when feedin is called with a different model
        than initially specified.
        """
        test_module = Photovoltaic(**pvlib_pv_system)
        msg = "The specified model 'windpowerlib_single_turbine' requires"
        with pytest.raises(AttributeError, match=msg):
            test_module.feedin(weather=pvlib_weather,
                               model=WindpowerlibTurbine, location=(52, 13))

    def test_pv_feedin_scaling(self, pvlib_pv_system, pvlib_weather):
        """
        Test that PV feedin timeseries are scaled correctly.
        """
        test_module = Photovoltaic(**pvlib_pv_system)
        feedin = test_module.feedin(
            weather=pvlib_weather, location=(52, 13), scaling='peak_power')
        assert 0.67462 == pytest.approx(feedin.values[0], 1e-5)
        feedin = test_module.feedin(
            weather=pvlib_weather, location=(52, 13), scaling='area')
        assert 84.28732 == pytest.approx(feedin.values[0], 1e-5)

    def test_wind_feedin_scaling(
            self, windpowerlib_turbine, windpowerlib_weather):
        """
        Test that wind feedin timeseries are scaled correctly.
        """
        test_turbine = WindPowerPlant(**windpowerlib_turbine)
        feedin = test_turbine.feedin(weather=windpowerlib_weather,
                                     scaling='nominal_power')
        assert 833050.32551 / 3e6 == pytest.approx(feedin.values[0], 1e-5)


class TestPvlib(Fixtures):
    """
    Class to test Pvlib model.
    """

    def test_pvlib_feedin(self, pvlib_pv_system, pvlib_weather):
        """
        Test basic feedin calculation using pvlib.
        It is also tested if dictionary with PV system parameters remains the
        same to make sure it could be further used to calculate feed-in with
        a different model.
        """
        test_copy = deepcopy(pvlib_pv_system)
        test_module = Photovoltaic(**pvlib_pv_system)
        feedin = test_module.feedin(weather=pvlib_weather,
                                    location=(52, 13))
        assert 143.28844 == pytest.approx(feedin.values[0], 1e-5)
        assert test_copy == pvlib_pv_system

    def test_pvlib_feedin_with_surface_type(
            self, pvlib_pv_system, pvlib_weather):
        """
        Test basic feedin calculation using pvlib and providing surface type
        instead of albedo.
        """
        del pvlib_pv_system['albedo']
        pvlib_pv_system['surface_type'] = 'grass'
        test_module = Photovoltaic(**pvlib_pv_system)
        feedin = test_module.feedin(weather=pvlib_weather, location=(52, 13))
        assert 143.28844 == pytest.approx(feedin.values[0], 1e-5)

    def test_pvlib_feedin_with_optional_pp_parameter(
            self, pvlib_pv_system, pvlib_weather):
        """
        Test basic feedin calculation using pvlib and providing an optional
        PV system parameter.
        """
        pvlib_pv_system['strings_per_inverter'] = 2
        test_module = Photovoltaic(**pvlib_pv_system)
        feedin = test_module.feedin(weather=pvlib_weather, location=(52, 13))
        # power output is in this case limited by the inverter, which is why
        # power output with 2 strings is not twice as high as power output of
        # one string
        assert 250.0 == pytest.approx(feedin.values[0], 1e-5)

    def test_pvlib_feedin_with_optional_model_parameters(
            self, pvlib_pv_system, pvlib_weather):
        """
        Test basic feedin calculation using pvlib and providing an optional
        PV system parameter.
        """
        pvlib_pv_system['strings_per_inverter'] = 2
        test_module = Photovoltaic(**pvlib_pv_system)
        feedin = test_module.feedin(weather=pvlib_weather, location=(52, 13),
                                    mode='dc')
        # power output is in this case limited by the inverter, which is why
        # power output with 2 strings is not twice as high as power output of
        # one string
        assert 298.27921 == pytest.approx(feedin.values[0], 1e-5)

    def test_pvlib_missing_powerplant_parameter(self, pvlib_pv_system):
        """
        Test if initialization of powerplant fails in case of missing power
        plant parameter.
        """
        del(pvlib_pv_system['albedo'])
        msg = "The specified model 'pvlib' requires"
        with pytest.raises(AttributeError, match=msg):
            Photovoltaic(**pvlib_pv_system)


class TestWindpowerlibSingleTurbine(Fixtures):
    """
    Class to test WindpowerlibTurbine model.
    """

    def test_windpowerlib_single_turbine_feedin(
            self, windpowerlib_turbine, windpowerlib_weather):
        """
        Test basic feedin calculation using windpowerlib single turbine.
        It is also tested if dictionary with turbine parameters remains the
        same to make sure it could be further used to calculate feed-in with
        a different model.
        """
        test_copy = deepcopy(windpowerlib_turbine)
        test_turbine = WindPowerPlant(**windpowerlib_turbine)
        feedin = test_turbine.feedin(weather=windpowerlib_weather)
        assert 833050.32551 == pytest.approx(feedin.values[0], 1e-5)
        assert test_copy == windpowerlib_turbine

    def test_windpowerlib_single_turbine_feedin_with_optional_pp_parameter(
            self, windpowerlib_turbine, windpowerlib_weather):
        """
        Test basic feedin calculation using windpowerlib single turbine and
        using optional parameters for power plant and modelchain.
        """
        windpowerlib_turbine['rotor_diameter'] = 82
        test_turbine = WindPowerPlant(**windpowerlib_turbine)
        feedin = test_turbine.feedin(
            weather=windpowerlib_weather,
            power_output_model='power_coefficient_curve')
        assert 847665.85209 == pytest.approx(feedin.values[0], 1e-5)

    def test_windpowerlib_missing_powerplant_parameter(
            self, windpowerlib_turbine):
        """
        Test if initialization of powerplant fails in case of missing power
        plant parameter.
        """
        del(windpowerlib_turbine['turbine_type'])
        msg = "The specified model 'windpowerlib_single_turbine' requires"
        with pytest.raises(AttributeError, match=msg):
            WindPowerPlant(**windpowerlib_turbine)


class TestWindpowerlibCluster(Fixtures):
    """
    Class to test WindpowerlibTurbineCluster model.
    """

    def test_windpowerlib_windfarm_feedin(
            self, windpowerlib_farm, windpowerlib_weather):
        """
        Test basic feedin calculation using windpowerlib wind turbine cluster
        modelchain for a wind farm where wind turbine data is provided in a
        dictionary.
        It is also tested if dataframe with wind turbine fleet remains the
        same to make sure it could be further used to calculate feed-in with
        a different model.
        """
        test_copy = deepcopy(windpowerlib_farm)
        farm = WindPowerPlant(**windpowerlib_farm,
                              model=WindpowerlibTurbineCluster)
        feedin = farm.feedin(weather=windpowerlib_weather,
                             wake_losses_model=None)
        assert 7658841.386277 == pytest.approx(feedin.values[0], 1e-5)
        assert_frame_equal(test_copy['wind_turbine_fleet'],
                           windpowerlib_farm['wind_turbine_fleet'])

    def test_windpowerlib_windfarm_feedin_2(
            self, windpowerlib_farm_3, windpowerlib_weather):
        """
        Test basic feedin calculation using windpowerlib wind turbine cluster
        modelchain for a wind farm where wind turbines are provided as
        feedinlib WindPowerPlant objects.
        It is also tested if dataframe with wind turbine fleet remains the
        same to make sure it could be further used to calculate feed-in with
        a different model.
        """
        test_copy = deepcopy(windpowerlib_farm_3)
        farm = WindPowerPlant(**windpowerlib_farm_3,
                              model=WindpowerlibTurbineCluster)
        feedin = farm.feedin(weather=windpowerlib_weather,
                             wake_losses_model=None)
        assert 7658841.386277 == pytest.approx(feedin.values[0], 1e-5)
        assert_frame_equal(test_copy['wind_turbine_fleet'],
                           windpowerlib_farm_3['wind_turbine_fleet'])

    def test_windpowerlib_turbine_cluster_feedin(
            self, windpowerlib_turbine_cluster, windpowerlib_weather):
        """
        Test basic feedin calculation using windpowerlib wind turbine cluster
        modelchain for a wind turbine cluster.
        """
        test_cluster = WindPowerPlant(**windpowerlib_turbine_cluster,
                                      model=WindpowerlibTurbineCluster)
        feedin = test_cluster.feedin(weather=windpowerlib_weather)
        assert 7285008.02048 == pytest.approx(feedin.values[0], 1e-5)

    def test_windpowerlib_windfarm_feedin_with_optional_parameters(
            self, windpowerlib_farm, windpowerlib_weather):
        """
        Test basic feedin calculation using windpowerlib wind turbine cluster
        modelchain and supplying an optional power plant and modelchain
        parameter.
        """

        # test optional parameter
        test_farm = windpowerlib_farm
        test_farm['efficiency'] = 0.9
        farm = WindPowerPlant(**test_farm, model=WindpowerlibTurbineCluster)
        feedin = farm.feedin(weather=windpowerlib_weather,
                             wake_losses_model='wind_farm_efficiency')
        assert 6892957.24764 == pytest.approx(feedin.values[0], 1e-5)

    def test_windpowerlib_turbine_equals_windfarm(
            self, windpowerlib_turbine, windpowerlib_farm_2,
            windpowerlib_weather):
        """
        Test if wind turbine feedin calculation yields the same as wind farm
        calculation with one turbine.
        """
        # turbine feedin
        test_turbine = WindPowerPlant(**windpowerlib_turbine)
        feedin = test_turbine.feedin(weather=windpowerlib_weather)
        # farm feedin
        test_farm = WindPowerPlant(
            **windpowerlib_farm_2, model=WindpowerlibTurbineCluster)
        feedin_farm = test_farm.feedin(weather=windpowerlib_weather,
                                       wake_losses_model=None)
        assert feedin.values[0] == pytest.approx(feedin_farm.values[0], 1e-5)

    def test_windpowerlib_windfarm_equals_cluster(
            self, windpowerlib_farm, windpowerlib_weather):
        """
        Test if windfarm feedin calculation yields the same as turbine cluster
        calculation with one wind farm.
        """
        # farm feedin
        test_farm = WindPowerPlant(
            **windpowerlib_farm, model=WindpowerlibTurbineCluster)
        feedin_farm = test_farm.feedin(weather=windpowerlib_weather)
        # turbine cluster
        test_cluster = {'wind_farms': [windpowerlib_farm]}
        test_cluster = WindPowerPlant(
            **test_cluster, model=WindpowerlibTurbineCluster)
        feedin_cluster = test_cluster.feedin(weather=windpowerlib_weather)
        assert feedin_farm.values[0] == pytest.approx(
            feedin_cluster.values[0], 1e-5)
