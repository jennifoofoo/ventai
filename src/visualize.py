# Visualization functions
import plotly.express as px
import pandas as pd
from typing import Optional


def create_category_bar_chart(df: pd.DataFrame) -> Optional[object]:
    # Create bar chart by category
    if df is None or len(df) == 0 or 'category' not in df.columns:
        return None
    
    category_counts = df['category'].value_counts().head(10)
    
    fig = px.bar(
        x=category_counts.values,
        y=category_counts.index,
        orientation='h',
        title='Startups by Category (Top 10)',
        labels={'x': 'Number of Startups', 'y': 'Category'},
        color=category_counts.values,
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_title="Number of Startups",
        yaxis_title="Category"
    )
    
    return fig


def create_country_pie_chart(df: pd.DataFrame) -> Optional[object]:
    # Create pie chart by country
    if df is None or len(df) == 0 or 'country' not in df.columns:
        return None
    
    country_counts = df['country'].value_counts()
    
    # Show top 10 countries, group others as "Other"
    if len(country_counts) > 10:
        top_countries = country_counts.head(10)
        other_count = country_counts.tail(len(country_counts) - 10).sum()
        if other_count > 0:
            top_countries['Other'] = other_count
    else:
        top_countries = country_counts
    
    fig = px.pie(
        values=top_countries.values,
        names=top_countries.index,
        title='Startups by Country',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(height=400)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig

