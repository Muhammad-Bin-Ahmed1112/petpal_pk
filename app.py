elif menu == "🚨 Emergency":
    st.header("🚨 Emergency Help")
    col1, col2 = st.columns(2)
    with col1:
        pet_type = st.selectbox("Pet Type", ["Dog", "Cat", "Rabbit"])
    with col2:
        age = st.text_input("Age", "2 years")

    city = st.text_input("Your City", "Rawalpindi")
    symptoms = st.text_area("Describe Symptoms", "vomiting, not eating, weak")

    if st.button("Get Help Now"):
        ai_result, clinics = get_emergency_advice(pet_type, age, symptoms, city)

        st.markdown("### 🩺 First Aid & Severity")
        st.write(ai_result)

        st.markdown("### 🏥 Live Veterinary Clinics Near You")
        st.caption(f"Live from OpenStreetMap • Updated {datetime.now().strftime('%I:%M %p')}")

        if clinics:
            for i, clinic in enumerate(clinics, 1):
                with st.container(border=True):
                    st.markdown(f"**{i}. {clinic['name']}**")
                    st.write(f"📍 {clinic['address']}")
                    if clinic['lat']:
                        st.write(f"[📍 Open in Maps](https://www.google.com/maps?q={clinic['lat']},{clinic['lon']})")
        else:
            st.info("Could not load live clinics. Try 'Rawalpindi' or 'Lahore'")

        st.warning("**Disclaimer**: This is first-aid guidance only. Contact a licensed vet immediately.")
