import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# --- Page Configuration ---
st.set_page_config(
    page_title="Schengen Visa Calculator",
    page_icon="✈️",
    layout="centered"
)

# --- Title and Introduction ---
st.title("🇪🇺 Optimized Schengen Calculator")
st.markdown("""
Plan your trips to maximize your stay in the Schengen Area while respecting the **90/180-day rule**.
Now includes your **First Trip** customization.
""")

st.divider()

# --- User Input Section ---
st.subheader("1. Visa Details")
col1, col2 = st.columns([1, 2])
with col1:
    st.write("📅 **Visa Valid From**")
with col2:
    start_date = st.date_input(
        "Select visa start date",
        value=datetime.today(),
        label_visibility="collapsed"
    )

start = datetime.combine(start_date, datetime.min.time())

# --- Manual First Trip Section ---
st.subheader("2. First Trip (Optional)")
with st.expander("✈️ I already have a first trip planned", expanded=True):
    has_manual_trip = st.checkbox("Include a specific first trip?")
    
    if has_manual_trip:
        c1, c2 = st.columns(2)
        with c1:
            manual_entry_date = st.date_input("Entry Date", value=start_date)
        with c2:
            manual_exit_date = st.date_input("Exit Date", value=start_date + timedelta(days=15))
        
        # Validation logic
        manual_entry = datetime.combine(manual_entry_date, datetime.min.time())
        manual_exit = datetime.combine(manual_exit_date, datetime.min.time())
        manual_duration = (manual_exit - manual_entry).days + 1
        
        if manual_entry < start:
            st.error("⚠️ Entry date cannot be before Visa Start Date.")
            valid_manual = False
        elif manual_exit < manual_entry:
            st.error("⚠️ Exit date must be after Entry date.")
            valid_manual = False
        elif manual_duration > 90:
            st.error(f"⚠️ Trip is too long ({manual_duration} days). Max is 90.")
            valid_manual = False
        else:
            st.success(f"✅ First trip recorded: {manual_duration} days")
            valid_manual = True
    else:
        valid_manual = False

# --- Calculation Logic ---
validities = {
    "3 months": 90,
    "1 year": 365,
    "2 years": 730,
    "5 years": 1825
}

st.divider()
st.subheader("3. Optimized Schedule")

# Create tabs
tabs = st.tabs(list(validities.keys()))

for (label, days), tab in zip(validities.items(), tabs):
    with tab:
        validity_delta = timedelta(days=days)
        visa_end = start + validity_delta - timedelta(days=1)
        
        st.info(f"**{label} Visa** — Valid until **{visa_end.strftime('%Y-%m-%d')}**")

        stays = []
        current = start # Default start point

        # --- Handle Manual Trip Integration ---
        if has_manual_trip and valid_manual:
            # Check if manual trip fits within THIS specific visa validity
            if manual_exit > visa_end:
                st.warning(f"⚠️ Your planned first trip ends after this visa expires ({visa_end.strftime('%Y-%m-%d')}).")
                # We skip calculation for this tab if the trip is impossible
                continue 
            else:
                stays.append({
                    "Type": "Manual (Fixed)",
                    "Entry Date": manual_entry.strftime('%Y-%m-%d'),
                    "Exit Date": manual_exit.strftime('%Y-%m-%d'),
                    "Duration": manual_duration
                })
                # STRATEGY: To guarantee a full 90-day reset, we wait 91 days after exit.
                # This is the safest way to optimize "Max Days" for subsequent trips.
                current = manual_exit + timedelta(days=91)
        
        # --- Algorithm for Remaining Time ---
        while True:
            entry = current
            
            # Stop if we passed visa validity
            if entry > visa_end:
                break
                
            # Try to stay max 90 days
            potential_exit = entry + timedelta(days=89)
            
            # Cap exit at visa end date
            exit_date = min(potential_exit, visa_end)
            stay_days = (exit_date - entry).days + 1
            
            # If the stay is valid (positive days), add it
            if stay_days > 0:
                stays.append({
                    "Type": "Optimized (Auto)",
                    "Entry Date": entry.strftime('%Y-%m-%d'),
                    "Exit Date": exit_date.strftime('%Y-%m-%d'),
                    "Duration": stay_days
                })
            
            # Next entry: Exit + 91 days (90 days out rule simplified)
            next_current = exit_date + timedelta(days=91)
            current = next_current

        # --- Display Results ---
        if stays:
            df = pd.DataFrame(stays)
            total_days = df["Duration"].sum()

            c1, c2 = st.columns(2)
            c1.metric("Total Trips", len(stays))
            c2.metric("Total Days in Schengen", total_days)

            # Styling the dataframe to highlight the Manual trip
            st.dataframe(
                df, 
                width='stretch', 
                hide_index=True,
                column_config={
                    "Type": st.column_config.TextColumn("Trip Type"),
                    "Duration": st.column_config.NumberColumn("Days", format="%d")
                }
            )
        else:
            st.warning("No travel periods possible.")

# --- Footer ---
st.caption("ℹ️ 'Optimized' trips assume a 90-day reset period after each trip to safely maximize stay length.")