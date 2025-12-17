import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go

from database.models import User, Vehicle, Alert, get_db_session
from utils.auth import hash_password, verify_password, create_access_token, decode_token
from backend.services.vehicle_service import get_user_vehicles, get_vehicle_details, get_vehicle_prediction
from backend.services.service_request_service import schedule_service, get_user_service_requests
from backend.services.breakdown_service import report_breakdown, get_user_breakdowns, get_breakdown_details
from backend.services.garage_service import get_nearby_garages
from backend.services.alert_service import get_user_alerts, mark_alert_read, dismiss_alert, get_unread_count
from backend.services.analytics_service import get_user_service_history
from frontend.components.charts import create_gauge_chart, table_to_chart_widget, create_bar_chart

def authenticate_user(username: str, password: str):
    db = get_db_session()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    
    if user and verify_password(password, user.password_hash):
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role
        }
    return None

def login_page():
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1 style='color: #2c3e50;'>AutoSenseAI</h1>
        <p style='color: #7f8c8d; font-size: 18px;'>Predictive Maintenance & Smart Breakdown Management</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("User Login")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submit:
                if username and password:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.warning("Please enter both username and password")
        
        st.markdown("---")
        st.info("Demo Credentials: john_user / password123")
        
        if st.button("Switch to Admin Portal"):
            st.session_state.portal = 'admin'
            st.rerun()

def dashboard_page():
    user = st.session_state.user
    
    st.subheader(f"Welcome, {user['full_name']}")
    
    alert_count = get_unread_count(user['id'])
    if alert_count > 0:
        st.warning(f"You have {alert_count} unread alert(s)")
    
    vehicles = get_user_vehicles(user['id'])
    
    if not vehicles:
        st.info("No vehicles registered. Please contact admin to add your vehicles.")
        return
    
    st.markdown("### Your Vehicles")
    
    for vehicle in vehicles:
        with st.expander(f"{vehicle['make']} {vehicle['model']} - {vehicle['registration_number']}", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                fig = create_gauge_chart(vehicle['engine_health'] or 100, "Engine")
                st.plotly_chart(fig, use_container_width=True, key=f"engine_{vehicle['id']}")
            
            with col2:
                fig = create_gauge_chart(vehicle['brake_health'] or 100, "Brakes")
                st.plotly_chart(fig, use_container_width=True, key=f"brake_{vehicle['id']}")
            
            with col3:
                fig = create_gauge_chart(vehicle['battery_health'] or 100, "Battery")
                st.plotly_chart(fig, use_container_width=True, key=f"battery_{vehicle['id']}")
            
            with col4:
                fig = create_gauge_chart(vehicle['tire_health'] or 100, "Tires")
                st.plotly_chart(fig, use_container_width=True, key=f"tire_{vehicle['id']}")
            
            info_col1, info_col2 = st.columns(2)
            
            with info_col1:
                st.markdown(f"""
                **Vehicle Details:**
                - Year: {vehicle['year'] or 'N/A'}
                - Total KM: {vehicle['total_km']:,.0f} km
                - Avg Usage: {vehicle['avg_km_per_month']:,.0f} km/month
                """)
            
            with info_col2:
                last_service = vehicle['last_service_date']
                if last_service:
                    last_service_str = datetime.fromisoformat(last_service).strftime('%d %b %Y')
                else:
                    last_service_str = "No record"
                
                st.markdown(f"""
                **Service Info:**
                - Last Service: {last_service_str}
                - Next Service: Loading prediction...
                """)
            
            prediction = get_vehicle_prediction(vehicle['id'], user['id'])
            if prediction.get('success') and prediction.get('prediction'):
                pred = prediction['prediction']
                urgency = pred.get('urgency_score', 0)
                days = pred.get('days_until_service', 0)
                
                if urgency >= 75:
                    st.error(f"URGENT: Service needed in {days} days (Urgency: {urgency:.0f}%)")
                elif urgency >= 50:
                    st.warning(f"Service recommended in {days} days (Urgency: {urgency:.0f}%)")
                else:
                    st.success(f"Next service in {days} days (Urgency: {urgency:.0f}%)")

def vehicle_details_page():
    user = st.session_state.user
    vehicles = get_user_vehicles(user['id'])
    
    if not vehicles:
        st.info("No vehicles registered.")
        return
    
    st.subheader("Vehicle Details")
    
    vehicle_options = {f"{v['make']} {v['model']} ({v['registration_number']})": v['id'] for v in vehicles}
    selected_vehicle_name = st.selectbox("Select Vehicle", list(vehicle_options.keys()))
    vehicle_id = vehicle_options[selected_vehicle_name]
    
    vehicle = get_vehicle_details(vehicle_id)
    
    if vehicle:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Vehicle Information")
            st.markdown(f"""
            | Property | Value |
            |----------|-------|
            | Registration | {vehicle['registration_number']} |
            | Make | {vehicle['make']} |
            | Model | {vehicle['model']} |
            | Year | {vehicle['year'] or 'N/A'} |
            | VIN | {vehicle['vin'] or 'N/A'} |
            | Total KM | {vehicle['total_km']:,.0f} |
            | Monthly Usage | {vehicle['avg_km_per_month']:,.0f} km |
            """)
        
        with col2:
            st.markdown("### Health Status")
            health_data = [
                {"Component": "Engine", "Health": vehicle['engine_health']},
                {"Component": "Brakes", "Health": vehicle['brake_health']},
                {"Component": "Battery", "Health": vehicle['battery_health']},
                {"Component": "Tires", "Health": vehicle['tire_health']}
            ]
            
            fig = create_bar_chart(health_data, "Component", "Health", "Component Health Status", "#3498db")
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### AI Service Prediction")
        prediction = get_vehicle_prediction(vehicle_id, user['id'])
        
        if prediction.get('success') and prediction.get('prediction'):
            pred = prediction['prediction']
            
            pred_col1, pred_col2, pred_col3 = st.columns(3)
            
            with pred_col1:
                st.metric("Next Service", f"{pred.get('days_until_service', 'N/A')} days")
            
            with pred_col2:
                st.metric("Urgency Score", f"{pred.get('urgency_score', 0):.0f}%")
            
            with pred_col3:
                st.metric("Confidence", f"{pred.get('confidence_score', 0) * 100:.0f}%")
            
            if pred.get('factors'):
                with st.expander("Prediction Factors"):
                    st.json(pred['factors'])

def schedule_service_page():
    user = st.session_state.user
    vehicles = get_user_vehicles(user['id'])
    
    if not vehicles:
        st.info("No vehicles registered.")
        return
    
    st.subheader("Schedule Service")
    
    col1, col2 = st.columns(2)
    
    with col1:
        vehicle_options = {f"{v['make']} {v['model']} ({v['registration_number']})": v['id'] for v in vehicles}
        selected_vehicle_name = st.selectbox("Select Vehicle", list(vehicle_options.keys()))
        vehicle_id = vehicle_options[selected_vehicle_name]
        
        service_type = st.selectbox("Service Type", [
            "Regular Service",
            "Oil Change",
            "Brake Inspection",
            "Engine Tune-up",
            "Full Service",
            "Tire Replacement",
            "Battery Check",
            "AC Service"
        ])
    
    with col2:
        preferred_date = st.date_input(
            "Preferred Date",
            min_value=datetime.now().date(),
            value=datetime.now().date() + timedelta(days=1)
        )
        
        st.info("Our system will automatically find the best available slot")
    
    if st.button("Schedule Service", type="primary", use_container_width=True):
        with st.spinner("Finding the best slot..."):
            result = schedule_service(
                vehicle_id=vehicle_id,
                preferred_date=datetime.combine(preferred_date, datetime.min.time()),
                service_type=service_type
            )
            
            if result.get('success') and result.get('slot_found'):
                st.success(f"""
                Service scheduled successfully!
                
                - **Date**: {result.get('scheduled_date', 'N/A')[:10]}
                - **Time**: {result.get('time_slot', 'N/A')}
                - **Garage**: {result.get('garage_name', 'N/A')}
                """)
            else:
                st.error(result.get('message', 'Failed to schedule service'))
    
    st.markdown("---")
    st.subheader("Your Service Requests")
    
    requests = get_user_service_requests(user['id'])
    
    if requests:
        for req in requests[:5]:
            status_color = {
                'open': 'blue',
                'in_progress': 'orange',
                'completed': 'green',
                'cancelled': 'red'
            }.get(req['status'], 'gray')
            
            st.markdown(f"""
            **{req['vehicle_name']}** - {req['service_type']}
            - Status: :{status_color}[{req['status'].upper()}]
            - Scheduled: {req['scheduled_date'][:10] if req['scheduled_date'] else 'Pending'}
            - Garage: {req['garage_name']}
            """)
            st.divider()
    else:
        st.info("No service requests yet")

def breakdown_assistance_page():
    user = st.session_state.user
    vehicles = get_user_vehicles(user['id'])
    
    if not vehicles:
        st.info("No vehicles registered.")
        return
    
    st.subheader("Emergency Breakdown Assistance")
    
    st.error("If you're in an emergency, use the form below to get immediate help!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        vehicle_options = {f"{v['make']} {v['model']} ({v['registration_number']})": v['id'] for v in vehicles}
        selected_vehicle_name = st.selectbox("Select Vehicle", list(vehicle_options.keys()))
        vehicle_id = vehicle_options[selected_vehicle_name]
        
        breakdown_type = st.selectbox("Breakdown Type", [
            "Flat Tire",
            "Battery Dead",
            "Engine Overheating",
            "Brake Failure",
            "Electrical Issue",
            "Fuel Issue",
            "Transmission Problem",
            "Other"
        ])
        
        description = st.text_area("Description (Optional)", placeholder="Describe the issue...")
    
    with col2:
        st.markdown("### Your Location")
        
        vehicle = get_vehicle_details(vehicle_id)
        default_lat = vehicle['latitude'] if vehicle and vehicle['latitude'] else 28.6139
        default_lng = vehicle['longitude'] if vehicle and vehicle['longitude'] else 77.2090
        
        lat = st.number_input("Latitude", value=default_lat, format="%.6f")
        lng = st.number_input("Longitude", value=default_lng, format="%.6f")
        
        m = folium.Map(location=[lat, lng], zoom_start=14)
        folium.Marker(
            [lat, lng],
            popup="Your Location",
            icon=folium.Icon(color='red', icon='car', prefix='fa')
        ).add_to(m)
        st_folium(m, height=200, width=None)
    
    if st.button("REPORT BREAKDOWN", type="primary", use_container_width=True):
        with st.spinner("Reporting breakdown and finding help..."):
            result = report_breakdown(
                vehicle_id=vehicle_id,
                breakdown_type=breakdown_type,
                description=description,
                latitude=lat,
                longitude=lng
            )
            
            if result.get('success'):
                st.success("Breakdown reported successfully!")
                
                if result.get('nearby_garages', {}).get('recommendations'):
                    st.markdown("### Nearby Garages")
                    
                    garages = result['nearby_garages']['recommendations']
                    
                    m2 = folium.Map(location=[lat, lng], zoom_start=13)
                    folium.Marker(
                        [lat, lng],
                        popup="Your Location",
                        icon=folium.Icon(color='red', icon='car', prefix='fa')
                    ).add_to(m2)
                    
                    for garage in garages:
                        folium.Marker(
                            [garage['latitude'], garage['longitude']],
                            popup=f"{garage['name']} - {garage['distance_km']} km",
                            icon=folium.Icon(color='blue', icon='wrench', prefix='fa')
                        ).add_to(m2)
                    
                    st_folium(m2, height=300, width=None)
                    
                    for i, garage in enumerate(garages[:3]):
                        eta_info = result.get('eta_estimates', [{}])[i] if i < len(result.get('eta_estimates', [])) else {}
                        eta_data = eta_info.get('eta', {})
                        
                        with st.container():
                            gcol1, gcol2, gcol3 = st.columns([2, 1, 1])
                            
                            with gcol1:
                                st.markdown(f"""
                                **{garage['name']}**
                                - Distance: {garage['distance_km']} km
                                - Rating: {'⭐' * int(garage['rating'])} ({garage['rating']})
                                - Phone: {garage.get('phone', 'N/A')}
                                """)
                            
                            with gcol2:
                                if eta_data:
                                    st.metric("Arrival", eta_data.get('formatted', {}).get('arrival', 'N/A'))
                                    st.metric("Repair", eta_data.get('formatted', {}).get('repair', 'N/A'))
                            
                            with gcol3:
                                if st.button(f"Select", key=f"select_garage_{garage['id']}"):
                                    st.success(f"Selected {garage['name']}. They will be notified!")
                            
                            st.divider()
                
                if result.get('cost_estimate', {}).get('cost_breakdown'):
                    with st.expander("Estimated Cost"):
                        cost = result['cost_estimate']['cost_breakdown']
                        st.markdown(f"""
                        - Labor: ₹{cost.get('labor', {}).get('amount', 0):,.2f}
                        - Parts: ₹{cost.get('parts_total', 0):,.2f}
                        - Tax (18%): ₹{cost.get('tax', 0):,.2f}
                        - **Total: ₹{cost.get('total', 0):,.2f}**
                        """)
            else:
                st.error(result.get('error', 'Failed to report breakdown'))
    
    st.markdown("---")
    st.subheader("Your Breakdown History")
    
    breakdowns = get_user_breakdowns(user['id'])
    
    if breakdowns:
        for bd in breakdowns[:5]:
            status_emoji = {
                'reported': '🔴',
                'garage_assigned': '🟡',
                'garage_en_route': '🟡',
                'repair_in_progress': '🟠',
                'completed': '🟢'
            }.get(bd['status'], '⚪')
            
            st.markdown(f"""
            {status_emoji} **{bd['breakdown_type']}** - {bd['vehicle_name']}
            - Status: {bd['status'].replace('_', ' ').title()}
            - Reported: {bd['reported_at'][:10] if bd['reported_at'] else 'N/A'}
            - Garage: {bd['garage_name']}
            """)
            st.divider()
    else:
        st.info("No breakdown history")

def alerts_page():
    user = st.session_state.user
    
    st.subheader("Your Alerts")
    
    show_all = st.checkbox("Show read alerts", value=False)
    alerts = get_user_alerts(user['id'], include_read=show_all)
    
    if not alerts:
        st.success("No alerts! Your vehicles are in good condition.")
        return
    
    for alert in alerts:
        priority_colors = {
            'critical': 'red',
            'high': 'orange',
            'medium': 'blue',
            'low': 'gray'
        }
        color = priority_colors.get(alert['priority'], 'gray')
        
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"""
                :{color}[**{alert['title']}**]
                
                {alert['message']}
                
                *{alert['created_at'][:10] if alert['created_at'] else ''}*
                """)
            
            with col2:
                if not alert['is_read']:
                    if st.button("Mark Read", key=f"read_{alert['id']}"):
                        mark_alert_read(alert['id'])
                        st.rerun()
                
                if st.button("Dismiss", key=f"dismiss_{alert['id']}"):
                    dismiss_alert(alert['id'])
                    st.rerun()
            
            st.divider()

def service_history_page():
    user = st.session_state.user
    
    st.subheader("Service History")
    
    history = get_user_service_history(user['id'])
    
    if not history:
        st.info("No service history yet")
        return
    
    table_to_chart_widget(history, "service_history")

def run_user_portal():
    st.set_page_config(
        page_title="AutoSenseAI - User Portal",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'portal' not in st.session_state:
        st.session_state.portal = 'user'
    
    if st.session_state.portal == 'admin':
        from frontend.admin_portal import run_admin_portal
        run_admin_portal()
        return
    
    if not st.session_state.authenticated:
        login_page()
        return
    
    user = st.session_state.user
    
    if user['role'] == 'admin':
        st.session_state.portal = 'admin'
        st.rerun()
    
    with st.sidebar:
        st.markdown(f"""
        ### AutoSenseAI
        **User Portal**
        
        ---
        
        Logged in as: **{user['full_name']}**
        """)
        
        page = st.radio("Navigation", [
            "Dashboard",
            "Vehicle Details",
            "Schedule Service",
            "Breakdown Assistance",
            "Alerts",
            "Service History"
        ])
        
        st.markdown("---")
        
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()
        
        if st.button("Switch to Admin", use_container_width=True):
            st.session_state.portal = 'admin'
            st.session_state.authenticated = False
            st.rerun()
    
    if page == "Dashboard":
        dashboard_page()
    elif page == "Vehicle Details":
        vehicle_details_page()
    elif page == "Schedule Service":
        schedule_service_page()
    elif page == "Breakdown Assistance":
        breakdown_assistance_page()
    elif page == "Alerts":
        alerts_page()
    elif page == "Service History":
        service_history_page()

if __name__ == "__main__":
    run_user_portal()
