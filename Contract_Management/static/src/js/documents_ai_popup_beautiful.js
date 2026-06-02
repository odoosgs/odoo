/** @odoo-module **/
console.log("🚀 contract_management beautiful popup JS loaded!");

// Initialize hook: if user clicked our Upload Contract entry, set window._cmUploadContract = true
// Then when the hidden upload input changes (files selected), show our AI popup.
(function initUploadContractPopupHook() {
    if (window._cmUploadHookInstalled) return;
    window._cmUploadHookInstalled = true;
    document.addEventListener(
        'change',
        (ev) => {
            try {
                if (!window._cmUploadContract) return; // only when coming from our menu
                const el = ev.target;
                if (!(el instanceof HTMLInputElement)) return;
                // The Documents control panel uses an <input type="file" class="o_input_file o_hidden" t-ref="uploadFileInput">
                if (el.type === 'file' && el.classList.contains('o_input_file')) {
                    // Reset flag to avoid duplicate popups
                    window._cmUploadContract = false;
                    // Open our AI popup
                    setTimeout(() => {
                        try { createBeautifulAIPopup(); } catch (e) { console.error('Failed to open AI popup', e); }
                    }, 0);
                }
            } catch (e) {
                console.warn('Upload Contract hook error:', e);
            }
        },
        true // capture to catch early
    );
})();

// Open popup on drag-and-drop, but only when user is in our Contract tab action.
(function initContractTabDropHook() {
    if (window._cmDropHookInstalled) return;
    window._cmDropHookInstalled = true;

    const getCSRF = () => document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    let contractActionNumericId = null; // act_window id
    const contractActionXmlId = 'Contract_Management.action_documents_contract_only';
    const resolveContractActionNumericId = async () => {
        if (contractActionNumericId !== null) return contractActionNumericId;
        try {
            const body = {
                jsonrpc: '2.0', method: 'call', params: {
                    model: 'ir.model.data', method: 'search_read',
                    args: [[['module', '=', 'Contract_Management'], ['name', '=', 'action_documents_contract_only']]],
                    kwargs: { fields: ['res_id'], limit: 1 }
                }
            };
            const res = await fetch('/web/dataset/call_kw', {
                method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRF() },
                body: JSON.stringify(body)
            });
            if (!res.ok) return null;
            const data = await res.json();
            contractActionNumericId = (data.result && data.result[0] && data.result[0].res_id) || null;
            return contractActionNumericId;
        } catch (e) { return null; }
    };

    const isInContractTab = async () => {
        const hash = window.location.hash || '';
        // Case 1: hash contains the xmlid string
        if (hash.includes(`action=${encodeURIComponent(contractActionXmlId)}`) || hash.includes(`action=${contractActionXmlId}`)) {
            return true;
        }
        // Case 2: hash contains the numeric id
        const id = await resolveContractActionNumericId();
        if (id) {
            const re = new RegExp(`[?#&]action=${id}(?:&|$)`);
            if (re.test(hash)) return true;
        }
        return false;
    };

    // Listen to drop events in Documents content area
    document.addEventListener('drop', async (ev) => {
        try {
            // Only if the event occurs in the documents main content
            const target = ev.target;
            const container = target && (target.closest?.('.o_documents_content') || target.closest?.('.o_documents_kanban'));
            if (!container) return;
            if (!(await isInContractTab())) return;
            // Give Odoo a moment to start the upload then show popup
            setTimeout(() => {
                try { createBeautifulAIPopup(); } catch (e) { console.error('Failed to open AI popup (drop)', e); }
            }, 50);
        } catch (e) { /* ignore */ }
    }, true);
})();

// Beautiful custom popup for AI assistant
function createBeautifulAIPopup() {
    // Remove any existing popup first
    const existingPopup = document.getElementById('ai-beautiful-popup');
    if (existingPopup) {
        existingPopup.remove();
    }

    // Create the main overlay
    const overlay = document.createElement('div');
    overlay.id = 'ai-beautiful-popup';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.45);
        backdrop-filter: blur(4px);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: fadeIn 0.25s ease-out;
    `;

    // Create the popup container
    const popup = document.createElement('div');
    popup.style.cssText = `
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
        max-width: 520px;
        width: 92%;
        position: relative;
        animation: slideIn 0.3s ease-out;
        overflow: hidden;
        border: 1px solid rgba(0,0,0,0.08);
    `;

    // Create the content
    const content = document.createElement('div');
    content.style.cssText = `
        padding: 28px 26px;
        text-align: center;
        color: #1f2937;
        position: relative;
        z-index: 2;
    `;

    // Add AI icon
    const icon = document.createElement('div');
    icon.style.cssText = `
        font-size: 40px;
        margin-bottom: 16px;
        animation: bounce 3s infinite;
    `;
    icon.innerHTML = '';

    // Add title
    const title = document.createElement('h2');
    title.style.cssText = `
        margin: 0 0 10px 0;
        font-size: 22px;
        font-weight: 600;
        letter-spacing: 0.2px;
    `;
    title.textContent = 'AI Assistant';

    // Close (X) button for the first popup
    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.style.cssText = `
        position: absolute;
        top: 10px;
        right: 12px;
        width: 28px;
        height: 28px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: 1px solid rgba(0,0,0,0.12);
        border-radius: 999px;
        background: rgba(0,0,0,0.02);
        color: #6b7280;
        cursor: pointer;
        transition: all 0.2s ease;
    `;
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('mouseenter', function () {
        this.style.background = 'rgba(0,0,0,0.05)';
        this.style.transform = 'translateY(-1px)';
    });
    closeBtn.addEventListener('mouseleave', function () {
        this.style.background = 'rgba(0,0,0,0.02)';
        this.style.transform = 'translateY(0)';
    });
    closeBtn.addEventListener('click', function () {
        closeBeautifulPopup();
    });

    // Add message
    const message = document.createElement('p');
    message.style.cssText = `
        margin: 0 0 24px 0;
        font-size: 15px;
        line-height: 1.6;
        color: #4b5563;
    `;
    message.textContent = 'Do you want to Fetch start and end date?';

    // Create button container
    const buttonContainer = document.createElement('div');
    buttonContainer.style.cssText = `
        display: flex;
        gap: 12px;
        justify-content: center;
        margin-top: 16px;
    `;

    // Create No button
    const noButton = document.createElement('button');
    noButton.id = 'ai-popup-no-beautiful';
    noButton.style.cssText = `
        padding: 10px 22px;
        background: transparent;
        color: var(--o-brand-odoo, #714B67);
        border: 1px solid var(--o-brand-odoo, #714B67);
        border-radius: 10px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s ease;
    `;
    noButton.textContent = 'No';
    noButton.innerHTML = 'No';

    // Create Yes button
    const yesButton = document.createElement('button');
    yesButton.id = 'ai-popup-yes-beautiful';
    yesButton.style.cssText = `
        padding: 10px 22px;
        background: var(--o-brand-odoo, #714B67);
        color: #ffffff;
        border: none;
        border-radius: 10px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 6px 18px rgba(113, 75, 103, 0.35);
    `;
    yesButton.textContent = 'Yes';
    yesButton.innerHTML = 'Yes';

    // Add hover effects
    noButton.addEventListener('mouseenter', function() {
        this.style.background = 'rgba(113, 75, 103, 0.06)';
        this.style.transform = 'translateY(-1px)';
    });
    noButton.addEventListener('mouseleave', function() {
        this.style.background = 'transparent';
        this.style.transform = 'translateY(0)';
    });

    yesButton.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-1px)';
        this.style.boxShadow = '0 8px 22px rgba(113, 75, 103, 0.45)';
    });
    yesButton.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
        this.style.boxShadow = '0 6px 18px rgba(113, 75, 103, 0.35)';
    });

    // Add event listeners
    noButton.addEventListener('click', function() {
        closeBeautifulPopup();
    });

    yesButton.addEventListener('click', function() {
        // Close the prompt and immediately start extraction (no thank-you popup)
        closeBeautifulPopup();
        setTimeout(() => {
            try { extractDatesFromFile(); } catch (e) { console.error('extractDatesFromFile failed', e); }
        }, 200);
    });

    // Assemble the popup
    content.appendChild(icon);
    content.appendChild(title);
    content.appendChild(closeBtn);
    content.appendChild(message);
    buttonContainer.appendChild(noButton);
    buttonContainer.appendChild(yesButton);
    content.appendChild(buttonContainer);
    popup.appendChild(content);
    overlay.appendChild(popup);

    // Add to document
    document.body.appendChild(overlay);


    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slideIn {
            from { 
                opacity: 0;
                transform: translateY(-50px) scale(0.9);
            }
            to { 
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-10px); }
            60% { transform: translateY(-5px); }
        }
    `;
    document.head.appendChild(style);

    // Close on background click
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            closeBeautifulPopup();
        }
    });

    // Close on Escape key
    const escapeHandler = function(e) {
        if (e.key === 'Escape') {
            closeBeautifulPopup();
            document.removeEventListener('keydown', escapeHandler);
        }
    };
    document.addEventListener('keydown', escapeHandler);
}

// Function to close the beautiful popup
function closeBeautifulPopup() {
    const popup = document.getElementById('ai-beautiful-popup');
    if (popup) {
        popup.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => {
            popup.remove();
        }, 300);
    }
    // Reset state
    uploadInProgress = false;
    popupShown = false;
}

// Function to show "Thank you" popup
function showThankYouPopup() {
    // Remove any existing popup first
    const existingPopup = document.getElementById('ai-thank-you-popup');
    if (existingPopup) {
        existingPopup.remove();
    }

    // Create the main overlay
    const overlay = document.createElement('div');
    overlay.id = 'ai-thank-you-popup';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.45);
        backdrop-filter: blur(4px);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: fadeIn 0.25s ease-out;
    `;

    // Create the popup container
    const popup = document.createElement('div');
    popup.style.cssText = `
        background: #ffffff;
        border-radius: 14px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
        max-width: 420px;
        width: 92%;
        position: relative;
        animation: slideIn 0.3s ease-out;
        overflow: hidden;
        border: 1px solid rgba(0,0,0,0.08);
    `;

    // Create the content
    const content = document.createElement('div');
    content.style.cssText = `
        padding: 26px 24px;
        text-align: center;
        color: #1f2937;
        position: relative;
        z-index: 2;
    `;

    // Add success icon
    const icon = document.createElement('div');
    icon.style.cssText = `
        font-size: 40px;
        margin-bottom: 14px;
        animation: bounce 3s infinite;
    `;
    icon.innerHTML = '';

    // Add title
    const title = document.createElement('h2');
    title.style.cssText = `
        margin: 0 0 8px 0;
        font-size: 20px;
        font-weight: 600;
        letter-spacing: 0.2px;
    `;
    title.textContent = 'Thank you!';

    // Add message
    const message = document.createElement('p');
    message.style.cssText = `
        margin: 0 0 18px 0;
        font-size: 14px;
        line-height: 1.6;
        color: #4b5563;
    `;
    message.textContent = 'AI processing will start for your document.';

    // Create OK button
    const okButton = document.createElement('button');
    okButton.id = 'ai-thank-you-ok';
    okButton.style.cssText = `
        padding: 10px 22px;
        background: var(--o-brand-odoo, #714B67);
        color: #ffffff;
        border: none;
        border-radius: 10px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 6px 18px rgba(113, 75, 103, 0.35);
    `;
    okButton.textContent = 'OK';
    okButton.innerHTML = 'OK';

    // Add hover effect
    okButton.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-1px)';
        this.style.boxShadow = '0 8px 22px rgba(113, 75, 103, 0.45)';
    });
    okButton.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
        this.style.boxShadow = '0 6px 18px rgba(113, 75, 103, 0.35)';
    });

    // Add event listener
    okButton.addEventListener('click', function() {
        closeThankYouPopup();
    });

    // Assemble the popup
    content.appendChild(icon);
    content.appendChild(title);
    content.appendChild(message);
    content.appendChild(okButton);
    popup.appendChild(content);
    overlay.appendChild(popup);

    // Add to document
    document.body.appendChild(overlay);

    // Close on background click
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            closeThankYouPopup();
        }
    });

    // Close on Escape key
    const escapeHandler = function(e) {
        if (e.key === 'Escape') {
            closeThankYouPopup();
            document.removeEventListener('keydown', escapeHandler);
        }
    };
    document.addEventListener('keydown', escapeHandler);

    // Auto-close after 5 seconds
    setTimeout(() => {
        closeThankYouPopup();
    }, 5000);
}

// Function to close the thank you popup
function closeThankYouPopup() {
    const popup = document.getElementById('ai-thank-you-popup');
    if (popup) {
        popup.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => {
            popup.remove();
        }, 300);
    }
}

// Function to call FastAPI and extract dates
async function extractDatesFromFile() {
    try {
        // Show loading popup
        showLoadingPopup();
        
        // Get the uploaded file from the recent upload
        // We'll send a request to Odoo to get the file data
        const odooResponse = await fetch('/web/dataset/call_kw', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    model: 'ir.attachment',
                    method: 'search_read',
                    args: [[['res_model', '=', 'documents.document']]],
                    kwargs: {
                        fields: ['name', 'datas', 'mimetype', 'res_id'],
                        limit: 1,
                        order: 'create_date desc'
                    }
                }
            })
        });
        
        if (odooResponse.ok) {
            const odooData = await odooResponse.json();
            const attachment = odooData.result[0];
            
            if (attachment) {
                // Tag the related document with the 'Contract' tag (so it appears in the Contract tab)
                try {
                    const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
                    const rpc = async (model, method, args = [], kwargs = {}) => {
                        const body = { jsonrpc: '2.0', method: 'call', params: { model, method, args, kwargs } };
                        const res = await fetch('/web/dataset/call_kw', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                            body: JSON.stringify(body),
                        });
                        if (!res.ok) throw new Error('RPC HTTP error');
                        const data = await res.json();
                        if (data.error) throw new Error(data.error.message || 'RPC error');
                        return data.result;
                    };
                    // Ensure tag exists
                    let tagId = 0;
                    const tagIds = await rpc('documents.tag', 'search', [[['name', '=', 'Contract']]], { limit: 1 });
                    if (Array.isArray(tagIds) && tagIds.length) {
                        tagId = tagIds[0];
                    } else {
                        tagId = await rpc('documents.tag', 'create', [[{ name: 'Contract' }]]);
                    }
                    const docId = attachment.res_id;
                    if (docId && tagId) {
                        // Append the tag to the document
                        await rpc('documents.document', 'write', [[docId], { tag_ids: [[4, tagId]] }]);
                    }
                } catch (e) {
                    console.warn('Failed to tag document as Contract:', e);
                }
                // Send file to FastAPI
                const formData = new FormData();
                // Proper base64 -> binary conversion to avoid corruption
                const base64Data = attachment.datas;
                const byteChars = atob(base64Data);
                const byteNumbers = new Array(byteChars.length);
                for (let i = 0; i < byteChars.length; i++) {
                    byteNumbers[i] = byteChars.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                const fileBlob = new Blob([byteArray], { type: attachment.mimetype });
                formData.append('file', fileBlob, attachment.name);
                // Fetch FastAPI credentials (uuid, secret_key) from Odoo model contract.registration
                try {
                    // Define local RPC helper (do not rely on outer scope)
                    const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
                    const rpc = async (model, method, args = [], kwargs = {}) => {
                        const body = { jsonrpc: '2.0', method: 'call', params: { model, method, args, kwargs } };
                        const res = await fetch('/web/dataset/call_kw', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                            body: JSON.stringify(body),
                        });
                        if (!res.ok) throw new Error('RPC HTTP error');
                        const data = await res.json();
                        if (data.error) throw new Error(data.error.message || 'RPC error');
                        return data.result;
                    };

                    // Prefer active registration; fallback to any latest if none active
                    let creds = await rpc(
                        'contract.registration',
                        'search_read',
                        [[['status', '=', 'active']]],
                        { fields: ['uuid', 'secret_key'], limit: 1, order: 'id desc' }
                    );
                    if (!Array.isArray(creds) || !creds.length) {
                        creds = await rpc(
                            'contract.registration',
                            'search_read',
                            [[]],
                            { fields: ['uuid', 'secret_key'], limit: 1, order: 'id desc' }
                        );
                    }
                    const uuid = (creds && creds[0] && creds[0].uuid) || '';
                    const secretKey = (creds && creds[0] && creds[0].secret_key) || '';
                    if (uuid) formData.append('uuid', uuid);
                    if (secretKey) formData.append('secret_key', secretKey);
                } catch (e) {
                    console.warn('Could not fetch FastAPI credentials from contract.registration:', e);
                }
                
                const response = await fetch('https://cm.sufalamtech.com/extract-dates', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    // Normalize dates to strict YYYY-MM-DD
                    const norm = (d) => {
                        if (!d) return '';
                        const m = String(d).match(/\b\d{4}-\d{2}-\d{2}\b/);
                        return m ? m[0] : '';
                    };
                    const result = (data && data.result) || {};
                    const startIso = norm(result.start_date);
                    const endIso = norm(result.end_date);
                    console.log('[ContractMgmt] AI dates:', data, 'normalized:', { startIso, endIso });
                    if (typeof data.file_count === 'number') {
                        try { showCMToast('AI Processed', `Total files processed for your key: ${data.file_count}`, 'info', 3500); } catch(e) { /* ignore */ }
                    }
                    // Resolve a display name for the uploaded file
                    let displayName = attachment.name || '';
                    if ((!displayName || !displayName.trim()) && attachment.res_id) {
                        try {
                            const docInfo = await rpc('documents.document', 'read', [[attachment.res_id], ['name']]);
                            if (Array.isArray(docInfo) && docInfo[0] && docInfo[0].name) {
                                displayName = docInfo[0].name;
                            }
                        } catch (e) {
                            console.warn('Could not read documents.document name:', e);
                        }
                    }
                    closeLoadingPopup();
                    showDateExtractionPopup(startIso, endIso, (displayName || '').trim(), attachment.res_id || 0);
                } else {
                    throw new Error('FastAPI request failed');
                }
            } else {
                throw new Error('No file found');
            }
        } else {
            throw new Error('Failed to get file from Odoo');
        }
    } catch (error) {
        console.error('Error extracting dates:', error);
        closeLoadingPopup();
        showDateExtractionPopup('', '', '', 0); // Show empty dates for manual entry
    }
}

// Function to show loading popup
function showLoadingPopup() {
    const overlay = document.createElement('div');
    overlay.id = 'ai-loading-popup';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.45);
        backdrop-filter: blur(4px);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: fadeIn 0.25s ease-out;
    `;

    const popup = document.createElement('div');
    popup.style.cssText = `
        background: #ffffff;
        border-radius: 14px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
        max-width: 420px;
        width: 92%;
        position: relative;
        animation: slideIn 0.3s ease-out;
        overflow: hidden;
        text-align: center;
        color: #1f2937;
        padding: 26px 24px;
        border: 1px solid rgba(0,0,0,0.08);
    `;

    popup.innerHTML = `
        <div style="
            width: 48px;
            height: 48px;
            border: 4px solid rgba(113, 75, 103, 0.2);
            border-top-color: var(--o-brand-odoo, #714B67);
            border-radius: 50%;
            animation: spin 0.9s linear infinite;
            margin: 0 auto 14px auto;
        "></div>
        <h2 style="margin: 0 0 8px 0; font-size: 20px; font-weight: 600; letter-spacing: 0.2px; color:#111827;">Processing...</h2>
        <p style="margin: 0; font-size: 14px; color: #4b5563;">Extracting dates from your document using AI</p>
    `;

    overlay.appendChild(popup);
    document.body.appendChild(overlay);

    // Add spin animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}

// Function to close loading popup
function closeLoadingPopup() {
    const popup = document.getElementById('ai-loading-popup');
    if (popup) {
        popup.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => {
            popup.remove();
        }, 300);
    }
}

// Function to show date extraction popup with edit functionality
function showDateExtractionPopup(sDate, eDate, fileName, docId) {
    // Defensive normalize (trim) incoming values
    sDate = (sDate || '').trim();
    eDate = (eDate || '').trim();
    // Capture immutable copies for async callbacks
    const _startDate = sDate;
    const _endDate = eDate;
    const _fileName = (fileName || '').trim();
    const _docId = docId || 0;
    // Remove any existing popup first
    const existingPopup = document.getElementById('ai-date-extraction-popup');
    if (existingPopup) {
        existingPopup.remove();
    }

    // Create the main overlay
    const overlay = document.createElement('div');
    overlay.id = 'ai-date-extraction-popup';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.45);
        backdrop-filter: blur(4px);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: fadeIn 0.25s ease-out;
    `;

    // Create the popup container
    const popup = document.createElement('div');
    popup.style.cssText = `
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
        max-width: 560px;
        width: 94%;
        position: relative;
        animation: slideIn 0.3s ease-out;
        overflow: hidden;
        border: 1px solid rgba(0,0,0,0.08);
    `;

    // Create the content
    const content = document.createElement('div');
    content.style.cssText = `
        padding: 28px 26px;
        text-align: center;
        color: #1f2937;
        position: relative;
        z-index: 2;
    `;

    // Add success icon
    const icon = document.createElement('div');
    icon.style.cssText = `
        font-size: 40px;
        margin-bottom: 16px;
        animation: bounce 3s infinite;
    `;
    icon.innerHTML = '';

    // Add title
    const title = document.createElement('h2');
    title.style.cssText = `
        margin: 0 0 14px 0;
        font-size: 20px;
        font-weight: 600;
        letter-spacing: 0.2px;
    `;
    title.textContent = 'Here’s What We Found in Your Contract';

    // Add small cancel (X) icon in top-right corner
    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.style.cssText = `
        position: absolute;
        top: 10px;
        right: 12px;
        width: 28px;
        height: 28px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: 1px solid rgba(0,0,0,0.12);
        border-radius: 999px;
        background: rgba(0,0,0,0.02);
        color: #6b7280;
        cursor: pointer;
        transition: all 0.2s ease;
    `;
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('mouseenter', function () {
        this.style.background = 'rgba(0,0,0,0.05)';
        this.style.transform = 'translateY(-1px)';
    });
    closeBtn.addEventListener('mouseleave', function () {
        this.style.background = 'rgba(0,0,0,0.02)';
        this.style.transform = 'translateY(0)';
    });
    closeBtn.addEventListener('click', function () {
        closeDateExtractionPopup();
    });

    // Add File Name (read-only)
    const fileNameContainer = document.createElement('div');
    fileNameContainer.style.cssText = `
        margin: 0 0 16px 0;
        text-align: left;
    `;
    const fileNameLabel = document.createElement('label');
    fileNameLabel.style.cssText = `
        display: block;
        margin-bottom: 6px;
        font-weight: 500;
        font-size: 14px;
        color: #374151;
    `;
    fileNameLabel.textContent = 'File Name:';
    const fileNameInput = document.createElement('input');
    fileNameInput.type = 'text';
    fileNameInput.value = _fileName;
    fileNameInput.readOnly = false; // allow editing
    fileNameInput.style.cssText = `
        width: 100%;
        padding: 10px 12px;
        border: 1px solid rgba(0, 0, 0, 0.15);
        border-radius: 10px;
        background: #f9fafb;
        color: #6b7280;
        font-size: 14px;
    `;
    fileNameContainer.appendChild(fileNameLabel);
    fileNameContainer.appendChild(fileNameInput);

    // Add date fields
    // Helpers to compute reminder dates and format nicely for the user ("10 Jan 2025 - Mon")
    const MONTHS_SHORT = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const WEEKDAYS_SHORT = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
    const pad2 = (n) => String(n).padStart(2, '0');
    const formatPretty = (date) => {
        const d = pad2(date.getDate());
        const m = MONTHS_SHORT[date.getMonth()];
        const y = date.getFullYear();
        const wd = WEEKDAYS_SHORT[date.getDay()];
        return `${d} ${m} ${y} - ${wd}`;
    };
    const computeReminderDisplay = (endDateStr, daysAgoStr) => {
        if (!endDateStr) return '';
        const n = parseInt(daysAgoStr, 10);
        if (isNaN(n) || n < 0) return '';
        const d = new Date(endDateStr);
        d.setDate(d.getDate() - n);
        return formatPretty(d);
    };
    const dateContainer = document.createElement('div');
    dateContainer.style.cssText = `
        margin-bottom: 22px;
        text-align: left;
    `;

    // Start Date field
    const startDateContainer = document.createElement('div');
    startDateContainer.style.cssText = `
        margin-bottom: 16px;
    `;

    const startDateLabel = document.createElement('label');
    startDateLabel.style.cssText = `
        display: block;
        margin-bottom: 6px;
        font-weight: 500;
        font-size: 14px;
        color: #374151;
    `;
    startDateLabel.textContent = 'Start Date:';

    const startDateInput = document.createElement('input');
    startDateInput.type = 'date';
    startDateInput.value = _startDate || '';
    startDateInput.id = 'start-date-input';
    startDateInput.style.cssText = `
        width: 100%;
        padding: 10px 12px;
        border: 1px solid rgba(0, 0, 0, 0.15);
        border-radius: 10px;
        background: #ffffff;
        color: #111827;
        font-size: 14px;
    `;

    startDateContainer.appendChild(startDateLabel);
    startDateContainer.appendChild(startDateInput);

    // End Date field
    const endDateContainer = document.createElement('div');
    endDateContainer.style.cssText = `
        margin-bottom: 8px;
    `;

    const endDateLabel = document.createElement('label');
    endDateLabel.style.cssText = `
        display: block;
        margin-bottom: 6px;
        font-weight: 500;
        font-size: 14px;
        color: #d1d5db;
    `;
    endDateLabel.textContent = 'End Date:';

    const endDateInput = document.createElement('input');
    endDateInput.type = 'date';
    endDateInput.value = _endDate || '';
    endDateInput.id = 'end-date-input';
    endDateInput.style.cssText = `
        width: 100%;
        padding: 10px 12px;
        border: 1px solid rgba(0, 0, 0, 0.15);
        border-radius: 10px;
        background: #ffffff;
        color: #111827;
        font-size: 14px;
    `;

    endDateContainer.appendChild(endDateLabel);
    endDateContainer.appendChild(endDateInput);

    // Reminder 1 field (numeric)
    const reminder1Container = document.createElement('div');
    reminder1Container.style.cssText = `
        margin: 12px 0 8px 0;
    `;

    const reminder1Label = document.createElement('label');
    reminder1Label.style.cssText = `
        display: block;
        margin-bottom: 6px;
        font-weight: 500;
        font-size: 14px;
        color: #d1d5db;
    `;
    reminder1Label.textContent = 'Reminder 1 Days Before:';

    const reminder1Input = document.createElement('input');
    reminder1Input.type = 'number';
    reminder1Input.min = '0';
    reminder1Input.step = '1';
    reminder1Input.placeholder = 'e.g., 14';
    reminder1Input.id = 'reminder1-input';
    reminder1Input.style.cssText = `
        width: 100%;
        padding: 10px 12px;
        border: 1px solid rgba(0, 0, 0, 0.15);
        border-radius: 10px;
        background: #ffffff;
        color: #111827;
        font-size: 14px;
    `;

    // Helper text to preview the computed date for Reminder 1
    const reminder1Hint = document.createElement('div');
    reminder1Hint.id = 'reminder1-hint';
    reminder1Hint.style.cssText = `
        margin-top: 6px;
        font-size: 12px;
        color: var(--o-brand-odoo, #714B67);
    `;

    reminder1Container.appendChild(reminder1Label);
    reminder1Container.appendChild(reminder1Input);
    reminder1Container.appendChild(reminder1Hint);

    // Reminder 2 field (numeric)
    const reminder2Container = document.createElement('div');
    reminder2Container.style.cssText = `
        margin: 8px 0 0 0;
    `;

    const reminder2Label = document.createElement('label');
    reminder2Label.style.cssText = `
        display: block;
        margin-bottom: 6px;
        font-weight: 500;
        font-size: 14px;
        color: #d1d5db;
    `;
    reminder2Label.textContent = 'Reminder 2 Days Before:';

    const reminder2Input = document.createElement('input');
    reminder2Input.type = 'number';
    reminder2Input.min = '0';
    reminder2Input.step = '1';
    reminder2Input.placeholder = 'e.g., 7';
    reminder2Input.id = 'reminder2-input';
    reminder2Input.style.cssText = `
        width: 100%;
        padding: 10px 12px;
        border: 1px solid rgba(0, 0, 0, 0.15);
        border-radius: 10px;
        background: #ffffff;
        color: #111827;
        font-size: 14px;
    `;

    // Helper text to preview the computed date for Reminder 2
    const reminder2Hint = document.createElement('div');
    reminder2Hint.id = 'reminder2-hint';
    reminder2Hint.style.cssText = `
        margin-top: 6px;
        font-size: 12px;
        color: var(--o-brand-odoo, #714B67);
    `;

    reminder2Container.appendChild(reminder2Label);
    reminder2Container.appendChild(reminder2Input);
    reminder2Container.appendChild(reminder2Hint);

    // Inline validation error for reminder ordering
    const reminderOrderError = document.createElement('div');
    reminderOrderError.id = 'reminder-order-error';
    reminderOrderError.style.cssText = `
        margin-top: 6px;
        font-size: 12px;
        color: #fca5a5; /* soft red */
        display: none;
    `;
    reminder2Container.appendChild(reminderOrderError);

    dateContainer.appendChild(startDateContainer);
    dateContainer.appendChild(endDateContainer);
    dateContainer.appendChild(reminder1Container);
    dateContainer.appendChild(reminder2Container);

    // Email section (To, CC)
    const emailSection = document.createElement('div');
    emailSection.style.cssText = `
        margin-top: 16px;
        padding-top: 12px;
        border-top: 1px solid rgba(255, 255, 255, 0.12);
    `;

    const emailTitle = document.createElement('div');
    emailTitle.textContent = 'Email Notifications';
    emailTitle.style.cssText = `
        font-weight: 600;
        margin-bottom: 10px;
        color: #e5e7eb;
    `;

    const toContainer = document.createElement('div');
    toContainer.style.cssText = `
        margin-bottom: 10px;
    `;
    const toLabel = document.createElement('label');
    toLabel.textContent = 'To:';
    toLabel.style.cssText = `
        display: block; margin-bottom: 6px; font-weight: 500; font-size: 14px; color: #374151;
    `;
    const toInput = document.createElement('input');
    toInput.type = 'text';
    toInput.id = 'email-to-input';
    toInput.placeholder = 'e.g., user1@example.com, user2@example.com';
    toInput.style.cssText = `
        width: 100%; padding: 10px 12px; border: 1px solid rgba(0, 0, 0, 0.15); border-radius: 10px;
        background: #ffffff; color: #111827; font-size: 14px;
    `;
    toContainer.appendChild(toLabel);
    toContainer.appendChild(toInput);

    const ccContainer = document.createElement('div');
    ccContainer.style.cssText = `
        margin-bottom: 4px;
    `;
    const ccLabel = document.createElement('label');
    ccLabel.textContent = 'CC:';
    ccLabel.style.cssText = `
        display: block; margin-bottom: 6px; font-weight: 500; font-size: 14px; color: #374151;
    `;
    const ccInput = document.createElement('input');
    ccInput.type = 'text';
    ccInput.id = 'email-cc-input';
    ccInput.placeholder = 'e.g., cc1@example.com';
    ccInput.style.cssText = `
        width: 100%; padding: 10px 12px; border: 1px solid rgba(0, 0, 0, 0.15); border-radius: 10px;
        background: #ffffff; color: #111827; font-size: 14px;
    `;
    ccContainer.appendChild(ccLabel);
    ccContainer.appendChild(ccInput);

    // Focus states for email inputs
    ;[toInput, ccInput].forEach((el) => {
        el.addEventListener('focus', function() {
            this.style.border = '1px solid rgba(113, 75, 103, 0.6)';
            this.style.boxShadow = '0 0 0 3px rgba(113, 75, 103, 0.2)';
        });
        el.addEventListener('blur', function() {
            this.style.border = '1px solid rgba(0, 0, 0, 0.15)';
            this.style.boxShadow = 'none';
        });
    });

    emailSection.appendChild(emailTitle);
    emailSection.appendChild(toContainer);
    emailSection.appendChild(ccContainer);
    dateContainer.appendChild(emailSection);

    // Prepare reference for Save button to avoid TDZ when used inside validators
    let saveButton = null;

    // Update preview hints when inputs change
    const updateReminderHints = () => {
        const endVal = endDateInput.value;
        const r1 = reminder1Input.value;
        const r2 = reminder2Input.value;
        const d1 = computeReminderDisplay(endVal, r1);
        const d2 = computeReminderDisplay(endVal, r2);
        reminder1Hint.textContent = d1 ? `Will remind on: ${d1}` : '';
        reminder2Hint.textContent = d2 ? `Will remind on: ${d2}` : '';

        // Validate: Reminder 2 must be LESS than Reminder 1
        const n1 = parseInt(r1, 10);
        const n2 = parseInt(r2, 10);
        const bothNums = !isNaN(n1) && !isNaN(n2);
        if (bothNums && n2 >= n1) {
            reminderOrderError.textContent = 'Reminder 2 must be less than Reminder 1';
            reminderOrderError.style.display = 'block';
            reminder2Input.style.border = '1px solid rgba(239, 68, 68, 0.7)';
            if (saveButton) {
                saveButton.disabled = true;
                saveButton.title = 'Reminder 2 must be less than Reminder 1';
                saveButton.style.opacity = '0.7';
                saveButton.style.cursor = 'not-allowed';
            }
        } else {
            reminderOrderError.textContent = '';
            reminderOrderError.style.display = 'none';
            reminder2Input.style.border = '1px solid rgba(255, 255, 255, 0.18)';
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.title = '';
                saveButton.style.opacity = '';
                saveButton.style.cursor = 'pointer';
            }
        }
    };
    [endDateInput, reminder1Input, reminder2Input].forEach((el) => {
        el.addEventListener('input', updateReminderHints);
        el.addEventListener('change', updateReminderHints);
        // Subtle focus styling for professional feel
        el.addEventListener('focus', function() {
            this.style.border = '1px solid rgba(59, 130, 246, 0.6)';
            this.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.25)';
        });
        el.addEventListener('blur', function() {
            this.style.border = '1px solid rgba(255, 255, 255, 0.18)';
            this.style.boxShadow = 'none';
        });
    });
    // Initialize hints with current values (from extraction or user)
    updateReminderHints();

    // Create button container
    const buttonContainer = document.createElement('div');
    buttonContainer.style.cssText = `
        display: flex;
        gap: 12px;
        justify-content: center;
        margin-top: 18px;
    `;

    // Create Edit button
    const editButton = document.createElement('button');
    editButton.id = 'ai-date-edit';
    editButton.style.cssText = `
        padding: 10px 18px;
        background: transparent;
        color: var(--o-brand-odoo, #714B67);
        border: 1px solid var(--o-brand-odoo, #714B67);
        border-radius: 10px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s ease;
    `;
    editButton.innerHTML = 'Edit';

    // Create Save button
    saveButton = document.createElement('button');
    saveButton.id = 'ai-date-save';
    saveButton.style.cssText = `
        padding: 10px 18px;
        background: var(--o-brand-odoo, #714B67);
        color: #ffffff;
        border: none;
        border-radius: 10px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 6px 18px rgba(113, 75, 103, 0.35);
    `;
    saveButton.innerHTML = 'Save';

    // Add hover effects
    editButton.addEventListener('mouseenter', function() {
        this.style.background = 'rgba(113, 75, 103, 0.06)';
        this.style.transform = 'translateY(-1px)';
    });
    editButton.addEventListener('mouseleave', function() {
        this.style.background = 'transparent';
        this.style.transform = 'translateY(0)';
    });

    saveButton.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-1px)';
        this.style.boxShadow = '0 8px 22px rgba(113, 75, 103, 0.45)';
    });
    saveButton.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
        this.style.boxShadow = '0 6px 18px rgba(113, 75, 103, 0.35)';
    });

    // Add event listeners
    editButton.addEventListener('click', function() {
        // Enable editing mode
        startDateInput.disabled = false;
        endDateInput.disabled = false;
        startDateInput.style.background = 'rgba(255, 255, 255, 0.2)';
        endDateInput.style.background = 'rgba(255, 255, 255, 0.2)';
        startDateInput.focus();
    });

    saveButton.addEventListener('click', async function() {
        // Hard validation: Reminder 2 must be less than Reminder 1
        const n1 = parseInt(reminder1Input.value, 10);
        const n2 = parseInt(reminder2Input.value, 10);
        if (!isNaN(n1) && !isNaN(n2) && n2 >= n1) {
            reminderOrderError.textContent = 'Reminder 2 must be less than Reminder 1';
            reminderOrderError.style.display = 'block';
            reminder2Input.focus();
            return; // block save
        }

        // If filename changed, persist it to documents.document and its attachment
        const newName = (fileNameInput.value || '').trim();
        if (_docId && newName && newName !== _fileName) {
            try {
                const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
                const rpc = async (model, method, args = [], kwargs = {}) => {
                    const body = { jsonrpc: '2.0', method: 'call', params: { model, method, args, kwargs } };
                    const res = await fetch('/web/dataset/call_kw', {
                        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                        body: JSON.stringify(body),
                    });
                    if (!res.ok) throw new Error('RPC HTTP error');
                    const data = await res.json();
                    if (data.error) throw new Error(data.error.message || 'RPC error');
                    return data.result;
                };
                // Update document name
                await rpc('documents.document', 'write', [[_docId], { name: newName }]);
                // Read attachment and update its name as well
                const info = await rpc('documents.document', 'read', [[_docId], ['attachment_id']]);
                const attId = (Array.isArray(info) && info[0] && Array.isArray(info[0].attachment_id) && info[0].attachment_id[0]) || 0;
                if (attId) {
                    await rpc('ir.attachment', 'write', [[attId], { name: newName }]);
                }
            } catch (e) {
                console.warn('Failed to rename document/attachment:', e);
            }
        }
        const finalStartDate = startDateInput.value;
        const finalEndDate = endDateInput.value;
        const reminder1 = reminder1Input.value;
        const reminder2 = reminder2Input.value;
        const emailTo = toInput.value;
        const emailCc = ccInput.value;
        
        console.log('Final values:', { 
            startDate: finalStartDate, 
            endDate: finalEndDate,
            reminder1_days_ago: reminder1,
            reminder2_days_ago: reminder2
        });
        
        // Compute reminder dates based on end date
        const toISO = (d) => d.toISOString().slice(0,10);
        const computeReminderDate = (endDateStr, daysAgoStr) => {
            if (!endDateStr) return '';
            const n = parseInt(daysAgoStr, 10);
            if (isNaN(n) || n < 0) return '';
            const d = new Date(endDateStr);
            d.setDate(d.getDate() - n);
            return toISO(d);
        };
        const reminder1Date = computeReminderDate(finalEndDate, reminder1);
        const reminder2Date = computeReminderDate(finalEndDate, reminder2);

        // Try to create Odoo activities on the related document
        try {
            const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
            const rpc = async (model, method, args = [], kwargs = {}) => {
                const body = {
                    jsonrpc: '2.0',
                    method: 'call',
                    params: { model, method, args, kwargs },
                };
                const res = await fetch('/web/dataset/call_kw', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                    body: JSON.stringify(body),
                });
                if (!res.ok) throw new Error('RPC HTTP error');
                const data = await res.json();
                if (data.error) throw new Error(data.error.message || 'RPC error');
                return data.result;
            };

            // Get latest uploaded document via its attachment (same heuristic used for extraction)
            const attachments = await rpc(
                'ir.attachment',
                'search_read',
                [[['res_model', '=', 'documents.document']]],
                { fields: ['res_id', 'name'], limit: 1, order: 'create_date desc' }
            );
            const last = attachments && attachments[0];
            const docId = last?.res_id;
            // Resolve ir.model id for documents.document (mail.activity needs res_model_id on newer Odoo)
            let resModelId = 0;
            try {
                const modelIds = await rpc('ir.model', 'search', [[['model', '=', 'documents.document']]], { limit: 1 });
                resModelId = Array.isArray(modelIds) ? (modelIds[0] || 0) : (modelIds || 0);
            } catch(e) {
                console.warn('Could not resolve ir.model id for documents.document');
            }

            if (docId) {
                // Get a default activity type (To Do)
                const typeIds = await rpc('mail.activity.type', 'search', [[['name', '=', 'To Do']]], { limit: 1 });
                const activityTypeId = (Array.isArray(typeIds) ? typeIds[0] : (typeIds || 0)) || 1;

                const activities = [];
                if (finalEndDate) {
                    activities.push({ date: finalEndDate, summary: 'End Date', note: `Contract/document end date: ${finalEndDate}` });
                }
                if (reminder1Date) {
                    activities.push({ date: reminder1Date, summary: `Reminder (${reminder1} days before)`, note: `Reminder ${reminder1} days before end date ${finalEndDate}` });
                }
                if (reminder2Date) {
                    activities.push({ date: reminder2Date, summary: `Reminder (${reminder2} days before)`, note: `Reminder ${reminder2} days before end date ${finalEndDate}` });
                }

                for (const act of activities) {
                    try {
                        await rpc('mail.activity', 'create', [[{
                            res_model_id: resModelId || undefined,
                            res_id: docId,
                            activity_type_id: activityTypeId,
                            summary: act.summary,
                            note: act.note,
                            date_deadline: act.date,
                        }]]);
                    } catch (e) {
                        console.error('Failed to create activity:', act, e);
                    }
                }
                if (activities.length) {
                    console.log(`Created ${activities.length} Odoo reminder activities for document ${docId}.`);
                }

                // Create persistent record in contract.reminder
                try {
                    const reminderId = await rpc('contract.reminder', 'create', [[{
                        document_id: docId,
                        start_date: finalStartDate || false,
                        end_date: finalEndDate || false,
                        reminder1_days: reminder1 ? parseInt(reminder1, 10) : 0,
                        reminder2_days: reminder2 ? parseInt(reminder2, 10) : 0,
                        email_to: emailTo || '',
                        email_cc: emailCc || '',
                    }]]);
                    console.log('Created contract.reminder record id:', reminderId);
                } catch (e) {
                    console.error('Failed to create contract.reminder record:', e);
                }
            } else {
                console.warn('Could not determine documents.document to attach reminders. Skipping activity creation.');
            }
        } catch (err) {
            console.error('Error while creating Odoo reminders:', err);
        }
        
        // Close popup (no backend changes)
        closeDateExtractionPopup();

        // Show toast notification: only single line text
        showOdooNotification('Saved Successfully', '', 'success', false);
    });

    // Assemble the popup
    content.appendChild(icon);
    content.appendChild(title);
    content.appendChild(closeBtn);
    content.appendChild(fileNameContainer);
    content.appendChild(dateContainer);
    buttonContainer.appendChild(editButton);
    buttonContainer.appendChild(saveButton);
    content.appendChild(buttonContainer);
    popup.appendChild(content);
    overlay.appendChild(popup);

    // Add to document
    document.body.appendChild(overlay);
    // Do not close on background click or Escape; only the cancel (X) button closes this popup

    // Removed auto-close timer as requested; popup will close only on cancel or explicit actions
}

// Function to close the date extraction popup
function closeDateExtractionPopup() {
    const popup = document.getElementById('ai-date-extraction-popup');
    if (popup) {
        popup.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => {
            popup.remove();
        }, 300);
    }
}

// Add fadeOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
`;
document.head.appendChild(style);

// Lightweight Odoo-styled toast utility
function showCMToast(title, message = '', type = 'info', duration = 4000) {
    // Ensure container
    let container = document.getElementById('cm-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'cm-toast-container';
        container.style.cssText = `
            position: fixed;
            top: 16px;
            right: 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            z-index: 10001;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }

    // Colors per type
    const colors = {
        success: { bar: '#10B981', shadow: 'rgba(16,185,129,0.25)' },
        info:    { bar: 'var(--o-brand-odoo, #714B67)', shadow: 'rgba(113,75,103,0.25)' },
        warning: { bar: '#F59E0B', shadow: 'rgba(245,158,11,0.25)' },
        error:   { bar: '#EF4444', shadow: 'rgba(239,68,68,0.25)' },
    };
    const c = colors[type] || colors.info;

    // Toast element
    const toast = document.createElement('div');
    toast.style.cssText = `
        pointer-events: auto;
        display: grid;
        grid-template-columns: auto 1fr auto;
        column-gap: 12px;
        align-items: start;
        background: #ffffff;
        color: #111827;
        border: 1px solid rgba(0,0,0,0.08);
        border-left: 4px solid ${c.bar};
        border-radius: 8px;
        padding: 12px 12px;
        box-shadow: 0 8px 24px ${c.shadow};
        min-width: 300px;
        max-width: 420px;
        animation: cmToastIn 180ms ease-out;
    `;

    const badge = document.createElement('div');
    badge.style.cssText = `
        width: 10px; height: 10px; margin-top: 6px; border-radius: 999px; background: ${c.bar};
    `;

    const body = document.createElement('div');
    const h = document.createElement('div');
    h.textContent = title || '';
    h.style.cssText = 'font-weight:600; font-size:14px; margin-bottom:2px; color:#111827;';
    const p = document.createElement('div');
    p.innerHTML = message || '';
    p.style.cssText = 'font-size:13px; color:#4b5563;';
    body.appendChild(h); body.appendChild(p);

    const close = document.createElement('button');
    close.type = 'button';
    close.setAttribute('aria-label', 'Close');
    close.innerHTML = '&times;';
    close.style.cssText = `
        border: none; background: transparent; color:#6b7280; font-size:18px; line-height:18px;
        padding: 0 4px; cursor: pointer; border-radius:6px; margin-left:6px;
    `;
    close.addEventListener('mouseenter', function(){ this.style.background = 'rgba(0,0,0,0.05)'; });
    close.addEventListener('mouseleave', function(){ this.style.background = 'transparent'; });

    close.addEventListener('click', () => remove());

    toast.appendChild(badge);
    toast.appendChild(body);
    toast.appendChild(close);
    container.appendChild(toast);

    // Auto remove
    const timer = setTimeout(() => remove(), duration);

    function remove() {
        clearTimeout(timer);
        toast.style.animation = 'cmToastOut 180ms ease-in forwards';
        setTimeout(() => toast.remove(), 180);
    }

    // Inject animations once
    if (!document.getElementById('cm-toast-animations')) {
        const s = document.createElement('style');
        s.id = 'cm-toast-animations';
        s.textContent = `
            @keyframes cmToastIn { from { opacity:0; transform: translateY(-6px) scale(0.98);} to {opacity:1; transform: translateY(0) scale(1);} }
            @keyframes cmToastOut { from { opacity:1; } to { opacity:0; transform: translateY(-6px) scale(0.98);} }
        `;
        document.head.appendChild(s);
    }
}

// Try to use Odoo's native notification service (WOWL) when available
function showOdooNotification(title, message = '', type = 'info', sticky = false, duration = 4000) {
    try {
        // Attempt to locate OWL env from the webclient root
        const candidates = [
            document.querySelector('.o_web_client'),
            document.body,
        ];
        let env = null;
        for (const el of candidates) {
            if (el && el.__owl__ && el.__owl__.app && el.__owl__.app.env) {
                env = el.__owl__.app.env;
                break;
            }
        }
        // Some builds expose debug handle
        if (!env && window.odoo && window.odoo.__WOWL_DEBUG__ && window.odoo.__WOWL_DEBUG__.root && window.odoo.__WOWL_DEBUG__.root.env) {
            env = window.odoo.__WOWL_DEBUG__.root.env;
        }
        // Use notification service if present
        if (env && env.services && env.services.notification && typeof env.services.notification.add === 'function') {
            env.services.notification.add(message || '', {
                title: title || '',
                type: type || 'info',
                sticky: !!sticky,
            });
            return;
        }
    } catch (e) {
        console.warn('Falling back to custom toast. Odoo notification service not available:', e);
    }
    // Fallback to custom toast
    showCMToast(title, message, type, sticky ? 0 : duration);
}

// Track upload state to prevent multiple popups
let uploadInProgress = false;
let popupShown = false;
let pageLoaded = false;

// Wait for page to be fully loaded before enabling popup detection
setTimeout(() => {
    pageLoaded = true;
    console.log("📄 Page fully loaded, popup detection enabled");
}, 2000);

// Removed generic listeners that triggered popup for any upload or any drop.
// Popup is now strictly controlled by:
// - Upload Contract menu (flag window._cmUploadContract)
// - Contract tab drop (action id check)

// Test functions - call these from browser console to test popup
window.testBeautifulAIPopup = createBeautifulAIPopup;
window.testExtractDates = extractDatesFromFile;
window.testDateExtractionPopup = showDateExtractionPopup;
console.log("🧪 Test functions available:");
console.log("  - window.testBeautifulAIPopup() - Test first popup");
console.log("  - window.testExtractDates() - Test FastAPI call");
console.log("  - window.testDateExtractionPopup('2024-01-01', '2024-12-31') - Test date extraction popup");
