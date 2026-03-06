import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.aggregator import build_trend_series


st.set_page_config(page_title="Trend | 科技趋势", page_icon="📈", layout="wide")
st.title("📈 趋势页")

days_option = st.radio("时间范围", options=[7, 14, 30], index=0, horizontal=True)
series = build_trend_series(days_option)

stable_df = pd.DataFrame(series["stable"])
emerging_df = pd.DataFrame(series["emerging"])
heatmap_df = pd.DataFrame(series["source_heatmap"])

st.subheader("Stable Trend")
if not stable_df.empty:
    fig_stable = px.line(stable_df, x="date", y="final_score", color="topic", markers=True)
    st.plotly_chart(fig_stable, use_container_width=True)
else:
    st.info("暂无 stable trend 数据。")

st.subheader("Emerging Trend")
if not emerging_df.empty:
    fig_emerging = px.line(emerging_df, x="date", y="growth_rate", color="emerging_topic", markers=True)
    st.plotly_chart(fig_emerging, use_container_width=True)
else:
    st.info("暂无 emerging trend 数据。")

st.subheader("Topic × Source 热力图")
if not heatmap_df.empty:
    pivot = heatmap_df.pivot(index="stable_topic", columns="source", values="count").fillna(0)
    fig_heat = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale="YlGnBu")
    st.plotly_chart(fig_heat, use_container_width=True)

st.subheader("Rising / Falling 榜")
col1, col2 = st.columns(2)
if not stable_df.empty:
    latest_stable = stable_df[stable_df["date"] == stable_df["date"].max()]
    with col1:
        st.markdown("**Stable Topics**")
        rising = latest_stable.sort_values("trend_delta_7d", ascending=False).head(5)
        falling = latest_stable.sort_values("trend_delta_7d", ascending=True).head(5)
        st.write("升温")
        st.dataframe(rising[["topic", "final_score", "trend_delta_7d"]], hide_index=True, use_container_width=True)
        st.write("降温")
        st.dataframe(falling[["topic", "final_score", "trend_delta_7d"]], hide_index=True, use_container_width=True)

if not emerging_df.empty:
    latest_emerging = emerging_df[emerging_df["date"] == emerging_df["date"].max()]
    with col2:
        st.markdown("**Emerging Topics**")
        rising = latest_emerging.sort_values("growth_rate", ascending=False).head(5)
        falling = latest_emerging.sort_values("growth_rate", ascending=True).head(5)
        st.write("升温")
        st.dataframe(rising[["emerging_topic", "item_count", "growth_rate"]], hide_index=True, use_container_width=True)
        st.write("回落/边缘")
        st.dataframe(falling[["emerging_topic", "item_count", "growth_rate"]], hide_index=True, use_container_width=True)
