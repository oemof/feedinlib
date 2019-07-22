import xarray as xr # todo add to setup
import numpy as np
import pandas as pd

import os
from feedinlib import tools
from feedinlib import Photovoltaic, WindPowerPlant
from feedinlib.models import WindpowerlibTurbine
from feedinlib.models import WindpowerlibTurbineCluster

# delete these imports after windpowerlib integration
from windpowerlib.wind_turbine import WindTurbine
from windpowerlib.wind_farm import WindFarm
from windpowerlib.turbine_cluster_modelchain import TurbineClusterModelChain


class Region:
    """
    can also be multi-region
    """
    def __init__(self, geom, weather):
        """

        :param geom: polygon
        :param weather: Weather Objekt
        """
        self.geom = geom
        self.weather = weather

    def wind_feedin(self, register, assignment_func=None, snapshots=None,
                    **kwargs):
        """
        Bekommt Anlagenregister wie MaStR oder bekommt Anlagenregister wie OPSD
        und macht über assignment_func Annahme welche Anlage installiert ist,
        z.B. über mittlere Windgeschwindigkeit oder Anlagenleistung...

        Parameters
        ------------
        register : pd.DataFrame
            Contains power plant data and location of each power plant in columns
            'lat' (latitude) and 'lon' (longitude). Required power plant data:
            turbine type in column 'name', hub height in m in column 'hub_height'.
            Optional data: rotor diameter in m in 'rotor_diameter'.
            todo what about nominal power - comes from oedb. Aber wenn eigene leistungskurve angegeben wird...?
        assignment_func : Funktion, die Anlagen in einer Wetterzelle mit
            Information zu Leistung und Standort sowie die mittl.
            Windgeschwindigkeit der Wetterzelle bekommt und jeder Anlage einen
            Typ und eine Nabenhöhe zuordnet
        snapshots : Zeitschritte, für die Einspeisung berechnet werden soll

        Other parameters
        ----------------
        power_curves : optional, falls eigene power_curves vorgegeben werde
            sollen
            .... copy from windpowerlib --> ModelChain parameters

        Returns
        -------
        feedin : pd.Series
            Absolute feed-in of wind power plants in region in todo: unit W.

        """
        register = tools.add_weather_locations_to_register(
            register=register, weather_coordinates=self.weather)
        # todo: use function for retrieving all possible weather locations as
        #  df[['lat', 'lon']] instead of the above
        # register=register, weather_coordinates=self.weather.locations)
        weather_locations = register[['weather_lat', 'weather_lon']].groupby(
            ['weather_lat', 'weather_lon']).size().reset_index().drop([0],
                                                                      axis=1)
        # get turbine types (and data) from register
        turbine_data = register.groupby(
            ['name', 'hub_height',
             'rotor_diameter']).size().reset_index().drop(0, axis=1)
        # initialize wind turbine objects for each turbine type in register
        turbine_data['turbine'] = turbine_data.apply(
            lambda x: WindPowerPlant(model=WindpowerlibTurbine,
                                     power_curve=True,
                                     nominal_power=True, **x), axis=1)
        # turbine_data['turbine'] = turbine_data.apply(
        #     lambda x: WindPowerPlant(fetch_curve='power_curve',
        #                              **x), axis=1) # todo fetch_curve und andere parameter wo?
        turbine_data.index = turbine_data[['name', 'hub_height',
             'rotor_diameter']].applymap(str).apply(lambda x: '_'.join(x),
                                                    axis=1)
        turbines_region = dict(turbine_data['turbine'])

        region_feedin_df = pd.DataFrame()
        for weather_location, weather_index in zip([list(weather_locations.iloc[index])
                                 for index in weather_locations.index],
                                    weather_locations.index): # todo: weather id....
            # select power plants belonging to weather location
            power_plants = register.loc[
                (register['weather_lat'] == weather_location[0]) & (
                    register['weather_lon'] == weather_location[1])]  # todo: nicer way?
            # todo: assignment func
            # prepare power plants for windpowerlib TurbineClusterModelChain
            turbine_types_location = power_plants.groupby(
                'id').size().reset_index().drop(0, axis=1)
            wind_farm_data = {'name': 'todo',
                              'wind_turbine_fleet': []}
            for turbine_type in turbine_types_location['id']:
                capacity = power_plants.loc[
                    power_plants['id'] == turbine_type]['capacity'].sum()  # todo check capacpity of opsd register
                wind_farm_data['wind_turbine_fleet'].append(
                    {'wind_turbine': turbines_region[turbine_type],
                'number_of_turbines': capacity/turbines_region[turbine_type].nominal_power}) # todo: adapt to feedinlib WindPowerPlant

            # initialize wind farm and run TurbineClusterModelChain
            # todo: WindFarm model in feedinlib
            # todo: windpowerlib specific part from here in feedin()
            # todo: if nur ein turbine_type --> ModelChain verwenden??
            wind_farm = WindPowerPlant(model=WindpowerlibTurbineCluster, **wind_farm_data)
            # select weather of weather location and drop location index
            weather = self.weather.loc[
                (self.weather.index.get_level_values('lat') ==
                 weather_location[0]) & (
                        self.weather.index.get_level_values('lon') ==
                        weather_location[1])].droplevel(level=[1, 2])
            feedin_ts = TurbineClusterModelChain(wind_farm,
                                                 **kwargs).run_model(
                weather).power_output
            feedin_df = pd.DataFrame(data=feedin_ts).rename(
                columns={feedin_ts.name: 'feedin_{}'.format(weather_index)})
            region_feedin_df = pd.concat([region_feedin_df, feedin_df], axis=1)
        feedin = region_feedin_df.sum(axis=1).rename('feedin')
        # todo delete skeleton:
        # weise jeder Anlage eine Wetterzelle zu
        # for weather_cell in self.weather_cells
        #   filtere Anlagen in Wetterzelle
        #   wenn spezifiziert wähle Anlage mit assignment func
        #   aggregiere Leistungskurven der anlagen in register (wird in Modelchain gemacht)
        #   berechne mittlere Nabenhöhe? (wird in Modelchain gemacht)
        #   rufe die windpowerlib Cluster ModelChain auf (evtl. bei nur einer
        #       Anlage einfache ModelChain?)
        # summiere feedin über alle Zellen
        # return feedin
        return feedin

    def pv_feedin_distribution_register(self, distribution_dict,
                                    technical_parameters, register):
        """
        Innerhalb eines Wetterpunktes werden die Anlagen entsprechend des
        distribution_dict gewichtet. Jeder Wetterpunkt wird entsprechend der
        installierten Leistung nach Anlagenregister skaliert und anschließend
        eine absolute Zeitreihe für die Region zurück gegeben.

        Parameters
        ----------
        distribution_dict : dict
            Dict mit Anlagentyp und Anteil
            {'1': 0.6, 2: 0.4}
        technical_parameters : dict oder Liste mit PVSystems
            Dict mit Inverter, Ausrichtung, etc. der Module (alles was PVSystem
            benötigt)
        register : dataframe mit Standort und installierter Leistung für jede
            Anlage
        :return:
            absolute Einspeisung für Region
        """

        #lese Wetterdaten ein und preprocessing todo: hier Openfred-daten einsetzen

        output=pd.Series()
        register_pv_locations = tools.add_weather_locations_to_register(
            register=register, weather_coordinates=self.weather)

        # calculate installed capacity per weathercell
        installed_capacity = register_pv_locations.groupby(
            ['weather_lat', 'weather_lon'])['capacity'].agg('sum').reset_index()

        for index, row in installed_capacity.iterrows():
            for key in technical_parameters.keys():
                module = technical_parameters[key]
                pv_system = Photovoltaic(**module)
                lat = row['weather_lat']
                lon = row['weather_lon']
                weather_df = self.weather.loc[(self.weather['lat'] == lat)
                                              & (self.weather['lon'] == lon)]
                # calculate the feedin and set the scaling to 'area' or 'peak_power'
                feedin = pv_system.feedin(
                    weather=weather_df[
                        ['wind_speed', 'temp_air', 'dhi', 'dirhi', 'ghi']],
                    location=(lat, lon))
                feedin_scaled = pv_system.feedin(
                    weather=weather_df[
                        ['wind_speed', 'temp_air', 'dhi', 'dirhi', 'ghi']],
                    location=(lat, lon), scaling='peak_power', scaling_value=10)
                # get the distribution for the pv_module
                dist = distribution_dict[key]
                local_installed_capacity = row['capacity']
                # scale the output with the module_distribution and the local installed capacity
                module_feedin = feedin_scaled.multiply(
                    dist * local_installed_capacity)
                #        # add the module output to the output series
                output = output.add(other=module_feedin, fill_value=0).rename('feedin')
                output[output < 0] = 0

        return output.fillna(0)

    def pv_feedin(self, register, assignment_func=None, **kwargs):
        """
        Bekommt Anlagenregister wie MaStR oder OPSD
        und macht über assignment_func Annahme welche Anlage installiert ist,
        z.B. über Anlagenleistung...

        Parameters
        ------------
        register : dataframe mit Standort und installierter Leistung für jede
            Anlage
        assignment_func : Funktion, die Anlagen in einer Wetterzelle mit
            Information zu Leistung und Standort bekommt und jeder Anlage einen
            Modultyp, Wechselrichter, Ausrichtung, Neigung und Albedo zuordnet

        :return: feedin
            absolute Einspeisung für Region
        """
        # weise jeder Anlage eine Wetterzelle zu (pd.cut)
        # for weather_cell in self.weather_cells
        #   filtere Anlagen in Wetterzelle
        #   (wenn spezifiziert, wähle Anlage mit assignment func - nicht notwendig)
        #   aggregiere anlagen wenn möglich? groupby(['tilt', 'azimuth'...])
        #       für jede Anlagenkonfiguration
        #           initialisiere PVSystem
        #           berechne feedin, skaliert auf installierte Leistung
        #       summiere feedin über alle Anlagenkonfigurationen
        # summiere feedin über alle Zellen
        # return feedin
        pass


    def pv_feedin_distribution_rule(self, distribution_dict, technical_parameters, rule):
        """
        Innerhalb eines Wetterpunktes werden die Anlagen entsprechend des
        distribution_dict gewichtet. Jeder Wetterpunkt wird entsprechend der
        installierten Leistung nach Anlagenregister skaliert und anschließend
        eine absolute Zeitreihe für die Region zurück gegeben.

        Parameters
        ----------
        distribution_dict : dict
            Dict mit Anlagentyp und Anteil
            {'1': 0.6, 2: 0.4}
        technical_parameters : dict oder Liste mit PVSystems
            Dict mit Inverter, Ausrichtung, etc. der Module (alles was PVSystem
            benötigt)
        register : dataframe mit Standort und installierter Leistung für jede
            Anlage
        :return:
            absolute Einspeisung für Region
        """
        # (PVSystem initialisieren)
        # for weather_cell in rule
        #   initialisiere Location
        #       for each pvsystem
        #           rufe die pvlib ModelChain auf
        #       erstelle eine normierte Zeitreihe entsprechend der Gewichtung
        #       skaliere die normierte Zeitreihe entsprechend der rule Fkt.
        #  return feedin
        pass


def assignment_func_mean_wind_speed(register, weather):
    """
    todo move function from feedin_germany here (assign_turbine_data_by_wind_zone)
        after windzones were loaded into oedb
    :param register:
    :param weather: Dataarray mit Wetter einer Wetterzelle
    :return: register mit zusätzlich Anlagentyp und Nabenhöhe
    """
    # berechne avg_wind_speed
    avg_wind_speed = 7
    if avg_wind_speed < 5:
        register[:, 'type'] = 'E-82/2350'
        register[:, 'hub_height'] = 130
    else:
        register[:, 'type'] = 'E-101/3050'
        register[:, 'hub_height'] = 100
    return register

