# 仓库指南

## 项目结构与模块组织
- `app.py`：Flask 服务器。处理 `/`（UI）和 `/process`（文件上传，分发到分析器，返回 Excel）。
- `analysis_multi.py`：印尼分析器（多文件合并、组合 SKU 处理、货币换算）。入口：`process_financial_data(...)`。
- `analysis_mal.py`：马来西亚分析器（跳过第 2 行表头注释、筛选 `Type=order`、按 SKU 的订单操作费）。入口：`process_malaysia_financial_data(...)`。
- `index.html`：单页 UI（拖拽上传、模块切换、进度、下载）。
- `requirements.txt`、`start.sh`、`README.md`、`使用说明.md`。暂未有专门的 tests 或 assets 目录。

## 构建、测试与开发命令
- 创建虚拟环境：`python -m venv .venv && source .venv/bin/activate`
- 安装依赖：`pip install -r requirements.txt`
- 本地运行：`python app.py`（服务地址 `http://localhost:8080`）
- 备用启动：`./start.sh`
- 可选静态检查/格式化（若已安装）：`ruff .`、`black .`

## 代码风格与命名约定
- Python 3.x，4 空格缩进，UTF-8。
- 文件名与函数：`snake_case`；常量：`UPPER_SNAKE`（例如 `IDR_PER_RMB`）。
- 模块聚焦：Web（`app.py`）与分析引擎（`analysis_*.py`）分离。
- 日志：Web 层优先使用 `app.logger`；对用户的提示尽量简洁，必要时中英双语。
- 避免硬编码业务费率；优先使用配置或表驱动（如马来模块的操作费映射）。

## 测试指南
- 当前无测试套件。若新增测试，使用 `pytest`，目录结构：`tests/test_<module>.py`。
- 单元测试：针对纯转换逻辑（如 `preprocess_combo_sku`）使用小型 DataFrame。
- 集成测试：使用临时目录与合成 Excel，验证端到端的写表输出。
- 运行（如已添加）：`pytest -q`。

## 提交与拉取请求指南
- 提交信息：祈使语气，必要时添加作用域前缀：`server:`、`multi:`、`mal:`、`ui:`（例如：`mal: map operation fee from cost table`）。
- PR 应包含：目的、关键变更、风险/兼容性说明、UI 截图与生成工作簿片段、本地验证步骤。
- 不要提交真实数据或大体积二进制。保持 diff 聚焦；引用关联的 issue。

## 安全与配置建议
- 上传：仅允许 `.xlsx/.xls`；大小上限 100MB；文件在 `tempfile.TemporaryDirectory()` 中处理并自动清理。
- 不要提交任何凭证或包含 PII 的样例数据。若添加 Docker，请使用非 root 用户并配置健康检查。

## 架构概览
- 流程：UI 上传 → `POST /process` → 保存至临时目录 → 调用所选分析器 → 写出 Excel → `send_file` 响应 → 浏览器下载。
