"""
Translation Service - SiliconFlow API
"""

import json
import urllib.request
import urllib.error
import ssl


class TranslatorService:
    """Translation service class"""
    
    def __init__(self):
        self.api_key = ""  # Configure in app settings
        self.api_url = "https://api.siliconflow.cn"
        self.model = "Qwen/Qwen2.5-7B-Instruct"
        self.target_lang = "Chinese"
        
        # SSL context - disable verification for Android compatibility
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def set_config(self, api_key="", api_url="", model="", target_lang=""):
        """Set configuration"""
        if api_key:
            self.api_key = api_key
        if api_url:
            self.api_url = api_url.rstrip('/')
        if model:
            self.model = model
        if target_lang:
            self.target_lang = target_lang
    
    def translate(self, text):
        """Translate text"""
        if not self.api_key:
            return "Error: Please configure API Key in settings"
        
        if not text or not text.strip():
            return "Error: No text to translate"
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(text)
        
        try:
            result = self._call_api(system_prompt, user_prompt)
            return result
        except Exception as e:
            return f"Translation failed: {str(e)}"
    
    def _build_system_prompt(self):
        """Build system prompt"""
        return f"""You are a professional academic translator. Translate the given text to {self.target_lang}.

Rules:
1. Accurate translation preserving academic terminology
2. Natural and fluent output
3. Keep professional terms, add original in brackets if needed
4. Maintain paragraph structure
5. Output translation only, no explanations"""
    
    def _build_user_prompt(self, text):
        """Build user prompt"""
        return f"Translate to {self.target_lang}:\n\n{text}"
    
    def _call_api(self, system_prompt, user_prompt):
        """Call SiliconFlow API"""
        endpoint = f"{self.api_url}/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
            "stream": False
        }
        
        data = json.dumps(payload).encode('utf-8')
        
        request = urllib.request.Request(
            endpoint,
            data=data,
            headers=headers,
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(request, context=self.ssl_context, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    return "API returned unexpected format"
                    
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ''
            try:
                error_json = json.loads(error_body)
                error_msg = error_json.get('error', {}).get('message', str(e))
            except:
                error_msg = error_body or str(e)
            raise Exception(f"HTTP {e.code}: {error_msg}")
            
        except urllib.error.URLError as e:
            raise Exception(f"Network error: {e.reason}")
            
        except Exception as e:
            raise Exception(f"Request error: {str(e)}")
