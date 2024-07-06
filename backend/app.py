from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import logging
import json
import ast

load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'

def generate_gemini_response(prompt):
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'contents': [{'parts': [{'text': prompt}]}]
    }
    try:
        response = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", headers=headers, json=data)
        response.raise_for_status()
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error calling Gemini API: {e}")
        raise

def parse_characters(response):
    try:
        # 嘗試直接解析 JSON
        characters = json.loads(response)
        if isinstance(characters, list) and all(isinstance(char, dict) for char in characters):
            return characters
    except json.JSONDecodeError:
        pass
    
    try:
        # 嘗試使用 ast.literal_eval 解析
        characters = ast.literal_eval(response)
        if isinstance(characters, list) and all(isinstance(char, dict) for char in characters):
            return characters
    except (SyntaxError, ValueError):
        pass
    
    # 如果上述方法都失敗，嘗試手動解析
    characters = []
    lines = response.split('\n')
    current_char = {}
    for line in lines:
        if line.strip().startswith('{'):
            current_char = {}
        elif line.strip().endswith('}'):
            if current_char:
                characters.append(current_char)
                current_char = {}
        else:
            parts = line.split(':')
            if len(parts) == 2:
                key = parts[0].strip().strip('"')
                value = parts[1].strip().strip(',').strip('"')
                current_char[key] = value
    
    return characters if characters else None

@app.route('/generate-characters', methods=['POST'])
def generate_characters():
    app.logger.info("Received request to generate characters")
    data = request.json
    app.logger.debug(f"Received data: {data}")

    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    user_name = data.get('userName')
    anxiety_source = data.get('anxietySource')
    
    if not user_name or not anxiety_source:
        return jsonify({'error': 'Missing userName or anxietySource'}), 400
    
    prompt = f"""
    根據以下訊息生成4個角色:
    用戶名: {user_name}
    焦慮來源: {anxiety_source}
    每個角色應包含:名字、描述、如何幫助解決焦慮
    請以JSON格式返回結果，格式如下:
    [
        {{"name": "角色名", "description": "角色描述", "help": "如何幫助解決焦慮"}},
        ...
    ]
    """
    
    try:
        response = generate_gemini_response(prompt)
        app.logger.debug(f"Gemini API response: {response}")
        characters = parse_characters(response)
        if characters:
            app.logger.info(f"Generated characters: {characters}")
            return jsonify(characters)
        else:
            raise ValueError("Unable to parse character data")
    except Exception as e:
        app.logger.error(f"Error generating characters: {e}")
        app.logger.error(f"Raw response: {response}")
        # 返回預設角色
        default_characters = [
            {"name": "內心的批評者", "description": "代表你內心的自我懷疑", "help": "挑戰消極想法"},
            {"name": "冷靜的智者", "description": "一位年長的智者，擁有豐富的人生經驗。", "help": "提供理性的建議和長遠的視角。"},
            {"name": "活力四射的朋友", "description": "一個充滿正能量的年輕人。", "help": "通過積極的態度和有趣的活動分散注意力。"},
            {"name": "同理心強的諮詢師", "description": "專業的心理諮詢師。", "help": "提供專業的心理支持和具體的應對策略。"}
        ]
        return jsonify(default_characters)

if __name__ == '__main__':
    app.run(debug=True)