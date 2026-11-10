import streamlit as st
import pandas as pd
import numpy as np
from faker import Faker
import plotly.express as px
import matplotlib.pyplot as plt

# -----------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------
st.set_page_config(page_title="Micro-Loan Eligibility Tracker", layout="wide")
st.title("Micro-Loan Repeat Borrower Eligibility Tracker")
st.write(
    "Analyze historical micro-loan repayment behavior, limit utilization, and dormancy to segment borrowers into actionable campaigns.")


# -----------------------------------------
# DATA GENERATION (CACHED)
# -----------------------------------------
@st.cache_data
def load_and_score_data():
    fake = Faker()
    np.random.seed(42)
    SNAPSHOT_DATE = pd.to_datetime("2026-11-01")

    # Step 2: Generate Customers
    n_borrowers = 6000
    segments = ["SME Trader", "Salaried Worker", "Gig / Boda Operator", "Agri-Vendor"]
    regions = ["Nairobi", "Nakuru", "Kisumu", "Mombasa", "Eldoret"]
    credit_limits = [2500, 5000, 10000, 15000, 25000, 50000]

    borrowers = []
    for i in range(1, n_borrowers + 1):
        onboard_date = pd.to_datetime(fake.date_between(start_date="-18m", end_date="-3m"))
        borrowers.append({
            "borrower_id": f"BRW-{1000 + i}",
            "full_name": fake.name(),
            "region": np.random.choice(regions, p=[0.40, 0.18, 0.15, 0.15, 0.12]),
            "employment_segment": np.random.choice(segments, p=[0.40, 0.25, 0.20, 0.15]),
            "onboarding_date": onboard_date,
            "current_credit_limit_kes": int(np.random.choice(credit_limits, p=[0.15, 0.25, 0.25, 0.15, 0.12, 0.08]))
        })
    dim_borrowers = pd.DataFrame(borrowers)

    # Step 3: Simulate Historical Loans
    SNAPSHOT_DATE = pd.to_datetime(dim_borrowers["onboarding_date"]).max() + pd.Timedelta(days=365)

    loans = []
    loan_counter = 5000
    for _, brw in dim_borrowers.iterrows():
        n_loans = int(np.random.randint(2, 7))
        curr_date = pd.to_datetime(brw["onboarding_date"]) + pd.Timedelta(days=int(np.random.randint(2, 15)))
        persona = np.random.choice(["Prime", "Average", "Late_Risk"], p=[0.48, 0.32, 0.20])

        for l_idx in range(n_loans):
            if curr_date >= SNAPSHOT_DATE - pd.Timedelta(days=5):
                break

            util_pct = float(np.random.uniform(0.88, 1.0)) if persona == "Prime" else float(
                np.random.uniform(0.50, 0.95))
            loan_amt = int(round((brw["current_credit_limit_kes"] * util_pct) / 100.0) * 100)
            tenure_days = int(np.random.choice([14, 30], p=[0.35, 0.65]))
            due_date = curr_date + pd.Timedelta(days=tenure_days)

            if persona == "Prime":
                days_diff = int(np.random.choice([-5, -3, -2, -1, 0, 1], p=[0.20, 0.25, 0.20, 0.15, 0.15, 0.05]))
            elif persona == "Average":
                days_diff = int(np.random.choice([-2, 0, 2, 4, 6], p=[0.15, 0.40, 0.20, 0.15, 0.10]))
            else:
                days_diff = int(np.random.choice([0, 5, 10, 18, 35], p=[0.10, 0.25, 0.30, 0.20, 0.15]))

            actual_repay_date = due_date + pd.Timedelta(days=days_diff)

            if actual_repay_date > SNAPSHOT_DATE:
                status = "Active / Open"
                actual_repay_date = pd.NaT
                days_diff_recorded = np.nan
            else:
                days_diff_recorded = days_diff
                if days_diff < 0:
                    status = "Repaid Early"
                elif days_diff == 0:
                    status = "On-Time"
                elif days_diff <= 7:
                    status = "Late (1-7 Days)"
                else:
                    status = "High Risk (8+ Days Late)"

            interest_rate = 0.08 if tenure_days == 14 else 0.12
            fee_paid = int(round(loan_amt * interest_rate, 0)) if status != "Active / Open" else 0

            loan_counter += 1
            loans.append({
                "loan_id": f"LN-{loan_counter}",
                "borrower_id": brw["borrower_id"],
                "disbursement_date": curr_date,
                "tenure_days": tenure_days,
                "due_date": due_date,
                "actual_repayment_date": actual_repay_date,
                "loan_amount_kes": loan_amt,
                "interest_fee_kes": fee_paid,
                "days_from_due_date": days_diff_recorded,
                "repayment_status": status
            })

            if pd.isna(actual_repay_date):
                break

            gap_days = int(np.random.randint(4, 40))
            curr_date = actual_repay_date + pd.Timedelta(days=gap_days)

    fact_loans = pd.DataFrame(loans)

    # Step 4: Aggregate Repayment Behavior
    closed_loans = fact_loans[fact_loans["repayment_status"] != "Active / Open"].copy()
    active_borrowers = set(fact_loans[fact_loans["repayment_status"] == "Active / Open"]["borrower_id"])

    summary = closed_loans.groupby("borrower_id").agg(
        completed_loans=("loan_id", "count"),
        total_principal_borrowed_kes=("loan_amount_kes", "sum"),
        total_interest_paid_kes=("interest_fee_kes", "sum"),
        avg_loan_amount_kes=("loan_amount_kes", "mean"),
        avg_days_from_due=("days_from_due_date", "mean"),
        max_days_late=("days_from_due_date", "max"),
        last_repayment_date=("actual_repayment_date", "max")
    ).reset_index()

    summary["avg_loan_amount_kes"] = summary["avg_loan_amount_kes"].round(0)
    summary["avg_days_from_due"] = summary["avg_days_from_due"].round(2)

    # Step 5: Feature Engineering
    scored_df = pd.merge(dim_borrowers, summary, on="borrower_id", how="left")
    scored_df["has_active_loan"] = scored_df["borrower_id"].isin(active_borrowers)
    scored_df["limit_utilization_pct"] = (
                scored_df["avg_loan_amount_kes"] / scored_df["current_credit_limit_kes"]).round(3)
    scored_df["days_since_last_repayment"] = (SNAPSHOT_DATE - scored_df["last_repayment_date"]).dt.days

    # Step 6: Campaign Tier Rules
    def classify_borrower(row):
        if pd.isna(row["completed_loans"]) or row["max_days_late"] > 7:
            return "Tier 4: Risk Hold / Freeze"
        if row["has_active_loan"]:
            return "Tier 3: Standard Active (Open Loan)"
        if row["completed_loans"] >= 2 and row["avg_days_from_due"] <= 0.5 and row["limit_utilization_pct"] >= 0.85:
            return "Tier 1: Ready for 1.5x Limit Top-Up"
        if row["avg_days_from_due"] <= 2.0 and row["days_since_last_repayment"] >= 10:
            return "Tier 2: Dormant Reactivation Offer"
        return "Tier 3: Standard Repeat Offer"

    scored_df["campaign_tier"] = scored_df.apply(classify_borrower, axis=1)
    scored_df["recommended_limit_kes"] = np.where(
        scored_df["campaign_tier"] == "Tier 1: Ready for 1.5x Limit Top-Up",
        (scored_df["current_credit_limit_kes"] * 1.5).round(0),
        scored_df["current_credit_limit_kes"]
    )
    scored_df["upsell_credit_delta_kes"] = scored_df["recommended_limit_kes"] - scored_df["current_credit_limit_kes"]

    tier_summary = scored_df.groupby("campaign_tier").agg(
        borrower_count=("borrower_id", "count"),
        current_credit_exposure_kes=("current_credit_limit_kes", "sum"),
        incremental_credit_upsell_kes=("upsell_credit_delta_kes", "sum")
    ).reset_index()

    return scored_df, tier_summary, fact_loans


# Execute the data pipeline
scored_df, tier_summary, fact_loans = load_and_score_data()

# -----------------------------------------
# DASHBOARD UI
# -----------------------------------------

# Top KPI Row
col1, col2, col3 = st.columns(3)
col1.metric("Total Borrowers", f"{len(scored_df):,}")
col2.metric("Total Loans Issued", f"{len(fact_loans):,}")
upsell_opp = tier_summary['incremental_credit_upsell_kes'].sum()
col3.metric("Tier 1 Upsell Opportunity (KES)", f"KES {upsell_opp:,.0f}")

st.divider()

# Create Tabs for visual organization
tab1, tab2, tab3 = st.tabs(["Interactive Visualizations", "Campaign Tier Summary", "Matplotlib EDA"])

with tab1:
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        # Plotly Scatter Matrix
        fig1 = px.scatter(
            scored_df[scored_df["completed_loans"].notna()],
            x="avg_days_from_due",
            y="limit_utilization_pct",
            color="campaign_tier",
            size="current_credit_limit_kes",
            hover_data=["borrower_id", "full_name", "employment_segment", "days_since_last_repayment"],
            title="Borrower Eligibility Matrix",
            labels={
                "avg_days_from_due": "Avg Days from Due Date",
                "limit_utilization_pct": "Avg Credit Limit Utilization",
                "campaign_tier": "Campaign Tier"
            },
            template="plotly_white",
            height=520
        )
        fig1.add_vline(x=0.5, line_dash="dash", line_color="green", annotation_text="On-Time Cutoff (0.5d)")
        fig1.add_hline(y=0.85, line_dash="dash", line_color="green", annotation_text="85% Utilization")

        st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        # Plotly Bar Chart
        tier1_df = scored_df[scored_df["campaign_tier"] == "Tier 1: Ready for 1.5x Limit Top-Up"]
        seg_region_upsell = tier1_df.groupby(["employment_segment", "region"], as_index=False)[
            "upsell_credit_delta_kes"].sum()

        fig2 = px.bar(
            seg_region_upsell,
            x="employment_segment",
            y="upsell_credit_delta_kes",
            color="region",
            barmode="group",
            text_auto=".2s",
            title="Tier 1 Incremental Credit Opportunity (KES)",
            labels={
                "upsell_credit_delta_kes": "Incremental Line (KES)",
                "employment_segment": "Employment Segment",
                "region": "Region"
            },
            template="plotly_white",
            height=480
        )
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("Campaign Tier Breakdown")
    st.dataframe(tier_summary, use_container_width=True)

    st.subheader("Sample Scored Borrowers")
    st.dataframe(scored_df[["borrower_id", "current_credit_limit_kes", "completed_loans", "avg_days_from_due",
                            "limit_utilization_pct", "days_since_last_repayment", "campaign_tier"]].head(15),
                 use_container_width=True)

with tab3:
    col_mpl1, col_mpl2 = st.columns(2)

    with col_mpl1:
        st.write("**Borrower Repayment Timing Distribution**")
        fig, ax = plt.subplots(figsize=(8, 4))
        clean_days = scored_df["avg_days_from_due"].dropna()
        ax.hist(clean_days, bins=25, color="#2b5c8f", edgecolor="white", alpha=0.85)
        ax.axvline(0.5, color="#d95f02", linestyle="--", linewidth=2, label="Tier 1 Cutoff")
        ax.axvline(7.0, color="#e7298a", linestyle=":", linewidth=2, label="Risk Freeze Threshold")
        ax.set_title("Distribution of Repayment Timing")
        ax.set_xlabel("Avg Days from Due Date")
        ax.set_ylabel("Number of Borrowers")
        ax.legend()
        st.pyplot(fig)

    with col_mpl2:
        st.write("**Portfolio by Assigned Campaign Tier**")
        tier_counts = scored_df["campaign_tier"].value_counts().sort_values(ascending=True)
        fig_bar, ax_bar = plt.subplots(figsize=(8, 4))
        colors = ["#7570b3", "#d95f02", "#66a61e", "#1b9e77"]
        bars = ax_bar.barh(tier_counts.index, tier_counts.values, color=colors[:len(tier_counts)], edgecolor="black",
                           alpha=0.85)
        for bar in bars:
            width = bar.get_width()
            ax_bar.text(width + 5, bar.get_y() + bar.get_height() / 2, f"{int(width)}", va="center", fontsize=10,
                        fontweight="bold")
        ax_bar.set_title("Existing Borrower Portfolio")
        ax_bar.set_xlabel("Number of Borrowers")
        ax_bar.set_xlim(0, max(tier_counts.values) * 1.15)
        st.pyplot(fig_bar)