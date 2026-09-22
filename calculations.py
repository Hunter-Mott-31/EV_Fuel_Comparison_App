import pandas as pd
 
 
def _get_value(vehicle, *candidate_keys):
"""
Return the first matching value from a vehicle record.
 
EPA datasets can use different column names across years and
data extracts. This helper allows the rest of the code to
look for multiple possible column names without duplicating logic.
 
Parameters
----------
vehicle : pandas.Series
Vehicle record.
*candidate_keys : str
Possible column names for a given attribute.
 
Returns
-------
Any
Matching value if found, otherwise pd.NA.
"""
for key in candidate_keys:
if key in vehicle.index:
return vehicle[key]
 
return pd.NA
 
 
def vehicle_type(vehicle):
"""
Classify a vehicle's powertrain type.
 
Classification hierarchy:
1. BEV (Battery Electric Vehicle)
2. PHEV (Plug-In Hybrid Electric Vehicle)
3. Hybrid
4. ICE (Internal Combustion Engine)
 
Parameters
----------
vehicle : pandas.Series
Vehicle record.
 
Returns
-------
str
Vehicle type category.
"""
 
fuel_type = _get_value(vehicle, "fuelType1", "fuelType")
utility_factor = _get_value(vehicle, "combinedUF", "combinedCD")
drive_type = _get_value(vehicle, "atvType", "atvtype")
 
# Pure electric vehicles.
if str(fuel_type).strip().lower() == "electricity":
return "BEV"
 
# Utility factor is typically only populated for PHEVs.
if pd.notna(utility_factor):
return "PHEV"
 
# Standard hybrid vehicles.
if "Hybrid" in str(drive_type):
return "Hybrid"
 
# Everything else is treated as a traditional combustion vehicle.
return "ICE"
 
 
def gas_cost_per_mile(mpg, gas_price):
"""
Calculate estimated fuel cost per mile for a gasoline vehicle.
 
Formula:
Cost Per Mile = Gas Price / MPG
 
Parameters
----------
mpg : float
Combined fuel economy.
gas_price : float
Price per gallon.
 
Returns
-------
float
Cost per mile.
"""
return gas_price / mpg
 
 
def ev_cost_per_mile(kwh100, electric_rate):
"""
Calculate operating cost per mile for an electric vehicle.
 
EPA efficiency is reported as kWh per 100 miles, so it must
be converted to kWh per mile before applying the electricity rate.
 
Formula:
Cost Per Mile = (kWh per 100 miles / 100) * Electricity Rate
 
Parameters
----------
kwh100 : float
Electricity consumption per 100 miles.
electric_rate : float
Cost per kWh.
 
Returns
-------
float
Cost per mile.
"""
return (kwh100 / 100) * electric_rate
 
 
def phev_cost_per_mile(
utility_factor,
kwh100,
electric_rate,
mpg,
gas_price
):
"""
Calculate blended operating cost per mile for a plug-in hybrid.
 
Utility Factor represents the percentage of miles expected
to be driven using electricity. The remaining miles are
assumed to be driven using gasoline.
 
Parameters
----------
utility_factor : float
Share of miles driven electrically.
kwh100 : float
Electricity consumption per 100 miles.
electric_rate : float
Cost per kWh.
mpg : float
Fuel economy when running on gasoline.
gas_price : float
Price per gallon.
 
Returns
-------
float
Blended cost per mile.
"""
 
electric_cost = (
kwh100 / 100
) * electric_rate
 
gas_cost = (
gas_price / mpg
)
 
return (
utility_factor * electric_cost
+
(1 - utility_factor) * gas_cost
)
 
 
def calculate_cost_per_mile(
vehicle,
gas_price,
electric_rate
):
"""
Calculate vehicle operating cost per mile.
 
This function serves as the main entry point for vehicle
fuel-cost analysis. It determines the vehicle type and
applies the appropriate cost calculation method.
 
Parameters
----------
vehicle : pandas.Series
Vehicle record from the EPA dataset.
gas_price : float
Gasoline price per gallon.
electric_rate : float
Electricity price per kWh.
 
Returns
-------
float
Estimated operating cost per mile.
"""
 
# Determine vehicle powertrain category.
vtype = vehicle_type(vehicle)
 
# EPA combined electricity consumption (kWh/100 miles).
comb_e = _get_value(vehicle, "combE")
 
# Utility factor used for PHEV blended calculations.
utility_factor = _get_value(
vehicle,
"combinedUF",
"combinedCD"
)
 
# EPA combined fuel economy in MPG.
comb_mpg = _get_value(vehicle, "comb08")
 
if vtype == "BEV":
 
return ev_cost_per_mile(
comb_e,
electric_rate
)
 
elif vtype == "PHEV":
 
return phev_cost_per_mile(
utility_factor,
comb_e,
electric_rate,
comb_mpg,
gas_price
)
 
else:
 
return gas_cost_per_mile(
comb_mpg,
gas_price
)
