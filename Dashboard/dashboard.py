import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import folium
from folium.plugins import FastMarkerCluster

# Sidebar Title
st.sidebar.title(
    "E-commerce Order Performance and Customer Satisfaction Dashboard")

# Load the pre-loaded data


@st.cache_data
def load_data():
    df = pd.read_csv("https://raw.githubusercontent.com/rizkyyanuark/Submission_dicoding/refs/heads/main/Dashboard/ecommerce.csv?token=GHSAT0AAAAAACS2JU53C2U6RFGJHYT4DQ7QZYGK7JQ", usecols=[
        "order_purchase_timestamp", "order_delivered_customer_date", "order_delivered_carrier_date",
        "review_score", "product_category_name", "customer_unique_id", "payment_value", "customer_state",
        "geolocation_lat", "geolocation_lng"
    ])
    return df


df = load_data()

# Translate product names to English
product_translation = {
    'beleza_saude': 'health_beauty',
    'informatica_acessorios': 'computers_accessories',
    'automotivo': 'automotive',
    'cama_mesa_banho': 'bed_bath_table',
    'moveis_decoracao': 'furniture_decor',
    'esporte_lazer': 'sports_leisure',
    'perfumaria': 'perfumery',
    'bebes': 'baby',
    'utilidades_domesticas': 'home_appliances',
    'relogios_presentes': 'watches_gifts',
    'telefonia': 'telephony',
    'papelaria': 'stationery',
    'fashion_bolsas_e_acessorios': 'fashion_bags_accessories',
    'construcao_ferramentas_seguranca': 'construction_tools_safety',
    'livros_interesse_geral': 'books_general_interest',
    'alimentos': 'food',
}

# Apply translation and convert date columns to datetime
df["product_category_name"] = df["product_category_name"].map(
    product_translation).fillna(df["product_category_name"])
df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
df["order_delivered_customer_date"] = pd.to_datetime(
    df["order_delivered_customer_date"])
df["order_delivered_carrier_date"] = pd.to_datetime(
    df["order_delivered_carrier_date"])

# Select a page for navigation
page = st.sidebar.selectbox("Drilldown", [
    "Overview", "Shipping Delays and Customer Satisfaction", "Sales by Region", "High Delay by Region"
])

# Function to calculate monthly revenue and growth


@st.cache_data
def calculate_monthly_revenue(filtered_data):
    filtered_data["month"] = filtered_data["order_purchase_timestamp"].dt.to_period(
        "M")
    monthly_revenue = filtered_data.groupby("month")["payment_value"].sum()
    monthly_growth = monthly_revenue.pct_change() * 100
    return monthly_revenue, monthly_growth

# Function to display key metrics


def display_key_metrics(filtered_df):
    unique_customers = filtered_df["customer_unique_id"].nunique()
    avg_review_score = filtered_df["review_score"].mean()
    top_product_category = filtered_df["product_category_name"].mode()[0]
    top_product_category_count = filtered_df["product_category_name"].value_counts(
    ).max()
    total_revenue = filtered_df["payment_value"].sum()
    avg_order_value = filtered_df["payment_value"].mean()

    st.subheader("Key Metrics")
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    col1.metric(label="Unique Customers", value=unique_customers)
    col2.metric(label="Average Review Score", value=f"{avg_review_score:.2f}")
    col3.metric(label="Top Product Category", value=top_product_category,
                delta=str(top_product_category_count))
    col4.metric(label="Total Revenue", value=f"${total_revenue:,.2f}")
    col5.metric(label="Average Order Value", value=f"${avg_order_value:,.2f}")
    col6.metric(label="Monthly Revenue Growth",
                value=f"{monthly_revenue_growth.iloc[-1]:.2f}%")

# Function to display monthly revenue and growth charts


def display_revenue_charts(monthly_revenue, monthly_revenue_growth):
    st.subheader("Monthly Total Revenue")
    fig_revenue = px.line(monthly_revenue, x=monthly_revenue.index.astype(str), y=monthly_revenue.values,
                          labels={"x": "Month", "y": "Total Revenue ($)"}, title="Monthly Total Revenue")
    st.plotly_chart(fig_revenue)

    st.subheader("Monthly Revenue Growth")
    fig_growth = px.line(monthly_revenue_growth, x=monthly_revenue_growth.index.astype(str), y=monthly_revenue_growth.values,
                         labels={"x": "Month", "y": "Revenue Growth (%)"}, title="Monthly Revenue Growth")
    st.plotly_chart(fig_growth)

# Function to display top product categories


def display_top_product_categories(filtered_df):
    st.subheader("Top Product Categories")
    top_categories = filtered_df["product_category_name"].value_counts().head(
        10)
    fig_categories = px.bar(top_categories, x=top_categories.index, y=top_categories.values,
                            labels={"x": "Product Category", "y": "Number of Orders"}, title="Top 10 Product Categories")
    st.plotly_chart(fig_categories)


# Overview Page
if page == "Overview":
    filtered_df = df.copy()
    monthly_revenue, monthly_revenue_growth = calculate_monthly_revenue(
        filtered_df)
    display_key_metrics(filtered_df)
    display_revenue_charts(monthly_revenue, monthly_revenue_growth)
    display_top_product_categories(filtered_df)

# High Delay by Region Page
elif page == "High Delay by Region":
    filtered_df = df.copy()
    total_orders_per_region = filtered_df.groupby(
        'customer_state').size().reset_index(name='total_orders')
    high_delays_per_region = filtered_df[(filtered_df['order_delivered_customer_date'] - filtered_df['order_purchase_timestamp']
                                          ).dt.days.between(4, 7)].groupby('customer_state').size().reset_index(name='high_delays')
    region_delay_stats = pd.merge(
        total_orders_per_region, high_delays_per_region, on='customer_state', how='left')
    region_delay_stats['high_delays'].fillna(0, inplace=True)
    region_delay_stats['total_orders'].fillna(0, inplace=True)
    region_delay_stats['high_delay_percentage'] = (
        region_delay_stats['high_delays'] / region_delay_stats['total_orders']) * 100
    region_delay_stats['high_delay_percentage'].fillna(0, inplace=True)

    # Zipping locations
    lats = list(filtered_df[(filtered_df['order_delivered_customer_date'] - filtered_df['order_purchase_timestamp']
                             ).dt.days.between(4, 7)]['geolocation_lat'].dropna().values)
    longs = list(filtered_df[(filtered_df['order_delivered_customer_date'] - filtered_df['order_purchase_timestamp']
                              ).dt.days.between(4, 7)]['geolocation_lng'].dropna().values)
    locations = list(zip(lats, longs))

    # Creating a map using folium
    map1 = folium.Map(location=[-15, -50], zoom_start=4.0)

    # Plugin: FastMarkerCluster
    FastMarkerCluster(data=locations).add_to(map1)

    # Display the map in Streamlit
    st.subheader("High Delay Locations")
    st.components.v1.html(map1._repr_html_(), height=600)

    st.subheader("High Delay by Region")
    st.dataframe(region_delay_stats)

# Sales by Region Page
elif page == "Sales by Region":
    region_filter = st.sidebar.multiselect(
        "Region", options=df["customer_state"].unique(), default=df["customer_state"].unique())
    filtered_df = df[df["customer_state"].isin(region_filter)]
    filtered_df["month_year"] = filtered_df["order_purchase_timestamp"].dt.to_period(
        "M")
    df_regions_group = filtered_df.groupby(by=['month_year', 'customer_state'], as_index=False).agg({
        'customer_unique_id': 'count',
        'payment_value': 'sum'
    }).sort_values(by='month_year')
    df_regions_group.columns = [
        'month', 'region', 'order_count', 'order_amount']
    df_regions_group.reset_index(drop=True, inplace=True)
    df_regions_group['month'] = df_regions_group['month'].astype(str)
    df_regions_group['order_amount'] = pd.to_numeric(
        df_regions_group['order_amount'])

    fig = px.line(df_regions_group, x='month', y='order_amount', color='region',
                  labels={"month": "Month",
                          "order_amount": "Order Amount ($)", "region": "Region"},
                  title="Evolution of Sales by Region")
    fig.update_layout(title={'x': 0.5, 'xanchor': 'center'}, xaxis_title="Month", yaxis_title="Order Amount ($)",
                      legend_title="Region", template="plotly_white")
    st.plotly_chart(fig)

# Shipping Delays and Customer Satisfaction Page
elif page == "Shipping Delays and Customer Satisfaction":
    data = df[["order_delivered_customer_date",
               "order_delivered_carrier_date", "review_score", "product_category_name"]]
    data["order_delivered_customer_date"] = pd.to_datetime(
        data["order_delivered_customer_date"])
    data["order_delivered_carrier_date"] = pd.to_datetime(
        data["order_delivered_carrier_date"])
    data["delay_days"] = (data["order_delivered_customer_date"] -
                          data["order_delivered_carrier_date"]).dt.days

    bins = [-1, 0, 3, 7, 14, float("inf")]
    labels = ["No Delay", "1-3 Days", "4-7 Days", "8-14 Days", "15+ Days"]
    data["delay_category"] = pd.cut(
        data["delay_days"], bins=bins, labels=labels)

    fig_violin = px.violin(data, x="delay_category", y="review_score", color="delay_category",
                           category_orders={"delay_category": labels},
                           title="Distribution of Review Scores by Shipping Delay Category",
                           labels={"delay_category": "Shipping Delay Category",
                                   "review_score": "Review Score"},
                           box=True, points="all")
    fig_violin.update_layout(title={'x': 0.5, 'xanchor': 'center'}, xaxis_title="Shipping Delay Category",
                             yaxis_title="Review Score", template="plotly_white")
    st.plotly_chart(fig_violin)

    st.subheader("Top Product Categories with Highest Delays")
    delayed_orders = data[data["delay_days"] > 0]
    top_delayed_categories = delayed_orders["product_category_name"].value_counts(
    ).head(10)
    fig_top_delayed_categories = px.bar(top_delayed_categories, x=top_delayed_categories.index, y=top_delayed_categories.values,
                                        labels={"x": "Product Category", "y": "Number of Delayed Orders"}, title="Top 10 Product Categories with Highest Delays")
    fig_top_delayed_categories.update_layout(title={'x': 0.5, 'xanchor': 'center'}, xaxis_title="Product Category",
                                             yaxis_title="Number of Delayed Orders", template="plotly_white")
    st.plotly_chart(fig_top_delayed_categories)
