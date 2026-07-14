import streamlit as st
st.write("**Disclaimer:** This calculator is for reference only. For official impact fee calculations, please contact the City of Palo Alto Planning Department at (650) 329-2116.")
st.write("---")

st.title("Palo Alto Residential Impact Fee Calculator")

st.write("Hello! Welcome to the Palo Alto Residential Impact Fee Calculator!!!!!!!")



#To run in terminal use the following

#   cd C:\Users\again\Downloads\Palo-Alto-Impact-Fee-Calculator

#   python -m streamlit run Palo-Alto-Impact-Fee-Calculator.py

#Structure of code

#Pt. 1
#Check for exemptions. Takes input and determines which fees apply

#Pt. 2
#Figure out which variables are needed

#Pt. 3
#Request variables

#Pt. 4
#Calculate fees

#Pt. 5
#Outputs fees and breakdown

#FUNCTIONS TO CALC FEES
#returns community facilities fee
def calc_community (project_sq_ft, project_num_units, res_type):
    if res_type=="Single Family":
        return (project_sq_ft * 20.95) + (project_num_units * 3108.33)
    elif res_type=="Multi-Family":
        return (project_sq_ft * 49.64) + (project_num_units * 2486.15)

#returns housing fee
def calc_housing (project_sq_ft, project_type):
    z=0
    if project_type=="Single family detached":
        z=99.57
    elif project_type in ["Single family attached", "Condominiums"]:
        z=66.38
    elif project_type=="Apartment (rentals)":
        z=26.55
    return (project_sq_ft*z)

#returns traffic fee
def calc_traffic(place,project_num_units, parking, trips):
    location_specific=0
    if place=="Downtown assessment district":
        location_specific=parking*134623.5
    elif place=="Charleston or Arastradero":
        location_specific=project_num_units*1733.12
    citywide=10037.58*trips
    return location_specific+citywide

def calc_art (valuation ,project_num_units):
    if  project_num_units>=5:
        if valuation<=131800000:
            return .01*valuation
        else:
            return 1318000+.009*(valuation-131800000)
    else:
        return 0

def calc_park (res_type, project_num_units):
    if res_type=="Single Family":
        return 81324.95*project_num_units
    else:
        return 56054.48*project_num_units

# Exemption checks
st.write("---")
st.write("Please answer the following so we can determine which fees apply to your project?")

# Checks project types

project_type = st.selectbox("Please select the project type", ["Single-family home remodels or additions","New home on an empty parcel", "Second units","ADU","Multi-family Residential", "None of the above"])
if project_type=="ADU":
    adu_type = st.selectbox(
    "Which of the following is true for the ADU?",
    ["ADU under 750 sq ft", "ADU 750+ sq ft", "Garage/Carport or Junior ADU"])
# Checks affordability based exemptions
bmr_units=st.selectbox("Please select the box that best describes the number of Below Market Rate (BMR) units in the project", ["Below required BMR units","Required BMR", "BMR Housing beyond required units"])
affordability_hundred=st.checkbox("Project is %100 affordable housing")
#Checks Parcels
map_used=st.checkbox("Project uses a subdivision or parcel map?")
st.write("---")
#applying fees. All start as applied and then get exempted
st.write("The following fees apply to this project:")
fees_apply = {
    "community_facilities": True,
    "housing": True,
    "traffic": True,
    "public_art": True,
    "parkland": True
}
#Add exemptions for ADU
if project_type == "ADU":
    for key in fees_apply.keys():
        fees_apply[key] = False
    if adu_type=="ADU 750+ sq ft":
        fees_apply["community_facilities"]=True

#Check Parkland Dedication fee
if map_used==False:
    fees_apply["parkland"]=False
else:
    fees_apply["parkland"]=True

#add exemptions based on BMR units
if bmr_units=="BMR Housing beyond required units":
    for key, value in fees_apply.items():
        fees_apply[key]=False
elif bmr_units=="Required BMR":
    fees_apply["housing"]=False

#check things that exempt all and then sets all fees to be not applied
if project_type=="Single-family home remodels or additions" or affordability_hundred==True:
    for key, value in fees_apply.items():
        fees_apply[key]=False


#Writes all applying fees
for key, value in fees_apply.items():
    if value:
        st.write(f"{key} applies :/")



st.write("---")

st.write("Give the following information on your project:")
# Here we will solicit variables depending on fees

#Square feet
if fees_apply["community_facilities"]==True or fees_apply["housing"]==True:
    sq_ft=st.number_input("How many square feet is the project?", min_value=0)

#location
if fees_apply["traffic"]==True:
    location=st.selectbox("Where is your project?", ["Downtown assessment district", "Charleston or Arastradero", "None of the above"])

#value
if fees_apply["public_art"]==True:
    value=st.number_input("What is the valuation of the construction on your project?", min_value=0)

#Unit count
if fees_apply["traffic"]==True or fees_apply["parkland"]==True or fees_apply["community_facilities"]==True:
    num_units=st.number_input("How many units is the project?", min_value=0)

#PM Trips and new parking
if fees_apply["traffic"]:
    pm_trips=st.number_input("What is the net new PM peak hour trips which this project will make?", min_value=0)
    new_parking=st.number_input("How much new parking will this project require?", min_value=0)

#single or multi
if fees_apply["community_facilities"]==True or fees_apply["parkland"]==True:
    residential_type = st.selectbox("Is this Single Family or Multi-Family?", ["Single Family", "Multi-Family"])

#type for housing fee
if fees_apply["housing"]==True:
    housing_type=st.selectbox("Which of the following describes your project best?", ["Single family detached", "Single family attached", "Condominiums", "Apartment (rentals)"])

st.write("---")

final_fees={}

#Then run 0-5 commands depending on inputs.
if fees_apply["community_facilities"]==True:
    final_fees["community_facilities"]=calc_community(sq_ft,num_units,residential_type)
    st.write(f"The community facility fee is ${final_fees['community_facilities']:,.2f}")

if fees_apply["housing"]==True:
    final_fees["housing"]=calc_housing(sq_ft, housing_type)
    st.write(f"The housing  fee is ${final_fees['housing']:,.2f}")

if fees_apply["traffic"]==True:
    final_fees["traffic"]=calc_traffic(location,num_units,new_parking,pm_trips)
    st.write(f"The traffic fee is ${final_fees['traffic']:,.2f}")

if fees_apply["public_art"]==True:
    final_fees["public_art"]=calc_art (value ,num_units)
    st.write(f"The art fee is ${final_fees['public_art']:,.2f}")

if fees_apply["parkland"]==True:
    final_fees["parkland"]=calc_park (residential_type ,num_units)
    st.write(f"The parkland fee is ${final_fees['parkland']:,.2f}")


st.write("---")
total_fee=0
for value in final_fees.values():
    total_fee=total_fee+value

st.header(f"THE TOTAL FEE IS ${total_fee:,.2f}")

if st.button("Calculate Another Project"):
    st.rerun()

