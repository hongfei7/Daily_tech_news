import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.aggregator import get_today_dashboard_data
from src.database import get_latest_date
from src.utils import today_str


st.set_page_config(page_title="Today | 科技趋势仪表盘", page_icon="📌", layout="wide")
st.title("📌 今日科技趋势仪表盘")

target_date = get_latest_date() or today_str()
st.caption(f"数据日期: {target_date}")

dashboard = get_today_dashboard_data(target_date)
items = dashboard["items"]
stable_stats = dashboard["stable_stats"]
emerging_stats = dashboard["emerging_stats"]
selection_stats = dashboard["selection_stats"]

if not items:
    st.warning("当前没有可展示的数据，请先运行 pipeline 或 backfill_demo_data。")
    st.stop()

st.subheader("Stable Topics 主方向图")
if stable_stats:
    df_stable = pd.DataFrame(stable_stats).sort_values("final_score", ascending=True)
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
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Stable Topic 一句话卡片")
card_columns = st.columns(3)
for idx, stat in enumerate(stable_stats[:6]):
    delta = stat["trend_delta_7d"]
    arrow = "↑" if delta > 1 else "↓" if delta < -1 else "→"
    topic_items = [item for item in items if item.get("stable_topic") == stat["topic"]]
    best_item = max(topic_items, key=lambda item: item.get("final_score", 0.0)) if topic_items else None
    with card_columns[idx % 3]:
        st.markdown(f"### {stat['topic']} {arrow}")
        st.write(stat["top_summary"])
        if best_item:
            st.markdown(f"[代表链接]({best_item['url']})")

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
    st.plotly_chart(fig_bucket, use_container_width=True)

st.divider()
st.subheader("今日条目")
df_items = pd.DataFrame(items)
show_columns = [
    "source",
    "stable_topic",
    "emerging_topic",
    "final_score",
    "llm_selected",
    "selection_bucket",
    "one_line_summary",
    "title",
    "url",
]
st.dataframe(
    df_items[show_columns].sort_values("final_score", ascending=False),
    column_config={"url": st.column_config.LinkColumn("链接")},
    hide_index=True,
    use_container_width=True,
    height=460,
)
