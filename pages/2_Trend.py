import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.aggregator import build_trend_series
from src.ui import apply_light_theme, apply_plot_style


st.set_page_config(page_title="Trend | 科技趋势", page_icon="📈", layout="wide")
st.title("📈 趋势页")
apply_light_theme()

days_option = st.radio("时间范围", options=[7, 14, 30], index=0, horizontal=True)
series = build_trend_series(days_option)

stable_df = pd.DataFrame(series["stable"])
emerging_df = pd.DataFrame(series["emerging"])
heatmap_df = pd.DataFrame(series["source_heatmap"])

st.subheader("Stable Trend")
if not stable_df.empty:
    fig_stable = px.line(stable_df, x="date", y="final_score", color="topic", markers=True)
    fig_stable.update_layout(height=420)
    st.plotly_chart(apply_plot_style(fig_stable), use_container_width=True)
else:
    st.info("暂无 stable trend 数据。")

st.subheader("Emerging Trend")
if not emerging_df.empty:
    latest_date = emerging_df["date"].max()
    latest_emerging = emerging_df[emerging_df["date"] == latest_date].sort_values("growth_rate", ascending=False).head(10)
    fig_emerging = px.bar(
        latest_emerging.sort_values("growth_rate"),
        x="growth_rate",
        y="emerging_topic",
        orientation="h",
        color="source_count",
        color_continuous_scale="Blues",
        labels={"growth_rate": "最新增长率", "emerging_topic": "Emerging Topic", "source_count": "来源数"},
    )
    fig_emerging.update_layout(height=420)
    st.plotly_chart(apply_plot_style(fig_emerging), use_container_width=True)
else:
    st.info("暂无 emerging trend 数据。")

st.subheader("Topic × Source 热力图")
if not heatmap_df.empty:
    filtered_heatmap = heatmap_df[heatmap_df["stable_topic"] != "Other"]
    pivot = filtered_heatmap.pivot(index="stable_topic", columns="source", values="count").fillna(0)
    fig_heat = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale="YlGnBu")
    fig_heat.update_layout(height=440)
    st.plotly_chart(apply_plot_style(fig_heat), use_container_width=True)

st.subheader("Rising / Falling 榜")
col1, col2 = st.columns(2)
if not stable_df.empty:
    latest_stable = stable_df[stable_df["date"] == stable_df["date"].max()].copy()
    latest_stable = latest_stable[latest_stable["topic"] != "Other"]
    with col1:
        st.markdown("**Stable Topics**")
        stable_rank = latest_stable.sort_values("trend_delta_7d", ascending=False).head(8)
        fig_rank = px.bar(
            stable_rank.sort_values("trend_delta_7d"),
            x="trend_delta_7d",
            y="topic",
            orientation="h",
            color="trend_delta_7d",
            color_continuous_scale="RdYlGn",
            labels={"trend_delta_7d": "7日变化", "topic": "Stable Topic"},
        )
        fig_rank.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(apply_plot_style(fig_rank), use_container_width=True)

if not emerging_df.empty:
    latest_emerging = emerging_df[emerging_df["date"] == emerging_df["date"].max()].copy()
    with col2:
        st.markdown("**Emerging Topics**")
        emerging_rank = latest_emerging.sort_values("growth_rate", ascending=False).head(8)
        fig_emerging_rank = px.bar(
            emerging_rank.sort_values("growth_rate"),
            x="growth_rate",
            y="emerging_topic",
            orientation="h",
            color="growth_rate",
            color_continuous_scale="Bluered",
            labels={"growth_rate": "增长率", "emerging_topic": "Emerging Topic"},
        )
        fig_emerging_rank.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(apply_plot_style(fig_emerging_rank), use_container_width=True)
