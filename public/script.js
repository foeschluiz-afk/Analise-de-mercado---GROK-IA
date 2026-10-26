document.addEventListener('DOMContentLoaded', () => {
  const btnBuscar = document.getElementById('btnBuscar');
  const temaInput = document.getElementById('tema');

  btnBuscar.addEventListener('click', buscarTendencias);

  temaInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      buscarTendencias();
    }
  });
});

async function buscarTendencias() {
  const temaInput = document.getElementById('tema');
  const btn = document.getElementById('btnBuscar');
  const loading = document.getElementById('loading');
  const container = document.getElementById('resultadoContainer');
  const texto = document.getElementById('resultadoTexto');

  const tema = temaInput.value.trim();
  if (!tema) {
    alert('Por favor, informe um tema!');
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
      texto.innerText = '⚠️ Erro ao processar: ' + data.error;
    } else {
      // 1. Exibir o texto do relatório
      let relatorio = data.resultado;
      
      // 2. Extrair o prompt da imagem do relatório para gerar a foto
      let promptImagem = tema; 
      if (relatorio.includes("PROMPT DA IMAGEM:")) {
        promptImagem = relatorio.split("PROMPT DA IMAGEM:")[1].trim();
      }

      // 3. Criar a URL da imagem via Pollinations.ai (Gratuito e sem API Key)
      const urlImagem = `https://pollinations.ai/p/${encodeURIComponent(promptImagem)}?width=800&height=450&seed=${Math.floor(Math.random() * 1000)}&nologo=true`;

      // 4. Inserir o relatório e a imagem gerada no HTML
      texto.innerHTML = `
        <div class="mb-4 whitespace-pre-line">${relatorio}</div>
        <div class="mt-6 border-t border-gray-700 pt-4">
          <h3 class="font-bold text-blue-400 mb-2">🎨 Imagem Gerada em Tempo Real:</h3>
          <img src="${urlImagem}" alt="Ilustração da tendência" class="w-full rounded-lg shadow-md border border-gray-700 loading-bg min-h-[250px] object-cover">
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