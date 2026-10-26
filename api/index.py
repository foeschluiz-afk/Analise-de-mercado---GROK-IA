import os
import json
from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.error

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 1. Ler o corpo da requisição de forma segura
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                body = json.loads(post_data.decode('utf-8'))
            else:
                body = {}

            tema = body.get('tema', 'Geral')

            # 2. Obter a chave de API do Groq das variáveis de ambiente
            api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("XAI_API_KEY")
            
            if not api_key:
                self._send_json({
                    "error": "Chave de API (GROQ_API_KEY ou XAI_API_KEY) não foi encontrada nas variáveis de ambiente da Vercel."
                }, 500)
                return

            # 3. Prompt C.A.R.O. estruturado para Inteligência de Mercado
            system_prompt = (
                "Você é o 'GrokMarketIntel', um agente especialista em Inteligência de Mercado. "
                "Sua tarefa é analisar tendências digitais recentes sobre o assunto solicitado "
                "e entregar um relatório resumido e executivo em Português.\n"
                "Mantenha tom profissional, direto e sem piadas. Desconsidere spam, memes isolados e ironias.\n\n"
                "Retorne a resposta estritamente no seguinte formato:\n"
                "🚀 RELATÓRIO DE TENDÊNCIA EM ALTA\n"
                "📌 Tema Principal: [Nome da peça, produto ou tópico em alta]\n"
                "📊 Aprovação do Público: [Ex: 88% de aprovação / Alta demanda]\n"
                "💡 Por que está em alta: [Explicação curta em 1 frase]\n"
                "🔑 Destaques: [2 a 3 palavras-chave ou hashtags]\n\n"
                "🖼️ PROMPT DA IMAGEM:\n"
                "[Descrição detalhada em português de uma imagem conceitual e realista para ilustrar a tendência]"
            )

            user_prompt = f"Analise as principais tendências de mercado mais recentes sobre: {tema}"

            # 4. Requisição para a API do Groq Cloud com User-Agent para ignorar o bloqueio 1010
            payload = {
                "model": "llama-3.3-70b-versatile",
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
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
                method="POST"
            )

            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                resposta_ia = result['choices'][0]['message']['content']
                self._send_json({"resultado": resposta_ia}, 200)

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            self._send_json({"error": f"Erro na API do Groq ({e.code}): {error_body}"}, 500)
        except Exception as e:
            self._send_json({"error": f"Erro interno no servidor: {str(e)}"}, 500)

    def _send_json(self, data, status_code):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))