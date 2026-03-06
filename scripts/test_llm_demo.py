import sys
from pathlib import Path

# 添加项目根目录到 sys.path，以便可以直接运行脚本
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.classifier import classify_item
from src.summarizer import generate_one_line_summary

def test_llm_processing():
    print("=" * 60)
    print("🤖 测试 MiniMax M2.5 大模型摘要与分类功能")
    print("=" * 60)

    test_cases = [
        {
            "title": "Anthropic Announces Claude 3.5 Sonnet",
            "summary": "Today, we're announcing Claude 3.5 Sonnet—our newest model that raises the industry bar for intelligence while operating at twice the speed of Claude 3 Opus and one-fifth the cost. It is now available for free on Claude.ai and the Claude iOS app."
        },
        {
            "title": "NVIDIA Blackwell B200 Architecture Technical Overview",
            "summary": "NVIDIA Blackwell architecture features a new tensor core capable of processing 20 petaflops of FP4 precision. This drastically reduces the cost and energy required to run trillion-parameter AI models."
        },
        {
            "title": "Introducing SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering",
            "summary": "SWE-agent turns LMs (e.g. GPT-4) into software engineering agents that can fix bugs and issues in real GitHub repositories. On SWE-bench, SWE-agent resolves 12.29% of issues."
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n[测试案例 {i}]")
        print(f"📌 原标题: {case['title']}")
        print(f"📄 原摘要: {case['summary']}")
        
        print("\n⏳ 正在调用大模型进行处理...")
        
        topic = classify_item(case['title'], case['summary'])
        print(f"👉 【大模型分类结果】: {topic}")
        
        summary = generate_one_line_summary(case['title'], case['summary'])
        print(f"👉 【大模型一句话摘要】: {summary}")
        
        print("-" * 60)

if __name__ == "__main__":
    test_llm_processing()
