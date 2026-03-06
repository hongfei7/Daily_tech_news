import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import TOPICS
from src.database import (
    get_distinct_dates,
    get_distinct_emerging_topics,
    get_distinct_sources,
    query_items,
)
from src.ui import apply_light_theme, apply_plot_style


st.set_page_config(page_title="Explore | 数据探索", page_icon="🔎", layout="wide")
st.title("🔎 Explore")
apply_light_theme()

dates = ["全部"] + get_distinct_dates()
stable_topics = ["全部"] + TOPICS
emerging_topics = ["全部"] + get_distinct_emerging_topics()
sources = ["全部"] + get_distinct_sources()

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    selected_date = st.selectbox("日期", dates)
with col2:
    selected_stable = st.selectbox("Stable Topic", stable_topics)
with col3:
    selected_emerging = st.selectbox("Emerging Topic", emerging_topics)
with col4:
    selected_source = st.selectbox("Source", sources)
with col5:
    llm_filter = st.selectbox("LLM Selected", ["全部", "是", "否"])

search = st.text_input("搜索标题或摘要")
llm_selected = None if llm_filter == "全部" else 1 if llm_filter == "是" else 0

items = query_items(
    date=None if selected_date == "全部" else selected_date,
    stable_topic=None if selected_stable == "全部" else selected_stable,
    emerging_topic=None if selected_emerging == "全部" else selected_emerging,
    source=None if selected_source == "全部" else selected_source,
    llm_selected=llm_selected,
    search=search or None,
    limit=1000,
)

if not items:
    st.info("没有匹配到数据。")
    st.stop()

df = pd.DataFrame(items)

st.subheader("评分分布图")
fig = px.scatter(
    df,
    x="final_score",
    y="importance_score",
    color="stable_topic",
    symbol="llm_selected",
    size="momentum_score",
    hover_name="title",
    hover_data=["source", "emerging_topic", "selection_bucket", "selection_reason", "novelty_score"],
    labels={"final_score": "综合得分", "importance_score": "重要性", "momentum_score": "趋势动量"},
)
fig.update_layout(height=620)
st.plotly_chart(apply_plot_style(fig), use_container_width=True)

st.subheader("原始条目")
show_columns = [
    "date",
    "source",
    "stable_topic",
    "emerging_topic",
    "llm_selected",
    "selection_bucket",
    "selection_reason",
    "final_score",
    "one_line_summary",
    "title",
    "url",
]
st.dataframe(
    df[show_columns].sort_values(["date", "final_score"], ascending=[False, False]),
    column_config={
        "url": st.column_config.LinkColumn("链接"),
        "one_line_summary": st.column_config.TextColumn("一句话摘要", width="medium"),
        "title": st.column_config.TextColumn("标题", width="large"),
        "selection_reason": st.column_config.TextColumn("选样原因", width="medium"),
    },
    hide_index=True,
    use_container_width=True,
    height=560,
)
