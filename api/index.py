import os
import json
import re
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

            # 2. Obter a chave de API do Gemini
            api_key = os.environ.get("GEMINI_API_KEY")
            
            if not api_key:
                self._send_json({
                    "error": "A variável GEMINI_API_KEY não foi configurada no painel da Vercel."
                }, 500)
                return

            # 3. Instrução de sistema para o Gemini
            system_instruction = (
                "Você é o 'MarketIntel AI', um agente especialista em Inteligência de Mercado. "
                "Sua tarefa é analisar tendências digitais recentes sobre o assunto solicitado "
                "e entregar um relatório resumido e executivo em Português.\n"
                "Mantenha um tom profissional, direto e objetivo.\n\n"
                "Retorne a resposta estritamente no seguinte formato:\n"
                "🚀 RELATÓRIO DE TENDÊNCIA EM ALTA\n"
                "📌 Tema Principal: [Nome da peça, produto ou tópico em alta]\n"
                "📊 Aprovação do Público: [Ex: 88% de aprovação / Alta demanda]\n"
                "💡 Por que está em alta: [Explicação curta em 1 frase]\n"
                "🔑 Destaques: [2 a 3 palavras-chave ou hashtags]\n\n"
                "🔗 LINK_IMAGEM: [https://picsum.photos/seed/](https://picsum.photos/seed/)[palavra_chave_em_ingles_sem_espaço]/800/450"
            )

            user_prompt = f"Analise as principais tendências de mercado mais recentes sobre: {tema}"

            # 4. Lista de identificadores de modelos da API v1beta do Gemini
            modelos = ["gemini-2.5-flash", "gemini-1.5-flash"]
            resposta_ia = None
            ultimo_erro = ""

            for modelo in modelos:
                url = f"[https://generativelanguage.googleapis.com/v1beta/models/](https://generativelanguage.googleapis.com/v1beta/models/){modelo}:generateContent?key={api_key}"
                
                payload = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": f"{system_instruction}\n\nSolicitação do usuário: {user_prompt}"}]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.3
                    }
                }

                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )

                try:
                    with urllib.request.urlopen(req) as response:
                        result = json.loads(response.read().decode('utf-8'))
                        resposta_ia = result['candidates'][0]['content']['parts'][0]['text']
                        break
                except urllib.error.HTTPError as e:
                    ultimo_erro = e.read().decode('utf-8')
                    continue

            if resposta_ia:
                self._send_json({"resultado": resposta_ia}, 200)
            else:
                self._send_json({"error": f"Erro na API do Gemini: {ultimo_erro}"}, 500)

        except Exception as e:
            self._send_json({"error": f"Erro interno no servidor: {str(e)}"}, 500)

    def _send_json(self, data, status_code):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))