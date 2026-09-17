// Instagram Non-Followers Finder - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const loginSection = document.getElementById('loginSection');
    const loadingSection = document.getElementById('loadingSection');
    const resultsSection = document.getElementById('resultsSection');
    const loadingStatus = document.getElementById('loadingStatus');
    const usersList = document.getElementById('usersList');
    const exportBtn = document.getElementById('exportBtn');
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');

    let currentUsername = '';

    // Manejar formulario de login
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const analyzeBtn = document.getElementById('analyzeBtn');

        currentUsername = username;

        // Mostrar loading
        loginSection.classList.add('hidden');
        loadingSection.classList.remove('hidden');

        // Deshabilitar botón
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analizando...';

        // Simular progreso
        updateLoadingStatus('Iniciando sesión...');
        await sleep(1500);

        updateLoadingStatus('Obteniendo lista de seguidores...');
        await sleep(2000);

        updateLoadingStatus('Obteniendo lista de seguidos...');
        await sleep(2000);

        updateLoadingStatus('Analizando no seguidores...');
        await sleep(1500);

        // Llamar a la API
        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (data.success) {
                displayResults(data.data);
                loadingSection.classList.add('hidden');
                resultsSection.classList.remove('hidden');
            } else {
                alert('Error: ' + data.message);
                resetToLogin();
            }
        } catch (error) {
            alert('Error de conexión: ' + error.message);
            resetToLogin();
        }
    });

    // Exportar resultados
    exportBtn.addEventListener('click', async function() {
        try {
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username: currentUsername })
            });

            const data = await response.json();

            if (data.success) {
                const blob = new Blob([JSON.stringify(data.data, null, 2)], {
                    type: 'application/json'
                });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `non_followers_${currentUsername}.json`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }
        } catch (error) {
            alert('Error al exportar: ' + error.message);
        }
    });

    // Nuevo análisis
    newAnalysisBtn.addEventListener('click', function() {
        resultsSection.classList.add('hidden');
        loginSection.classList.remove('hidden');
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
    });

    // Funciones auxiliares
    function updateLoadingStatus(message) {
        loadingStatus.textContent = message;
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function resetToLogin() {
        loadingSection.classList.add('hidden');
        loginSection.classList.remove('hidden');
        const analyzeBtn = document.getElementById('analyzeBtn');
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-search"></i> Analizar Cuenta';
    }

    function displayResults(data) {
        // Actualizar contadores
        document.getElementById('followersCount').textContent = data.followers_count.toLocaleString();
        document.getElementById('followingCount').textContent = data.following_count.toLocaleString();
        document.getElementById('nonFollowersCount').textContent = data.non_followers_count.toLocaleString();

        // Mostrar lista de no seguidores
        usersList.innerHTML = '';

        if (data.non_followers.length === 0) {
            usersList.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 40px;">¡Excelente! Todos tus seguidos te siguen de vuelta 🎉</p>';
            return;
        }

        data.non_followers.forEach(user => {
            const userCard = createUserCard(user);
            usersList.appendChild(userCard);
        });

        // Si hay más de 50, mostrar mensaje
        if (data.non_followers_count > 50) {
            const moreMessage = document.createElement('div');
            moreMessage.style.cssText = 'text-align: center; padding: 20px; color: var(--text-secondary);';
            moreMessage.innerHTML = `<p>Mostrando 50 de ${data.non_followers_count} no seguidores. Exporta el JSON para ver la lista completa.</p>`;
            usersList.appendChild(moreMessage);
        }
    }

    function createUserCard(user) {
        const card = document.createElement('div');
        card.className = 'user-card';

        const initial = user.username.charAt(0).toUpperCase();

        card.innerHTML = `
            <div class="user-info">
                <div class="user-avatar">${initial}</div>
                <div class="user-details">
                    <h4>@${user.username}</h4>
                    <p>${user.full_name || 'Sin nombre'}</p>
                </div>
            </div>
            <button class="btn-unfollow" onclick="window.open('https://instagram.com/${user.username}', '_blank')">
                <i class="fas fa-external-link-alt"></i> Ver Perfil
            </button>
        `;

        return card;
    }
});