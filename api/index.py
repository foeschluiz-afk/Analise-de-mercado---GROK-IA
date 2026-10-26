import os
import json
import base64
from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.error

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 1. Leitura segura do corpo da requisição
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                body = json.loads(post_data.decode('utf-8'))
            else:
                body = {}

            tema = body.get('tema', 'Geral')

            # 2. Obter chave do Groq
            api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("XAI_API_KEY")
            
            if not api_key:
                self._send_json({
                    "error": "Chave GROQ_API_KEY não foi encontrada nas variáveis da Vercel."
                }, 500)
                return

            # 3. Prompt para inteligência de mercado
            system_prompt = (
                "Você é o 'GrokMarketIntel', um agente especialista em Inteligência de Mercado. "
                "Sua tarefa é analisar tendências digitais recentes sobre o assunto solicitado "
                "e entregar um relatório resumido e executivo em Português.\n"
                "Mantenha tom profissional, direto e sem piadas.\n\n"
                "Retorne a resposta estritamente no seguinte formato:\n"
                "🚀 RELATÓRIO DE TENDÊNCIA EM ALTA\n"
                "📌 Tema Principal: [Nome da peça, produto ou tópico em alta]\n"
                "📊 Aprovação do Público: [Ex: 88% de aprovação / Alta demanda]\n"
                "💡 Por que está em alta: [Explicação curta em 1 frase]\n"
                "🔑 Destaques: [2 a 3 palavras-chave ou hashtags]\n\n"
                "🖼️ PROMPT DA IMAGEM:\n"
                "[Descrição em inglês detalhada de uma imagem conceitual e realista para ilustrar a tendência]"
            )

            user_prompt = f"Analise as principais tendências de mercado mais recentes sobre: {tema}"

            # 4. Requisição ao Groq para o Relatório de Texto
            modelos = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.1-8b-instant"]
            resposta_ia = None

            for modelo in modelos:
                payload = {
                    "model": modelo,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3
                }

                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    "https://api.groq.com/openai/v1/chat/completions",
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}",
                        "User-Agent": "Mozilla/5.0"
                    },
                    method="POST"
                )

                try:
                    with urllib.request.urlopen(req) as response:
                        result = json.loads(response.read().decode('utf-8'))
                        resposta_ia = result['choices'][0]['message']['content']
                        break
                except Exception:
                    continue

            if not resposta_ia:
                self._send_json({"error": "Não foi possível conectar aos modelos do Groq."}, 500)
                return

            # 5. Extração do prompt para gerar a imagem
            prompt_imagem = tema
            if "PROMPT DA IMAGEM:" in resposta_ia:
                prompt_imagem = resposta_ia.split("PROMPT DA IMAGEM:")[1].strip()

            # 6. Geração de Imagem via Hugging Face Inference API (Modelo FLUX.1-schnell / Stable Diffusion)
            image_b64 = self.gerar_imagem_huggingface(prompt_imagem)

            # 7. Retorna o texto e a imagem em formato base64
            self._send_json({
                "resultado": resposta_ia,
                "imagem_b64": image_b64
            }, 200)

        except Exception as e:
            self._send_json({"error": f"Erro interno no servidor: {str(e)}"}, 500)

    def gerar_imagem_huggingface(self, prompt):
        try:
            # Modelo FLUX.1-schnell público e de alta velocidade no Hugging Face
            url_hf = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
            
            # Token de acesso Hugging Face (opcional, mas recomendado nas variáveis da Vercel: HF_TOKEN)
            hf_token = os.environ.get("HF_TOKEN", "")
            
            headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
            if hf_token:
                headers["Authorization"] = f"Bearer {hf_token}"

            data_hf = json.dumps({"inputs": prompt}).encode('utf-8')
            req_hf = urllib.request.Request(url_hf, data=data_hf, headers=headers, method="POST")

            with urllib.request.urlopen(req_hf, timeout=15) as resp:
                image_bytes = resp.read()
                return "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode('utf-8')
        except Exception:
            return None  # Se falhar ou expirar tempo, retorna None sem quebrar a resposta de texto

    def _send_json(self, data, status_code):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))