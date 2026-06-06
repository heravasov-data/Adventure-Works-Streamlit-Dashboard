import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="AdventureWorks Dashboard", layout="wide")

# ── Data ─────────────────────────────────────────────────────────────────────
BASE = Path(r"C:\Users\ShamilHeravasovNovum\Desktop\sample data")

@st.cache_data
def load_data():
    sales = pd.concat([
        pd.read_csv(BASE / f"AdventureWorks_Sales_{y}.csv")
        for y in [2015, 2016, 2017]
    ], ignore_index=True)

    prod = pd.read_csv(BASE / "AdventureWorks_Products.csv")
    cust = pd.read_csv(BASE / "AdventureWorks_Customers.csv", encoding="cp1252")

    # ProductName + Price
    prod_cols = ["ProductKey", "ProductPrice"] + (["ProductName"] if "ProductName" in prod.columns else [])
    sales = sales.merge(prod[prod_cols], on="ProductKey", how="left")
    if "ProductName" not in sales.columns:
        sales["ProductName"] = "Product-" + sales["ProductKey"].astype(str)

    # CustomerName
    if "FirstName" in cust.columns:
        cust["CustomerName"] = cust["FirstName"].str.strip() + " " + cust["LastName"].str.strip()
    elif "CustomerName" not in cust.columns:
        cust["CustomerName"] = "Cust-" + cust["CustomerKey"].astype(str)
    sales = sales.merge(cust[["CustomerKey", "CustomerName"]], on="CustomerKey", how="left")

    # Date + amount
    sales["OrderDate"]   = pd.to_datetime(sales["OrderDate"], errors="coerce")
    sales["Year"]        = sales["OrderDate"].dt.year
    sales["Quarter"]     = "Q" + sales["OrderDate"].dt.quarter.astype(str)
    sales["MonthNo"]     = sales["OrderDate"].dt.month
    sales["Month"]       = sales["OrderDate"].dt.strftime("%b")
    sales["YearMonth"]   = sales["OrderDate"].dt.to_period("M").astype(str)
    sales["OrderAmount"] = sales["OrderQuantity"] * sales["ProductPrice"]
    return sales

df_all = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("Filters")
year      = st.sidebar.selectbox("Year", sorted(df_all["Year"].unique()), index=2)
sel_cust  = st.sidebar.multiselect("Customer", sorted(df_all["CustomerName"].dropna().unique()))
sel_prod  = st.sidebar.multiselect("Product",  sorted(df_all["ProductName"].dropna().unique()))

def filt(base, y):
    d = base[base["Year"] == y].copy()
    if sel_cust: d = d[d["CustomerName"].isin(sel_cust)]
    if sel_prod: d = d[d["ProductName"].isin(sel_prod)]
    return d

df   = filt(df_all, year)
prev = filt(df_all, year - 1)

def delta(a, b):
    return f"{(a-b)/b*100:+.1f}%" if b > 0 else "—"

# ── Title + Tabs ──────────────────────────────────────────────────────────────
st.title("📊 AdventureWorks Sales Dashboard")
t1, t2, t3, t4, t5, t6 = st.tabs(
    ["📈 Overview", "🛍️ Products", "👥 Customers", "🎯 RFM", "🔄 Cohort", "⚠️ Churn"]
)

# ── Overview ──────────────────────────────────────────────────────────────────
with t1:
    s, o, c = df["OrderAmount"].sum(), len(df), df["CustomerKey"].nunique()
    ps, po, pc = prev["OrderAmount"].sum(), len(prev), prev["CustomerKey"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Sales",     f"${s:,.0f}",  delta(s, ps))
    c2.metric("📦 Orders",    f"{o:,}",      delta(o, po))
    c3.metric("👤 Customers", f"{c:,}",      delta(c, pc))
    c4.metric("🧾 Avg Order", f"${s/o:,.2f}" if o else "$0", delta(s/o if o else 0, ps/po if po else 0))

    st.markdown("---")
    col1, col2 = st.columns(2)

    monthly = df.groupby(["MonthNo","Month"])["OrderAmount"].sum().reset_index().sort_values("MonthNo")
    col1.plotly_chart(
        px.line(monthly, x="Month", y="OrderAmount", markers=True,
                title=f"Monthly Sales – {year}", labels={"OrderAmount":"Sales ($)"}),
        use_container_width=True
    )

    quarterly = df.groupby("Quarter")["OrderAmount"].sum().reset_index()
    col2.plotly_chart(
        px.bar(quarterly, x="Quarter", y="OrderAmount",
               title="Quarterly Sales", color="Quarter",
               color_discrete_sequence=px.colors.qualitative.Set2,
               labels={"OrderAmount":"Sales ($)"}).update_layout(showlegend=False),
        use_container_width=True
    )

    if len(prev) > 0:
        mc = df.groupby(["MonthNo","Month"])["OrderAmount"].sum().reset_index()
        mp = prev.groupby(["MonthNo","Month"])["OrderAmount"].sum().reset_index()
        mc["Year"], mp["Year"] = str(year), str(year-1)
        st.plotly_chart(
            px.line(pd.concat([mc, mp]).sort_values("MonthNo"),
                    x="Month", y="OrderAmount", color="Year", markers=True,
                    title="YoY Comparison", labels={"OrderAmount":"Sales ($)"},
                    color_discrete_sequence=["#1f77b4","#ff7f0e"]),
            use_container_width=True
        )

# ── Products ──────────────────────────────────────────────────────────────────
with t2:
    col1, col2 = st.columns(2)
    top_rev = df.groupby("ProductName")["OrderAmount"].sum().nlargest(10).reset_index().sort_values("OrderAmount")
    col1.plotly_chart(
        px.bar(top_rev, x="OrderAmount", y="ProductName", orientation="h",
               title="Top 10 – Revenue", color="OrderAmount", color_continuous_scale="Blues",
               labels={"OrderAmount":"Sales ($)","ProductName":""}).update_layout(coloraxis_showscale=False),
        use_container_width=True
    )
    top_qty = df.groupby("ProductName")["OrderQuantity"].sum().nlargest(10).reset_index().sort_values("OrderQuantity")
    col2.plotly_chart(
        px.bar(top_qty, x="OrderQuantity", y="ProductName", orientation="h",
               title="Top 10 – Units Sold", color="OrderQuantity", color_continuous_scale="Greens",
               labels={"OrderQuantity":"Units","ProductName":""}).update_layout(coloraxis_showscale=False),
        use_container_width=True
    )

    top5 = df.groupby("ProductName")["OrderAmount"].sum().nlargest(5).index.tolist()
    trend = (df[df["ProductName"].isin(top5)]
             .groupby(["MonthNo","Month","ProductName"])["OrderAmount"]
             .sum().reset_index().sort_values("MonthNo"))
    st.plotly_chart(
        px.line(trend, x="Month", y="OrderAmount", color="ProductName", markers=True,
                title="Top 5 Products – Monthly Trend", labels={"OrderAmount":"Sales ($)"}),
        use_container_width=True
    )

# ── Customers ─────────────────────────────────────────────────────────────────
with t3:
    col1, col2 = st.columns(2)
    top_c = df.groupby("CustomerName")["OrderAmount"].sum().nlargest(10).reset_index().sort_values("OrderAmount")
    col1.plotly_chart(
        px.bar(top_c, x="OrderAmount", y="CustomerName", orientation="h",
               title="Top 10 Customers", color="OrderAmount", color_continuous_scale="Oranges",
               labels={"OrderAmount":"Sales ($)","CustomerName":""}).update_layout(coloraxis_showscale=False),
        use_container_width=True
    )
    spend = df.groupby("CustomerKey")["OrderAmount"].sum().reset_index()
    col2.plotly_chart(
        px.histogram(spend, x="OrderAmount", nbins=40,
                     title="Spend Distribution", labels={"OrderAmount":"Total Spend ($)"},
                     color_discrete_sequence=["#636EFA"]),
        use_container_width=True
    )

    first_yr = df_all.groupby("CustomerKey")["OrderDate"].min().dt.year.reset_index().rename(columns={"OrderDate":"FirstYear"})
    d2 = df.merge(first_yr, on="CustomerKey", how="left")
    d2["Type"] = d2["FirstYear"].apply(lambda x: "🆕 New" if x == year else "🔄 Returning")
    type_agg = d2.groupby("Type").agg(Revenue=("OrderAmount","sum"), Customers=("CustomerKey","nunique")).reset_index()

    col3, col4 = st.columns(2)
    col3.plotly_chart(
        px.pie(type_agg, values="Revenue",   names="Type", title="Revenue: New vs Returning",   hole=0.45),
        use_container_width=True
    )
    col4.plotly_chart(
        px.pie(type_agg, values="Customers", names="Type", title="Customers: New vs Returning", hole=0.45),
        use_container_width=True
    )

# ── RFM ───────────────────────────────────────────────────────────────────────
with t4:
    st.subheader("RFM Segmentation")
    base = df_all[df_all["Year"] <= year]
    snap = base["OrderDate"].max() + pd.Timedelta(days=1)

    rfm = base.groupby("CustomerKey").agg(
        Recency   = ("OrderDate",   lambda x: (snap - x.max()).days),
        Frequency = ("OrderDate",   "count"),
        Monetary  = ("OrderAmount", "sum")
    ).reset_index().merge(
        df_all[["CustomerKey","CustomerName"]].drop_duplicates(), on="CustomerKey", how="left"
    )

    for col, vals, dup in [
        ("R_Score", [5,4,3,2,1], rfm["Recency"]),
        ("F_Score", [1,2,3,4,5], rfm["Frequency"].rank(method="first")),
        ("M_Score", [1,2,3,4,5], rfm["Monetary"])
    ]:
        try:    rfm[col] = pd.qcut(dup, 5, labels=vals, duplicates="drop")
        except: rfm[col] = 3

    rfm["RFM_Score"] = rfm["R_Score"].astype(int) + rfm["F_Score"].astype(int) + rfm["M_Score"].astype(int)

    def seg(r):
        r_, f_, m_ = int(r["R_Score"]), int(r["F_Score"]), int(r["M_Score"])
        if r_ >= 4 and f_ >= 4 and m_ >= 4: return "🏆 Champions"
        if r_ >= 3 and f_ >= 3:             return "💎 Loyal"
        if r_ >= 4 and f_ <= 2:             return "🆕 New"
        if r_ <= 2 and f_ >= 3:             return "⚠️ At Risk"
        if r_ <= 2 and f_ <= 2:             return "💀 Lost"
        return "🌱 Potential"

    rfm["Segment"] = rfm.apply(seg, axis=1)
    sc, n = rfm["Segment"].value_counts(), len(rfm)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🏆 Champions", f'{sc.get("🏆 Champions",0):,}', f'{sc.get("🏆 Champions",0)/n*100:.1f}%')
    k2.metric("💎 Loyal",     f'{sc.get("💎 Loyal",0):,}',     f'{sc.get("💎 Loyal",0)/n*100:.1f}%')
    k3.metric("⚠️ At Risk",   f'{sc.get("⚠️ At Risk",0):,}',   f'{sc.get("⚠️ At Risk",0)/n*100:.1f}%')
    k4.metric("💀 Lost",      f'{sc.get("💀 Lost",0):,}',      f'{sc.get("💀 Lost",0)/n*100:.1f}%')
    st.markdown("---")

    seg_agg = rfm.groupby("Segment").agg(Customers=("CustomerKey","count"), Revenue=("Monetary","sum")).reset_index()
    col1, col2 = st.columns(2)
    col1.plotly_chart(px.pie(seg_agg, values="Customers", names="Segment", title="Segment Distribution", hole=0.45), use_container_width=True)
    col2.plotly_chart(
        px.bar(seg_agg.sort_values("Revenue"), x="Revenue", y="Segment", orientation="h",
               title="Revenue by Segment", color="Revenue", color_continuous_scale="RdYlGn",
               labels={"Revenue":"Revenue ($)"}).update_layout(coloraxis_showscale=False, yaxis_title=""),
        use_container_width=True
    )
    st.plotly_chart(
        px.scatter(rfm, x="Recency", y="Monetary", size="Frequency", color="Segment",
                   hover_data=["CustomerName","RFM_Score"],
                   title="RFM Scatter (bubble = Frequency)",
                   labels={"Recency":"Recency (days)","Monetary":"Revenue ($)"}),
        use_container_width=True
    )
    st.dataframe(
        rfm[["CustomerName","Recency","Frequency","Monetary","RFM_Score","Segment"]]
          .sort_values("RFM_Score", ascending=False),
        use_container_width=True
    )

# ── Cohort & Retention ────────────────────────────────────────────────────────
with t5:
    st.subheader("Cohort & Retention")
    coh = df_all.copy()
    coh["CohortMonth"] = coh.groupby("CustomerKey")["OrderDate"].transform("min").dt.to_period("M")
    coh["OrderPeriod"] = coh["OrderDate"].dt.to_period("M")
    coh["CohortIndex"] = (coh["OrderPeriod"] - coh["CohortMonth"]).apply(lambda x: x.n)

    pivot = (coh.groupby(["CohortMonth","CohortIndex"])["CustomerKey"]
               .nunique().reset_index()
               .pivot(index="CohortMonth", columns="CohortIndex", values="CustomerKey"))
    ret = (pivot.divide(pivot.iloc[:,0], axis=0) * 100).round(1).iloc[:,:12]
    ret.index, ret.columns = ret.index.astype(str), [f"M+{c}" for c in ret.columns]

    st.plotly_chart(
        px.imshow(ret, color_continuous_scale="Blues", aspect="auto",
                  title="Retention Heatmap (%)",
                  labels={"x":"Month Since 1st Purchase","y":"Cohort","color":"%"})
          .update_xaxes(side="top"),
        use_container_width=True
    )

    col1, col2 = st.columns(2)
    avg = ret.mean()
    col1.plotly_chart(
        px.line(x=avg.index, y=avg.values, markers=True,
                title="Average Retention Curve", labels={"x":"Month","y":"Retention %"})
          .update_traces(line_color="#e63946", line_width=2.5),
        use_container_width=True
    )
    new_c = pivot.iloc[:,0].reset_index().rename(columns={0:"NewCustomers","CohortMonth":"Cohort"})
    new_c["Cohort"] = new_c["Cohort"].astype(str)
    col2.plotly_chart(
        px.bar(new_c, x="Cohort", y="NewCustomers", title="New Customers per Cohort",
               color="NewCustomers", color_continuous_scale="Purples")
          .update_layout(coloraxis_showscale=False, xaxis_tickangle=-45),
        use_container_width=True
    )

# ── Churn ─────────────────────────────────────────────────────────────────────
with t6:
    st.subheader("Churn Analysis")
    threshold = st.slider("Churn threshold (days since last purchase)", 30, 365, 90, 30)

    base = df_all[df_all["Year"] <= year]
    snap = base["OrderDate"].max()

    lp = (base.groupby(["CustomerKey","CustomerName"])["OrderDate"]
              .max().reset_index()
              .rename(columns={"OrderDate":"LastPurchase"}))
    lp["Days"]   = (snap - lp["LastPurchase"]).dt.days
    lp["Status"] = lp["Days"].apply(lambda x: "Churned" if x > threshold else "Active")

    total  = len(lp)
    active = (lp["Status"] == "Active").sum()
    churn  = total - active

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("👥 Total",    f"{total:,}")
    k2.metric("✅ Active",   f"{active:,}", f"{active/total*100:.1f}%")
    k3.metric("❌ Churned",  f"{churn:,}",  f"{churn/total*100:.1f}%")
    k4.metric("📉 Churn Rate", f"{churn/total*100:.1f}%")
    st.markdown("---")

    col1, col2 = st.columns(2)
    col1.plotly_chart(
        px.pie(lp["Status"].value_counts().reset_index().rename(columns={"Status":"Status","count":"Count"}),
               values="Count", names="Status", title="Active vs Churned", hole=0.5,
               color="Status", color_discrete_map={"Active":"#2ecc71","Churned":"#e74c3c"}),
        use_container_width=True
    )
    col2.plotly_chart(
        px.histogram(lp, x="Days", nbins=50, color="Status",
                     color_discrete_map={"Active":"#2ecc71","Churned":"#e74c3c"},
                     title="Days Since Last Purchase",
                     labels={"Days":"Days Since Last Purchase"})
          .add_vline(x=threshold, line_dash="dash", line_color="red",
                     annotation_text=f"Threshold ({threshold}d)"),
        use_container_width=True
    )

    # High-value churned
    churned_keys = lp.loc[lp["Status"]=="Churned","CustomerKey"].tolist()
    top_churned  = (base[base["CustomerKey"].isin(churned_keys)]
                    .groupby(["CustomerKey","CustomerName"])["OrderAmount"]
                    .sum().nlargest(10).reset_index().sort_values("OrderAmount"))
    st.plotly_chart(
        px.bar(top_churned, x="OrderAmount", y="CustomerName", orientation="h",
               title="Top Churned – Historical Spend",
               color="OrderAmount", color_continuous_scale="Reds",
               labels={"OrderAmount":"Spend ($)","CustomerName":""})
          .update_layout(coloraxis_showscale=False),
        use_container_width=True
    )

    st.subheader("Churned Customers")
    tbl = lp[lp["Status"]=="Churned"].copy()
    tbl["LastPurchase"] = tbl["LastPurchase"].dt.date
    st.dataframe(tbl.sort_values("Days", ascending=False), use_container_width=True)
