import pandas as pd


# This helper checks a few likely column names in the dataset and grabs the first
# one that actually exists. That keeps the code resilient when EPA field names are
# not perfectly consistent across rows.
def _get_value(vehicle, *candidate_keys):
    """Return the first matching EPA field from a vehicle row."""
    for key in candidate_keys:
        if key in vehicle.index:
            return vehicle[key]

    return pd.NA


# A lot of vehicle data has blanks or odd values in it, so this makes sure we can
# convert numbers safely without the code crashing on missing entries.
def _safe_float(value, default=0.0):
    """Convert a value to a float and return a safe default if it is missing."""
    if pd.isna(value):
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# This function decides what kind of vehicle we are looking at before we do any
# cost math. It is the logic gate that tells the app whether to use gasoline,
# electric, or hybrid formulas.
def vehicle_type(vehicle):
    """Identify whether the vehicle is BEV, PHEV, hybrid, or gasoline."""
    fuel_type = _get_value(vehicle, "fuelType1", "fuelType")
    utility_factor = _get_value(vehicle, "combinedUF", "combinedCD")
    drive_type = _get_value(vehicle, "atvType", "atvtype")

    if str(fuel_type).strip().lower() == "electricity":
        return "BEV"

    if pd.notna(utility_factor):
        return "PHEV"

    if "Hybrid" in str(drive_type):
        return "Hybrid"

    return "ICE"


# Gas vehicles are priced using MPG, so this function turns fuel economy into a
# cost-per-mile estimate based on the gas price the user selected.
def gas_cost_per_mile(mpg, gas_price):
    """Estimate the fuel cost per mile for a gasoline vehicle."""
    mpg = _safe_float(mpg)
    gas_price = _safe_float(gas_price)

    if mpg <= 0:
        return 0.0

    return gas_price / mpg


# Electric vehicle cost is based on how many kWh the vehicle uses for 100 miles,
# then we multiply that by the electricity rate to get a per-mile cost.
def ev_cost_per_mile(kwh100, electric_rate):
    """Estimate the cost per mile for an electric vehicle."""
    kwh100 = _safe_float(kwh100)
    electric_rate = _safe_float(electric_rate)

    if kwh100 <= 0:
        return 0.0

    return (kwh100 / 100) * electric_rate


# Plug-in hybrids are a little more nuanced because they use both electricity and
# gasoline. This function blends those two costs based on the vehicle's utility
# factor, which represents how much of the driving is powered by electricity.
def phev_cost_per_mile(
    utility_factor,
    kwh100,
    electric_rate,
    mpg,
    gas_price
):
    """Blend electric and gasoline cost for a plug-in hybrid."""
    utility_factor = _safe_float(utility_factor)
    kwh100 = _safe_float(kwh100)
    electric_rate = _safe_float(electric_rate)
    mpg = _safe_float(mpg)
    gas_price = _safe_float(gas_price)

    electric_cost = (kwh100 / 100) * electric_rate
    gas_cost = gas_price / mpg if mpg > 0 else 0.0

    return (utility_factor * electric_cost) + ((1 - utility_factor) * gas_cost)


# This is the main decision point. It reads the vehicle type and then sends the
# data through the right formula so the app can compare costs across vehicle types.
def calculate_cost_per_mile(vehicle, gas_price, electric_rate):
    """Return the estimated cost per mile for the selected vehicle type."""
    vtype = vehicle_type(vehicle)
    comb_e = _safe_float(_get_value(vehicle, "combE"))
    utility_factor = _safe_float(_get_value(vehicle, "combinedUF", "combinedCD"))
    comb_mpg = _safe_float(_get_value(vehicle, "comb08"))

    if vtype == "BEV":
        return ev_cost_per_mile(comb_e, electric_rate)

    if vtype == "PHEV":
        return phev_cost_per_mile(
            utility_factor,
            comb_e,
            electric_rate,
            comb_mpg,
            gas_price,
        )

    return gas_cost_per_mile(comb_mpg, gas_price)
