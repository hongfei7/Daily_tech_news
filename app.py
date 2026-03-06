import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.aggregator import build_trend_series, get_today_dashboard_data
from src.database import get_latest_date, init_db, migrate_db
from src.ui import apply_light_theme, apply_plot_style
from src.utils import today_str


st.set_page_config(
    page_title="科技趋势总览",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_light_theme()


st.title("科技趋势总览")
st.caption("稳定骨架 + 动态雷达 + 分层精读")

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

display_stable_stats = [row for row in stable_stats if row["topic"] != "Other"] or stable_stats
stable_df = pd.DataFrame(display_stable_stats)
selected_df = pd.DataFrame([item for item in items if item.get("llm_selected") == 1])
trend_df = pd.DataFrame(trend_series["stable"])

top_stable = display_stable_stats[0] if display_stable_stats else None
top_emerging = emerging_stats[0] if emerging_stats else None

hero_left, hero_right = st.columns([1.45, 1])
with hero_left:
    st.markdown("<div class='hero-card'>", unsafe_allow_html=True)
    st.markdown("### 今日结论")
    lead_parts = []
    if top_stable:
        lead_parts.append(f"主方向是 {top_stable['topic']}")
    if top_emerging:
        lead_parts.append(f"最新爆点是 {top_emerging['emerging_topic']}")
    if selection_stats:
        lead_parts.append(f"LLM 精读 {int(selection_stats.get('llm_items_selected', 0))} 条代表样本")
    st.write("；".join(lead_parts) + "。")
    if top_stable:
        st.markdown(
            f"<span class='badge'>主方向</span><b>{top_stable['topic']}</b> 今日热度 {top_stable['final_score']}，"
            f"7日变化 {top_stable['trend_delta_7d']:+.1f}",
            unsafe_allow_html=True,
        )
        st.write(top_stable["top_summary"])
    if top_emerging:
        st.markdown(
            f"<span class='badge'>动态爆点</span><b>{top_emerging['emerging_topic']}</b> 增长 {top_emerging['growth_rate']:.1f}x，"
            f"来源 {int(top_emerging['source_count'])}",
            unsafe_allow_html=True,
        )
        st.write(top_emerging["top_summary"])
    st.markdown("</div>", unsafe_allow_html=True)

with hero_right:
    st.markdown("<div class='hero-card'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("数据日期", target_date)
    c2.metric("总条目", len(items))
    c3.metric("LLM 精读", int(selection_stats.get("llm_items_selected", 0)))
    c4, c5, c6 = st.columns(3)
    c4.metric("Stable Topics", len({item.get("stable_topic") for item in items if item.get("stable_topic")}))
    c5.metric("Emerging Topics", len({item.get("emerging_topic") for item in items if item.get("emerging_topic")}))
    c6.metric("覆盖率", f"{selection_stats.get('coverage_ratio', 0):.1%}")
    if selection_stats:
        st.markdown(f"<p class='muted'>{selection_stats.get('notes', '')}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()
row1_left, row1_right = st.columns([1.2, 1])

with row1_left:
    st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
    st.subheader("主方向热力")
    if not stable_df.empty:
        fig = px.bar(
            stable_df.head(8).sort_values("final_score", ascending=True),
            x="final_score",
            y="topic",
            orientation="h",
            color="trend_delta_7d",
            color_continuous_scale="Tealgrn",
            labels={"final_score": "热度", "topic": "Stable Topic"},
        )
        fig.update_layout(height=360)
        st.plotly_chart(apply_plot_style(fig), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with row1_right:
    st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
    st.subheader("本周变化")
    rising = sorted(display_stable_stats, key=lambda row: row["trend_delta_7d"], reverse=True)[:4]
    falling = sorted(display_stable_stats, key=lambda row: row["trend_delta_7d"])[:4]
    st.markdown("**升温的 stable topics**")
    for row in rising:
        st.markdown(f"- `{row['topic']}`  `{row['trend_delta_7d']:+.1f}`")
    st.markdown("**值得盯的 emerging topics**")
    if emerging_stats:
        for row in sorted(emerging_stats, key=lambda row: row["growth_rate"], reverse=True)[:4]:
            st.markdown(f"- `{row['emerging_topic']}`  增长 `{row['growth_rate']:.1f}x`")
    st.markdown("**回落的 stable topics**")
    for row in falling:
        st.markdown(f"- `{row['topic']}`  `{row['trend_delta_7d']:+.1f}`")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()
row2_left, row2_right = st.columns([1, 1.15])

with row2_left:
    st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
    st.subheader("今天该看什么")
    if not selected_df.empty:
        for _, row in selected_df.sort_values("final_score", ascending=False).head(6).iterrows():
            st.markdown(f"- `[{row['stable_topic']}]` {str(row['one_line_summary'])[:120]} [原文]({row['url']})")
    st.markdown("</div>", unsafe_allow_html=True)

with row2_right:
    st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
    st.subheader("代表样本明细")
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
            column_config={
                "url": st.column_config.LinkColumn("链接"),
                "one_line_summary": st.column_config.TextColumn("一句话摘要", width="medium"),
                "title": st.column_config.TextColumn("标题", width="large"),
            },
            hide_index=True,
            use_container_width=True,
            height=360,
        )
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()
row3_left, row3_right = st.columns([1, 1])

with row3_left:
    st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
    st.subheader("一周主题快照")
    if not trend_df.empty:
        latest = trend_df[trend_df["date"] == trend_df["date"].max()].copy()
        latest = latest[latest["topic"] != "Other"].sort_values("final_score", ascending=False).head(6)
        fig_week = px.bar(
            latest.sort_values("final_score"),
            x="final_score",
            y="topic",
            orientation="h",
            color="trend_delta_7d",
            color_continuous_scale="Temps",
            labels={"final_score": "热度", "topic": "Stable Topic"},
        )
        fig_week.update_layout(height=320)
        st.plotly_chart(apply_plot_style(fig_week), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with row3_right:
    st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
    st.subheader("继续深挖")
    st.markdown("<p class='muted'>首页负责结论和代表样本，Today 看主题组织，Trend 看趋势，Explore 看原始数据。</p>", unsafe_allow_html=True)
    n1, n2, n3 = st.columns(3)
    with n1:
        st.page_link("pages/1_Today.py", label="进入 Today", icon="📌")
    with n2:
        st.page_link("pages/2_Trend.py", label="进入 Trend", icon="📈")
    with n3:
        st.page_link("pages/3_Explore.py", label="进入 Explore", icon="🔎")
    st.markdown("</div>", unsafe_allow_html=True)
