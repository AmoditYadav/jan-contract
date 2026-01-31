document.addEventListener('DOMContentLoaded', () => {
    // Navigation Logic
    const navLinks = document.querySelectorAll('.nav-links li');
    const sections = document.querySelectorAll('main section');

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Remove active class from all
            navLinks.forEach(l => l.classList.remove('active'));
            sections.forEach(s => {
                s.classList.add('hidden-section');
                s.classList.remove('active-section');
            });

            // Add active to clicked
            link.classList.add('active');
            const targetId = link.getAttribute('data-tab');
            const targetSection = document.getElementById(targetId);
            targetSection.classList.remove('hidden-section');
            setTimeout(() => targetSection.classList.add('active-section'), 10);
        });
    });

    // --- CONTRACT GENERATOR ---
    const btnGenerate = document.getElementById('btn-generate-contract');
    const contractInput = document.getElementById('contract-input');
    const contractResult = document.getElementById('contract-result');
    const contractText = document.getElementById('contract-text');
    const contractTrivia = document.getElementById('contract-trivia');
    const triviaContent = document.getElementById('trivia-content');

    btnGenerate.addEventListener('click', async () => {
        const text = contractInput.value.trim();
        if (!text) return showToast('Please describe the agreement first.', 'error');

        setLoading(btnGenerate, true);
        try {
            const resp = await fetch('/api/v1/contracts/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_request: text })
            });
            const data = await resp.json();
            
            if (data.success) {
                contractResult.classList.remove('hidden');
                contractText.innerHTML = marked.parse(data.data.contract);
                
                // Render Trivia
                if (data.data.legal_trivia && data.data.legal_trivia.trivia) {
                    contractTrivia.classList.remove('hidden');
                    triviaContent.innerHTML = data.data.legal_trivia.trivia.map(t => `
                        <div class="trivia-item">
                            <h5>${t.point}</h5>
                            <p>${t.explanation}</p>
                            <a href="${t.source_url}" target="_blank">Source <i class="fa-solid fa-arrow-up-right-from-square"></i></a>
                        </div>
                    `).join('');
                } else {
                    contractTrivia.classList.add('hidden');
                }
                showToast('Contract generated successfully!');
            } else {
                showToast(data.message || 'Error generating contract', 'error');
            }
        } catch (e) {
            showToast('Connection failed', 'error');
        } finally {
            setLoading(btnGenerate, false);
        }
    });

    // --- SCHEME FINDER ---
    const btnFindSchemes = document.getElementById('btn-find-schemes');
    const schemeInput = document.getElementById('scheme-input');
    const schemesList = document.getElementById('schemes-list');
    const schemesLoader = document.getElementById('schemes-loader');

    btnFindSchemes.addEventListener('click', async () => {
        const profile = schemeInput.value.trim();
        if (!profile) return showToast('Please enter a profile.', 'error');

        schemesList.innerHTML = '';
        schemesLoader.classList.remove('hidden');
        
        try {
            const resp = await fetch('/api/v1/schemes/find', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_profile: profile })
            });
            const data = await resp.json();

            if (data.success && data.data.schemes) {
                schemesList.innerHTML = data.data.schemes.map(s => `
                    <div class="scheme-card">
                        <h4>${s.scheme_name}</h4>
                        <p>${s.description}</p>
                        <br>
                        <small><strong>Target:</strong> ${s.target_audience}</small>
                        <br>
                        <a href="${s.official_link}" target="_blank">Visit Official Site &rarr;</a>
                    </div>
                `).join('');
            } else {
                schemesList.innerHTML = '<p class="text-dim">No schemes found. Try a different description.</p>';
            }
        } catch (e) {
            showToast('Search failed', 'error');
        } finally {
            schemesLoader.classList.add('hidden');
        }
    });

    // --- DEMYSTIFIER ---
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('pdf-upload');
    const analysisView = document.getElementById('analysis-view');
    let currentSessionId = null;

    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileUpload);
    
    // Drag and Drop
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.borderColor = 'var(--primary)'; });
    dropZone.addEventListener('dragleave', (e) => { e.preventDefault(); dropZone.style.borderColor = 'var(--border)'; });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--border)';
        if (e.dataTransfer.files.length) {
            handleFileUpload({ target: { files: e.dataTransfer.files } });
        }
    });

    async function handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file || file.type !== 'application/pdf') return showToast('Please upload a PDF', 'error');

        // Show simplified loading
        dropZone.innerHTML = '<div class="loader"></div><p>Analyzing Document...</p>';

        const formData = new FormData();
        formData.append('file', file);

        try {
            const resp = await fetch('/api/v1/demystify/upload', {
                method: 'POST',
                body: formData
            });
            const data = await resp.json();

            if (data.success) {
                currentSessionId = data.data.session_id;
                dropZone.classList.add('hidden');
                analysisView.classList.remove('hidden');

                document.getElementById('doc-summary').innerHTML = `<p>${data.data.report.summary}</p>`;
                document.getElementById('doc-terms').innerHTML = data.data.report.key_terms.map(t => `
                    <div class="term-item" style="margin-bottom:1rem; padding-bottom:1rem; border-bottom:1px solid rgba(255,255,255,0.05)">
                        <strong style="color:var(--secondary)">${t.term}:</strong> ${t.explanation}
                    </div>
                `).join('');
            } else {
                showToast('Analysis failed', 'error');
                resetUpload();
            }
        } catch (e) {
            showToast('Upload error', 'error');
            resetUpload();
        }
    }

    // Doc Chat
    const btnDocChat = document.getElementById('btn-doc-chat');
    const docChatInput = document.getElementById('doc-chat-input');
    const docChatMessages = document.getElementById('doc-chat-messages');

    btnDocChat.addEventListener('click', () => sendChat(docChatInput, docChatMessages, '/api/v1/demystify/chat', { session_id: currentSessionId }));

    // --- GENERAL ASSISTANT ---
    const btnGeneralChat = document.getElementById('btn-general-chat');
    const generalChatInput = document.getElementById('general-chat-input');
    const generalChatMessages = document.getElementById('general-chat-messages');

    btnGeneralChat.addEventListener('click', () => sendChat(generalChatInput, generalChatMessages, '/api/v1/assistant/chat', {}));

    // Chat Helper
    async function sendChat(inputEl, containerEl, endpoint, extraPayload) {
        const question = inputEl.value.trim();
        if (!question) return;

        // Add User Message
        addMessage(containerEl, question, 'user');
        inputEl.value = '';

        // Add Loading Bubble
        const loadingId = addMessage(containerEl, '<i class="fa-solid fa-ellipsis fa-fade"></i>', 'ai');

        try {
            const resp = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question, ...extraPayload })
            });
            const data = await resp.json();
            
            // Remove Loader and Add Response
            document.getElementById(loadingId).remove();
            
            const answer = data.data.answer || data.data.response || "I couldn't understand that.";
            addMessage(containerEl, marked.parse(answer), 'ai');

        } catch (e) {
            document.getElementById(loadingId).remove();
            addMessage(containerEl, "Sorry, something went wrong.", 'ai');
        }
    }

    function addMessage(container, html, type) {
        const id = 'msg-' + Date.now();
        const div = document.createElement('div');
        div.className = `message ${type}`;
        div.id = id;
        div.innerHTML = `
            <div class="avatar"><i class="fa-solid ${type === 'ai' ? 'fa-robot' : 'fa-user'}"></i></div>
            <div class="bubble">${html}</div>
        `;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
        return id;
    }

    // Utilities
    function showToast(msg, type = 'success') {
        const toast = document.getElementById('toast');
        toast.textContent = msg;
        toast.style.background = type === 'error' ? '#ef4444' : '#10b981';
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 3000);
    }

    function setLoading(btn, isLoading) {
        if (isLoading) {
            btn.dataset.original = btn.innerHTML;
            btn.innerHTML = '<div class="loader" style="width:20px; height:20px; margin:0; border-width:2px;"></div>';
            btn.disabled = true;
        } else {
            btn.innerHTML = btn.dataset.original;
            btn.disabled = false;
        }
    }

    function resetUpload() {
        dropZone.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i><h3>Drag & Drop PDF here</h3><p>or click to browse</p><input type="file" id="pdf-upload" accept="application/pdf" hidden>';
        dropZone.classList.remove('hidden');
    }
});
