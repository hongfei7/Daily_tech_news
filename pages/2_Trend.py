import streamlit as st
import pandas as pd
import plotly.express as px

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import query_daily_stats, query_items, get_distinct_dates
from src.config import TOPICS

st.set_page_config(page_title="Trend | 趋势", page_icon="📈", layout="wide")
st.title("📈 趋势分析")

# --- 模块 A：7/14/30 天趋势折线图 ---
st.header("历时热度变化")

days_option = st.radio("时间范围", options=[7, 14, 30], index=0, horizontal=True)

stats = query_daily_stats(days=days_option)

if not stats:
    st.warning("暂无历史统计数据。")
    st.stop()

df_stats = pd.DataFrame(stats)

fig_line = px.line(
    df_stats, 
    x="date", 
    y="final_score", 
    color="topic",
    markers=True,
    title=f"过去 {days_option} 天方向热度趋势"
)
st.plotly_chart(fig_line, use_container_width=True)

# --- 模块 B：上升 / 下降方向榜 ---
st.divider()
st.header("🏆 涨跌幅榜")

# 使用最近一天的数据来看 trend_delta_7d
latest_date = df_stats["date"].max()
df_latest = df_stats[df_stats["date"] == latest_date]

if not df_latest.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 ↑ 升温最快")
        rising = df_latest.sort_values(by="trend_delta_7d", ascending=False).head(3)
        for _, row in rising.iterrows():
            if row["trend_delta_7d"] > 0:
                st.metric(label=row["topic"], value=row["final_score"], delta=f"+{row['trend_delta_7d']}")
                
    with col2:
        st.subheader("❄️ ↓ 降温最快")
        falling = df_latest.sort_values(by="trend_delta_7d", ascending=True).head(3)
        for _, row in falling.iterrows():
            if row["trend_delta_7d"] < 0:
                st.metric(label=row["topic"], value=row["final_score"], delta=f"{row['trend_delta_7d']}")


# --- 模块 C：Topic × Source 热力图 (最近7天总览) ---
st.divider()
st.header("🔍 热度来源分布 (过去7天)")
st.caption("观察某个方向到底是'论文研究驱动'(arXiv) 还是 '工程界驱动'(GitHub) 或是 '厂商发布驱动'(Blogs)。")

recent_items = []
dates = get_distinct_dates()[:7]
for d in dates:
    recent_items.extend(query_items(date=d, limit=500))

if recent_items:
    df_items = pd.DataFrame(recent_items)
    
    # 构造交叉表 (频次)
    pivot = pd.pivot_table(
        df_items, 
        values='id', 
        index='topic', 
        columns='source', 
        aggfunc='count', 
        fill_value=0
    )
    
    fig_heat = px.imshow(
        pivot,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        title="不同主题的信息来源频次"
    )
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("最近没有收集到 Item 数据来生成热力图。")
