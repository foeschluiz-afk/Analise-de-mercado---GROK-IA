document.addEventListener('DOMContentLoaded', () => {
  const btnBuscar = document.getElementById('btnBuscar');
  const temaInput = document.getElementById('tema');

  if (btnBuscar) {
    btnBuscar.addEventListener('click', buscarTendencias);
  }

  if (temaInput) {
    temaInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        buscarTendencias();
      }
    });
  }
});

async function buscarTendencias() {
  const temaInput = document.getElementById('tema');
  const btn = document.getElementById('btnBuscar');
  const loading = document.getElementById('loading');
  const container = document.getElementById('resultadoContainer');
  const texto = document.getElementById('resultadoTexto');

  // Subtitui pela tua chave de API obtida no painel do Pollinations.ai
  const POLLINATIONS_API_KEY = "pk_nIA6GPFFA12xEXsr"; 

  const tema = temaInput.value.trim();
  if (!tema) {
    alert('Por favor, informe um tema ou nicho de mercado!');
    return;
  }

  // Ajuste do estado visual durante o carregamento
  btn.disabled = true;
  loading.classList.remove('hidden');
  container.classList.add('hidden');
  texto.innerHTML = '';

  try {
    // 1. Chamada ao backend Python Serverless na Vercel (/api)
    const response = await fetch('/api', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tema: tema })
    });

    const data = await response.json();

    if (data.error) {
      texto.innerHTML = `<div class="p-4 bg-red-900/40 border border-red-500 rounded-lg text-red-200">
        ⚠️ <strong>Erro ao processar:</strong> ${data.error}
      </div>`;
    } else {
      let relatorio = data.resultado;

      // 2. Extrair o trecho do PROMPT DA IMAGEM gerado pelo Groq
      let promptImagem = tema;
      if (relatorio.includes("PROMPT DA IMAGEM:")) {
        promptImagem = relatorio.split("PROMPT DA IMAGEM:")[1].trim();
      }

      // 3. Montar a URL da API do Pollinations autenticada com a tua conta
      const params = new URLSearchParams({
        width: "800",
        height: "450",
        seed: Math.floor(Math.random() * 100000).toString(),
        nologo: "true"
      });

      // Inclui a chave se ela tiver sido preenchida
      if (POLLINATIONS_API_KEY && POLLINATIONS_API_KEY !== "SUA_CHAVE_AQUI") {
        params.append("key", POLLINATIONS_API_KEY);
      }

      const urlImagem = `https://pollinations.ai/p/${encodeURIComponent(promptImagem)}?${params.toString()}`;

      // 4. Renderizar o texto e o elemento de imagem no HTML
      texto.innerHTML = `
        <div class="mb-6 whitespace-pre-line text-gray-200 leading-relaxed">${relatorio}</div>
        <div class="mt-6 border-t border-gray-700 pt-4">
          <h3 class="font-bold text-blue-400 mb-3 flex items-center gap-2">
            🎨 <span>Imagem Conceitual Gerada em Tempo Real:</span>
          </h3>
          <div class="relative overflow-hidden rounded-lg border border-gray-700 bg-gray-900 min-h-[250px] flex items-center justify-center">
            <img 
              src="${urlImagem}" 
              alt="Ilustração da tendência: ${tema}" 
              class="w-full h-auto object-cover rounded-lg shadow-md transition-opacity duration-300"
              loading="lazy"
            />
          </div>
        </div>
      `;
    }

    container.classList.remove('hidden');

  } catch (err) {
    alert('Erro de conexão ao tentar contactar o servidor.');
    console.error('Erro na requisição:', err);
  } finally {
    btn.disabled = false;
    loading.classList.add('hidden');
  }
}