from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import logging
import json
import traceback

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Gemini API configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'

def generate_gemini_response(prompt):
    """Generate a response from Gemini API with improved error handling."""
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'contents': [{'parts': [{'text': prompt}]}]
    }
    try:
        response = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        app.logger.debug(f"Gemini API raw response: {response_json}")

        # 检查不同的可能的响应结构
        if 'candidates' in response_json and response_json['candidates']:
            candidate = response_json['candidates'][0]
            if 'content' in candidate:
                return candidate['content']['parts'][0]['text']
            elif 'parts' in candidate:
                return candidate['parts'][0]['text']
        
        # 如果无法找到预期的结构，记录错误并返回一个默认响应
        app.logger.error(f"Unexpected response structure from Gemini API: {response_json}")
        return "I'm sorry, I couldn't generate a proper response at this time."

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error calling Gemini API: {e}")
        return "I'm sorry, there was an error communicating with the AI service."
    except KeyError as e:
        app.logger.error(f"KeyError in Gemini API response: {e}")
        app.logger.error(f"Response JSON: {response_json}")
        return "I'm sorry, the AI service returned an unexpected response format."
    except Exception as e:
        app.logger.error(f"Unexpected error in generate_gemini_response: {e}")
        app.logger.error(traceback.format_exc())
        return "I'm sorry, an unexpected error occurred while generating the response."

def parse_characters(response):
    """Parse the character data from Gemini API response."""
    # Remove possible markdown syntax
    # response = response.strip('`')
    # if response.startswith('json\n'):
    #     response = response[5:]  # Remove 'json\n'

    try:
        characters = json.loads(response)
        if isinstance(characters, list) and all(isinstance(char, dict) for char in characters):
            return characters
    except json.JSONDecodeError as e:
        app.logger.error(f"Failed to parse JSON: {e}")
        app.logger.error(f"Response: {response}")

    """If JSON parsing fails, try manual parsing"""
    # characters = []
    # current_char = {}
    # lines = response.split('\n')
    # for line in lines:
    #     line = line.strip()
    #     if line.startswith('{'):
    #         current_char = {}
    #     elif line.endswith('}'):
    #         if current_char:
    #             characters.append(current_char)
    #             current_char = {}
    #     else:
    #         parts = line.split(':')
    #         if len(parts) == 2:
    #             key = parts[0].strip().strip('"')
    #             value = parts[1].strip().strip(',').strip('"')
    #             current_char[key] = value

    return characters if characters else None

@app.route('/generate-story', methods=['POST', 'OPTIONS'])
def generate_story():
    """Generate story based on user input."""
    if request.method == 'OPTIONS':
        return '', 204
    
    app.logger.info("Received request to generate story")
    
    try:
        data = request.json
        app.logger.debug(f"Received data: {data}")

        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_name = data.get('userName')
        anxiety_source = data.get('anxietySource')
        
        if not user_name or not anxiety_source:
            return jsonify({'error': 'Missing userName or anxietySource'}), 400
        
        prompt = f"""
        你是一位trpg game designer, 請根據以下訊息以繁體中文(Traditional Mandarin) 生成一個能感動我的trpg 故事：
        使用者名稱: {user_name}
        焦慮來源: {anxiety_source}
        並以一段話呈現
        """
        
        response = generate_gemini_response(prompt)
        app.logger.debug(f"Gemini API response: {response}")

        return jsonify({'story': response})
    except Exception as e:
        app.logger.error(f"Unexpected error in generate_characters: {e}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/generate-characters', methods=['POST', 'OPTIONS'])
def generate_characters():
    """Generate characters based on user input."""
    if request.method == 'OPTIONS':
        return '', 204
    
    app.logger.info("Received request to generate characters")
    
    try:
        data = request.json
        app.logger.debug(f"Received data: {data}")

        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_name = data.get('userName')
        anxiety_source = data.get('anxietySource')
        story = data.get('story')
        if not user_name or not anxiety_source:
            return jsonify({'error': 'Missing userName or anxietySource'}), 400
        
        prompt = f"""
        你是一位trpg game designer, 請根據以下訊息以繁體中文(Traditional Mandarin) 生成6位故事中的角色:
        使用者名稱: {user_name}
        焦慮來源: {anxiety_source}
        故事: {story}
        每位角色皆應包含:名字、描述、如何幫助解決焦慮
        請確保以JSON格式返回結果不是Markdown，格式如下:
        [
            {{"name": "角色名字", "description": "角色描述", "help": "角色如何幫助解決焦慮"}},
            {{"name": "角色名字", "description": "角色描述", "help": "角色如何幫助解決焦慮"}},
            {{"name": "角色名字", "description": "角色描述", "help": "角色如何幫助解決焦慮"}},
            {{"name": "角色名字", "description": "角色描述", "help": "角色如何幫助解決焦慮"}},
            {{"name": "角色名字", "description": "角色描述", "help": "角色如何幫助解決焦慮"}},
            {{"name": "角色名字", "description": "角色描述", "help": "角色如何幫助解決焦慮"}}
        ]
        """
        
        response = generate_gemini_response(prompt)
        app.logger.debug(f"Gemini API response: {response}")
        
        characters = parse_characters(response)
        if characters:
            app.logger.info(f"Generated characters: {characters}")
            return jsonify(characters)
        else:
            app.logger.warning("Failed to parse characters, using default")
            default_characters = [
                {"name": "內心的批評者", "description": "代表你內心的自我懷疑", "help": "挑戰消極想法"},
                {"name": "冷靜的智者", "description": "一位年長的智者，擁有豐富的人生經驗。", "help": "提供理性的建議和長遠的視角。"},
                {"name": "活力四射的朋友", "description": "一個充滿正能量的年輕人。", "help": "通過積極的態度和有趣的活動分散注意力。"},
                {"name": "同理心強的諮詢師", "description": "專業的心理諮詢師。", "help": "提供專業的心理支持和具體的應對策略。"},
                {"name": "勇敢的冒險家", "description": "一位無所畏懼的冒險家，鼓勵你面對恐懼。", "help": "通過設定挑戰來幫助你建立自信和韌性。"},
                {"name": "樂觀的激勵者", "description": "一位帶來希望和積極心態的激勵者。", "help": "通過分享正面經歷和鼓勵正向思維來幫助你保持積極心態。"}
            ]
            return jsonify(default_characters)
    
    except Exception as e:
        app.logger.error(f"Unexpected error in generate_characters: {e}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/generate-interaction', methods=['POST', 'OPTIONS'])
def generate_interaction():
    if request.method == 'OPTIONS':
        return '', 204
    
    app.logger.info("Received request to generate interaction")
    
    try:
        data = request.json
        app.logger.debug(f"Received data: {data}")

        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_name = data.get('userName')
        anxiety_source = data.get('anxietySource')
        character = data.get('character')
        user_thought = data.get('userThought')
        progress = data.get('progress')
        
        if not all([user_name, anxiety_source, character, user_thought, progress is not None]):
            return jsonify({'error': 'Missing required data'}), 400
        
        prompt = f"""
        請根據以下訊息以繁體中文(Traditional Mandarin)生成生成這位角色的回應並以一句話呈現:
        格式為："角色名稱"："回應"
        使用者名稱: {user_name}
        焦虑来源: {anxiety_source}
        选择的角色: {character['name']}
        角色能如何帮助: {character['help']}
        使用者的想法: {user_thought}
        当前进度: {progress}%
        """
        
        response = generate_gemini_response(prompt)
        app.logger.debug(f"Generated interaction: {response}")
        
        # 添加更多的日志来检查生成的交互内容
        # interaction_lines = response.split('\n')
        # app.logger.info(f"Number of interaction lines: {len(interaction_lines)}")
        # app.logger.info(f"First few lines of interaction: {interaction_lines[:3]}")
        
        return jsonify({'interaction': response})
    
    except Exception as e:
        app.logger.error(f"Unexpected error in generate_interaction: {e}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)