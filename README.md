# 💰 财务数据分析系统

一个基于Web的财务数据分析系统，支持多文件上传和自动化财务指标计算。

## ✨ 功能特点

- 🔗 **多文件支持**: 支持上传多个订单表和结算表文件进行合并分析
- 📊 **拖拽上传**: 现代化的拖拽式文件上传界面
- 🚀 **一键分析**: 自动化财务指标计算和报告生成
- 📈 **详细报告**: 生成包含多个工作表的Excel分析报告
- 🎨 **美观界面**: 响应式设计，支持移动设备

## 📁 文件结构

```
├── app.py              # Flask Web服务器
├── analysis_multi.py   # 多文件分析引擎  
├── analysis_mal.py     # 马来西亚财务分析模块
├── index.html          # Web前端页面
├── requirements.txt    # 项目依赖
├── start.sh           # 本地启动脚本
├── docker-start.sh    # Docker一键启动脚本
├── Dockerfile         # Docker镜像构建文件
├── docker-compose.yml # Docker Compose配置
├── .dockerignore      # Docker构建忽略文件
├── Docker-README.md   # Docker部署详细指南
├── 使用说明.md        # 详细使用说明
└── README.md          # 项目说明
```

## 🚀 快速开始

### 方式一：Docker部署（推荐）

#### 1. 使用一键脚本

```bash
./docker-start.sh
```

#### 2. 手动部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 3. 直接使用Docker

```bash
# 构建镜像
docker build -t financial-analysis .

# 运行容器
docker run -d -p 8080:8080 --name financial-app financial-analysis
```

### 方式二：本地部署

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

如果遇到SSL证书问题，可使用：
```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

#### 2. 启动服务

```bash
python app.py
# 或使用启动脚本
./start.sh
```

### 访问系统

打开浏览器访问：`http://localhost:8080`

## 🐳 Docker部署优势

- **🔒 环境隔离**: 避免本地环境污染和依赖冲突
- **⚡ 快速部署**: 一键启动，无需配置Python环境
- **🚀 易于扩展**: 支持容器编排和负载均衡
- **📦 便携性强**: 在任何支持Docker的环境中运行
- **🛡️ 安全性好**: 使用非root用户运行，包含健康检查
- **🔄 自动重启**: 容器异常时自动重启服务

## 📊 使用说明

### 文件要求

1. **订单表** (支持多个文件)
   - Excel格式 (.xlsx, .xls)
   - 必须包含：订单ID、SKU、数量、是否出库、平台状态等列

2. **结算表** (支持多个文件)
   - Excel格式 (.xlsx, .xls)  
   - 必须包含：订单ID、结算金额等列

3. **产品成本消耗表** (单个文件)
   - Excel格式 (.xlsx, .xls)
   - 必须包含：SKU、印尼盾ads消耗、印尼盾gmvmax消耗、印尼盾单sku成本等列

### 操作步骤

1. **上传文件**: 在网页中拖拽或点击选择文件
2. **检查文件**: 确认所有三类文件都已上传
3. **开始分析**: 点击"🚀 开始分析"按钮
4. **下载结果**: 分析完成后下载Excel报告

## 📈 输出报告

分析完成后将生成包含以下工作表的Excel文件：

- **订单表_含结算与操作费**: 原始订单数据加上计算字段
- **sku汇总_结算与操作费**: SKU级别的汇总数据  
- **排除订单_多行结算**: 被排除的重复结算订单
- **sku财务指标**: 详细的SKU级别财务指标分析

## 💡 技术特点

- **后端**: Flask + pandas + openpyxl
- **前端**: 原生HTML/CSS/JavaScript，响应式设计
- **文件处理**: 支持多文件合并和临时目录管理
- **错误处理**: 完善的异常处理和用户反馈

## 🔧 配置参数

在 `analysis_multi.py` 中可修改汇率设置：

```python
IDR_PER_RMB, IDR_PER_USD = 2300, 16000  # 印尼盾对人民币和美元汇率
```

## 📝 注意事项

- 确保上传的Excel文件格式正确且包含必要的列
- 系统会自动识别列名，支持中英文列名
- 文件大小限制为100MB
- 处理大量数据时请耐心等待

## 🐛 故障排除

### 常见问题

1. **SSL证书错误**: 使用 `--trusted-host` 参数安装依赖
2. **列名识别失败**: 检查Excel文件中的列名是否包含关键字
3. **内存不足**: 减少上传文件大小或增加系统内存

### Docker相关问题

1. **容器启动失败**: 
   ```bash
   # 查看详细日志
   docker-compose logs financial-analysis
   
   # 重新构建镜像
   docker-compose build --no-cache
   ```

2. **端口冲突**: 
   ```bash
   # 修改docker-compose.yml中的端口映射
   ports:
     - "8081:8080"  # 改为其他端口
   ```

3. **权限问题**: 
   ```bash
   # 确保临时目录有正确权限
   mkdir -p temp
   chmod 755 temp
   ```

### Docker管理命令

```bash
# 查看容器状态
docker-compose ps

# 重启服务
docker-compose restart

# 更新并重新部署
docker-compose pull && docker-compose up -d

# 清理未使用的镜像
docker system prune

# 查看容器资源使用
docker stats financial-analysis-app
```

### 日志查看

Flask服务器会在控制台输出详细的处理日志，包括：
- 文件读取状态
- 数据合并过程  
- 列名识别结果
- 处理统计信息

## 🚀 扩展功能

系统设计为模块化架构，可以轻松扩展：

- 添加新的数据源类型
- 增加更多财务指标计算
- 支持其他文件格式 (CSV, JSON等)
- 集成数据库存储
- 添加用户认证和权限管理

---

**开发者**: 自动算利润团队  
**版本**: v1.0  
**更新时间**: 2024年12月 