import json
import os
import re

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

st.set_page_config(page_title="合同风险初筛", page_icon="📄", layout="wide")

MODEL_DEFAULT = "deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

SYSTEM_PROMPT = """你是一名资深合同审查律师，擅长识别合同中的法律风险和商业风险。

请审查用户提供的合同文本，找出其中对签约方不利的风险条款，并输出一个严格的 JSON 数组。数组中的每个元素是一个对象，包含以下四个字段：

- "risk_type": 风险类型，例如"违约金过高"、"付款条件不利"、"管辖条款不利"、"单方解除权"、"知识产权归属不清"、"保密义务过重"、"责任限制不合理"等；
- "excerpt": 原文摘录，尽量逐字引用合同中对应的关键文字；
- "risk": 风险说明，用一到两句话解释该条款为什么对签约方不利；
- "suggestion": 修改建议，给出具体、可操作的修改方向。

要求：
1. 只输出 JSON 数组，不要输出任何解释性文字、前后缀或 Markdown 代码块标记。
2. 如果合同文本中没有明显风险，输出空数组 []。
3. excerpt 必须尽量引用原文，不要改写。
"""


def build_user_prompt(contract_text: str) -> str:
    return f"请审查以下合同文本：\n\n{contract_text}"


def extract_json(text: str):
    """从模型返回内容中稳健地提取 JSON。"""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    starts = [i for i in (text.find("["), text.find("{")) if i != -1]
    end = max(text.rfind("]"), text.rfind("}"))
    if not starts or end <= min(starts):
        raise ValueError("模型未返回有效的 JSON")

    candidate = text[min(starts) : end + 1]
    return json.loads(candidate)


def format_result_text(items) -> str:
    lines = []
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. 风险类型：{item.get('risk_type', '未分类风险')}")
        lines.append(f"   原文摘录：{item.get('excerpt', '')}")
        lines.append(f"   风险说明：{item.get('risk', '')}")
        lines.append(f"   修改建议：{item.get('suggestion', '')}")
        lines.append("")
    return "\n".join(lines).strip()


def get_api_key() -> str:
    secret = ""
    try:
        secret = st.secrets.get("DEEPSEEK_API_KEY", "")
    except Exception:
        secret = ""
    return (os.getenv("DEEPSEEK_API_KEY", "") or secret).strip()


def render_copy_button(text: str) -> None:
    js_text = json.dumps(text)
    html = f"""
    <style>
      .copy-btn {{
        background-color: #ff4b4b;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 14px;
        cursor: pointer;
      }}
      .copy-btn:hover {{ background-color: #e63b3b; }}
    </style>
    <button class="copy-btn" id="copy-btn">复制结果</button>
    <script>
      const btn = document.getElementById("copy-btn");
      const text = {js_text};
      function fallbackCopy(t) {{
        const ta = document.createElement("textarea");
        ta.value = t;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
      }}
      btn.addEventListener("click", () => {{
        const done = () => {{
          btn.textContent = "已复制";
          setTimeout(() => {{ btn.textContent = "复制结果"; }}, 1500);
        }};
        if (navigator.clipboard && window.isSecureContext) {{
          navigator.clipboard.writeText(text).then(done).catch(() => {{
            fallbackCopy(text);
            done();
          }});
        }} else {{
          fallbackCopy(text);
          done();
        }}
      }});
    </script>
    """
    components.html(html, height=42)


def run_analysis(contract_text: str, api_key: str, model: str) -> str:
    client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(contract_text)},
        ],
        temperature=0.2,
        max_tokens=4096,
        stream=False,
    )
    return response.choices[0].message.content


def main() -> None:
    st.title("合同风险初筛")
    st.caption("粘贴合同文本，自动识别风险条款并给出修改建议")

    env_key = get_api_key()

    with st.sidebar:
        st.header("设置")
        if env_key:
            st.success("已从环境变量读取 API Key")
            api_key = env_key
        else:
            st.warning("未检测到环境变量 DEEPSEEK_API_KEY")
            api_key = st.text_input(
                "DeepSeek API Key",
                type="password",
                help="在 https://platform.deepseek.com 申请后填入",
            ).strip()

        model = st.selectbox(
            "模型",
            ["deepseek-chat", "deepseek-reasoner"],
            index=0,
        )
        st.divider()
        st.markdown(
            "**免责声明**：本工具仅作风险提示参考，不构成正式法律意见，"
            "重要合同请由执业律师审核。"
        )

    contract_text = st.text_area(
        "合同文本",
        height=280,
        placeholder="在此粘贴合同正文，例如：本合同自双方签字之日起生效，任何一方违约应支付合同总金额 50% 的违约金……",
        key="contract_text",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        analyze = st.button("分析", type="primary", use_container_width=True)
    with col2:
        clear = st.button("清空", use_container_width=True)

    if clear:
        st.session_state["contract_text"] = ""
        st.session_state.pop("analysis_items", None)
        st.session_state.pop("analysis_text", None)
        st.rerun()

    if analyze:
        if not contract_text.strip():
            st.warning("请先粘贴合同文本。")
        elif not api_key:
            st.error("请先在环境变量中设置 DEEPSEEK_API_KEY，或在左侧填入 API Key。")
        else:
            with st.spinner("正在分析合同风险……"):
                try:
                    raw = run_analysis(contract_text, api_key, model)
                    items = extract_json(raw)
                    if not isinstance(items, list):
                        raise ValueError("模型返回内容不是数组")
                    st.session_state["analysis_items"] = items
                    st.session_state["analysis_text"] = format_result_text(items)
                except Exception as exc:
                    st.error(f"分析失败：{exc}")
                    st.session_state.pop("analysis_items", None)
                    st.session_state.pop("analysis_text", None)

    items = st.session_state.get("analysis_items")
    if items is not None:
        st.subheader("风险条款")
        if not items:
            st.info("未识别出明显风险条款。")
        else:
            for i, item in enumerate(items, 1):
                risk_type = item.get("risk_type") or "未分类风险"
                with st.expander(f"{i}. {risk_type}", expanded=True):
                    st.markdown("**原文摘录**")
                    st.write(item.get("excerpt", ""))
                    st.markdown("**风险说明**")
                    st.write(item.get("risk", ""))
                    st.markdown("**修改建议**")
                    st.write(item.get("suggestion", ""))

        if items:
            render_copy_button(st.session_state.get("analysis_text", ""))


if __name__ == "__main__":
    main()
