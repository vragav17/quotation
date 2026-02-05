import streamlit as st
from dataclasses import dataclass
import base64
from pathlib import Path
import pandas as pd

# -------------------------------------------------------
# Page config + favicon
# -------------------------------------------------------
st.set_page_config(
    page_title="SSS - Quotation Builder",
    page_icon="logo.png",
    layout="wide"
)

# -------------------------------------------------------
# HTML header (logo + title in one line)
# -------------------------------------------------------
def get_base64_image(path):
    if not Path(path).exists():
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = get_base64_image("logo.png")

st.markdown(
    f"""
    <div style="display:flex;align-items:center;gap:15px;margin-bottom:10px;">
        <img src="data:image/png;base64,{logo_base64}" style="height:60px;" />
        <h2 style="margin:0;">Success Shipping Services – Quotation Builder </h2>
    </div>
    <hr/>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------------
# Data model
# -------------------------------------------------------
@dataclass
class Tariff:

    # Common
    custom_clearance: float = 20000
    gate_mechanical: float = 600
    gate_hydraulic: float = 2000

    # ---------- MAFI MODE ----------
    handling_option_1: float = 900
    handling_option_2: float = 1800
    lashing_charges: float = 1100
    lashing_manpower_per_mafi: float = 3000
    survey_per_mafi: float = 2500
    tug_master_per_mafi: float = 8800

    # ---------- BBK MODE ----------
    bbk_handling_per_cbm: float = 175
    bbk_survey_lumpsum: float = 2500
    bbk_port_permission: float = 2500
    bbk_security_per_shift_person: float = 850


TARIFF = Tariff()

# -------------------------------------------------------
# Inputs
# -------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Cargo Dimensions")
    length = st.number_input("Length (m)", value=12.5, step=0.1)
    width = st.number_input("Width (m)", value=4.0, step=0.1)
    height = st.number_input("Height (m)", value=4.5, step=0.1)

with col2:
    st.subheader("Cargo & Units")
    weight_mt = st.number_input("Weight (MT)", value=30.0, step=1.0)
    no_of_trailers = st.number_input("No. of trailers", min_value=1, value=1)
    no_of_mafi = st.number_input("No. of Mafi (for MAFI mode)", min_value=1, value=1)

with col3:
    st.subheader("Quotation Modes")

    quote_modes = st.multiselect(
        "Select Shipping Modes",
        ["MAFI MODE", "BBK MODE"],
        default=["MAFI MODE"]
    )

    trailer_type = st.selectbox(
        "Gate IN/OUT Trailer Type",
        [
            "Mechanical Trailer (<50 MT & <12 m)",
            "Hydraulic Axle Trailer (>50 MT & >14 m)"
        ]
    )

    include_custom_clearance = st.checkbox(
        "Include Custom Clearance Charges",
        value=True
    )

# -------------------------------------------------------
# BBK extra inputs
# -------------------------------------------------------
bbk_security_persons = 0
bbk_security_shifts = 0

if "BBK MODE" in quote_modes:
    st.markdown("### BBK – Security Requirement")
    bbk_security_persons = st.number_input("No of persons", min_value=0, value=1)
    bbk_security_shifts = st.number_input("No of 8Hr shifts", min_value=0, value=1)

# -------------------------------------------------------
# Common calculations
# -------------------------------------------------------
cbm = length * width * height

custom_clearance = TARIFF.custom_clearance if include_custom_clearance else 0

if trailer_type.startswith("Mechanical"):
    gate_rate = TARIFF.gate_mechanical
else:
    gate_rate = TARIFF.gate_hydraulic

gate_charges = gate_rate * no_of_trailers

# -------------------------------------------------------
# Cargo summary
# -------------------------------------------------------
st.subheader("📦 Cargo Summary")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Length (m)", f"{length:.2f}")
c2.metric("Width (m)", f"{width:.2f}")
c3.metric("Height (m)", f"{height:.2f}")
c4.metric("Volume (CBM)", f"{cbm:.2f}")

st.metric("Weight (MT)", f"{weight_mt:.2f}")

# =======================================================
# ======================= MAFI MODE =====================
# =======================================================
if "MAFI MODE" in quote_modes:

    handling_option1_charges = TARIFF.handling_option_1 * weight_mt
    handling_option2_charges = TARIFF.handling_option_2 * weight_mt

    lashing_charges = TARIFF.lashing_charges * weight_mt
    lashing_manpower = TARIFF.lashing_manpower_per_mafi * no_of_mafi
    survey_charges = TARIFF.survey_per_mafi * no_of_mafi
    tug_master_charges = TARIFF.tug_master_per_mafi * no_of_mafi

    mafi_common_total = (
        custom_clearance
        + gate_charges
        + lashing_charges
        + lashing_manpower
        + survey_charges
        + tug_master_charges
    )

    mafi_option1_total = mafi_common_total + handling_option1_charges
    mafi_option2_total = mafi_common_total + handling_option2_charges

    st.markdown("---")
    st.subheader("💰 Quotation Breakdown – MAFI MODE")

    mafi_rows = []

    if include_custom_clearance:
        mafi_rows.append(["1", "Custom clearance charges", custom_clearance])

    mafi_rows.extend([
        ["2", f"Cargo gate IN/OUT – {trailer_type}", gate_charges],
        ["3A", "Option 1 – Direct Handling (Rs 900 / MT)", handling_option1_charges],
        ["3B", "Option 2 – Double Handling (Rs 1800 / MT)", handling_option2_charges],
        ["4", "Lashing charges (Rs 1100 / MT)", lashing_charges],
        ["5", f"Lashing manpower (per Mafi x {no_of_mafi})", lashing_manpower],
        ["6", f"Survey (per Mafi x {no_of_mafi})", survey_charges],
        ["7", f"Tug master (per Mafi x {no_of_mafi})", tug_master_charges],
    ])

    mafi_table = pd.DataFrame(
        mafi_rows,
        columns=["Sl.No", "Description", "Amount (₹)"]
    )

    st.dataframe(mafi_table, use_container_width=True, hide_index=True)

    st.markdown("#### 🧾 Quoted Amount – MAFI MODE")

    q1, q2 = st.columns(2)

    with q1:
        st.info("Option 1 – Direct Handling")
        st.success(f"₹ {mafi_option1_total:,.0f}")

    with q2:
        st.info("Option 2 – Double Handling")
        st.success(f"₹ {mafi_option2_total:,.0f}")

# =======================================================
# ======================= BBK MODE ======================
# =======================================================
if "BBK MODE" in quote_modes:

    bbk_handling = TARIFF.bbk_handling_per_cbm * cbm
    bbk_survey = TARIFF.bbk_survey_lumpsum
    bbk_port_permission = TARIFF.bbk_port_permission
    bbk_security = (
        TARIFF.bbk_security_per_shift_person
        * bbk_security_persons
        * bbk_security_shifts
    )

    bbk_total = (
        custom_clearance
        + gate_charges
        + bbk_handling
        + bbk_survey
        + bbk_port_permission
        + bbk_security
    )

    st.markdown("---")
    st.subheader("💰 Quotation Breakdown – BBK MODE")

    bbk_rows = []

    if include_custom_clearance:
        bbk_rows.append(["1", "Custom clearance charges", custom_clearance])

    bbk_rows.extend([
        ["2", f"Cargo gate IN/OUT – {trailer_type}", gate_charges],
        ["3", f"BBK handling (Rs 175 / CBM x {cbm:.2f})", bbk_handling],
        ["4", "Survey charges (W/M – Lumpsum)", bbk_survey],
        ["5", "Port permission charges (one time)", bbk_port_permission],
        ["6", f"Security charges (Rs 850 x {bbk_security_persons} persons x {bbk_security_shifts} shifts)", bbk_security],
    ])

    bbk_table = pd.DataFrame(
        bbk_rows,
        columns=["Sl.No", "Description", "Amount (₹)"]
    )

    st.dataframe(bbk_table, use_container_width=True, hide_index=True)

    st.markdown("#### 🧾 Quoted Amount – BBK MODE")
    st.success(f"₹ {bbk_total:,.0f}")

# -------------------------------------------------------
# No mode selected
# -------------------------------------------------------
if len(quote_modes) == 0:
    st.warning("Please select at least one shipping mode.")

# -------------------------------------------------------
# Footer
# -------------------------------------------------------
st.markdown(
    """
    <hr/>
    <div style="text-align:center; color:gray; font-size:14px;">
        Built with ❤️ by 
        <a href="https://www.linkedin.com/in/vragav17/" target="_blank" style="text-decoration:none;">
            <b>@vragav17</b>
        </a>
    </div>
    """,
    unsafe_allow_html=True
)
