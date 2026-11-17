# 合同风险初筛工具

一个基于 Streamlit + DeepSeek API 的合同风险初筛小工具。粘贴合同文本，自动识别风险条款并给出修改建议。

## 本地运行

1. 进入项目目录：

   ```bash
   cd contract-risk-checker
   ```

2. 创建并激活虚拟环境（推荐）：

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

4. 设置 DeepSeek API Key（二选一）：

   - 环境变量方式：

     ```bash
     export DEEPSEEK_API_KEY="sk-你的key"
     ```

   - 或复制 `.env.example` 为 `.env`，填入你的 key：

     ```bash
     cp .env.example .env
     ```

5. 启动应用：

   ```bash
   streamlit run app.py
   ```

   浏览器会自动打开 `http://localhost:8501`。

## API Key 获取

到 DeepSeek 开放平台注册并创建 API Key：https://platform.deepseek.com

## 说明

- 默认使用 `deepseek-chat` 模型，可在左侧切换为 `deepseek-reasoner`。
- 结果仅供风险提示参考，不构成正式法律意见。

## 部署给客户

### 方式一：Streamlit Community Cloud（免费，最快）

1. 把本项目上传到 GitHub 仓库（包含 `app.py`、`requirements.txt`）。
2. 打开 https://share.streamlit.io ，点击 New app，选择仓库和 `app.py`。
3. 在应用的 Settings → Secrets 中添加：

   ```toml
   DEEPSEEK_API_KEY = "sk-你的key"
   ```

4. Deploy 后会得到一个形如 `https://你的用户名-仓库名.streamlit.app` 的公网链接，把这个链接发给客户即可。

注意：API Key 存在服务端，客户看不到；但所有调用走你的 DeepSeek 账户，按量计费，报价时要把 API 成本算进去。国内访问 Community Cloud 可能不稳定。

### 方式二：国内云服务器（客户可直接访问）

用阿里云/腾讯云轻量应用服务器，安装 Python 后把代码传上去，运行：

```bash
export DEEPSEEK_API_KEY="sk-你的key"
nohup streamlit run app.py --server.port 8501 --server.headless true > streamlit.log 2>&1 &
```

然后把 `http://服务器IP:8501` 发给客户，有域名可以再绑定域名并配置 HTTPS。

### 方式三：打包成桌面程序（仅演示用）

可以用 PyInstaller 打成 macOS/Windows 可执行文件，双击即可运行。但这种方式会把 API Key 打包进程序里，容易被提取，只适合给单个客户做演示，不建议用于正式商用交付。
