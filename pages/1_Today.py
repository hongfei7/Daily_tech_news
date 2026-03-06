import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.aggregator import get_today_dashboard_data
from src.database import get_latest_date
from src.ui import apply_light_theme, apply_plot_style
from src.utils import today_str


st.set_page_config(page_title="Today | 科技趋势仪表盘", page_icon="📌", layout="wide")
st.title("📌 今日科技趋势仪表盘")

apply_light_theme()

target_date = get_latest_date() or today_str()
st.caption(f"数据日期: {target_date}")

dashboard = get_today_dashboard_data(target_date)
items = dashboard["items"]
stable_stats = dashboard["stable_stats"]
emerging_stats = dashboard["emerging_stats"]
selection_stats = dashboard["selection_stats"]
display_stable_stats = [row for row in stable_stats if row["topic"] != "Other"] or stable_stats

if not items:
    st.warning("当前没有可展示的数据，请先运行 pipeline 或 backfill_demo_data。")
    st.stop()

st.subheader("Stable Topics 主方向图")
if display_stable_stats:
    df_stable = pd.DataFrame(display_stable_stats).sort_values("final_score", ascending=True)
    fig = px.bar(
        df_stable,
        x="final_score",
        y="topic",
        orientation="h",
        color="trend_delta_7d",
        color_continuous_scale="Tealrose",
        labels={"final_score": "今日热度", "topic": "稳定主题"},
    )
    fig.update_layout(height=420)
    st.plotly_chart(apply_plot_style(fig), use_container_width=True)

st.subheader("Stable Topic 一句话卡片")
card_columns = st.columns(2)
for idx, stat in enumerate(display_stable_stats[:6]):
    delta = stat["trend_delta_7d"]
    arrow = "↑" if delta > 1 else "↓" if delta < -1 else "→"
    topic_items = [item for item in items if item.get("stable_topic") == stat["topic"]]
    best_item = max(topic_items, key=lambda item: item.get("final_score", 0.0)) if topic_items else None
    with card_columns[idx % 2]:
        st.markdown(
            f"<div class='topic-card'><h3>{stat['topic']} {arrow}</h3><p>{stat['top_summary']}</p>",
            unsafe_allow_html=True,
        )
        if best_item:
            st.markdown(f"[代表链接]({best_item['url']})")
        st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.subheader("Emerging Now")
if emerging_stats:
    for stat in emerging_stats[:8]:
        topic_items = [item for item in items if item.get("emerging_topic") == stat["emerging_topic"]]
        best_item = max(topic_items, key=lambda item: item.get("final_score", 0.0)) if topic_items else None
        col1, col2, col3, col4 = st.columns([2, 1, 1, 3])
        col1.markdown(f"**{stat['emerging_topic']}**")
        col2.metric("增长率", f"{stat['growth_rate']:.1f}x")
        col3.metric("来源数", int(stat["source_count"]))
        col4.write(stat["top_summary"])
        if best_item:
            st.markdown(f"[代表链接]({best_item['url']})")
else:
    st.info("今日没有满足阈值的动态爆点。")

st.divider()
st.subheader("代表性覆盖说明")
if selection_stats:
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("总条目", int(selection_stats["total_items"]))
    col2.metric("LLM 精读", int(selection_stats["llm_items_selected"]))
    col3.metric("Stable 覆盖", int(selection_stats["stable_topic_count"]))
    col4.metric("Emerging 覆盖", int(selection_stats["emerging_topic_count"]))
    col5.metric("覆盖率", f"{selection_stats['coverage_ratio']:.1%}")
    st.write(selection_stats["notes"])
    bucket_df = pd.DataFrame(
        [
            {"bucket": "top_pool", "count": selection_stats["top_bucket_count"]},
            {"bucket": "stable_pool", "count": selection_stats["stable_bucket_count"]},
            {"bucket": "emerging_pool", "count": selection_stats["emerging_bucket_count"]},
        ]
    )
    fig_bucket = px.pie(bucket_df, values="count", names="bucket", hole=0.5)
    st.plotly_chart(apply_plot_style(fig_bucket), use_container_width=True)

st.divider()
st.subheader("按主题的头部条目")
st.caption("Today 聚焦主题代表链接；代表样本明细集中放在首页，原始条目集中放在 Explore。")

topic_feature_rows = []
for stat in display_stable_stats[:8]:
    topic_items = [item for item in items if item.get("stable_topic") == stat["topic"]]
    if not topic_items:
        continue
    best_item = max(topic_items, key=lambda item: item.get("final_score", 0.0))
    topic_feature_rows.append(
        {
            "stable_topic": stat["topic"],
            "emerging_topic": best_item.get("emerging_topic", ""),
            "final_score": best_item["final_score"],
            "one_line_summary": best_item["one_line_summary"],
            "title": best_item["title"],
            "url": best_item["url"],
        }
    )

if topic_feature_rows:
    topic_df = pd.DataFrame(topic_feature_rows).sort_values("final_score", ascending=False)
    st.dataframe(
        topic_df,
        column_config={
            "url": st.column_config.LinkColumn("代表链接"),
            "one_line_summary": st.column_config.TextColumn("一句话摘要", width="medium"),
            "title": st.column_config.TextColumn("标题", width="large"),
        },
        hide_index=True,
        use_container_width=True,
        height=420,
    )
