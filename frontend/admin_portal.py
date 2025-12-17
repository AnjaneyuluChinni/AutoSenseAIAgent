import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

from database.models import User, get_db_session
from utils.auth import hash_password, verify_password
from backend.services.vehicle_service import get_all_vehicles
from backend.services.service_request_service import get_all_service_requests, update_service_status
from backend.services.breakdown_service import get_all_breakdowns, update_breakdown_status
from backend.services.garage_service import get_all_garages, add_garage, update_garage, delete_garage, get_garage_details
from backend.services.spare_parts_service import get_all_spare_parts, add_spare_part, update_spare_part, get_low_stock_parts
from backend.services.analytics_service import get_dashboard_stats, get_breakdown_analytics, get_service_analytics, get_garage_performance, get_agent_logs
from backend.services.alert_service import get_all_alerts
from frontend.components.charts import create_bar_chart, create_pie_chart, create_line_chart, display_metric_cards, table_to_chart_widget

def authenticate_admin(username: str, password: str):
    db = get_db_session()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    
    if user and verify_password(password, user.password_hash) and user.role == 'admin':
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
        <p style='color: #7f8c8d; font-size: 18px;'>Admin / Management Portal</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Admin Login")
        
        with st.form("admin_login_form"):
            username = st.text_input("Username", placeholder="Enter admin username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submit:
                if username and password:
                    user = authenticate_admin(username, password)
                    if user:
                        st.session_state.admin_user = user
                        st.session_state.admin_authenticated = True
                        st.rerun()
                    else:
                        st.error("Invalid credentials or not an admin")
                else:
                    st.warning("Please enter both username and password")
        
        st.markdown("---")
        st.info("Demo Admin: admin / admin123")
        
        if st.button("Switch to User Portal"):
            st.session_state.portal = 'user'
            st.rerun()

def dashboard_page():
    st.subheader("Admin Dashboard")
    
    stats = get_dashboard_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Vehicles", stats.get('total_vehicles', 0))
    with col2:
        st.metric("Active Services", stats.get('active_services', 0))
    with col3:
        st.metric("Active Breakdowns", stats.get('active_breakdowns', 0))
    with col4:
        st.metric("Total Garages", stats.get('total_garages', 0))
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric("Completed Services", stats.get('completed_services', 0))
    with col6:
        st.metric("Completed Breakdowns", stats.get('completed_breakdowns', 0))
    with col7:
        st.metric("Avg Repair Time", f"{stats.get('avg_repair_time_minutes', 0):.0f} min")
    with col8:
        st.metric("Garage Utilization", f"{stats.get('garage_utilization_percent', 0):.1f}%")
    
    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### Breakdown Distribution")
        breakdown_stats = get_breakdown_analytics()
        
        if breakdown_stats.get('by_type'):
            fig = create_pie_chart(
                breakdown_stats['by_type'],
                'type',
                'count',
                'Breakdown Types'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.markdown("### Monthly Services")
        service_stats = get_service_analytics()
        
        if service_stats.get('by_month'):
            fig = create_line_chart(
                service_stats['by_month'],
                'month',
                'count',
                'Services Over Time'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Garage Performance")
    garage_perf = get_garage_performance()
    
    if garage_perf:
        fig = create_bar_chart(
            garage_perf,
            'garage',
            'avg_repair_time',
            'Average Repair Time by Garage (minutes)',
            '#3498db'
        )
        st.plotly_chart(fig, use_container_width=True)

def service_management_page():
    st.subheader("Service & Breakdown Management")
    
    tab1, tab2 = st.tabs(["Service Requests", "Breakdown Events"])
    
    with tab1:
        st.markdown("### All Service Requests")
        
        requests = get_all_service_requests()
        
        if requests:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "open", "in_progress", "completed", "cancelled"],
                key="service_status_filter"
            )
            
            if status_filter != "All":
                requests = [r for r in requests if r['status'] == status_filter]
            
            for req in requests:
                with st.expander(f"{req['vehicle_name']} - {req['service_type']} ({req['status'].upper()})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        **Request ID**: #{req['id']}
                        
                        **Vehicle**: {req['vehicle_name']} ({req['registration_number']})
                        
                        **Service Type**: {req['service_type']}
                        
                        **Current Status**: {req['status']}
                        
                        **Garage**: {req['garage_name']}
                        """)
                    
                    with col2:
                        st.markdown(f"""
                        **Requested**: {req['requested_date'][:10] if req['requested_date'] else 'N/A'}
                        
                        **Scheduled**: {req['scheduled_date'][:10] if req['scheduled_date'] else 'N/A'}
                        
                        **Completed**: {req['completed_date'][:10] if req['completed_date'] else 'N/A'}
                        
                        **Est. Cost**: ₹{req['estimated_cost'] or 0:,.2f}
                        
                        **Actual Cost**: ₹{req['actual_cost'] or 0:,.2f}
                        """)
                    
                    st.markdown("---")
                    st.markdown("**Update Status:**")
                    
                    ucol1, ucol2, ucol3 = st.columns(3)
                    
                    with ucol1:
                        new_status = st.selectbox(
                            "New Status",
                            ["open", "in_progress", "completed", "cancelled"],
                            index=["open", "in_progress", "completed", "cancelled"].index(req['status']),
                            key=f"status_{req['id']}"
                        )
                    
                    garages = get_all_garages()
                    garage_options = {g['name']: g['id'] for g in garages}
                    
                    with ucol2:
                        selected_garage = st.selectbox(
                            "Assign Garage",
                            list(garage_options.keys()),
                            key=f"garage_{req['id']}"
                        )
                    
                    with ucol3:
                        if st.button("Update", key=f"update_{req['id']}", type="primary"):
                            result = update_service_status(
                                req['id'],
                                new_status,
                                garage_options[selected_garage]
                            )
                            if result.get('success'):
                                st.success("Updated successfully!")
                                st.rerun()
                            else:
                                st.error(result.get('error', 'Update failed'))
        else:
            st.info("No service requests found")
    
    with tab2:
        st.markdown("### All Breakdown Events")
        
        breakdowns = get_all_breakdowns()
        
        if breakdowns:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "reported", "garage_assigned", "garage_en_route", "repair_in_progress", "completed"],
                key="breakdown_status_filter"
            )
            
            if status_filter != "All":
                breakdowns = [b for b in breakdowns if b['status'] == status_filter]
            
            for bd in breakdowns:
                status_color = {
                    'reported': '🔴',
                    'garage_assigned': '🟡',
                    'garage_en_route': '🟠',
                    'repair_in_progress': '🟠',
                    'completed': '🟢'
                }.get(bd['status'], '⚪')
                
                with st.expander(f"{status_color} {bd['breakdown_type']} - {bd['vehicle_name']} ({bd['status']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        **Event ID**: #{bd['id']}
                        
                        **Vehicle**: {bd['vehicle_name']} ({bd['registration_number']})
                        
                        **Type**: {bd['breakdown_type']}
                        
                        **Status**: {bd['status']}
                        
                        **Garage**: {bd['garage_name']}
                        """)
                    
                    with col2:
                        st.markdown(f"""
                        **Reported**: {bd['reported_at'][:16] if bd['reported_at'] else 'N/A'}
                        
                        **Garage Assigned**: {bd['garage_assigned_at'][:16] if bd['garage_assigned_at'] else 'N/A'}
                        
                        **Completed**: {bd['completed_at'][:16] if bd['completed_at'] else 'N/A'}
                        
                        **Est. Cost**: ₹{bd['estimated_cost'] or 0:,.2f}
                        
                        **Actual Cost**: ₹{bd['actual_cost'] or 0:,.2f}
                        """)
                    
                    if bd['vehicle_latitude'] and bd['vehicle_longitude']:
                        m = folium.Map(
                            location=[bd['vehicle_latitude'], bd['vehicle_longitude']],
                            zoom_start=14
                        )
                        folium.Marker(
                            [bd['vehicle_latitude'], bd['vehicle_longitude']],
                            popup="Vehicle Location",
                            icon=folium.Icon(color='red', icon='car', prefix='fa')
                        ).add_to(m)
                        st_folium(m, height=200, width=None, key=f"map_{bd['id']}")
                    
                    st.markdown("---")
                    st.markdown("**Update Status:**")
                    
                    ucol1, ucol2, ucol3 = st.columns(3)
                    
                    statuses = ["reported", "garage_assigned", "garage_en_route", "repair_in_progress", "completed"]
                    
                    with ucol1:
                        new_status = st.selectbox(
                            "New Status",
                            statuses,
                            index=statuses.index(bd['status']) if bd['status'] in statuses else 0,
                            key=f"bd_status_{bd['id']}"
                        )
                    
                    garages = get_all_garages()
                    garage_options = {g['name']: g['id'] for g in garages}
                    
                    with ucol2:
                        selected_garage = st.selectbox(
                            "Assign Garage",
                            list(garage_options.keys()),
                            key=f"bd_garage_{bd['id']}"
                        )
                    
                    with ucol3:
                        if st.button("Update", key=f"bd_update_{bd['id']}", type="primary"):
                            result = update_breakdown_status(
                                bd['id'],
                                new_status,
                                garage_options[selected_garage] if new_status == 'garage_assigned' else None
                            )
                            if result.get('success'):
                                st.success("Updated successfully!")
                                st.rerun()
                            else:
                                st.error(result.get('error', 'Update failed'))
        else:
            st.info("No breakdown events found")

def garage_management_page():
    st.subheader("Garage Management")
    
    tab1, tab2 = st.tabs(["View Garages", "Add New Garage"])
    
    with tab1:
        garages = get_all_garages()
        
        if garages:
            m = folium.Map(location=[28.6139, 77.2090], zoom_start=11)
            
            for g in garages:
                folium.Marker(
                    [g['latitude'], g['longitude']],
                    popup=f"{g['name']} - Rating: {g['rating']}",
                    icon=folium.Icon(color='blue', icon='wrench', prefix='fa')
                ).add_to(m)
            
            st_folium(m, height=300, width=None)
            
            for garage in garages:
                with st.expander(f"{garage['name']} - {garage['city']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        **Address**: {garage['address']}
                        
                        **City**: {garage['city']}
                        
                        **Phone**: {garage['phone'] or 'N/A'}
                        
                        **Email**: {garage['email'] or 'N/A'}
                        
                        **Rating**: {'⭐' * int(garage['rating'])} ({garage['rating']})
                        """)
                    
                    with col2:
                        st.markdown(f"""
                        **Capacity**: {garage['capacity']} vehicles
                        
                        **Current Load**: {garage['current_load']} vehicles
                        
                        **Available**: {garage['available_capacity']} slots
                        
                        **Hours**: {garage['opening_time']} - {garage['closing_time']}
                        
                        **Working Days**: {garage['working_days']}
                        """)
                    
                    st.markdown(f"**Supported Services**: {garage['supported_services'] or 'All'}")
                    
                    st.markdown("---")
                    
                    ecol1, ecol2, ecol3 = st.columns(3)
                    
                    with ecol1:
                        new_capacity = st.number_input(
                            "Update Capacity",
                            min_value=1,
                            value=garage['capacity'],
                            key=f"cap_{garage['id']}"
                        )
                    
                    with ecol2:
                        new_rating = st.number_input(
                            "Update Rating",
                            min_value=1.0,
                            max_value=5.0,
                            value=garage['rating'],
                            step=0.1,
                            key=f"rating_{garage['id']}"
                        )
                    
                    with ecol3:
                        if st.button("Update", key=f"update_garage_{garage['id']}", type="primary"):
                            result = update_garage(
                                garage['id'],
                                capacity=new_capacity,
                                rating=new_rating
                            )
                            if result.get('success'):
                                st.success("Updated!")
                                st.rerun()
                        
                        if st.button("Deactivate", key=f"delete_garage_{garage['id']}"):
                            result = delete_garage(garage['id'])
                            if result.get('success'):
                                st.success("Deactivated!")
                                st.rerun()
        else:
            st.info("No garages found")
    
    with tab2:
        st.markdown("### Add New Garage")
        
        with st.form("add_garage_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Garage Name*")
                address = st.text_input("Address*")
                city = st.text_input("City*")
                phone = st.text_input("Phone")
                email = st.text_input("Email")
            
            with col2:
                latitude = st.number_input("Latitude*", value=28.6139, format="%.6f")
                longitude = st.number_input("Longitude*", value=77.2090, format="%.6f")
                capacity = st.number_input("Capacity", min_value=1, value=10)
                opening_time = st.text_input("Opening Time", value="08:00")
                closing_time = st.text_input("Closing Time", value="18:00")
            
            working_days = st.text_input("Working Days", value="Mon-Sat")
            supported_services = st.text_area("Supported Services (comma separated)", 
                                              value="Engine,Brake,Battery,Tire,General")
            
            submitted = st.form_submit_button("Add Garage", type="primary")
            
            if submitted:
                if name and address and city:
                    result = add_garage(
                        name=name,
                        address=address,
                        city=city,
                        latitude=latitude,
                        longitude=longitude,
                        phone=phone,
                        email=email,
                        capacity=capacity,
                        opening_time=opening_time,
                        closing_time=closing_time,
                        working_days=working_days,
                        supported_services=supported_services
                    )
                    if result.get('success'):
                        st.success(f"Garage added with ID: {result['garage_id']}")
                        st.rerun()
                    else:
                        st.error(result.get('error', 'Failed to add garage'))
                else:
                    st.warning("Please fill all required fields")

def parts_management_page():
    st.subheader("Spare Parts & Pricing Management")
    
    tab1, tab2, tab3 = st.tabs(["All Parts", "Low Stock Alerts", "Add New Part"])
    
    with tab1:
        parts = get_all_spare_parts()
        
        if parts:
            df = pd.DataFrame(parts)
            
            st.dataframe(
                df[['part_number', 'name', 'category', 'oem_price', 'quantity_in_stock', 'in_stock']],
                use_container_width=True
            )
            
            st.markdown("---")
            
            for part in parts[:10]:
                with st.expander(f"{part['name']} ({part['part_number']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        **Category**: {part['category']}
                        
                        **OEM Price**: ₹{part['oem_price']:,.2f}
                        
                        **Aftermarket**: ₹{part['aftermarket_price'] or 0:,.2f}
                        """)
                    
                    with col2:
                        st.markdown(f"""
                        **In Stock**: {part['quantity_in_stock']}
                        
                        **Min Stock**: {part['minimum_stock']}
                        
                        **Status**: {'🟢 OK' if part['in_stock'] else '🔴 Out of Stock'}
                        """)
                    
                    st.markdown(f"**Breakdown Types**: {part['breakdown_types'] or 'N/A'}")
                    
                    ucol1, ucol2, ucol3 = st.columns(3)
                    
                    with ucol1:
                        new_price = st.number_input(
                            "Update OEM Price",
                            min_value=0.0,
                            value=float(part['oem_price']),
                            key=f"price_{part['id']}"
                        )
                    
                    with ucol2:
                        new_stock = st.number_input(
                            "Update Stock",
                            min_value=0,
                            value=part['quantity_in_stock'],
                            key=f"stock_{part['id']}"
                        )
                    
                    with ucol3:
                        if st.button("Update", key=f"update_part_{part['id']}", type="primary"):
                            result = update_spare_part(
                                part['id'],
                                oem_price=new_price,
                                quantity_in_stock=new_stock
                            )
                            if result.get('success'):
                                st.success("Updated!")
                                st.rerun()
        else:
            st.info("No spare parts found")
    
    with tab2:
        low_stock = get_low_stock_parts()
        
        if low_stock:
            st.warning(f"Found {len(low_stock)} items with low stock!")
            
            df = pd.DataFrame(low_stock)
            st.dataframe(df, use_container_width=True)
        else:
            st.success("All parts are well stocked!")
    
    with tab3:
        st.markdown("### Add New Spare Part")
        
        with st.form("add_part_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                part_number = st.text_input("Part Number*")
                name = st.text_input("Part Name*")
                category = st.selectbox("Category", [
                    "Engine", "Brakes", "Electrical", "Tires",
                    "Fluids", "Filters", "Cooling", "Transmission", "Other"
                ])
                oem_price = st.number_input("OEM Price*", min_value=0.0, value=1000.0)
            
            with col2:
                aftermarket_price = st.number_input("Aftermarket Price", min_value=0.0, value=800.0)
                quantity = st.number_input("Initial Stock", min_value=0, value=10)
                minimum_stock = st.number_input("Minimum Stock", min_value=0, value=5)
            
            compatible_makes = st.text_input("Compatible Makes (comma separated)", 
                                            value="Mahindra,Hero")
            breakdown_types = st.text_input("Breakdown Types (comma separated)")
            
            submitted = st.form_submit_button("Add Part", type="primary")
            
            if submitted:
                if part_number and name and oem_price:
                    result = add_spare_part(
                        part_number=part_number,
                        name=name,
                        category=category,
                        oem_price=oem_price,
                        aftermarket_price=aftermarket_price,
                        quantity=quantity,
                        minimum_stock=minimum_stock,
                        compatible_makes=compatible_makes,
                        breakdown_types=breakdown_types
                    )
                    if result.get('success'):
                        st.success(f"Part added with ID: {result['part_id']}")
                        st.rerun()
                    else:
                        st.error(result.get('error', 'Failed to add part'))
                else:
                    st.warning("Please fill all required fields")

def analytics_page():
    st.subheader("Analytics & Insights")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Breakdown Analytics",
        "Service Analytics",
        "Garage Performance",
        "Agent Activity"
    ])
    
    with tab1:
        st.markdown("### Breakdown Analytics")
        
        breakdown_data = get_breakdown_analytics()
        
        if breakdown_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Breakdowns", breakdown_data.get('total_breakdowns', 0))
                
                if breakdown_data.get('by_type'):
                    fig = create_pie_chart(
                        breakdown_data['by_type'],
                        'type',
                        'count',
                        'Breakdown by Type'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if breakdown_data.get('by_status'):
                    status_data = [{'status': k, 'count': v} for k, v in breakdown_data['by_status'].items()]
                    fig = create_bar_chart(status_data, 'status', 'count', 'Breakdown by Status', '#e74c3c')
                    st.plotly_chart(fig, use_container_width=True)
            
            if breakdown_data.get('by_month'):
                st.markdown("### Monthly Trend")
                fig = create_line_chart(
                    breakdown_data['by_month'],
                    'month',
                    'count',
                    'Breakdowns Over Time'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("### Service Analytics")
        
        service_data = get_service_analytics()
        
        if service_data:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Services", service_data.get('total_services', 0))
            with col2:
                st.metric("Delayed Services", service_data.get('delayed_count', 0))
            with col3:
                st.metric("Avg Delay", f"{service_data.get('avg_delay_days', 0):.1f} days")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if service_data.get('by_type'):
                    type_data = [{'type': k, 'count': v} for k, v in service_data['by_type'].items()]
                    fig = create_bar_chart(type_data, 'type', 'count', 'Services by Type', '#3498db')
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if service_data.get('by_status'):
                    status_data = [{'status': k, 'count': v} for k, v in service_data['by_status'].items()]
                    fig = create_pie_chart(status_data, 'status', 'count', 'Services by Status')
                    st.plotly_chart(fig, use_container_width=True)
            
            if service_data.get('by_month'):
                st.markdown("### Monthly Trend")
                fig = create_line_chart(
                    service_data['by_month'],
                    'month',
                    'count',
                    'Services Over Time'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### Garage Performance")
        
        garage_perf = get_garage_performance()
        
        if garage_perf:
            df = pd.DataFrame(garage_perf)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = create_bar_chart(
                    garage_perf,
                    'garage',
                    'avg_repair_time',
                    'Average Repair Time (minutes)',
                    '#2ecc71'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = create_bar_chart(
                    garage_perf,
                    'garage',
                    'utilization',
                    'Garage Utilization (%)',
                    '#9b59b6'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### Detailed Performance")
            table_to_chart_widget(garage_perf, "garage_perf")
    
    with tab4:
        st.markdown("### Agent Activity Logs")
        
        logs = get_agent_logs(50)
        
        if logs:
            for log in logs[:20]:
                success_icon = "✅" if log['success'] else "❌"
                
                st.markdown(f"""
                {success_icon} **{log['agent_name']}** - {log['action']}
                - Decision: {log['decision'] or 'N/A'}
                - Time: {log['execution_time_ms']}ms
                - {log['created_at'][:19] if log['created_at'] else 'N/A'}
                """)
                st.divider()
        else:
            st.info("No agent logs yet")

def vehicles_page():
    st.subheader("All Vehicles")
    
    vehicles = get_all_vehicles()
    
    if vehicles:
        df = pd.DataFrame(vehicles)
        
        st.dataframe(
            df[['registration_number', 'make', 'model', 'year', 'owner_name', 
                'engine_health', 'brake_health', 'battery_health', 'total_km']],
            use_container_width=True
        )
        
        st.markdown("---")
        st.markdown("### Convert to Chart")
        table_to_chart_widget(vehicles, "vehicles")
    else:
        st.info("No vehicles found")

def alerts_page():
    st.subheader("All System Alerts")
    
    alerts = get_all_alerts()
    
    if alerts:
        priority_counts = {}
        for a in alerts:
            p = a['priority']
            priority_counts[p] = priority_counts.get(p, 0) + 1
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Critical", priority_counts.get('critical', 0))
        with col2:
            st.metric("High", priority_counts.get('high', 0))
        with col3:
            st.metric("Medium", priority_counts.get('medium', 0))
        with col4:
            st.metric("Low", priority_counts.get('low', 0))
        
        st.markdown("---")
        
        for alert in alerts[:20]:
            priority_colors = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }
            icon = priority_colors.get(alert['priority'], '⚪')
            
            st.markdown(f"""
            {icon} **{alert['title']}** (User #{alert['user_id']})
            
            {alert['message']}
            
            *{alert['created_at'][:19] if alert['created_at'] else 'N/A'}* | 
            Read: {'Yes' if alert['is_read'] else 'No'} | 
            Dismissed: {'Yes' if alert['is_dismissed'] else 'No'}
            """)
            st.divider()
    else:
        st.info("No alerts found")

def run_admin_portal():
    st.set_page_config(
        page_title="AutoSenseAI - Admin Portal",
        page_icon="🔧",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if 'portal' not in st.session_state:
        st.session_state.portal = 'admin'
    
    if st.session_state.portal == 'user':
        from frontend.user_portal import run_user_portal
        run_user_portal()
        return
    
    if not st.session_state.admin_authenticated:
        login_page()
        return
    
    user = st.session_state.admin_user
    
    with st.sidebar:
        st.markdown(f"""
        ### AutoSenseAI
        **Admin Portal**
        
        ---
        
        Logged in as: **{user['full_name']}**
        
        Role: **{user['role'].upper()}**
        """)
        
        page = st.radio("Navigation", [
            "Dashboard",
            "Service Management",
            "Garage Management",
            "Parts & Pricing",
            "Analytics",
            "Vehicles",
            "Alerts"
        ])
        
        st.markdown("---")
        
        if st.button("Logout", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.session_state.admin_user = None
            st.rerun()
        
        if st.button("Switch to User Portal", use_container_width=True):
            st.session_state.portal = 'user'
            st.session_state.admin_authenticated = False
            st.rerun()
    
    if page == "Dashboard":
        dashboard_page()
    elif page == "Service Management":
        service_management_page()
    elif page == "Garage Management":
        garage_management_page()
    elif page == "Parts & Pricing":
        parts_management_page()
    elif page == "Analytics":
        analytics_page()
    elif page == "Vehicles":
        vehicles_page()
    elif page == "Alerts":
        alerts_page()

if __name__ == "__main__":
    run_admin_portal()
