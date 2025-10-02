import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Customer Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- LOAD DATA & CUSTOMER SEGMENT CREATION ---
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/Roysihombing/Building-Portfolio-with-Streamlit/main/data/data_final.csv"
    df = pd.read_csv(url)
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df.dropna(inplace=True)

    # Discount usage flag
    df["use_discount"] = df["coupon_code"].apply(lambda x: "Used Discount" if x != "NONKUPON" else "No Discount")

    # Customer segmentation (based on total spending)
    customer_sales = df.groupby("customer_id")["total"].sum().reset_index()
    quantiles = customer_sales["total"].quantile([0.33, 0.66])
    low_th, high_th = quantiles[0.33], quantiles[0.66]

    def segment_customer(x):
        if x <= low_th:
            return "Low Value"
        elif x <= high_th:
            return "Medium Value"
        else:
            return "High Value"

    customer_sales["customer_segment"] = customer_sales["total"].apply(segment_customer)
    df = df.merge(customer_sales[["customer_id", "customer_segment"]], on="customer_id", how="left")

    return df

df = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Data 🔎")

years = sorted(df["transaction_date"].dt.year.unique())
year_filter = st.sidebar.multiselect("Select Year", options=years)

cities = df["city"].unique()
city_filter = st.sidebar.multiselect("Select City", options=cities)

products = df["product_name"].unique()
product_filter = st.sidebar.multiselect("Select Product", options=products)

segments = df["customer_segment"].unique()
segment_filter = st.sidebar.multiselect("Select Customer Segment", options=segments)

df_selection = df.copy()
if year_filter:
    df_selection = df_selection[df_selection["transaction_date"].dt.year.isin(year_filter)]
if city_filter:
    df_selection = df_selection[df_selection["city"].isin(city_filter)]
if product_filter:
    df_selection = df_selection[df_selection["product_name"].isin(product_filter)]
if segment_filter:
    df_selection = df_selection[df_selection["customer_segment"].isin(segment_filter)]

# --- KPI METRICS ---
st.title("📊 Customer Dashboard (2022 - 2024)")
st.caption("This dashboard provides insights into sales trends, top products, city performance, storage preferences, discount usage, and customer demographics.")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Sales", f"{df_selection['total'].sum()/1e12:.2f} Trillion")
with col2:
    st.metric("Quantity Sold", f"{df_selection['quantity'].astype(int).sum():,}")
with col3:
    st.metric("Total Orders", f"{df_selection['transaction_id'].nunique():,}")
with col4:
    st.metric("Avg. Sales per Order", f"{df_selection['total'].mean()/1e6:.2f} Million")
with col5:
    st.metric("Unique Products", df_selection["product_name"].nunique())

st.markdown("---")

# 1. Monthly Sales Trend
st.subheader("How does the monthly sales trend look? 📈 ")
sales_trend = df_selection.groupby(df_selection["transaction_date"].dt.strftime("%Y-%m"))["total"].sum()
st.line_chart(sales_trend)

last_date = df["transaction_date"].max().strftime("%d %B %Y")
if "2024-12" in sales_trend.index:
    st.info(f"The decline ℹ️ in December 2024 is because the dataset only contains transactions until **{last_date}**, not the full month.")

if len(sales_trend) > 1:
    growth = (sales_trend.iloc[-1] - sales_trend.iloc[-2]) / sales_trend.iloc[-2] * 100
    st.markdown(f"**Insight:** Sales in the last month changed by **{growth:.1f}%** compared to the previous month.")

# 2. Top 5 Cities (Donut Chart)
st.subheader("Which cities contribute the most to sales?")
city_sales = df_selection.groupby("city")["total"].sum().sort_values(ascending=False).head(5).reset_index()
fig_city = px.pie(city_sales, values="total", names="city", hole=0.5,
                  color_discrete_sequence=px.colors.sequential.Viridis)
st.plotly_chart(fig_city, use_container_width=True)
if not city_sales.empty:
    top_city, top_value = city_sales.iloc[0]["city"], city_sales.iloc[0]["total"]
    st.markdown(f"**Insight:** The city with the highest sales is **{top_city}** with {top_value:,.0f} in total sales.")

# 3. Top 5 Products (Bar Chart)
st.subheader("Which products are the best sellers?")
top5_products = df_selection.groupby("product_name")["total"].sum().sort_values(ascending=False).head(5).reset_index()
fig_products = px.bar(top5_products, x="product_name", y="total",
                      color="total", color_continuous_scale="Blues")
fig_products.update_layout(xaxis={'categoryorder': 'total descending'})
st.plotly_chart(fig_products, use_container_width=True)
if not top5_products.empty:
    best_product = top5_products.iloc[0]["product_name"]
    st.markdown(f"**Insight:** The most sold product is **{best_product}**.")

# 4. Sales by Storage (Bar Chart)
st.subheader("Which storage options are most popular?")
storage_sales = df_selection.groupby("storage")["total"].sum().sort_values(ascending=False).reset_index()
fig_storage = px.bar(storage_sales, x="storage", y="total",
                     color="total", color_continuous_scale="Blues")
fig_storage.update_layout(xaxis={'categoryorder':'total descending'})
st.plotly_chart(fig_storage, use_container_width=True)
if not storage_sales.empty:
    fav_storage = storage_sales.iloc[0]["storage"]
    st.markdown(f"**Insight:** The most popular storage option is **{fav_storage}**.")

# 5. Discount Usage (Donut Chart)
st.subheader("How many customers use discounts?")
discount_dist = df_selection["use_discount"].value_counts().reset_index()
discount_dist.columns = ["use_discount", "count"]
fig_disc = px.pie(discount_dist, values="count", names="use_discount", hole=0.5,
                  color_discrete_sequence=px.colors.sequential.Magma)
st.plotly_chart(fig_disc, use_container_width=True)
if not discount_dist.empty:
    used = discount_dist.loc[discount_dist["use_discount"]=="Used Discount","count"].sum()
    total = discount_dist["count"].sum()
    st.markdown(f"**Insight:** {used/total*100:.1f}% of transactions used a discount.")

# 6. Age Distribution (Bar Chart)
st.subheader("What is the age distribution of customers?")
age_dist = df_selection["usia_group"].value_counts().sort_values(ascending=False).reset_index()
age_dist.columns = ["usia_group", "count"]
fig_age = px.bar(age_dist, x="usia_group", y="count",
                 color="count", color_continuous_scale="Blues")
fig_age.update_layout(xaxis={'categoryorder':'total descending'})
st.plotly_chart(fig_age, use_container_width=True)
if not age_dist.empty:
    dom_age = age_dist.iloc[0]["usia_group"]
    st.markdown(f"**Insight:** The dominant customer age group is **{dom_age}**.")

st.markdown("---")

# --- RAW DATA VIEW ---
st.subheader("📑 Raw Data")
with st.expander("Click to view raw data"):
    st.dataframe(df_selection)
    st.markdown(f"**Data Dimensions:** {df_selection.shape[0]} rows × {df_selection.shape[1]} columns")

st.markdown("---")
st.caption("Final Project Dashboard • by Roy Firman Sihombing")
