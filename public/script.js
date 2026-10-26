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

  btn.disabled = true;
  loading.classList.remove('hidden');
  container.classList.add('hidden');
  texto.innerHTML = '';

  try {
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
      
      // Se o Hugging Face gerou a imagem, usa o Base64, senão usa um fallback público
      let srcImagem = data.imagem_b64;
      if (!srcImagem) {
        srcImagem = `https://picsum.photos/800/450?random=${Math.floor(Math.random() * 1000)}`;
      }

      texto.innerHTML = `
        <div class="mb-6 whitespace-pre-line text-gray-200 leading-relaxed">${relatorio}</div>
        <div class="mt-6 border-t border-gray-700 pt-4">
          <h3 class="font-bold text-blue-400 mb-3 flex items-center gap-2">
            🎨 <span>Imagem Conceitual Gerada em Tempo Real (Hugging Face):</span>
          </h3>
          <div class="relative overflow-hidden rounded-lg border border-gray-700 bg-gray-900 min-h-[250px] flex items-center justify-center">
            <img 
              src="${srcImagem}" 
              alt="Ilustração da tendência: ${tema}" 
              class="w-full h-auto object-cover rounded-lg shadow-md"
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
  }
}