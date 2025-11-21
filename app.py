import datetime as dt
import random

import pandas as pd
import streamlit as st

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(
    page_title="Wise Decision Helper",
    page_icon="🧠",
    layout="wide",
)

# ---------------------------
# SCRIPTURE & HELPERS
# ---------------------------
SCRIPTURE = [
    (
        "Proverbs 3:5–6",
        "Trust in the LORD with all your heart and lean not on your own understanding; "
        "in all your ways submit to him, and he will make your paths straight.",
    ),
    (
        "James 1:5",
        "If any of you lacks wisdom, you should ask God, who gives generously to all without finding fault, "
        "and it will be given to you.",
    ),
    (
        "Luke 14:28",
        "Suppose one of you wants to build a tower. Won’t you first sit down and estimate the cost "
        "to see if you have enough money to complete it?",
    ),
    (
        "Proverbs 21:5",
        "The plans of the diligent lead to profit as surely as haste leads to poverty.",
    ),
    (
        "Matthew 6:21",
        "For where your treasure is, there your heart will be also.",
    ),
]


def show_scripture():
    if "verse_idx" not in st.session_state:
        st.session_state["verse_idx"] = random.randint(0, len(SCRIPTURE) - 1)
    idx = st.session_state["verse_idx"]
    ref, text = SCRIPTURE[idx]
    st.markdown(f"> ✝️ **{text}**  \n> *— {ref}*")
    if st.button("Next Verse 🔁"):
        st.session_state["verse_idx"] = (idx + 1) % len(SCRIPTURE)
        st.experimental_rerun()


def map_answer(val: str) -> float:
    """Map radio answer to numeric weight."""
    if val == "Yes":
        return 1.0
    if val == "Unsure":
        return 0.5
    return 0.0  # "No"


def classify_decision(scores: dict) -> str:
    """
    scores: dict with float values 0–1 for keys:
        god_authored, want, future_good, financial_sense
    """
    god = scores.get("god_authored", 0)
    fin = scores.get("financial_sense", 0)
    total = sum(scores.values())

    # Critical fails
    if god == 0 or fin == 0:
        return "🚫 Likely *No* — something important is off. Pray, wait, or adjust the plan."

    # Strong yes
    if total >= 3.5:
        return "✅ Strong *Yes* — green light with wisdom and stewardship."

    # In-between
    return "🟡 *Wait / Refine* — good pieces are here, but something needs clarity."


# ---------------------------
# PAGE HEADER
# ---------------------------
st.title("🧠 Wise Decision Helper (Faith + Finances)")
st.caption("Slow down, think biblically, and auto-plan how to use your money with peace.")

show_scripture()
st.markdown("---")

# ---------------------------
# 1️⃣ DECISION INPUTS
# ---------------------------
col_main, col_side = st.columns([2, 1])

with col_main:
    st.subheader("1️⃣ What decision are you making?")
    decision_name = st.text_input(
        "Describe the decision",
        placeholder="e.g., How should I use this $250 birthday money? Suit, jeans, shirts, savings, etc.",
    )
    decision_type = st.selectbox(
        "Type of decision",
        ["Purchase / Spending", "Partnership / Vendor", "Investment / Business", "Other"],
        index=0,
    )
    amount = st.number_input(
        "Total amount involved ($)",
        min_value=0.0,
        step=10.0,
        value=250.0,
    )
    urgent = st.checkbox("I feel rushed / FOMO / pressure on this decision")

with col_side:
    st.subheader("⏱ When will you revisit this?")
    default_review = dt.date.today() + dt.timedelta(days=7)
    review_date = st.date_input(
        "Date to come back to this decision",
        value=default_review,
    )
    st.info(
        "Tip: For non-emergencies, giving yourself ~1 week often brings clarity and removes pressure."
    )

st.markdown("---")

# ---------------------------
# 2️⃣ BIBLICAL & WISDOM FILTERS
# ---------------------------
st.subheader("2️⃣ Biblical & Wisdom Filters")

b1, b2 = st.columns(2)

with b1:
    q_god = st.radio(
        "Did this direction come from prayerful, God-honoring motives?",
        ["Unsure", "No", "Yes"],
        index=0,
    )
    q_want = st.radio(
        "Do we genuinely *want* this (not just comparison or impulse)?",
        ["Unsure", "No", "Yes"],
        index=0,
    )

with b2:
    q_future = st.radio(
        "Is this good for future generations / long-term stewardship?",
        ["Unsure", "No", "Yes"],
        index=0,
    )
    q_fin = st.radio(
        "Financially agreeable — do the numbers make sense *today*?",
        ["Unsure", "No", "Yes"],
        index=0,
    )

scores = {
    "god_authored": map_answer(q_god),
    "want": map_answer(q_want),
    "future_good": map_answer(q_future),
    "financial_sense": map_answer(q_fin),
}
summary_text = classify_decision(scores)

st.markdown("#### 🧾 Decision Evaluation")
e1, e2, e3, e4 = st.columns(4)
e1.metric("Did God author this?", q_god)
e2.metric("Do we actually want this?", q_want)
e3.metric("Good for future?", q_future)
e4.metric("Financially wise?", q_fin)

st.success(summary_text)

if urgent:
    st.warning(
        f"⚠️ You marked this as **rushed**. Strong recommendation: wait until "
        f"**{review_date.strftime('%b %d, %Y')}** before finalizing."
    )

st.markdown("---")

# ---------------------------
# 3️⃣ PRIORITIES & AUTO-ALLOCATED PLAN
# ---------------------------
st.subheader("3️⃣ Auto-plan how to use the money")

st.caption("Adjust the percentages below. They do **not** have to add to 100% — I'll normalize them safely.")

default_alloc = {
    "Tithe / Giving": 10,
    "Blessing Others (gifts, generosity)": 5,
    "Debt / Obligations": 20,
    "Savings / Future (emergency, investing)": 25,
    "Essentials Upgrade (e.g., work wardrobe)": 20,
    "Pure Joy / Fun": 20,
}

alloc_df = pd.DataFrame(
    {
        "Bucket": list(default_alloc.keys()),
        "Percent": list(default_alloc.values()),
    }
)

alloc_edit = st.data_editor(
    alloc_df,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="alloc_editor",
)

# Build dict from editor
bucket_pcts = dict(zip(alloc_edit["Bucket"], alloc_edit["Percent"]))

total_raw_pct = sum([p for p in bucket_pcts.values() if p is not None])

if total_raw_pct <= 0:
    st.error("Set at least one bucket to a percentage above 0 to generate a plan.")
else:
    if abs(total_raw_pct - 100) > 1e-6:
        st.info(
            f"Your buckets currently sum to **{total_raw_pct:.1f}%**. "
            "That's okay — I'll scale them so the full amount is allocated."
        )

    if st.button("💡 Generate Money Plan"):
        rows = []
        for bucket, pct in bucket_pcts.items():
            if pct is None:
                continue
            share = pct / total_raw_pct  # normalized
            bucket_amount = round(amount * share, 2)
            rows.append(
                {
                    "Bucket": bucket,
                    "Target % (raw)": pct,
                    "Normalized %": round(share * 100, 1),
                    "Planned Amount ($)": bucket_amount,
                }
            )

        plan_df = pd.DataFrame(rows)
        st.subheader("📊 Suggested Allocation")
        st.dataframe(plan_df, use_container_width=True)

        # Quick summary call-outs for key buckets
        key_buckets = {
            "Tithe / Giving": "Give first, in line with Malachi 3:10.",
            "Debt / Obligations": "Pay what you owe; it buys back margin and peace.",
            "Savings / Future (emergency, investing)": "Future you and your family will thank you.",
            "Essentials Upgrade (e.g., work wardrobe)": "Invest in things that help you show up well.",
            "Pure Joy / Fun": "Enjoy God’s gifts without guilt when the priorities are honored.",
        }

        st.markdown("#### 🔍 Notes on this plan")
        for _, row in plan_df.iterrows():
            bucket = row["Bucket"]
            amt = row["Planned Amount ($)"]
            note = key_buckets.get(bucket)
            if note:
                st.write(f"- **{bucket}** — ${amt:,.2f}: {note}")
            else:
                st.write(f"- **{bucket}** — ${amt:,.2f}")

        # Special callout for wardrobe example
        if "Essentials Upgrade (e.g., work wardrobe)" in plan_df["Bucket"].values:
            wardrobe_amt = float(
                plan_df.loc[
                    plan_df["Bucket"] == "Essentials Upgrade (e.g., work wardrobe)",
                    "Planned Amount ($)",
                ].iloc[0]
            )
            st.info(
                f"👔 Based on this plan, you have about **${wardrobe_amt:,.2f}** "
                "to put toward a suit / jeans / shirts while still honoring priorities."
            )

st.markdown("---")

# ---------------------------
# 4️⃣ PARTNER / VENDOR CHECK (OPTIONAL)
# ---------------------------
if decision_type == "Partnership / Vendor":
    st.subheader("4️⃣ Partner / Vendor Requirements Check")
    st.caption("Use this grid to evaluate *who* you're tying yourself to.")

    traits = [
        "High Communication",
        "Asks Good Questions",
        "Moves with Urgency (without chaos)",
        "Accountable",
        "Reliable",
        "Receptive to feedback / criticism",
        "Humble",
        "Financially agreeable (numbers make sense)",
        "Faithful / keeps commitments",
        "Committed for the long term",
        "Doesn't get easily offended if they don't get their way",
        "There is a clear, safe exit strategy",
        "Agreement is in writing / documented",
    ]

    partner_df = pd.DataFrame(
        {
            "Requirement": traits,
            "Meets This?": ["Unsure"] * len(traits),
        }
    )

    partner_edit = st.data_editor(
        partner_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Meets This?": st.column_config.SelectboxColumn(
                options=["Yes", "Unsure", "No"]
            )
        },
        key="partner_editor",
    )

    yes_count = (partner_edit["Meets This?"] == "Yes").sum()
    no_count = (partner_edit["Meets This?"] == "No").sum()
    unsure_count = (partner_edit["Meets This?"] == "Unsure").sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("✅ Yes", yes_count)
    c2.metric("⚠️ Unsure", unsure_count)
    c3.metric("❌ No", no_count)

    if no_count > 0:
        st.error(
            "There are **requirements marked 'No'**. That usually means **pause or renegotiate** before moving forward."
        )
    elif unsure_count > 0:
        st.warning(
            "Some items are still **'Unsure'**. Consider asking more questions or doing a small test before a big commitment."
        )
    else:
        st.success(
            "All partner requirements are currently marked **Yes**. "
            "This looks healthy on paper — still keep praying and listening."
        )
