import pandas as pd
import os
from feedinlib import tools
from feedinlib import Photovoltaic, WindPowerPlant


def pv_feedin_distribution_register(distribution_dict,
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

    # lese Wetterdaten ein und preprocessing todo: hier Openfred-daten einsetzen

    output = pd.Series()
    filename = os.path.abspath(
        "/home/local/RL-INSTITUT/inia.steinbach/mount_ordner/04_Projekte/163_Open_FRED/03-Projektinhalte/AP2 Wetterdaten/open_FRED_TestWetterdaten_csv/fred_data_test_2016.csv")
    if not os.path.isfile(filename):
        raise FileNotFoundError("Please adjust the path.")
    weather_df = pd.read_csv(filename, skiprows=range(1, 50), nrows=(5000),
                             index_col=0,
                             date_parser=lambda idx: pd.to_datetime(idx,
                                                                    utc=True))
    weather_df.index = pd.to_datetime(weather_df.index).tz_convert(
        'Europe/Berlin')
    # temperature in degree Celsius instead of Kelvin
    # weather_df['temp_air'] = weather_df.temp_air - 273.15
    # calculate ghi
    weather_df['ghi'] = weather_df.dirhi + weather_df.dhi
    # weather_df.rename(columns={'v_wind': 'wind_speed'}, inplace=True)
    df = weather_df.dropna()

    register_pv_locations = tools.add_weather_locations_to_register(
        register=register, weather_coordinates=weather_df)

    # calculate installed capacity per weathercell
    installed_capacity = register_pv_locations.groupby(
        ['weather_lat', 'weather_lon'])['capacity'].agg('sum').reset_index()
    print('installierte Leitung:', installed_capacity['capacity'])

    for index, row in installed_capacity.iterrows():
        for key in technical_parameters.keys():
            module = technical_parameters[key]
            pv_system = Photovoltaic(**module)
            lat = row['weather_lat']
            lon = row['weather_lon']
            weather = df.loc[(df['lat'] == lat) & (df['lon'] == lon)]
            # calculate the feedin and set the scaling to 'area' or 'peak_power'
            feedin = pv_system.feedin(
                weather=weather[
                    ['wind_speed', 'temp_air', 'dhi', 'dirhi', 'ghi']],
                location=(lat, lon))
            feedin_scaled = pv_system.feedin(
                weather=weather[
                    ['wind_speed', 'temp_air', 'dhi', 'dirhi', 'ghi']],
                location=(lat, lon), scaling='peak_power', scaling_value=1)
            # get the distribution for the pv_module
            dist = distribution_dict[key]
            local_installed_capacity = row['capacity']
            # scale the output with the module_distribution and the local installed capacity
            module_feedin = feedin_scaled.multiply(
                dist * local_installed_capacity)

            #        # add the module output to the output series
            output = output.add(other=module_feedin, fill_value=0).rename('feedin')

    return output
