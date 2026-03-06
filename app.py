import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.aggregator import build_trend_series, get_today_dashboard_data
from src.database import get_latest_date, init_db, migrate_db
from src.utils import today_str


st.set_page_config(
    page_title="科技趋势总览",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 科技趋势总览")
st.caption("面向程序员的稳定骨架 + 动态雷达 + 分层精读总览")

init_db()
migrate_db()

target_date = get_latest_date() or today_str()
dashboard = get_today_dashboard_data(target_date)
trend_series = build_trend_series(days=7)

items = dashboard["items"]
stable_stats = dashboard["stable_stats"]
emerging_stats = dashboard["emerging_stats"]
selection_stats = dashboard["selection_stats"]

if not items:
    st.warning("当前没有可展示的数据。先运行 `python scripts/backfill_demo_data.py` 或 `python scripts/run_pipeline.py --days 1`。")
    st.stop()

stable_df = pd.DataFrame(stable_stats)
emerging_df = pd.DataFrame(emerging_stats)
selected_df = pd.DataFrame([item for item in items if item.get("llm_selected") == 1])

top_stable = stable_stats[0] if stable_stats else None
top_emerging = emerging_stats[0] if emerging_stats else None
rising_stable = sorted(stable_stats, key=lambda row: row["trend_delta_7d"], reverse=True)[:3]
falling_stable = sorted(stable_stats, key=lambda row: row["trend_delta_7d"])[:3]
rising_emerging = sorted(emerging_stats, key=lambda row: row["growth_rate"], reverse=True)[:3]

def _lead_summary() -> str:
    parts = []
    if top_stable:
        parts.append(f"主方向是 {top_stable['topic']}")
    if top_emerging:
        parts.append(f"新爆点是 {top_emerging['emerging_topic']}")
    if selection_stats:
        parts.append(f"今日 LLM 精读 {int(selection_stats.get('llm_items_selected', 0))} 条代表样本")
    return "；".join(parts) + "。"


hero_left, hero_right = st.columns([1.35, 1])
with hero_left:
    st.markdown("## 今日结论")
    st.write(_lead_summary())
    if top_stable:
        st.markdown(
            f"**现在最该关注**：`{top_stable['topic']}`，今日热度 `{top_stable['final_score']}`，"
            f"7 日变化 `{top_stable['trend_delta_7d']:+.1f}`。"
        )
        st.write(top_stable["top_summary"])
    if top_emerging:
        st.markdown(
            f"**最值得追踪的新变化**：`{top_emerging['emerging_topic']}`，"
            f"增长 `{top_emerging['growth_rate']:.1f}x`，跨 `{int(top_emerging['source_count'])}` 个来源扩散。"
        )
        st.write(top_emerging["top_summary"])

with hero_right:
    c1, c2 = st.columns(2)
    c1.metric("数据日期", target_date)
    c2.metric("总条目", len(items))
    c3, c4 = st.columns(2)
    c3.metric("Stable Topics", len({item.get("stable_topic") for item in items if item.get("stable_topic")}))
    c4.metric("Emerging Topics", len({item.get("emerging_topic") for item in items if item.get("emerging_topic")}))
    c5, c6 = st.columns(2)
    c5.metric("LLM 精读", int(selection_stats.get("llm_items_selected", 0)))
    c6.metric("覆盖率", f"{selection_stats.get('coverage_ratio', 0):.1%}")
    if selection_stats:
        st.info(selection_stats.get("notes", ""))

st.divider()
row1_left, row1_mid, row1_right = st.columns([1.1, 1, 1])

with row1_left:
    st.subheader("主方向热力")
    if not stable_df.empty:
        fig = px.bar(
            stable_df.head(8).sort_values("final_score", ascending=True),
            x="final_score",
            y="topic",
            orientation="h",
            color="trend_delta_7d",
            color_continuous_scale="RdYlGn",
            labels={"final_score": "热度", "topic": "Stable Topic"},
        )
        fig.update_layout(height=360, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

with row1_mid:
    st.subheader("Top 3 Stable Movers")
    st.markdown("**升温**")
    for row in rising_stable:
        st.markdown(f"- `{row['topic']}`  `{row['trend_delta_7d']:+.1f}`")
    st.markdown("**降温**")
    for row in falling_stable:
        st.markdown(f"- `{row['topic']}`  `{row['trend_delta_7d']:+.1f}`")

with row1_right:
    st.subheader("Top 3 Emerging Movers")
    if rising_emerging:
        for row in rising_emerging:
            st.markdown(
                f"- `{row['emerging_topic']}`  增长 `{row['growth_rate']:.1f}x`  来源 `{int(row['source_count'])}`"
            )
    else:
        st.write("最近没有达到阈值的动态爆点。")

st.divider()
row2_left, row2_right = st.columns([1, 1.2])

with row2_left:
    st.subheader("今天该看什么")
    if not selected_df.empty:
        top_reads = selected_df.sort_values("final_score", ascending=False).head(5)
        for _, row in top_reads.iterrows():
            st.markdown(
                f"- `[{row['stable_topic']}]` {row['one_line_summary']}  "
                f"[原文]({row['url']})"
            )
    else:
        st.write("今天还没有 LLM 精读样本。")

    st.subheader("今天可以先跳过什么")
    low_priority = (
        pd.DataFrame(items)
        .sort_values(["final_score", "novelty_score"], ascending=[True, True])
        .head(5)
    )
    for _, row in low_priority.iterrows():
        st.markdown(f"- `{row['stable_topic']}` {row['title']}")

with row2_right:
    st.subheader("代表性结构")
    if selection_stats:
        bucket_df = pd.DataFrame(
            [
                {"bucket": "top_pool", "count": selection_stats.get("top_bucket_count", 0)},
                {"bucket": "stable_pool", "count": selection_stats.get("stable_bucket_count", 0)},
                {"bucket": "emerging_pool", "count": selection_stats.get("emerging_bucket_count", 0)},
            ]
        )
        fig_bucket = px.pie(bucket_df, values="count", names="bucket", hole=0.55)
        fig_bucket.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_bucket, use_container_width=True)

    st.subheader("一周快照")
    trend_df = pd.DataFrame(trend_series["stable"])
    if not trend_df.empty:
        latest = trend_df[trend_df["date"] == trend_df["date"].max()].sort_values("final_score", ascending=False).head(6)
        st.dataframe(latest[["topic", "final_score", "trend_delta_7d"]], hide_index=True, use_container_width=True)

st.divider()
st.subheader("今日代表样本明细")
if not selected_df.empty:
    st.dataframe(
        selected_df[
            [
                "stable_topic",
                "emerging_topic",
                "selection_bucket",
                "selection_reason",
                "final_score",
                "one_line_summary",
                "title",
                "url",
            ]
        ].sort_values("final_score", ascending=False),
        column_config={"url": st.column_config.LinkColumn("链接")},
        hide_index=True,
        use_container_width=True,
        height=320,
    )

st.divider()
st.subheader("继续深挖")
nav1, nav2, nav3 = st.columns(3)
with nav1:
    st.page_link("pages/1_Today.py", label="进入 Today", icon="📌")
with nav2:
    st.page_link("pages/2_Trend.py", label="进入 Trend", icon="📈")
with nav3:
    st.page_link("pages/3_Explore.py", label="进入 Explore", icon="🔎")
