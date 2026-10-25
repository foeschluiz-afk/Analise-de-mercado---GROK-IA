document.addEventListener('DOMContentLoaded', () => {
  const btnBuscar = document.getElementById('btnBuscar');
  const temaInput = document.getElementById('tema');

  // Disparar busca ao clicar no botão
  btnBuscar.addEventListener('click', buscarTendencias);

  // Disparar busca ao pressionar 'Enter' no input
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

  // Estado de Carregamento (UI)
  btn.disabled = true;
  loading.classList.remove('hidden');
  container.classList.add('hidden');
  texto.innerText = '';

  try {
    // Requisição enviada para a Serverless Function em Python no Vercel
    const response = await fetch('/api', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tema: tema })
    });

    const data = await response.json();

    if (data.error) {
      texto.innerText = '⚠️ Erro ao processar: ' + data.error;
    } else {
      texto.innerText = data.resultado;
    }
    
    container.classList.remove('hidden');

  } catch (err) {
    alert('Erro de conexão ao tentar contactar o servidor.');
    console.error(err);
  } finally {
    // Restaurar estado da UI
    btn.disabled = false;
    loading.classList.add('hidden');
  }
}