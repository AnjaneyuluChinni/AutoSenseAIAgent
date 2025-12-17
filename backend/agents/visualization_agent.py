from backend.agents.base_agent import BaseAgent
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json

class VisualizationAgent(BaseAgent):
    def __init__(self):
        super().__init__("VisualizationAgent")
    
    def execute(self, input_data: dict) -> dict:
        action = input_data.get('action', 'table_to_chart')
        data = input_data.get('data', [])
        chart_type = input_data.get('chart_type', 'bar')
        title = input_data.get('title', 'Chart')
        x_column = input_data.get('x_column')
        y_column = input_data.get('y_column')
        
        if action == 'table_to_chart':
            return self.table_to_chart(data, chart_type, title, x_column, y_column)
        elif action == 'create_dashboard':
            return self.create_dashboard_charts(input_data)
        else:
            return {"success": False, "error": "Unknown action"}
    
    def table_to_chart(self, data: list, chart_type: str, title: str, 
                       x_column: str = None, y_column: str = None) -> dict:
        try:
            if not data:
                return {"success": False, "error": "No data provided"}
            
            df = pd.DataFrame(data)
            
            if x_column is None:
                x_column = df.columns[0]
            if y_column is None:
                numeric_cols = df.select_dtypes(include=['number']).columns
                y_column = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[1]
            
            if chart_type == 'bar':
                fig = px.bar(df, x=x_column, y=y_column, title=title)
            elif chart_type == 'line':
                fig = px.line(df, x=x_column, y=y_column, title=title)
            elif chart_type == 'pie':
                fig = px.pie(df, names=x_column, values=y_column, title=title)
            elif chart_type == 'scatter':
                fig = px.scatter(df, x=x_column, y=y_column, title=title)
            elif chart_type == 'area':
                fig = px.area(df, x=x_column, y=y_column, title=title)
            else:
                fig = px.bar(df, x=x_column, y=y_column, title=title)
            
            fig.update_layout(
                template='plotly_white',
                title_font_size=16,
                showlegend=True
            )
            
            return {
                "success": True,
                "chart_type": chart_type,
                "figure": fig.to_json(),
                "decision": f"Created {chart_type} chart with {len(data)} data points"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_dashboard_charts(self, input_data: dict) -> dict:
        charts = []
        
        try:
            if 'breakdown_data' in input_data:
                breakdown_df = pd.DataFrame(input_data['breakdown_data'])
                if not breakdown_df.empty:
                    fig = px.pie(breakdown_df, names='type', values='count', 
                                title='Breakdown Types Distribution')
                    charts.append({
                        'name': 'breakdown_distribution',
                        'figure': fig.to_json()
                    })
            
            if 'service_data' in input_data:
                service_df = pd.DataFrame(input_data['service_data'])
                if not service_df.empty:
                    fig = px.bar(service_df, x='month', y='count',
                                title='Monthly Service Requests')
                    charts.append({
                        'name': 'monthly_services',
                        'figure': fig.to_json()
                    })
            
            if 'garage_performance' in input_data:
                garage_df = pd.DataFrame(input_data['garage_performance'])
                if not garage_df.empty:
                    fig = px.bar(garage_df, x='garage', y='avg_repair_time',
                                title='Average Repair Time by Garage')
                    charts.append({
                        'name': 'garage_performance',
                        'figure': fig.to_json()
                    })
            
            if 'health_trends' in input_data:
                health_df = pd.DataFrame(input_data['health_trends'])
                if not health_df.empty:
                    fig = go.Figure()
                    for col in ['engine', 'brake', 'battery']:
                        if col in health_df.columns:
                            fig.add_trace(go.Scatter(
                                x=health_df['date'], y=health_df[col],
                                mode='lines+markers', name=col.title()
                            ))
                    fig.update_layout(title='Vehicle Health Trends')
                    charts.append({
                        'name': 'health_trends',
                        'figure': fig.to_json()
                    })
            
            return {
                "success": True,
                "charts": charts,
                "total_charts": len(charts),
                "decision": f"Generated {len(charts)} dashboard charts"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_gauge_chart(self, value: float, title: str, max_value: float = 100) -> dict:
        try:
            if value >= 70:
                color = "green"
            elif value >= 40:
                color = "orange"
            else:
                color = "red"
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=value,
                title={'text': title},
                gauge={
                    'axis': {'range': [0, max_value]},
                    'bar': {'color': color},
                    'steps': [
                        {'range': [0, 40], 'color': "lightcoral"},
                        {'range': [40, 70], 'color': "lightyellow"},
                        {'range': [70, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 30
                    }
                }
            ))
            
            fig.update_layout(height=250)
            
            return {
                "success": True,
                "figure": fig.to_json(),
                "decision": f"Created gauge chart for {title}: {value}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
