import streamlit as st

# To run in terminal:
#   cd C:\Users\again\Downloads\Palo-Alto-Impact-Fee-Calculator
#   python -m streamlit run Palo-Alto-Impact-Fee-Calculator.py
#
# Structure:
#   Pt. 0  Fee schedule (all rates live here)
#   Pt. 1  Project description + exemption checks
#   Pt. 2  Decide which fees apply (exemptions can only turn fees OFF)
#   Pt. 3  Ask only for the inputs those fees need
#   Pt. 4  Calculate
#   Pt. 5  Output breakdown


# ============================================================
# PT. 0 — FEE SCHEDULE
# Source: City of Palo Alto Development Impact and In-Lieu Fees,
# rates as of August 22, 2022 (info sheet updated 10/12/22).
# To use a newer schedule, edit ONLY this block and update
# SCHEDULE_SOURCE so the app shows which rates it uses.
# ============================================================
SCHEDULE_SOURCE = "City of Palo Alto fee sheet, rates as of Aug 22, 2022"

COMMUNITY_FACILITIES_PER_UNIT = {
    "Single Family": {
        "Parks": 62039.67,
        "Community centers": 4795.06,
        "Libraries": 2857.80,
        "Public safety facilities": 1269.00,
        "General government facilities": 1600.00,
    },
    "Multi-Family": {
        "Parks": 45884.72,
        "Community centers": 3547.13,
        "Libraries": 2113.37,
        "Public safety facilities": 1015.00,
        "General government facilities": 1279.00,
    },
}

HOUSING_IN_LIEU_PER_SQFT = {
    "Single family detached": 91.92,
    "Single family attached": 61.28,
    "Condominiums": 61.29,
    "Apartment (rentals)": 24.52,
}

DOWNTOWN_PARKING_PER_SPACE = 124275.00
CHARLESTON_ARASTRADERO_PER_UNIT = 1599.00
CITYWIDE_TRAFFIC_PER_PM_TRIP = 9266.00

PUBLIC_ART_THRESHOLD = 120_250_000
PUBLIC_ART_RATE_BELOW = 0.01
PUBLIC_ART_RATE_ABOVE = 0.009
PUBLIC_ART_MIN_UNITS = 5

PARKLAND_IN_LIEU_PER_UNIT = {"Single Family": 75076.89, "Multi-Family": 51747.91}
PARKLAND_LAND_SQFT_PER_UNIT = {"Single Family": 531, "Multi-Family": 366}
# Sheet: fee if FEWER than 50 parcels, land if MORE than 50.
# Exactly 50 is ambiguous on the sheet; treated here as fee.
PARKLAND_MAX_PARCELS_FOR_FEE = 50

ADU_SIZE_THRESHOLD = 750

FEE_LABELS = {
    "community_facilities": "Community facilities fee",
    "housing": "Housing in-lieu fee",
    "traffic": "Traffic fees",
    "public_art": "Public art fee",
    "parkland": "Parkland dedication in-lieu fee",
}

# Option labels used in more than one place
ADU = "Accessory Dwelling Unit (ADU)"
ADU_SMALL_CONVERSION = "Garage/carport conversion (no FAR expansion) or Junior ADU"
ADU_SMALL = f"ADU under {ADU_SIZE_THRESHOLD} sq ft"
ADU_LARGE = f"ADU {ADU_SIZE_THRESHOLD} sq ft or larger"
REMODEL = "Single-family home remodel or addition"
MULTI_FAMILY = "Multi-family residential"
OTHER = "Non-residential or other"


# ============================================================
# FUNCTIONS
# ============================================================
def calc_community(units, res_type, skip_parks):
    """Per-unit community facilities fee. Parks portion is dropped
    when parkland dedication applies (sheet: park impact fees don't
    apply in that case)."""
    total = 0
    for component, rate in COMMUNITY_FACILITIES_PER_UNIT[res_type].items():
        if skip_parks and component == "Parks":
            continue
        total += rate * units
    return total


def calc_housing(sqft, housing_type):
    return sqft * HOUSING_IN_LIEU_PER_SQFT[housing_type]


def calc_traffic(location, units, parking_spaces_in_lieu, pm_trips):
    location_fee = 0
    if location == "Downtown Assessment District":
        location_fee = parking_spaces_in_lieu * DOWNTOWN_PARKING_PER_SPACE
    elif location == "Charleston/Arastradero corridor":
        location_fee = units * CHARLESTON_ARASTRADERO_PER_UNIT
    return location_fee + pm_trips * CITYWIDE_TRAFFIC_PER_PM_TRIP


def calc_art(valuation, units):
    if units < PUBLIC_ART_MIN_UNITS:
        return 0
    if valuation <= PUBLIC_ART_THRESHOLD:
        return PUBLIC_ART_RATE_BELOW * valuation
    return (PUBLIC_ART_RATE_BELOW * PUBLIC_ART_THRESHOLD
            + PUBLIC_ART_RATE_ABOVE * (valuation - PUBLIC_ART_THRESHOLD))


def calc_parkland_fee(units, res_type):
    return units * PARKLAND_IN_LIEU_PER_UNIT[res_type]


def reset():
    # Clearing session state resets every widget to its default
    st.session_state.clear()


# ============================================================
# HEADER
# ============================================================
st.title("Palo Alto Residential Impact Fee Calculator")
st.write("Welcome! This tool estimates development impact and in-lieu fees "
         "for residential projects in Palo Alto.")
st.caption(f"Rates: {SCHEDULE_SOURCE}.")
st.write("**Disclaimer:** This calculator is for reference only. For official "
         "impact fee calculations, please contact the City of Palo Alto "
         "Planning Department at (650) 329-2116.")
st.write("---")


# ============================================================
# PT. 1 — PROJECT DESCRIPTION
# ============================================================
st.subheader("1. Describe your project")

project_type = st.selectbox(
    "Project type",
    ["New home on an empty parcel", "Second unit", ADU, MULTI_FAMILY, REMODEL, OTHER],
)

if project_type == OTHER:
    st.warning("This calculator only covers residential projects. For commercial, "
               "hotel, institutional, or industrial projects, see the City's fee "
               "schedule or contact the Planning Department.")
    st.stop()

if project_type == REMODEL:
    st.success("Single-family remodels and additions are exempt from every fee "
               "covered here. Total estimated fees: $0.00")
    st.stop()

res_type = "Multi-Family" if project_type == MULTI_FAMILY else "Single Family"

adu_kind = None
if project_type == ADU:
    adu_kind = st.selectbox("Which describes the ADU?",
                            [ADU_SMALL_CONVERSION, ADU_SMALL, ADU_LARGE])
    total_units = 1
else:
    total_units = st.number_input("Total number of net new units",
                                  min_value=1, step=1, value=1)

all_affordable = False
extra_bmr_units = 0
map_used = False
num_parcels = 0

if project_type != ADU:
    all_affordable = st.checkbox("Project is 100% affordable housing")
    if not all_affordable:
        extra_bmr_units = st.number_input(
            "Number of BMR units BEYOND what the inclusionary requirement requires",
            min_value=0, max_value=total_units, step=1,
            help="Required BMR units are exempt only from the housing in-lieu fee. "
                 "BMR units beyond the requirement are also exempt from community "
                 "facilities and traffic fees.",
        )
    map_used = st.checkbox("Project requires a subdivision or parcel map")
    if map_used:
        num_parcels = st.number_input("Number of parcels created",
                                      min_value=1, step=1)

non_exempt_units = total_units - extra_bmr_units


# ============================================================
# PT. 2 — WHICH FEES APPLY
# Step A: base applicability. Step B: exemptions, which may only
# turn fees OFF — nothing later can switch a fee back on.
# ============================================================
applies = {
    "community_facilities": True,
    "housing": True,
    "traffic": True,
    "public_art": total_units >= PUBLIC_ART_MIN_UNITS,
    "parkland": map_used,
}

if project_type == ADU:
    applies["housing"] = False
    applies["traffic"] = False
    applies["parkland"] = False
    if adu_kind != ADU_LARGE:
        applies["community_facilities"] = False

if all_affordable:
    for key in ["community_facilities", "housing", "traffic", "parkland"]:
        applies[key] = False

parkland_mode = None  # "fee" or "land"
if applies["parkland"]:
    if num_parcels > PARKLAND_MAX_PARCELS_FOR_FEE:
        parkland_mode = "land"
    else:
        parkland_mode = "fee"

st.write("---")


# ============================================================
# PT. 3 — INPUTS FOR APPLICABLE FEES
# Every variable gets a default first so nothing is ever undefined.
# ============================================================
st.subheader("2. Project details")

housing_type = None
housing_sqft = 0
adu_sqft = 0
primary_sqft = 1
location = "Elsewhere in Palo Alto"
parking_spaces_in_lieu = 0
pm_trips = 0.0
valuation = 0

if applies["housing"]:
    in_lieu_choice = st.radio(
        "How is the affordable housing requirement being met?",
        ["Required BMR units built on site, or no requirement applies (no in-lieu fee)",
         "Paying the in-lieu fee (fractional unit, or Council has agreed to accept payment)"],
    )
    if in_lieu_choice.startswith("Paying"):
        housing_type = st.selectbox("Housing type", list(HOUSING_IN_LIEU_PER_SQFT))
        housing_sqft = st.number_input(
            "Square footage the in-lieu fee applies to",
            min_value=0, step=100,
            help="Confirm the applicable square footage with the City's Housing "
                 "division; it depends on how the fractional or in-lieu "
                 "obligation is calculated for your project.",
        )
    else:
        applies["housing"] = False

if project_type == ADU and applies["community_facilities"]:
    adu_sqft = st.number_input("ADU square footage",
                               min_value=ADU_SIZE_THRESHOLD, step=10)
    primary_sqft = st.number_input("Primary home square footage",
                                   min_value=1, step=10)

if applies["traffic"]:
    location = st.selectbox(
        "Project location",
        ["Elsewhere in Palo Alto", "Downtown Assessment District",
         "Charleston/Arastradero corridor"],
    )
    if location == "Downtown Assessment District":
        parking_spaces_in_lieu = st.number_input(
            "Required parking spaces NOT provided on site (paid in lieu)",
            min_value=0, step=1,
        )
    pm_trips = st.number_input(
        "Net new PM peak-hour trips",
        min_value=0.0, step=0.1,
        help="Exclude trips generated by BMR units beyond the requirement; "
             "those are exempt.",
    )

if applies["public_art"]:
    valuation = st.number_input("Construction valuation ($)",
                                min_value=0, step=100_000)

st.write("---")


# ============================================================
# PT. 4 — CALCULATE
# ============================================================
fees = {}
notes = {}

if applies["community_facilities"]:
    skip_parks = applies["parkland"]
    if project_type == ADU:
        # State ADU law: fees on ADUs 750+ sq ft must be proportional
        # to the size of the primary home.
        ratio = min(adu_sqft / primary_sqft, 1.0)
        fees["community_facilities"] = calc_community(1, "Single Family", False) * ratio
        notes["community_facilities"] = (f"Proportional: {ratio:.0%} of one "
                                         "single-family unit's fee.")
    else:
        fees["community_facilities"] = calc_community(non_exempt_units, res_type, skip_parks)
        note = f"{non_exempt_units} unit(s) at the {res_type} rate."
        if skip_parks:
            note += " Parks portion removed because parkland dedication applies."
        notes["community_facilities"] = note

if applies["housing"]:
    fees["housing"] = calc_housing(housing_sqft, housing_type)
    notes["housing"] = f"{housing_sqft:,} sq ft at the {housing_type} rate."

if applies["traffic"]:
    fees["traffic"] = calc_traffic(location, non_exempt_units,
                                   parking_spaces_in_lieu, pm_trips)
    notes["traffic"] = "Citywide fee per PM peak trip, plus any location-specific fee."

if applies["public_art"]:
    fees["public_art"] = calc_art(valuation, total_units)
    notes["public_art"] = ("Check the public art ordinance for exclusions that "
                           "may apply to your project.")

if parkland_mode == "fee":
    fees["parkland"] = calc_parkland_fee(total_units, res_type)
    notes["parkland"] = f"{total_units} unit(s) at the {res_type} rate."


# ============================================================
# PT. 5 — OUTPUT
# ============================================================
st.subheader("3. Fee breakdown")

if not fees:
    st.write("No fees apply to this project.")

for key, amount in fees.items():
    st.write(f"**{FEE_LABELS[key]}:** ${amount:,.2f}")
    if key in notes:
        st.caption(notes[key])

if parkland_mode == "land":
    land_needed = total_units * PARKLAND_LAND_SQFT_PER_UNIT[res_type]
    st.info(f"With more than {PARKLAND_MAX_PARCELS_FOR_FEE} parcels, land "
            f"dedication is required instead of a fee: about {land_needed:,} sq ft "
            "of parkland. Park impact fees don't apply.")

not_applied = [FEE_LABELS[k] for k, v in applies.items() if not v]
if not_applied:
    st.caption("Exempt or not applicable: " + ", ".join(not_applied))

st.write("---")
total_fee = sum(fees.values())
st.header(f"Total estimated fees: ${total_fee:,.2f}")

st.button("Start over", on_click=reset)
