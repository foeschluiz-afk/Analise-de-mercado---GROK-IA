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

            # 2. Verificar a chave de API nas variáveis de ambiente
            api_key = os.environ.get("XAI_API_KEY")
            if not api_key:
                self._send_json({"error": "Chave XAI_API_KEY não foi encontrada nas variáveis de ambiente da Vercel."}, 500)
                return

            # 3. Construção dos Prompts
            system_prompt = (
                "Você é o 'GrokMarketIntel', um agente de Inteligência de Mercado. "
                "Sua tarefa é analisar tendências em tempo real e entregar um relatório resumido e executivo em Português.\n"
                "Mantenha tom profissional, direto e sem piadas. Desconsidere spam e ironia.\n\n"
                "Retorne a resposta estritamente no seguinte formato:\n"
                "🚀 RELATÓRIO DE TENDÊNCIA EM ALTA\n"
                "📌 Tema Principal: [Nome da peça, produto ou tópico em alta]\n"
                "📊 Aprovação do Público: [Ex: 88% de aprovação / Alta demanda]\n"
                "💡 Por que está em alta: [Explicação curta em 1 frase]\n"
                "🔑 Destaques: [2 a 3 palavras-chave]\n\n"
                "🖼️ PROMPT DA IMAGEM:\n"
                "[Descrição detalhada em português de uma imagem conceitual para ilustrar a tendência]"
            )

            user_prompt = f"Analise as principais tendências recentes em tempo real sobre: {tema}"

            # 4. Requisição para a API do Grok (xAI)
            payload = {
                "model": "grok-beta",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3
            }

            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                "https://api.x.ai/v1/chat/completions",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                method="POST"
            )

            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                resposta_grok = result['choices'][0]['message']['content']
                self._send_json({"resultado": resposta_grok}, 200)

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            self._send_json({"error": f"Erro na API da xAI ({e.code}): {error_body}"}, 500)
        except Exception as e:
            self._send_json({"error": f"Erro interno do servidor: {str(e)}"}, 500)

    def _send_json(self, data, status_code):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))