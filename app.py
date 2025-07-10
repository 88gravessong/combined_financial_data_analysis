#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask后端服务器 - 财务数据分析系统
"""

import os
import tempfile
import traceback
from pathlib import Path
from flask import Flask, request, send_file, jsonify, render_template_string
from werkzeug.utils import secure_filename
import pandas as pd

# 导入分析模块
from analysis_multi import process_financial_data
from analysis_mal import process_malaysia_financial_data
from config import FLASK_CONFIG, MAX_FILE_SIZE, ALLOWED_EXTENSIONS

app = Flask(__name__)
# 使用配置文件中的文件大小限制
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """返回前端页面"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <h1>错误</h1>
        <p>找不到 index.html 文件。请确保前端文件存在。</p>
        """, 404

@app.route('/process', methods=['POST'])
def process_files():
    """处理上传的文件并执行分析"""
    try:
        # 获取分析模块类型
        analysis_type = request.form.get('analysis_type', 'indonesia')
        
        # 检查是否有文件上传
        if 'orders' not in request.files or 'settlements' not in request.files or 'consumption' not in request.files:
            return jsonify({'error': '缺少必要的文件。请确保上传了订单表、结算表和产品消耗表。'}), 400

        # 获取上传的文件
        order_files = request.files.getlist('orders')
        settlement_files = request.files.getlist('settlements')
        consumption_file = request.files['consumption']

        # 验证文件
        if not order_files or not settlement_files or not consumption_file:
            return jsonify({'error': '请上传所有必要的文件'}), 400

        # 检查文件类型
        all_files = order_files + settlement_files + [consumption_file]
        for file in all_files:
            if file.filename == '' or not allowed_file(file.filename):
                return jsonify({'error': f'文件 {file.filename} 格式不正确，请上传Excel文件'}), 400

        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 保存订单文件
            order_paths = []
            for i, file in enumerate(order_files):
                filename = f"order_{i+1}_{secure_filename(file.filename)}"
                file_path = temp_path / filename
                file.save(str(file_path))
                order_paths.append(file_path)

            # 保存结算文件
            settlement_paths = []
            for i, file in enumerate(settlement_files):
                filename = f"settlement_{i+1}_{secure_filename(file.filename)}"
                file_path = temp_path / filename
                file.save(str(file_path))
                settlement_paths.append(file_path)

            # 保存消耗文件
            consumption_filename = f"consumption_{secure_filename(consumption_file.filename)}"
            consumption_path = temp_path / consumption_filename
            consumption_file.save(str(consumption_path))

            # 根据选择的模块执行数据分析
            try:
                if analysis_type == 'malaysia':
                    output_path = process_malaysia_financial_data(
                        order_files=order_paths,
                        settlement_files=settlement_paths,
                        consumption_file=consumption_path,
                        output_dir=temp_path
                    )
                    download_name = '马来跨境店财务分析结果.xlsx'
                else:  # indonesia (默认)
                    output_path = process_financial_data(
                        order_files=order_paths,
                        settlement_files=settlement_paths,
                        consumption_file=consumption_path,
                        output_dir=temp_path
                    )
                    download_name = '印尼财务分析结果.xlsx'
                
                # 返回结果文件
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=download_name,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )

            except (ValueError, KeyError, pd.errors.EmptyDataError) as e:
                app.logger.error(f"数据分析错误: {str(e)}")
                app.logger.error(traceback.format_exc())
                return jsonify({'error': f'数据分析失败: 请检查文件格式和数据完整性 - {str(e)}'}), 400
            except Exception as e:
                app.logger.error(f"数据分析意外错误: {str(e)}")
                app.logger.error(traceback.format_exc())
                return jsonify({'error': '系统处理出现意外错误，请联系管理员'}), 500

    except (FileNotFoundError, PermissionError) as e:
        app.logger.error(f"文件操作错误: {str(e)}")
        return jsonify({'error': f'文件操作失败: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"文件处理意外错误: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': '系统处理出现意外错误，请联系管理员'}), 500

if __name__ == '__main__':
    print("🚀 启动财务数据分析系统...")
    print(f"📊 访问地址: http://{FLASK_CONFIG['host']}:{FLASK_CONFIG['port']}")
    print("💡 使用 Ctrl+C 停止服务器")
    
    # 使用配置文件中的Flask配置
    app.run(
        debug=FLASK_CONFIG['debug'], 
        host=FLASK_CONFIG['host'], 
        port=FLASK_CONFIG['port']
    ) 