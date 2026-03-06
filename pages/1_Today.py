import streamlit as st
import pandas as pd
import plotly.express as px

# 使它可以引用 src
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import query_items, query_daily_stats
from src.utils import get_latest_date, today_str
from src.config import TOPICS

st.set_page_config(page_title="Today | 今日罗盘", page_icon="🧭", layout="wide")
st.title("🧭 今日科技罗盘")

# 获取最近有数据的日期
target_date = get_latest_date() or today_str()
st.caption(f"数据日期: {target_date}")

# 读取当前 target_date 的 items 和 stats
items = query_items(date=target_date, limit=100)
stats = query_daily_stats(days=7)  # 获取最近7天的每日统计

if not items:
    st.warning(f"由于尚未抓取，{target_date} 没有可用数据。请先执行 pipeline 或 backfill_demo_data.py")
    st.stop()

# 过滤出 target_date 的统计
today_stats = [s for s in stats if s["date"] == target_date]
# 如果当天还没聚合（比如 pipeline 没跑完），尝试用昨天
if not today_stats:
    st.warning("当天尚未进行 Topic 聚合，请运行 pipeline。将暂时展示列表数据。")
    today_stats = []

# --- 模块 A：Top Topics 横向条形图 ---
st.header("🎯 最高优方向 (Top Topics)")
if today_stats:
    df_stats = pd.DataFrame(today_stats)
    df_stats = df_stats.sort_values(by="final_score", ascending=True) # Plotly 中 ascending=True 把分数高的排在最上面
    
    fig = px.bar(
        df_stats, 
        x="final_score", 
        y="topic", 
        orientation='h',
        color="trend_delta_7d",
        color_continuous_scale="RdBu_r", # 暖色代表上升，冷色代表下降
        title="今日热图 (颜色代表较过去7天的热度变化)",
        labels={"final_score": "综合热度分", "topic": "科技方向"}
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# --- 模块 B：一句话摘要卡片区 ---
st.divider()
st.header("💡 一句话速览")

# 选出分数最高的前 4 个 topic
df_sorted_stats = sorted(today_stats, key=lambda x: x["final_score"], reverse=True)[:4]

# 如果没有 stat 用 items 去分组模拟一下
if not df_sorted_stats:
    st.write("暂无聚合数据，请执行 pipeline 聚合。")

cols = st.columns(4)
for i, stat in enumerate(df_sorted_stats):
    topic = stat["topic"]
    score = stat["final_score"]
    delta = stat["trend_delta_7d"]
    
    if delta > 1.0:
        trend_icon = "🔥 ↑"
    elif delta < -1.0:
        trend_icon = "❄️ ↓"
    else:
        trend_icon = "稳定 →"
        
    with cols[i % 4]:
        st.info(f"**{topic}**\n\n综合分: {score} | {trend_icon}")
        st.write(f"*{stat['top_summary']}*")
        
        # 找一条该 topic 的链接
        topic_items = [item for item in items if item["topic"] == topic]
        if topic_items:
            best_item = max(topic_items, key=lambda x: x["final_score"])
            st.markdown(f"🔗 [{best_item['title']}]({best_item['url']})")

# --- 模块 C：今日高价值事件表 ---
st.divider()
st.header("📋 高价值事件列表")

col1, col2 = st.columns(2)
with col1:
    filter_topic = st.selectbox("筛选方向", ["全部"] + TOPICS)
with col2:
    sources = list(set([item["source"] for item in items]))
    filter_source = st.selectbox("筛选来源", ["全部"] + sources)

# 过滤数据
filtered_items = [i for i in items if i["final_score"] > 0]
if filter_topic != "全部":
    filtered_items = [i for i in filtered_items if i["topic"] == filter_topic]
if filter_source != "全部":
    filtered_items = [i for i in filtered_items if i["source"] == filter_source]

# 转换为 DataFrame 用于展示
df_items = pd.DataFrame(filtered_items)
if not df_items.empty:
    df_items = df_items[["source", "title", "topic", "final_score", "one_line_summary", "url"]]
    df_items = df_items.sort_values(by="final_score", ascending=False)
    
    st.dataframe(
        df_items,
        column_config={
            "url": st.column_config.LinkColumn("链接"),
            "final_score": st.column_config.NumberColumn("热度分", format="%.1f"),
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )
else:
    st.info("没有满足上述条件的数据。")
