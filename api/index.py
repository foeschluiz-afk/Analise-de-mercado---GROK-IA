import os
import json
from http.server import BaseHTTPRequestHandler
import urllib.request

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length))
        tema = body.get('tema', 'Geral')

        api_key = os.environ.get("XAI_API_KEY")
        
        if not api_key:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Chave XAI_API_KEY não configurada na Vercel."}).encode('utf-8'))
            return

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

        payload = {
            "model": "grok-beta",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3
        }

        req = urllib.request.Request(
            "https://api.x.ai/v1/chat/completions",
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                resposta_grok = result['choices'][0]['message']['content']

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"resultado": resposta_grok}).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))