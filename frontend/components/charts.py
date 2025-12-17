import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def create_gauge_chart(value: float, title: str, max_value: float = 100):
    if value >= 70:
        color = "#2ecc71"
    elif value >= 40:
        color = "#f39c12"
    else:
        color = "#e74c3c"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 14}},
        number={'suffix': '%', 'font': {'size': 24}},
        gauge={
            'axis': {'range': [0, max_value], 'tickwidth': 1},
            'bar': {'color': color, 'thickness': 0.8},
            'steps': [
                {'range': [0, 40], 'color': "#fadbd8"},
                {'range': [40, 70], 'color': "#fdebd0"},
                {'range': [70, 100], 'color': "#d5f5e3"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 2},
                'thickness': 0.75,
                'value': 30
            }
        }
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def create_bar_chart(data: list, x_col: str, y_col: str, title: str, color: str = None):
    df = pd.DataFrame(data)
    
    fig = px.bar(
        df, 
        x=x_col, 
        y=y_col, 
        title=title,
        color_discrete_sequence=[color] if color else px.colors.qualitative.Set2
    )
    
    fig.update_layout(
        template='plotly_white',
        title_font_size=16,
        xaxis_title="",
        yaxis_title="",
        showlegend=False,
        height=350
    )
    
    return fig

def create_pie_chart(data: list, names_col: str, values_col: str, title: str):
    df = pd.DataFrame(data)
    
    fig = px.pie(
        df,
        names=names_col,
        values=values_col,
        title=title,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        template='plotly_white',
        title_font_size=16,
        height=350
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig

def create_line_chart(data: list, x_col: str, y_col: str, title: str):
    df = pd.DataFrame(data)
    
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        title=title,
        markers=True
    )
    
    fig.update_layout(
        template='plotly_white',
        title_font_size=16,
        xaxis_title="",
        yaxis_title="",
        height=350
    )
    
    return fig

def create_multi_line_chart(data: dict, x_col: str, y_cols: list, title: str):
    fig = go.Figure()
    
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
    
    for i, y_col in enumerate(y_cols):
        fig.add_trace(go.Scatter(
            x=data[x_col],
            y=data[y_col],
            mode='lines+markers',
            name=y_col.replace('_', ' ').title(),
            line=dict(color=colors[i % len(colors)])
        ))
    
    fig.update_layout(
        title=title,
        template='plotly_white',
        title_font_size=16,
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_horizontal_bar(data: list, x_col: str, y_col: str, title: str):
    df = pd.DataFrame(data)
    df = df.sort_values(by=x_col, ascending=True)
    
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        title=title,
        orientation='h',
        color_discrete_sequence=['#3498db']
    )
    
    fig.update_layout(
        template='plotly_white',
        title_font_size=16,
        height=350
    )
    
    return fig

def display_metric_cards(metrics: dict, cols_per_row: int = 4):
    cols = st.columns(cols_per_row)
    for i, (label, value) in enumerate(metrics.items()):
        with cols[i % cols_per_row]:
            if isinstance(value, dict):
                st.metric(
                    label=label,
                    value=value.get('value', 0),
                    delta=value.get('delta'),
                    delta_color=value.get('delta_color', 'normal')
                )
            else:
                st.metric(label=label, value=value)

def table_to_chart_widget(data: list, key_prefix: str = "chart"):
    if not data:
        st.warning("No data available for chart")
        return
    
    df = pd.DataFrame(data)
    
    st.dataframe(df, use_container_width=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        chart_type = st.selectbox(
            "Chart Type",
            ["Bar", "Line", "Pie", "Area"],
            key=f"{key_prefix}_type"
        )
    
    with col2:
        x_column = st.selectbox(
            "X Axis",
            df.columns.tolist(),
            key=f"{key_prefix}_x"
        )
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    y_default = numeric_cols[0] if numeric_cols else df.columns[1]
    
    with col3:
        y_column = st.selectbox(
            "Y Axis",
            df.columns.tolist(),
            index=df.columns.tolist().index(y_default) if y_default in df.columns.tolist() else 0,
            key=f"{key_prefix}_y"
        )
    
    if st.button("Convert to Chart", key=f"{key_prefix}_btn", type="primary"):
        if chart_type == "Bar":
            fig = create_bar_chart(data, x_column, y_column, f"{y_column} by {x_column}")
        elif chart_type == "Line":
            fig = create_line_chart(data, x_column, y_column, f"{y_column} over {x_column}")
        elif chart_type == "Pie":
            fig = create_pie_chart(data, x_column, y_column, f"{y_column} Distribution")
        else:
            fig = px.area(df, x=x_column, y=y_column, title=f"{y_column} over {x_column}")
            fig.update_layout(template='plotly_white', height=350)
        
        st.plotly_chart(fig, use_container_width=True)
