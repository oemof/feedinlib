import xarray as xr # todo add to setup
import numpy as np
import pandas as pd

from feedinlib import tools
from feedinlib import WindPowerPlant

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
        register : dataframe mit Standort und installierter Leistung für jede
            Anlage
        assignment_func : Funktion, die Anlagen in einer Wetterzelle mit
            Information zu Leistung und Standort sowie die mittl.
            Windgeschwindigkeit der Wetterzelle bekommt und jeder Anlage einen
            Typ und eine Nabenhöhe zuordnet
        snapshots : Zeitschritte, für die Einspeisung berechnet werden soll

        power_curves : optional, falls eigene power_curves vorgegeben werde
            sollen
        :return: feedin
            absolute Einspeisung für Region
        """
        # todo @Birgit: parameters in **kwargs? f.e. 'fetch_turbine'
        tools.add_weather_locations_to_register(
            register=register,
            weather_coordinates=self.weather)
        # todo: use function for retrieving all possible weather locations as
        #  df[['lat', 'lon']] instead of the above
        # register=register, weather_coordinates=self.weather.locations)
        weather_locations = register[['weather_lat', 'weather_lon']].groupby(
            ['weather_lat', 'weather_lon']).size().reset_index().drop([0],
                                                                      axis=1)
        # initialize wind turbine objects for each turbine type in register
        turbine_data = register.groupby(
            ['turbine_type', 'hub_height',
             'rotor_diameter']).size().reset_index().drop(0, axis=1).rename(
            columns={'turbine_type': 'name'})
        # turbine = WindPowerPlant(fetch_curve='power_curve',
        #                          **dict(turbine_data.loc[0])) # todo delete
        turbine_data['turbine'] = turbine_data.apply(
            lambda x: WindPowerPlant(fetch_curve='power_curve',
                                     **dict(x)), axis=1) # todo fetch_curve und andere parameter wo?
        turbine_data.index = turbine_data[['name', 'hub_height',
             'rotor_diameter']].apply(lambda x: '_'.join(x), axis=1)
        turbines_region = dict(turbine_data['turbine'])
        feedin_df = pd.DataFrame()
        for weather_location in [list(weather_locations.iloc[index])
                                 for index in weather_locations.index]:
            # select power plants belonging to weather location
            power_plants = register.loc[
                (register['weather_lat'] == weather_location[0]) & (
                    register['weather_lon'] == weather_location[1])]  # todo: nicer way?
            # todo: assignment func
            # prepare power plants for windpowerlib TurbineClusterModelChain
            # todo HIER WEITER: klare turbine id in register!!!! dann einfach anlage aus dict auswählen.
            turbines_weather = pd.merge(power_plants.groupby(
                ['turbine_type', 'hub_height',
                 'rotor_diameter']).size().reset_index().drop(0,
                                                              axis=1).rename(
                columns={'turbine_type': 'name'}), turbines_region, how='inner', left_on='')


                # for  group in groupby
                    # sum up capacity
                    # amount of turbines of one turbine type
                # initialize wind farm
                # run TurbineClusterModelChain
            # turbine.feedin(weather=self.weather)
            # todo: if nur ein turbine_type --> ModelChain verwenden??
            feedin_df = pd.concat(feedin_df, feedin)

        feedin = feedin_df.sum(axis=1)

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

def pv_feedin_distribution_register(self, distribution_dict, technical_parameters, register):
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
    # define the output series
    feedin = pd.series()
    
    # -> weise jeder Anlage eine Wetterzelle zu (pd.cut) bzw. ersetze lat,lon mit Wetter-Koordinaten 
        
    #calculate installed capacity per weathercell
    installed_capacity= register.groupby(['lat', 'lon'])['capacity'].agg('sum')
    
    # -> for weather_cell in register

    #   for each pvsystem initialize the PVSystem
    for key in technical_parameters:
        module_dict = technical_parameters[key]
        pv_system = Photovoltaic(**module_dict)

        #calculate the feedin and set the scaling to 'area' or 'peak_power'
        feedin_scaled = pv_system.feedin(
                weather=weather_df[['wind_speed', 'temp_air', 'dhi', 'dirhi', 'ghi']],
                location=(lat, lon),
                scaling='peak_power', scaling_value=1)

        # get the distribution for the pv_module
        dist = distribution_dict[key]
        # get the local total installed capacity
        local_installed_capacity = installed_capacity['lat', 'lon']
        # scale the output with the module_distribution and the local installed capacity
        module_feedin = feedin_scaled.multiply(dist * local_installed_capacity)
        # add the module output to the output series
        feedin = output.add(module_feedin)
    # return the total feedin time series
    return feedin


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

    def pv_feedin_distribution_register(self, distribution_dict, technical_parameters, register):
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
        # for weather_cell in register
        #   initialisiere Location
        #       for each pvsystem
        #           rufe die pvlib ModelChain auf
        #       erstelle eine normierte Zeitreihe entsprechend der Gewichtung
        #       skaliere die normierte Zeitreihe mit gesamt installierter Leistung
        #  return feedin
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

