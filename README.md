# Adventure-Works-Streamlit-Dashboard
AdventureWorks Sales Dashboard – Layout Description
General Overview of Layihəyeye
An interactive analytics dashboard was prepared based on AdventureWorks sales information.
By combining sales, customer and product information covering the years 2015-2017
Visualized using Streamlit and Plotly.

Bringing Technology to Life (Python)
Information Preparation

Three years' sales CSVs merged with pd.concat
ProductPrice and CustomerName were added by merging from the appropriate tables
OrderAmount = OrderQuantity × ProductPrice calculated
Year, Quarter, Month, YearMonth removed from history columns

Performance

With @st.cache_data, the information is loaded only once, it is not read again with each filter change.

Dynamic Filters

Province, customer and product filters can be placed in the sidebar.
filter() Its functionality filters both the current year and the previous year with the same parameters.
delta() function calculates YoY interest rate change

Analytical Modules
ModulMethodRFMgroupby + pd.qcut with 5 pills scoring, special seqment functionalityCohortto_period("M") with cohort index, pivot + normalizeChurnDay calculation since last purchase date, dynamic threshold slider

Dashboard Functionality (6 Tabs)
* Overview
KPIs (Sales, Order, Customer, AOV) with YoY delta, monthly trend, rubluk bar, provincial comparison
* Products
Top-10 crop revenue and quantity, Top-5 monthly trend
* Customers
Top-10 customers, xərc sharing histogram, New vs. Kayidan customer donut
* RFM Segmentation
Champions / Loyal / At Risk / Lost / New / Potential segments,
segment sharing, income bar, Recency-Monetary scatter (bubble = Frequency)
* Cohort & Retention
Retention heatmap, average retention rate, new customers per cohort
* Churn
Dynamic threshold slider, Active vs Churned donut, day allocation histogram,
high value churn customers, detail sheet

Technologies Used
Python · Pandas · Streamlit · Plotly Express
