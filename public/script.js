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

      // Gera um seed aleatório para o Picsum fornecer uma foto diferente a cada pesquisa
      const randomSeed = Math.floor(Math.random() * 1000);
      const urlPicsum = `https://picsum.photos/seed/${randomSeed}/800/450`;

      texto.innerHTML = `
        <div class="mb-6 whitespace-pre-line text-gray-200 leading-relaxed">${relatorio}</div>
        <div class="mt-6 border-t border-gray-700 pt-4">
          <h3 class="font-bold text-blue-400 mb-3 flex items-center gap-2">
            🖼️ <span>Conceito Visual de Mercado (Picsum HD):</span>
          </h3>
          <div class="relative overflow-hidden rounded-lg border border-gray-700 bg-gray-900 min-h-[250px] flex items-center justify-center">
            <img 
              src="${urlPicsum}" 
              alt="Imagem conceitual de mercado para: ${tema}" 
              class="w-full h-auto object-cover rounded-lg shadow-md"
              loading="lazy"
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