# 📋 配置使用说明

## 🔧 环境变量配置

系统现在支持通过环境变量来配置关键参数，提高了灵活性和安全性。

### 汇率配置

```bash
# 印尼盾汇率
export IDR_PER_RMB=2300    # 印尼盾对人民币汇率
export IDR_PER_USD=16000   # 印尼盾对美元汇率

# 马来币汇率
export MYR_PER_RMB=0.6     # 马来币对人民币汇率
```

### 操作费配置

```bash
# 印尼模块操作费（人民币）
export IDN_OP_FEE_SINGLE=2.0    # 单品订单操作费
export IDN_OP_FEE_MULTI=2.5     # 多品订单操作费

# 马来模块操作费（马来币）
export MYR_OP_FEE_XIFASHUI=2.5   # xifashui产品操作费
export MYR_OP_FEE_KINGSTICK=2.5  # kingstick产品操作费
export MYR_OP_FEE_DEFAULT=2.5    # 默认操作费
```

### Web服务配置

```bash
# Flask服务器配置
export FLASK_HOST=127.0.0.1      # 服务器绑定地址（安全）
export FLASK_PORT=8080           # 服务器端口
export FLASK_DEBUG=false         # 调试模式（生产环境务必设为false）

# 文件处理配置
export MAX_FILE_SIZE=52428800     # 最大文件大小（字节，默认50MB）
export LOG_LEVEL=INFO            # 日志级别
```

## 🚀 使用方法

### 1. 默认配置启动

直接启动，使用内置默认配置：

```bash
python app.py
```

### 2. 自定义配置启动

设置环境变量后启动：

```bash
# 设置自定义汇率
export IDR_PER_RMB=2350
export IDR_PER_USD=16100

# 设置安全的生产环境配置
export FLASK_DEBUG=false
export FLASK_HOST=127.0.0.1

# 启动服务
python app.py
```

### 3. 一次性配置

在启动命令中直接设置：

```bash
IDR_PER_RMB=2350 FLASK_DEBUG=false python app.py
```

## 📊 配置查看

查看当前配置：

```bash
python config.py
```

输出示例：
```
📋 当前系统配置:
  汇率配置: IDR/RMB=2300, IDR/USD=16000, MYR/RMB=0.6
  文件大小限制: 50MB
  Flask配置: {'host': '127.0.0.1', 'port': 8080, 'debug': False}
  日志级别: INFO
```

## ⚠️ 安全建议

### 生产环境配置

```bash
# 必须设置的安全配置
export FLASK_DEBUG=false         # 关闭调试模式
export FLASK_HOST=127.0.0.1      # 只绑定本地地址
export LOG_LEVEL=WARNING         # 减少日志输出

# 可选的性能配置
export MAX_FILE_SIZE=26214400     # 减小文件大小限制到25MB
```

### 开发环境配置

```bash
# 开发时的便利配置
export FLASK_DEBUG=true          # 启用调试模式
export FLASK_HOST=0.0.0.0        # 允许局域网访问
export LOG_LEVEL=DEBUG           # 详细日志
```

## 🔄 配置文件更新

如需永久修改默认配置，可直接编辑 `config.py` 文件中的默认值。

## 📝 注意事项

1. **汇率更新**: 建议定期更新汇率配置以确保数据准确性
2. **安全性**: 生产环境务必关闭调试模式并限制主机绑定
3. **文件大小**: 根据实际需求调整文件大小限制
4. **重启生效**: 修改环境变量后需要重启服务才能生效