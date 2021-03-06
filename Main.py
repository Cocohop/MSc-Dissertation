from datetime import datetime
import pytz
import numpy as np
import pandas as pd
import pvlib
from matplotlib import pyplot as plt
from pandas.plotting import register_matplotlib_converters
from RenewableNinjaAPI import get_ninja_data
from Finance import financial_calculator

class SolarCell(object):

    def __init__(self, solar_cell_data, inverter_location, maximum_power, loc=[52.4068, 1.5197], tilt=0,
                 azimuth=180, pv_array_size = 1):
        self.solar_cell = solar_cell_data
        self.solar_cell["GHI"] = self.solar_cell["GHI"]*pv_array_size
        self.inverter = pd.read_csv(inverter_location)
        # This line is to fix the output power issue encountered in efficiency curves.
        # That is, it turns output power on the x-axis to input power
        self.inverter["Percent"] = self.inverter["Percent"] / (self.inverter["Efficiency"]/100)
        self.max_power = maximum_power
        self.loc = loc
        self.tilt = tilt
        self.azimuth = azimuth
        self.panel = 0

    def return_cell(self):
        return self.solar_cell

    def invert(self, option="None"):
        if option == "percent":
            self.inverter["Percent"] = self.inverter["Percent"] * self.max_power / 100
        elif option == "normalise":
            self.inverter["Percent"] = (self.inverter["Percent"] / self.inverter["Percent"].max()) * self.max_power
        for i in range(len(self.solar_cell)):
            GHIValue = self.solar_cell["GHI"].iloc[i]
            dateandtimeValue = self.solar_cell.index[i]
            # Gets index of Row
            result_index = self.inverter['Percent'].sub(GHIValue).abs().idxmin()
            # Now we need to multiply Efficiency by it.
            self.solar_cell.at[dateandtimeValue, "GHI"] = GHIValue * \
                                                          self.inverter.at[
                                                              result_index, "Efficiency"] / 100
            # Clipping the data
            if self.solar_cell.at[dateandtimeValue, "GHI"] > self.max_power:
                self.solar_cell.at[dateandtimeValue, "GHI"] = self.max_power

    def total_energy(self):
        return self.solar_cell["GHI"].sum()


if __name__ == "__main__":
    # The main event am I right
    inverter_list = ["Fronius_Inverter", "Huawei_Inverter", "SIC_Inverter", "SMA_Inverter","Sungrow_Inverter"]
    orientation_list = np.linspace(90,270, num=5)
    column_names = ["Model", "Orientation", "Mean_Electricity" , "City"]

    coordinates_list = [[28.6139, 77.2090],[39.9042, 116.4074],[35.6762, 139.6503],[36.7783, -119.4179]]
    city_list = ["New Delhi","Beijing","Tokyo","California"]
    for Y in range(len(coordinates_list)):
        output_df = pd.DataFrame(columns=column_names)

        for X in range(len(orientation_list)):
            SC_Data = get_ninja_data(latitude=coordinates_list[Y][0], longitude=coordinates_list[Y][1], azimuth=orientation_list[X])
            for i in range(len(inverter_list)):
                data = SC_Data.copy()
                solar_cell = SolarCell(
                     data,
                     r"D:\Personal Folder\Study\-MSc\Dissertation\Data\Industrial Inverters\\" + str(inverter_list[i]) + ".csv", 10, pv_array_size= 10)
                #money_before = financial_calculator(solar_cell.return_cell())
                solar_cell.invert(option="percent")
                mean = solar_cell.return_cell().mean().values
                output_df.loc[len(output_df)] = [inverter_list[i], orientation_list[X], mean, city_list[Y]]
            print(output_df)
        output_df.sort_values(by = ["Model","Orientation"],inplace=True)
        output_df.to_csv(str("orientation_rectified_2_") + str(city_list[Y]) + str(".csv"))
