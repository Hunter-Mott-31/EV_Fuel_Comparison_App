import pandas as pd


def _get_value(vehicle, *candidate_keys):

    for key in candidate_keys:
        if key in vehicle.index:
            return vehicle[key]

    return pd.NA


def vehicle_type(vehicle):

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


def gas_cost_per_mile(mpg, gas_price):

    return gas_price / mpg


def ev_cost_per_mile(kwh100, electric_rate):

    return (kwh100 / 100) * electric_rate


def phev_cost_per_mile(
    utility_factor,
    kwh100,
    electric_rate,
    mpg,
    gas_price
):

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

    vtype = vehicle_type(vehicle)
    comb_e = _get_value(vehicle, "combE")
    utility_factor = _get_value(vehicle, "combinedUF", "combinedCD")
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