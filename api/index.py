
import os
import json
import re
import unicodedata
import urllib.request
import urllib.error

from http.server import BaseHTTPRequestHandler


# =========================================================
# MARKETINTEL AI — API COMPLETA PARA VERCEL
# =========================================================

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
)

# O primeiro modelo é configurável nas Environment Variables.
DEFAULT_MODEL = os.environ.get(
    "GEMINI_MODEL", "gemini-2.5-flash"
)

FALLBACK_MODELS = [
    DEFAULT_MODEL,
    "gemini-2.5-flash",
]

MAX_BODY_SIZE = 20_000
MAX_TEMA_SIZE = 500


SYSTEM_INSTRUCTION = """
Você é o MarketIntel AI, especialista em inteligência de mercado,
tendências digitais, comportamento do consumidor e oportunidades
comerciais.

OBJETIVO:
Analisar o tema solicitado utilizando pesquisa na web quando a
ferramenta de pesquisa estiver disponível. Priorize informações
recentes, fontes confiáveis e dados verificáveis.

REGRAS:
1. Responda em português brasileiro.
2. Seja profissional, direto e objetivo.
3. Diferencie fatos verificados de estimativas.
4. Nunca invente percentuais de aprovação, vendas, pesquisas,
   fontes, URLs ou estatísticas.
5. Se não encontrar dados quantitativos confiáveis, escreva
   "Não há dados suficientes para quantificar".
6. Identifique o período das informações quando disponível.
7. Inclua fontes e links reais consultados, quando disponíveis.
8. Se não conseguir verificar a atualidade, informe essa limitação.
9. Não apresente uma tendência como comprovada sem evidências.
10. A imagem solicitada é ilustrativa, não uma fotografia
    necessariamente correspondente ao produto analisado.

FORMATO OBRIGATÓRIO DO RELATÓRIO:

🚀 RELATÓRIO DE TENDÊNCIA EM ALTA

📌 Tema Principal:
[Produto, serviço, comportamento ou tópico analisado]

📈 Situação da Tendência:
[Em alta, emergente, estável, em queda ou evidências insuficientes]

📊 Aprovação do Público:
[Percentual apenas se houver fonte verificável; caso contrário,
descreva qualitativamente ou informe que faltam dados]

💡 Por que está em alta:
[Explicação objetiva baseada nas evidências encontradas]

🎯 Público-Alvo:
[Perfil provável do consumidor]

💰 Oportunidade de Mercado:
[Possíveis oportunidades comerciais, sem prometer resultados]

🔑 Destaques:
[Palavras-chave e hashtags relevantes]

⚠️ Nível de Confiança:
[Alto, moderado ou baixo, com justificativa breve]

🔗 Fontes:
[URLs reais consultadas, com o nome das fontes e datas quando
disponíveis. Não invente links.]

🖼️ LINK_IMAGEM:
[URL de imagem ilustrativa relacionada ao tema]
"""


def limpar_texto(valor):
    """Normaliza texto recebido e remove caracteres de controle."""
    if not isinstance(valor, str):
        return ""

    return "".join(
        caractere
        for caractere in valor.strip()
        if caractere in "\n\t" or ord(caractere) >= 32
    )


def criar_link_imagem(tema):
    """
    Cria um endereço de imagem ilustrativa estável.
    A imagem não representa necessariamente o produto real.
    """
    texto = unicodedata.normalize("NFKD", tema)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    palavra = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-")
    palavra = (palavra or "market-trend")[:70].lower()

    return (
        "https://picsum.photos/seed/"
        + palavra
        + "/800/450"
    )


def extrair_resposta(resultado):
    """Extrai o texto gerado e detecta respostas vazias."""
    candidatos = resultado.get("candidates", [])

    if not candidatos:
        feedback = resultado.get("promptFeedback", {})
        motivo = feedback.get("blockReason", "Resposta vazia")
        raise ValueError(f"O Gemini não retornou conteúdo: {motivo}")

    partes = candidatos[0].get("content", {}).get("parts", [])

    textos = [
        parte["text"]
        for parte in partes
        if isinstance(parte.get("text"), str)
    ]

    resposta = "\n".join(textos).strip()

    if not resposta:
        raise ValueError("O Gemini retornou uma resposta sem texto.")

    return resposta


def consultar_gemini(api_key, tema):
    """Consulta o Gemini com pesquisa na web e modelos alternativos."""

    modelos = list(dict.fromkeys(FALLBACK_MODELS))
    ultimo_erro = "Nenhum modelo disponível."

    prompt_usuario = (
        f"Analise as tendências de mercado relacionadas a: {tema}\n\n"
        "Pesquise informações recentes usando a ferramenta de pesquisa "
        "na web, se disponível para o modelo. Priorize dados verificáveis, "
        "fontes confiáveis e oportunidades comerciais relevantes. "
        "Não invente métricas ou fontes. Gere o relatório no formato "
        "definido nas instruções do sistema."
    )

    for modelo in modelos:
        url = GEMINI_API_URL + modelo + ":generateContent"

        payload = {
            "systemInstruction": {
                "parts": [
                    {"text": SYSTEM_INSTRUCTION}
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt_usuario}
                    ]
                }
            ],
            "tools": [
                {
                    "google_search": {}
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1800
            }
        }

        request_data = json.dumps(
            payload, ensure_ascii=False
        ).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=50) as response:
                resultado = json.loads(
                    response.read().decode("utf-8")
                )

            texto = extrair_resposta(resultado)

            return {
                "resultado": texto,
                "tema": tema,
                "modelo": modelo,
                "imagem": criar_link_imagem(tema),
                "status": "sucesso",
            }

        except urllib.error.HTTPError as erro:
            detalhes = erro.read().decode(
                "utf-8", errors="replace"
            )

            ultimo_erro = detalhes[:1500]

            # Falhas de autenticação e limites de uso não devem
            # ser ocultados por tentativas repetidas com outros modelos.
            if erro.code in (400, 401, 403, 429):
                if erro.code in (401, 403):
                    break

                if erro.code == 429:
                    break

                # Erros 400 podem indicar ferramenta incompatível
                # ou parâmetros inválidos. Tenta o próximo modelo.
                continue

            # Modelo inexistente, erro temporário ou indisponibilidade.
            continue

        except (urllib.error.URLError, TimeoutError) as erro:
            ultimo_erro = str(erro)
            continue

        except (ValueError, KeyError, TypeError) as erro:
            ultimo_erro = str(erro)
            continue

        except Exception as erro:
            ultimo_erro = str(erro)
            continue

    raise RuntimeError(
        "Não foi possível gerar o relatório. "
        "Verifique a chave, os modelos disponíveis, as permissões "
        "da API e os limites de utilização. Detalhes: "
        + ultimo_erro[:1000]
    )


class handler(BaseHTTPRequestHandler):

    def _send_json(self, data, status_code=200):
        resposta = json.dumps(
            data, ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status_code)
        self.send_header(
            "Content-Type", "application/json; charset=utf-8"
        )
        self.send_header("Content-Length", str(len(resposta)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods", "POST, OPTIONS, GET"
        )
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization"
        )
        self.end_headers()

        self.wfile.write(resposta)

    def do_OPTIONS(self):
        self._send_json({"status": "ok"}, 200)

    def do_GET(self):
        self._send_json({
            "nome": "MarketIntel AI",
            "status": "online",
            "endpoint": "/api",
            "metodo_analise": "POST",
            "campo_obrigatorio": "tema",
        })

    def do_POST(self):
        try:
            # 1. Verifica o tamanho da requisição.
            tamanho = self.headers.get("Content-Length")

            if tamanho is None:
                self._send_json(
                    {"error": "Content-Length é obrigatório."},
                    411
                )
                return

            try:
                tamanho = int(tamanho)
            except (TypeError, ValueError):
                self._send_json(
                    {"error": "Content-Length inválido."}, 400
                )
                return

            if tamanho <= 0:
                self._send_json(
                    {"error": "Envie um JSON com o campo tema."},
                    400
                )
                return

            if tamanho > MAX_BODY_SIZE:
                self._send_json(
                    {"error": "Requisição muito grande."}, 413
                )
                return

            # 2. Lê e valida o JSON.
            dados = self.rfile.read(tamanho)

            try:
                body = json.loads(dados.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_json(
                    {"error": "O corpo precisa ser um JSON válido."},
                    400
                )
                return

            if not isinstance(body, dict):
                self._send_json(
                    {"error": "O JSON precisa ser um objeto."},
                    400
                )
                return

            tema = limpar_texto(body.get("tema", "Geral"))

            if not tema:
                self._send_json(
                    {"error": "Informe um tema para analisar."},
                    400
                )
                return

            if len(tema) > MAX_TEMA_SIZE:
                self._send_json(
                    {
                        "error": (
                            f"O tema deve ter no máximo "
                            f"{MAX_TEMA_SIZE} caracteres."
                        )
                    },
                    400
                )
                return

            # 3. Obtém a chave secreta.
            api_key = os.environ.get("GEMINI_API_KEY")

            if not api_key:
                self._send_json(
                    {
                        "error": (
                            "GEMINI_API_KEY não configurada. "
                            "Adicione a variável nas configurações "
                            "do projeto na Vercel."
                        )
                    },
                    500
                )
                return

            # 4. Gera o relatório.
            resultado = consultar_gemini(api_key, tema)

            self._send_json(resultado, 200)

        except RuntimeError as erro:
            self._send_json(
                {"error": str(erro)}, 502
            )

        except Exception:
            # Não expõe detalhes internos ou segredos ao cliente.
            self._send_json(
                {"error": "Erro interno ao processar a solicitação."},
                500
            )

    def log_message(self, format, *args):
        # Evita registrar informações desnecessárias no log.
        super().log_message(format, *args)
