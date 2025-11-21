import datetime as dt
import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(
    page_title="Kingdom Decision Coach",
    page_icon="🧠",
    layout="wide",
)

# ---------------------------
# HELPERS
# ---------------------------
SCRIPTURE = [
    ("Proverbs 3:5–6", "Trust in the LORD with all your heart and lean not on your own understanding; in all your ways submit to him, and he will make your paths straight."),
    ("Luke 14:28", "Suppose one of you wants to build a tower. Won’t you first sit down and estimate the cost to see if you have enough money to complete it?"),
    ("2 Corinthians 9:7", "Each of you should give what you have decided in your heart to give... for God loves a cheerful giver."),
    ("Proverbs 21:20", "The wise store up choice food and olive oil, but fools gulp theirs down."),
    ("Philippians 4:11–12", "I have learned to be content whatever the circumstances."),
]

def show_random_scripture():
    ref, text = SCRIPTURE[st.session_state.get("dec_verse_idx", 0)]
    st.markdown(f"> *“{text}”*  \n> — **{ref}**")
    if st.button("Next Verse 🔁", key="next_verse_decision"):
        st.session_state["dec_verse_idx"] = (st.session_state.get("dec_verse_idx", 0) + 1) % len(SCRIPTURE)
        st.experimental_rerun()

def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Compute value/joy per dollar scores safely."""
    df = df.copy()
    # Clean numeric
    df["Cost"] = pd.to_numeric(df["Cost"], errors="coerce").fillna(0.0)
    df["ValueScore"] = pd.to_numeric(df["ValueScore"], errors="coerce").fillna(0.0)
    df["Joy"] = pd.to_numeric(df["Joy"], errors="coerce").fillna(0.0)

    # Avoid divide-by-zero
    with np.errstate(divide="ignore", invalid="ignore"):
        df["Score"] = (df["ValueScore"] / df["Cost"].replace(0, np.nan)) * df["Joy"]
    df["Score"] = df["Score"].replace([np.inf, -np.inf, np.nan], 0.0)

    return df

def allocate_wants(df: pd.DataFrame, wants_budget: float) -> (pd.DataFrame, pd.DataFrame):
    """
    Given a scored options DF and a wants budget,
    greedily pick highest-score items that fit within budget.
    """
    df = df.sort_values("Score", ascending=False).reset_index(drop=True)
    spent = 0.0
    decisions = []

    for _, row in df.iterrows():
        cost = float(row["Cost"])
        if cost <= 0:
            decisions.append("Skip (no cost)")
            continue

        if spent + cost <= wants_budget:
            spent += cost
            decisions.append("✅ Do Now")
        else:
            decisions.append("🕒 Backlog / Wait")

    df["Decision"] = decisions
    df["CumSpentIfChosen"] = df.apply(
        lambda r: np.nan,
        axis=1
    )

    # recompute cumulative spent only for "Do Now"
    cum = 0.0
    for i in range(len(df)):
        if df.loc[i, "Decision"] == "✅ Do Now":
            cum += float(df.loc[i, "Cost"])
            df.loc[i, "CumSpentIfChosen"] = cum

    do_now = df[df["Decision"] == "✅ Do Now"].copy()
    backlog = df[df["Decision"] != "✅ Do Now"].copy()

    return do_now, backlog, spent

# ---------------------------
# UI
# ---------------------------
st.title("🧠 Kingdom Decision Coach")
st.caption("Help your future self make wise, biblically-aligned money decisions — without overthinking every purchase.")

show_random_scripture()

st.markdown("---")

# ==========================================================
# STEP 1 — DECISION CONTEXT & HEART CHECK
# ==========================================================
st.header("1️⃣ Decision Context & Heart Check")

col_left, col_right = st.columns([2, 1])

with col_left:
    decision_name = st.text_input(
        "What decision are you working through?",
        value="Birthday gift — wardrobe upgrade",
        help="Example: 'How to use my $250 birthday money' or 'Should we upgrade our phones this year?'"
    )

    available_amount = st.number_input(
        "Total amount available for this decision ($)",
        min_value=0.0,
        step=10.0,
        value=250.0
    )

    c1, c2, c3 = st.columns(3)
    giving_pct = c1.number_input("Giving %", min_value=0.0, max_value=100.0, step=1.0, value=10.0)
    saving_pct = c2.number_input("Saving / Investing %", min_value=0.0, max_value=100.0, step=1.0, value=10.0)
    wait_review_date = c3.date_input("Review this decision again on", value=dt.date.today() + dt.timedelta(days=7))

with col_right:
    st.markdown("#### 🧭 Heart & Wisdom Checks")

    god_authored = st.checkbox("Did God author or affirm this desire?", value=True)
    good_for_future = st.checkbox("Is this good for future generations?", value=True)
    financially_agreeable = st.checkbox("Do the numbers make sense?", value=False)
    aligned_with_calling = st.checkbox("Does this support your calling / mission?", value=True)

    st.markdown("#### ⏳ Speed Bump")
    st.write("To avoid rushed decisions, you’ve set a review date above.")
    if wait_review_date > dt.date.today():
        st.info(f"🕒 Remember: you planned to re-check this on **{wait_review_date}**.")

# Simple visual feedback
if not god_authored or not good_for_future:
    st.warning("⚠️ One or more heart checks are **not** aligned. That doesn’t mean 'never', but it might mean **'not right now'** or **'rethink the why'**.")

st.markdown("---")

# ==========================================================
# STEP 2 — LIST YOUR OPTIONS
# ==========================================================
st.header("2️⃣ List Your Options")

st.write("Add or edit the options you’re considering. Cost is what you pay, ValueScore is how much long-term impact/usefulness you feel it has (1–10), Joy is how much it lights you up (1–10).")

default_options = pd.DataFrame([
    {"Name": "Suit Supply Suit", "Cost": 800, "ValueScore": 9, "Joy": 9, "Category": "Fashion"},
    {"Name": "Suit Supply Jeans", "Cost": 250, "ValueScore": 8, "Joy": 8, "Category": "Fashion"},
    {"Name": "Uniqlo Wardrobe Refresh", "Cost": 250, "ValueScore": 7, "Joy": 7, "Category": "Fashion"},
])

options_df = st.data_editor(
    default_options,
    num_rows="dynamic",
    use_container_width=True,
    key="options_editor",
)

# Clean options (drop empty rows)
options_df = options_df.fillna({"Name": ""})
options_df = options_df[options_df["Name"].str.strip() != ""]

if options_df.empty:
    st.info("Add at least one option above to continue.")
    can_run = False
else:
    can_run = True

st.markdown("---")

# ==========================================================
# STEP 3 — RUN THE DECISION COACH
# ==========================================================
st.header("3️⃣ Run the Decision Coach")

if st.button("🤖 Evaluate My Options", disabled=not can_run):
    if available_amount <= 0:
        st.error("Available amount must be greater than 0.")
    else:
        # 1) Reserve giving & savings first (conservative style)
        giving_amount = available_amount * giving_pct / 100.0
        saving_amount = available_amount * saving_pct / 100.0
        wants_budget = max(0.0, available_amount - giving_amount - saving_amount)

        st.subheader("📌 High-Level Allocation")
        g1, g2, g3, g4 = st.columns(4)
        g1.metric("Total Available", f"${available_amount:,.2f}")
        g2.metric("Reserved for Giving", f"${giving_amount:,.2f}")
        g3.metric("Reserved for Saving/Investing", f"${saving_amount:,.2f}")
        g4.metric("Budget for 'Wants'", f"${wants_budget:,.2f}")

        # 2) Compute scores
        scored_df = compute_scores(options_df)

        st.subheader("📊 Options with Value/Joy Scores")
        st.dataframe(
            scored_df[["Name", "Cost", "ValueScore", "Joy", "Score", "Category"]],
            use_container_width=True
        )

        # 3) Allocate best options within wants budget
        do_now, backlog, spent_now = allocate_wants(scored_df, wants_budget)
        remaining_wants_budget = wants_budget - spent_now

        st.subheader("✅ Recommended to Do Now (within budget)")
        if do_now.empty:
            st.info("Based on your budget and scores, nothing clearly fits *right now*. That might be a nudge to save this round.")
        else:
            st.write(f"Total to spend now: **${spent_now:,.2f}** (of ${wants_budget:,.2f} wants budget)")
            st.dataframe(
                do_now[["Name", "Cost", "Score", "Category"]],
                use_container_width=True
            )

        st.subheader("🕒 Backlog / 'Not Right Now'")
        if backlog.empty:
            st.success("No backlog — everything you listed fits within this gift and your priorities.")
        else:
            st.write("These are *good desires* to revisit later, not forgotten or forever denied.")
            st.dataframe(
                backlog[["Name", "Cost", "Score", "Category"]],
                use_container_width=True
            )

        st.subheader("📌 Simple Recommendation Summary")

        summary_lines = []

        summary_lines.append(f"- **Give:** about **${giving_amount:,.0f}**")
        summary_lines.append(f"- **Save/Invest:** about **${saving_amount:,.0f}**")

        if not do_now.empty:
            buy_list = ", ".join(do_now["Name"].tolist())
            summary_lines.append(f"- **Buy now (within your 'wants' budget):** {buy_list} (total ≈ ${spent_now:,.0f})")

        if remaining_wants_budget > 0 and do_now.empty:
            summary_lines.append(f"- **You still have ≈ ${remaining_wants_budget:,.0f} of wants-budget unassigned** — you could choose to save more or wait until you’re clearer.")

        if not backlog.empty:
            backlog_list = ", ".join(backlog["Name"].tolist())
            summary_lines.append(f"- **Backlog / Wait list:** {backlog_list} — revisit around **{wait_review_date}**.")

        st.markdown("\n".join(summary_lines))

        st.info("This isn’t a command — it’s a wise suggestion that keeps your giving, saving, and future in view while still allowing joy purchases.")

else:
    st.info("When you’re ready, click **“Evaluate My Options”** to see a suggested plan.")
