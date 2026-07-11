"""
EduPro - Instructor Performance and Course Quality Evaluation Dashboard
Run with: streamlit run app.py

Place Teachers.csv, Courses.csv, Transactions.csv in the same folder.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="EduPro Instructor Performance", layout="wide")

# ---------------------------------------------------------------
# DATA LOADING & CACHING
# ---------------------------------------------------------------
@st.cache_data
def load_data():
    teachers = pd.read_csv("Teachers.csv")
    courses = pd.read_csv("Courses.csv")
    transactions = pd.read_csv("Transactions.csv")

    df = transactions.merge(teachers, on="TeacherID", how="left")
    df = df.merge(courses, on="CourseID", how="left")

    teachers["RatingTier"] = pd.cut(
        teachers["TeacherRating"], bins=[0, 2.5, 3.75, 5],
        labels=["Low", "Mid", "High"]
    )
    tier_map = teachers.set_index("TeacherID")["RatingTier"]
    df["RatingTier"] = df["TeacherID"].map(tier_map)

    return teachers, courses, df

teachers, courses, df = load_data()

# ---------------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------------
st.sidebar.header("Filters")

expertise_options = sorted(teachers["Expertise"].dropna().unique())
selected_expertise = st.sidebar.multiselect(
    "Instructor Expertise", expertise_options, default=expertise_options
)

category_options = sorted(courses["CourseCategory"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Course Category", category_options, default=category_options
)

level_options = sorted(courses["CourseLevel"].dropna().unique())
selected_levels = st.sidebar.multiselect(
    "Course Level", level_options, default=level_options
)

rating_range = st.sidebar.slider(
    "Teacher Rating Range", 0.0, 5.0, (0.0, 5.0), step=0.1
)

# Apply filters
filtered_teachers = teachers[
    (teachers["Expertise"].isin(selected_expertise)) &
    (teachers["TeacherRating"].between(*rating_range))
]

filtered_df = df[
    (df["Expertise"].isin(selected_expertise)) &
    (df["CourseCategory"].isin(selected_categories)) &
    (df["CourseLevel"].isin(selected_levels)) &
    (df["TeacherRating"].between(*rating_range))
]

# ---------------------------------------------------------------
# HEADER + KPIs
# ---------------------------------------------------------------
st.title("Instructor Performance & Course Quality Evaluation")
st.caption("EduPro Online Platform — Instructor effectiveness and course quality analytics")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Avg Teacher Rating", f"{filtered_teachers['TeacherRating'].mean():.2f}")
k2.metric("Avg Course Rating", f"{filtered_df['CourseRating'].mean():.2f}")
rating_std = filtered_teachers["TeacherRating"].std()
rating_mean = filtered_teachers["TeacherRating"].mean()
consistency = 1 - (rating_std / rating_mean) if rating_mean else np.nan
k3.metric("Rating Consistency Index", f"{consistency:.2f}")
corr = filtered_teachers[["YearsOfExperience", "TeacherRating"]].corr().iloc[0, 1]
k4.metric("Experience Impact (r)", f"{corr:.2f}")
k5.metric("Total Enrollments", f"{len(filtered_df):,}")

st.divider()

# ---------------------------------------------------------------
# TABS FOR CORE MODULES
# ---------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Leaderboard", "📈 Experience vs Rating", "🔥 Course Quality Heatmap", "🎯 Expertise Comparison"
])

with tab1:
    st.subheader("Instructor Performance Leaderboard")
    leaderboard = filtered_teachers.sort_values("TeacherRating", ascending=False)[
        ["TeacherName", "Expertise", "YearsOfExperience", "TeacherRating"]
    ].reset_index(drop=True)
    leaderboard.index += 1
    st.dataframe(leaderboard, use_container_width=True, height=500)

with tab2:
    st.subheader("Experience vs Rating")
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.scatter(
            filtered_teachers, x="YearsOfExperience", y="TeacherRating",
            color="Expertise", trendline="ols",
            title="Years of Experience vs Teacher Rating",
            hover_data=["TeacherName"]
        )
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        course_exp = filtered_df.groupby("CourseID").agg(
            CourseRating=("CourseRating", "first"),
            YearsOfExperience=("YearsOfExperience", "first"),
            CourseCategory=("CourseCategory", "first")
        ).dropna()
        fig2 = px.scatter(
            course_exp, x="YearsOfExperience", y="CourseRating",
            color="CourseCategory", trendline="ols",
            title="Years of Experience vs Course Rating"
        )
        st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("Course Quality Heatmap")
    pivot = filtered_df.pivot_table(
        index="CourseCategory", columns="CourseLevel",
        values="CourseRating", aggfunc="mean"
    )
    fig3 = px.imshow(
        pivot, text_auto=".2f", color_continuous_scale="YlGnBu",
        title="Avg Course Rating by Category & Level", aspect="auto"
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Instructor Rating Tier Impact")
    tier_summary = filtered_df.groupby("RatingTier", observed=True).agg(
        AvgCourseRating=("CourseRating", "mean"),
        Enrollments=("TransactionID", "count")
    ).reset_index()
    col3, col4 = st.columns(2)
    with col3:
        fig4 = px.bar(tier_summary, x="RatingTier", y="AvgCourseRating",
                       title="Avg Course Rating by Instructor Tier", color="RatingTier")
        st.plotly_chart(fig4, use_container_width=True)
    with col4:
        fig5 = px.bar(tier_summary, x="RatingTier", y="Enrollments",
                       title="Enrollment Volume by Instructor Tier", color="RatingTier")
        st.plotly_chart(fig5, use_container_width=True)

with tab4:
    st.subheader("Expertise-wise Performance Comparison")
    expertise_summary = filtered_teachers.groupby("Expertise").agg(
        AvgTeacherRating=("TeacherRating", "mean"),
        AvgExperience=("YearsOfExperience", "mean"),
        InstructorCount=("TeacherID", "count")
    ).sort_values("AvgTeacherRating", ascending=False).reset_index()

    fig6 = px.bar(
        expertise_summary, x="AvgTeacherRating", y="Expertise",
        orientation="h", color="AvgTeacherRating", color_continuous_scale="Purples",
        title="Average Teacher Rating by Expertise"
    )
    st.plotly_chart(fig6, use_container_width=True)
    st.dataframe(expertise_summary, use_container_width=True)

st.divider()
st.caption("Built for EduPro Instructor Performance and Course Quality Evaluation project")
