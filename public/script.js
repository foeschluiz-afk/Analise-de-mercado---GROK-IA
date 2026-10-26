document.addEventListener('DOMContentLoaded', () => {
  const btnBuscar = document.getElementById('btnBuscar');
  const temaInput = document.getElementById('tema');

  if (btnBuscar) btnBuscar.addEventListener('click', buscarTendencias);
  if (temaInput) {
    temaInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') buscarTendencias();
    });
  }
});

async function buscarTendencias() {
  const temaInput = document.getElementById('tema');
  const btn = document.getElementById('btnBuscar');
  const loading = document.getElementById('loading');
  const container = document.getElementById('resultadoContainer');
  const texto = document.getElementById('resultadoTexto');

  const tema = temaInput.value.trim();
  if (!tema) {
    alert('Por favor, informe um tema ou nicho de mercado!');
    return;
  }

  // Desativa o botão e exibe o estado de loading
  btn.disabled = true;
  loading.classList.remove('hidden');
  loading.classList.add('flex');
  container.classList.add('hidden');
  texto.innerHTML = '';

  try {
    // Requisição ao Backend Serverless da Vercel
    const response = await fetch('/api', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tema: tema })
    });

    const data = await response.json();

    if (data.error) {
      texto.innerHTML = `
        <div class="p-4 bg-red-900/40 border border-red-500 rounded-xl text-red-200">
          ⚠️ <strong>Erro ao processar:</strong> ${data.error}
        </div>`;
    } else {
      let relatorio = data.resultado;

      // 1. Extrair a descrição de imagem do relatório
      let promptImagem = tema;
      if (relatorio.includes("PROMPT DA IMAGEM:")) {
        promptImagem = relatorio.split("PROMPT DA IMAGEM:")[1].trim();
      }

      // 2. Montar a URL da imagem no Pollinations.ai
      const randomSeed = Math.floor(Math.random() * 99999);
      const urlPollinations = `https://image.pollinations.ai/prompt/${encodeURIComponent(promptImagem)}?width=800&height=450&seed=${randomSeed}&nologo=true`;

      // 3. Renderizar relatório e elemento visual no DOM
      texto.innerHTML = `
        <div class="mb-6 whitespace-pre-line text-gray-200 leading-relaxed text-base">${relatorio}</div>
        <div class="mt-8 border-t border-gray-700/80 pt-6">
          <h3 class="font-bold text-blue-400 mb-3 flex items-center gap-2 text-lg">
            🎨 <span>Conceito Visual Gerado em Tempo Real (Pollinations):</span>
          </h3>
          <div class="relative overflow-hidden rounded-xl border border-gray-700 bg-gray-900 min-h-[250px] flex items-center justify-center">
            <img 
              src="${urlPollinations}" 
              alt="Ilustração da tendência: ${tema}" 
              class="w-full h-auto object-cover rounded-xl shadow-lg transition-opacity duration-300"
              loading="lazy"
              onerror="this.src='https://picsum.photos/800/450'"
            />
          </div>
        </div>
      `;
    }

    container.classList.remove('hidden');

  } catch (err) {
    alert('Erro de conexão ao tentar contactar o servidor.');
    console.error(err);
  } finally {
    btn.disabled = false;
    loading.classList.add('hidden');
    loading.classList.remove('flex');
  }
}