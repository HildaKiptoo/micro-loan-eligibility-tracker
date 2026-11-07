# Microfinance Credit Risk & Eligibility Analytics

![Borrower Eligibility Matrix](images/borrower_eligibility_matrix.png)

## 📌 Executive Summary
**The Business Problem:** Microfinance institutions must balance expanding financial access with managing default risk. Lenders need a reliable, automated way to evaluate borrower repayment discipline to confidently offer credit limit expansions without exposing the business to bad debt.

**The Solution:** I engineered a programmatic credit scoring engine and a synthetic micro-lending database using Python. The project evaluates borrower repayment history and automatically segments users into risk tiers, visualized through interactive Plotly charts. 

**Business Impact:** This automated scoring logic allows credit teams to instantly identify the top percentage of "Tier 1: Prime" borrowers eligible for credit limit expansion, removing manual guesswork and optimizing the loan portfolio's profitability.

---

## 🛠️ Tools & Technologies Used
* **Data Engineering (Synthetic):** Python (Pandas, NumPy, Faker)
* **Interactive Visualization:** Plotly
* **Development Environment:** Jupyter Notebook
* **Domain Context:** Micro-lending, Credit Risk Scoring, Kenyan Shillings (KES) Denomination

---

## 📊 Key Insights & Scoring Model
*(Note: As the data is synthetic, these findings demonstrate the logic and capability of the scoring engine.)*

1. **Automated Tiering:** The scoring engine successfully segments borrowers into four distinct campaign categories based on historical repayment consistency and limit utilization.
2. **Expansion Targeting (Tier 1):** The model isolated a specific cohort of highly disciplined borrowers ("Ready for 1.5x Limit Top-Up") who consistently clear their micro-loans early or exactly on time, while maintaining over 85% credit utilization.
3. **Risk Mitigation (Tier 4):** Borrowers averaging more than 5 days late on payments are automatically flagged for a "Risk Hold / Freeze," regardless of their utilization rate.

### Incremental Credit Opportunity

![Incremental Credit Opportunity by Segment](images/borrower_eligibility_matrix2.png)

By applying the 1.5x limit expansion exclusively to Tier 1 borrowers, the model projects the potential incremental credit line (in KES) available across different employment segments and regions. 

**Finding:** The SME Trader segment in Nairobi represents the highest volume opportunity for safe credit expansion, with a projected 3.0M KES in safe, incremental credit lines.

---

## ⚙️ Methodology & Approach

1. **Synthetic Data Generation:** Designed a custom Python script utilizing the `Faker` library to generate a realistic, reproducible dataset of borrower profiles and historical loan transactions denominated in KES.
2. **Feature Engineering:** Calculated critical financial metrics for each borrower, including Average Days from Due Date and Average Credit Limit Utilization Ratio.
3. **Logic-Based Scoring:** Built a weighted algorithmic scoring system in Pandas to evaluate borrower behavior and assign a definitive risk/campaign tier.
4. **Data Visualization:** Deployed interactive Plotly scatter plots and bar charts to provide a clear visual matrix of borrower eligibility and projected financial opportunity.

---

## 💻 How to Run This Project

1. **Clone this repository:**
   ```bash
   git clone [https://github.com/HildaKiptoo/micro-loan-eligibility-tracker.git](https://github.com/HildaKiptoo/micro-loan-eligibility-tracker.git)
