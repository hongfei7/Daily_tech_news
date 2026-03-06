import streamlit as st
import pandas as pd
import plotly.express as px

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import query_items
from src.config import TOPICS

st.set_page_config(page_title="Explore | 探索", page_icon="🔭", layout="wide")
st.title("🔭 数据探索")

st.markdown("这一页用于深入探索原始数据，找到高新鲜度和高重要性的“宝藏信息”。")

# 读取最近的一些数据
# 由于需要画散点图，我们不去强求某一天，取最近 300 条分高的
items = query_items(limit=300)
if not items:
    st.warning("暂无数据。")
    st.stop()
    
df_items = pd.DataFrame(items)

# --- 模块 A：新鲜度 × 重要性散点图 ---
st.header("🧭 价值发现罗盘 (新鲜度 vs 绝对重要性)")

fig_scatter = px.scatter(
    df_items,
    x="novelty_score",
    y="importance_score",
    color="topic",
    size="final_score",
    hover_name="title",
    hover_data=["source", "date", "final_score"],
    title="气泡越大代表综合得分(final_score)越高",
    labels={"novelty_score": "新鲜度 (Novelty)", "importance_score": "重要度 (Importance)"}
)
fig_scatter.update_layout(height=600)
st.plotly_chart(fig_scatter, use_container_width=True)

# --- 模块 B：原始条目搜索与过滤 ---
st.divider()
st.header("📖 原始数据库检索")

col1, col2, col3 = st.columns(3)
with col1:
    search_q = st.text_input("🔍 搜索标题", "")
with col2:
    f_topic = st.selectbox("📂 过滤主题", ["全部"] + TOPICS)
with col3:
    sources = ["全部"] + list(df_items["source"].unique())
    f_source = st.selectbox("🌐 过滤来源", sources)

# 后端执行检索
results = query_items(
    limit=100,
    search=search_q if search_q else None,
    topic=f_topic if f_topic != "全部" else None,
    source=f_source if f_source != "全部" else None
)

if results:
    df_res = pd.DataFrame(results)
    df_res = df_res[["date", "source", "topic", "final_score", "title", "url"]]
    st.dataframe(
        df_res,
        column_config={
            "url": st.column_config.LinkColumn("外部链接"),
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("没有找到匹配的数据。")
