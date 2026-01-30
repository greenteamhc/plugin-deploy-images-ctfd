// Challenge Deployer JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Load challenges on page load
    loadChallenges();
    
    // Setup form submission
    const form = document.getElementById('deploy-form');
    form.addEventListener('submit', handleDeploy);
});

async function handleDeploy(e) {
    e.preventDefault();
    
    const btn = document.getElementById('deploy-btn');
    const originalText = btn.innerHTML;
    
    // Disable button and show loading
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deployando...';
    
    // Hide previous output
    document.getElementById('deploy-output').style.display = 'none';
    
    // Get form data
    const data = {
        challenge_name: document.getElementById('challenge_name').value.trim(),
        docker_image: document.getElementById('docker_image').value.trim(),
        internal_port: document.getElementById('internal_port').value,
        protocol: document.getElementById('protocol').value,
        hostname: document.getElementById('hostname').value.trim(),
        registry: document.getElementById('registry').value.trim()
    };
    
    try {
        const response = await fetch('/admin/challenge-deployer/api/deploy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'CSRF-Token': window.init.csrfNonce || ''
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        // Show output section
        document.getElementById('deploy-output').style.display = 'block';
        
        const messageDiv = document.getElementById('deploy-message');
        const registryUrlDiv = document.getElementById('deploy-registry-url');
        const buildOutputContainer = document.getElementById('build-output-container');
        const buildOutputPre = document.getElementById('build-output');
        
        if (result.success) {
            // Success
            messageDiv.className = 'alert alert-success';
            messageDiv.innerHTML = '<i class="fas fa-check-circle"></i> ' + result.message;
            
            // Show registry URL
            registryUrlDiv.style.display = 'block';
            document.getElementById('registry-url-output').value = result.registry_url;
            
            // Show build output if available
            if (result.output) {
                buildOutputContainer.style.display = 'block';
                buildOutputPre.textContent = result.output;
            }
            
            // Clear form
            document.getElementById('deploy-form').reset();
            
            // Reload challenges list
            setTimeout(() => loadChallenges(), 1000);
            
        } else {
            // Error
            messageDiv.className = 'alert alert-danger';
            messageDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i> <strong>Erro:</strong> ' + result.error;
            
            registryUrlDiv.style.display = 'none';
            
            // Show error output if available
            if (result.output) {
                buildOutputContainer.style.display = 'block';
                buildOutputPre.textContent = result.output;
            }
        }
        
    } catch (error) {
        // Network error
        document.getElementById('deploy-output').style.display = 'block';
        const messageDiv = document.getElementById('deploy-message');
        messageDiv.className = 'alert alert-danger';
        messageDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i> <strong>Erro de rede:</strong> ' + error.message;
        
        document.getElementById('deploy-registry-url').style.display = 'none';
        document.getElementById('build-output-container').style.display = 'none';
    } finally {
        // Re-enable button
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

async function loadChallenges() {
    const loadingDiv = document.getElementById('challenges-loading');
    const listDiv = document.getElementById('challenges-list');
    const emptyDiv = document.getElementById('challenges-empty');
    
    // Show loading
    loadingDiv.style.display = 'block';
    listDiv.style.display = 'none';
    emptyDiv.style.display = 'none';
    
    try {
        const response = await fetch('/admin/challenge-deployer/api/challenges', {
            headers: {
                'CSRF-Token': window.init.csrfNonce || ''
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            const challenges = result.challenges;
            
            if (challenges.length === 0) {
                emptyDiv.style.display = 'block';
            } else {
                // Populate table
                const tbody = document.getElementById('challenges-tbody');
                tbody.innerHTML = '';
                
                challenges.forEach(challenge => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td><strong>${escapeHtml(challenge.name)}</strong></td>
                        <td><code>${escapeHtml(challenge.path)}</code></td>
                        <td>
                            <button class="btn btn-sm btn-danger" onclick="deleteChallenge('${escapeHtml(challenge.name)}')">
                                <i class="fas fa-trash"></i> Deletar
                            </button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
                
                listDiv.style.display = 'block';
            }
        } else {
            emptyDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Erro ao carregar desafios: ' + result.error;
            emptyDiv.className = 'alert alert-danger';
            emptyDiv.style.display = 'block';
        }
        
    } catch (error) {
        emptyDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Erro de rede: ' + error.message;
        emptyDiv.className = 'alert alert-danger';
        emptyDiv.style.display = 'block';
    } finally {
        loadingDiv.style.display = 'none';
    }
}

async function deleteChallenge(challengeName) {
    if (!confirm(`Tem certeza que deseja deletar o desafio "${challengeName}"?\n\nIsso removerá apenas o diretório local, não o registry.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/challenge-deployer/api/delete/${encodeURIComponent(challengeName)}`, {
            method: 'DELETE',
            headers: {
                'CSRF-Token': window.init.csrfNonce || ''
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            loadChallenges();
        } else {
            alert('Erro ao deletar: ' + result.error);
        }
        
    } catch (error) {
        alert('Erro de rede: ' + error.message);
    }
}

function copyToClipboard() {
    const input = document.getElementById('registry-url-output');
    input.select();
    document.execCommand('copy');
    
    // Show feedback
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-check"></i> Copiado!';
    btn.classList.add('btn-success');
    btn.classList.remove('btn-outline-secondary');
    
    setTimeout(() => {
        btn.innerHTML = originalHTML;
        btn.classList.remove('btn-success');
        btn.classList.add('btn-outline-secondary');
    }, 2000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
