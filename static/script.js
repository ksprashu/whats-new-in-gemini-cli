/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const syncBtn = document.getElementById('sync-btn');
    const reportListContainer = document.getElementById('report-list');

    // Content Views
    const welcomeMessage = document.getElementById('welcome-message');
    const contentContainer = document.getElementById('content-container');
    const contentViewer = document.getElementById('content-viewer');
    const actionFooter = document.getElementById('action-footer');

    // Content Details
    const reportVersion = document.getElementById('report-version');
    const reportTitle = document.getElementById('report-title');
    const statusIndicator = document.getElementById('status-indicator');
    const markDoneBtn = document.getElementById('mark-done-btn');
    const footerStatusText = document.getElementById('footer-status-text');

    // Loaders
    const sidebarLoading = document.getElementById('sidebar-loading');
    const contentLoading = document.getElementById('content-loading');

    const API_BASE = '/api';
    let currentReports = [];
    let currentSelectedId = null;
    let currentMarkdownData = '';
    let currentViewMode = 'public'; // 'public' or 'admin'

    // DOM Elements for extra buttons
    const viewPublicBtn = document.getElementById('view-public');
    const viewAdminBtn = document.getElementById('view-admin');
    const fetchMoreBtn = document.getElementById('fetch-more-btn');

    // Authentication Helper
    const getAuthHeaders = () => {
        let headers = {};

        // Only attempt to attach auth if we are actually on the admin page
        if (window.location.pathname.includes('admin.html') || viewAdminBtn) {
            let apiKey = sessionStorage.getItem('ADMIN_API_KEY');
            if (!apiKey) {
                apiKey = prompt("Please enter the ADMIN_API_KEY to access restricted features:");
                if (apiKey) {
                    sessionStorage.setItem('ADMIN_API_KEY', apiKey);
                }
            }
            if (apiKey) {
                headers['Authorization'] = `Bearer ${apiKey}`;
            }
        }
        return headers;
    };

    // Configure marked with syntax highlighting
    marked.setOptions({
        highlight: function (code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        }
    });

    // Helper loading states
    const toggleSidebarLoading = (isLoading) => {
        const buttons = [syncBtn, fetchMoreBtn].filter(Boolean);
        if (isLoading) {
            if (sidebarLoading) sidebarLoading.classList.remove('hidden');
            buttons.forEach(btn => {
                btn.disabled = true;
                btn.classList.add('opacity-50', 'cursor-not-allowed');
            });
        } else {
            if (sidebarLoading) sidebarLoading.classList.add('hidden');
            buttons.forEach(btn => {
                btn.disabled = false;
                btn.classList.remove('opacity-50', 'cursor-not-allowed');
            });
        }
    };

    const toggleContentLoading = (isLoading) => {
        if (isLoading) {
            contentLoading.classList.remove('hidden');
            if (markDoneBtn) markDoneBtn.disabled = true;
        } else {
            contentLoading.classList.add('hidden');
        }
    };

    const getFeatureStatusHtml = (status) => {
        if (status === 'Experimental') {
            return `<span class="inline-flex items-center gap-1 bg-purple-500/10 text-purple-600 dark:bg-purple-500/20 dark:text-purple-400 border border-purple-500/20 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
                        <span class="material-symbols-outlined text-[12px]">science</span> Experimental
                    </span>`;
        }
        return `<span class="inline-flex items-center gap-1 bg-green-500/10 text-green-600 dark:bg-green-500/20 dark:text-green-400 border border-green-500/20 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
                    <span class="material-symbols-outlined text-[12px]">check_circle</span> Available
                </span>`;
    };

    const renderReportCard = (report) => {
        const isActive = currentSelectedId === report.id;
        const isDone = report.status === 'Done';

        // Tailwind Card Base Classes
        let cardClasses = 'group relative flex flex-col gap-2 p-4 rounded-xl cursor-pointer transition-all duration-200 border ';

        if (isActive) {
            cardClasses += 'bg-white dark:bg-surface-dark border-primary/50 shadow-md ring-1 ring-primary/20';
        } else {
            cardClasses += 'bg-transparent hover:bg-white dark:hover:bg-surface-dark border-transparent hover:border-gray-200 dark:hover:border-border-dark';
        }

        // Status pill classes inside card
        let pillClass = 'inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ';
        if (isActive) {
            pillClass += 'bg-primary/20 text-primary border border-primary/20';
        } else {
            pillClass += 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300';
        }

        // Title text classes
        let titleClass = 'text-base font-bold line-clamp-1 ';
        if (isActive) {
            titleClass += 'text-slate-900 dark:text-white';
        } else {
            titleClass += 'text-slate-700 dark:text-slate-200 group-hover:text-primary transition-colors font-medium';
        }

        // Card Checkmark or Active Dot indicator
        let checkmarkHtml = '';
        if (isDone) {
            checkmarkHtml = `
            <div class="absolute right-4 top-4 opacity-50">
                <span class="material-symbols-outlined text-[18px] text-slate-500">check_circle</span>
            </div>`;
        } else if (isActive) {
            checkmarkHtml = `
            <div class="absolute right-4 top-4">
                <div class="h-2 w-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
            </div>`;
        }

        const featureStatusHtml = getFeatureStatusHtml(report.feature_status);

        return `
            <div class="${cardClasses}" data-id="${report.id}">
                ${checkmarkHtml}
                <div class="flex items-center gap-2">
                    <span class="${pillClass}">
                        ${report.version || 'v?.?.?'}
                    </span>
                    <span class="text-xs text-slate-500 dark:text-slate-400 font-medium">
                        ${report.date || ''}
                    </span>
                    ${featureStatusHtml}
                </div>
                <h3 class="${titleClass}">${report.title}</h3>
                <p class="text-sm text-slate-500 dark:text-slate-400 line-clamp-2">Click to view details and changelog breakdown.</p>
            </div>
        `;
    };

    const loadReportList = async (selectedId = null) => {
        try {
            toggleSidebarLoading(true);
            const res = await fetch(`${API_BASE}/reports`, { headers: getAuthHeaders() });

            if (res.status === 401) {
                sessionStorage.removeItem('ADMIN_API_KEY');
                alert("Unauthorized or Token Expired. Please supply a valid ADMIN_API_KEY.");
                return;
            }
            currentReports = await res.json();

            if (selectedId) currentSelectedId = selectedId;

            reportListContainer.innerHTML = currentReports.map(renderReportCard).join('');

            // Attach Events
            const cards = reportListContainer.querySelectorAll('div[data-id]');
            cards.forEach(card => {
                card.addEventListener('click', () => {
                    loadReportContent(card.getAttribute('data-id'));
                });
            });

        } catch (error) {
            console.error('Failed to load reports:', error);
            reportListContainer.innerHTML = `<div class="p-4 text-sm text-red-500">Error loading reports. Backend might be down.</div>`;
        } finally {
            toggleSidebarLoading(false);
        }
    };

    const updateStatusDetails = (status, featureStatus) => {
        if (featureStatus === 'Experimental') {
            statusIndicator.className = 'ml-auto flex items-center gap-1 text-purple-600 dark:text-purple-400 text-sm font-bold uppercase tracking-wider bg-purple-500/10 border border-purple-500/20 px-3 py-1 rounded';
            statusIndicator.innerHTML = '<span class="material-symbols-outlined text-[18px]">science</span> Experimental';
        } else {
            statusIndicator.className = 'ml-auto flex items-center gap-1 text-green-600 dark:text-green-400 text-sm font-bold uppercase tracking-wider bg-green-500/10 border border-green-500/20 px-3 py-1 rounded';
            statusIndicator.innerHTML = '<span class="material-symbols-outlined text-[18px]">check_circle</span> Available';
        }

        if (markDoneBtn) {
            if (status === 'Done') {
                markDoneBtn.disabled = true;
                markDoneBtn.innerHTML = '<span class="material-symbols-outlined">done_all</span><span>Completed</span>';
                markDoneBtn.classList.add('bg-slate-300', 'text-slate-600');
                markDoneBtn.classList.remove('bg-primary', 'hover:bg-primary-dark', 'text-white');
            } else {
                markDoneBtn.disabled = false;
                markDoneBtn.innerHTML = '<span class="material-symbols-outlined">check</span><span>Mark as Done</span>';
                markDoneBtn.classList.remove('bg-slate-300', 'text-slate-600');
                markDoneBtn.classList.add('bg-primary', 'hover:bg-primary-dark', 'text-white');
            }
        }
    };

    const renderMarkdownView = () => {
        if (!currentMarkdownData) return;

        let markdownToRender = currentMarkdownData;

        // Remove hallucinatory "Version:" line completely
        markdownToRender = markdownToRender.replace(/^> \*\*Status:\*\*.*$/gm, '');

        const adminDelimiter = '<!-- === ADMIN === -->';
        const parts = markdownToRender.split(adminDelimiter);

        const publicHtml = marked.parse(parts[0] || '');

        contentViewer.innerHTML = publicHtml;

        if (currentViewMode === 'admin' && parts.length > 1) {
            const adminHtml = marked.parse(parts[1]);
            const adminContainer = document.createElement('div');
            adminContainer.className = 'mt-12 relative bg-amber-50 dark:bg-[#2c1c0d]/40 border border-amber-200 dark:border-amber-900/50 rounded-xl p-8 pt-10 shadow-sm';

            const badge = document.createElement('div');
            badge.className = 'absolute -top-4 left-6 bg-amber-500 text-white text-xs font-bold uppercase tracking-wider px-3 py-1.5 rounded-full shadow-sm flex items-center gap-1.5';
            badge.innerHTML = '<span class="material-symbols-outlined text-[14px]">admin_panel_settings</span> Admin Only';

            const contentWrapper = document.createElement('div');
            contentWrapper.className = 'prose prose-amber dark:prose-invert max-w-none prose-pre:bg-[#0d1117]/80';
            contentWrapper.innerHTML = adminHtml;

            adminContainer.appendChild(badge);
            adminContainer.appendChild(contentWrapper);
            contentViewer.appendChild(adminContainer);
        }
    };

    const updateViewToggleState = () => {
        if (currentViewMode === 'public') {
            viewPublicBtn.className = 'px-4 py-1.5 rounded-md bg-white dark:bg-surface-dark shadow-sm text-primary transition-all';
            viewAdminBtn.className = 'px-4 py-1.5 rounded-md text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-all';
        } else {
            viewAdminBtn.className = 'px-4 py-1.5 rounded-md bg-white dark:bg-surface-dark shadow-sm text-primary transition-all';
            viewPublicBtn.className = 'px-4 py-1.5 rounded-md text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-all';
        }
        renderMarkdownView();
    };


    const loadReportContent = async (reportId) => {
        if (!reportId) return;

        currentSelectedId = reportId;
        // Re-render sidebar to highlight active
        reportListContainer.innerHTML = currentReports.map(renderReportCard).join('');
        // Re-attach
        reportListContainer.querySelectorAll('div[data-id]').forEach(card => card.addEventListener('click', () => loadReportContent(card.getAttribute('data-id'))));

        toggleContentLoading(true);
        // Hide welcome message
        welcomeMessage.classList.add('hidden');

        try {
            const res = await fetch(`${API_BASE}/reports/${reportId}`, { headers: getAuthHeaders() });
            if (!res.ok) throw new Error('Report not found');
            const data = await res.json();

            // Populate content area
            reportTitle.textContent = data.title;
            reportVersion.textContent = data.version || 'v?.?.?';
            document.getElementById('report-date').textContent = data.date || '';
            currentMarkdownData = data.content;
            renderMarkdownView();

            if (footerStatusText) footerStatusText.textContent = `Reading ${data.title}`;

            updateStatusDetails(data.status, data.feature_status);

            // Show content and footer
            contentContainer.classList.remove('hidden');
            if (actionFooter) actionFooter.classList.remove('hidden');

        } catch (error) {
            console.error('Failed to load report:', error);
            contentViewer.innerHTML = `<div class="text-red-500 p-4 border border-red-500 rounded bg-red-500/10">Failed to load report.</div>`;
            if (actionFooter) actionFooter.classList.add('hidden');
        } finally {
            toggleContentLoading(false);
        }
    };

    // View Toggles
    if (viewPublicBtn) {
        viewPublicBtn.addEventListener('click', () => {
            if (currentViewMode !== 'public') {
                currentViewMode = 'public';
                updateViewToggleState();
            }
        });
    }

    if (viewAdminBtn) {
        viewAdminBtn.addEventListener('click', () => {
            if (currentViewMode !== 'admin') {
                currentViewMode = 'admin';
                updateViewToggleState();
            }
        });
    }

    // Sync Action
    if (syncBtn) {
        syncBtn.addEventListener('click', async () => {
            try {
                toggleSidebarLoading(true);
                const originalIconHtml = syncBtn.innerHTML;
                syncBtn.innerHTML = '<span class="material-symbols-outlined text-[20px] animate-spin">refresh</span><span>Syncing...</span>';

                const res = await fetch(`${API_BASE}/sync`, { method: 'POST', headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify({ fetch_more: false }) });
                if (!res.ok) throw new Error('Sync failed');

                await loadReportList(currentSelectedId); // Refresh list
            } catch (error) {
                console.error('Sync failed:', error);
                alert("Failed to sync with changelog. Please check backend.");
            } finally {
                syncBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">sync</span><span>Sync</span>';
                toggleSidebarLoading(false);
            }
        });
    }

    // Fetch More Action
    if (fetchMoreBtn) {
        fetchMoreBtn.addEventListener('click', async () => {
            try {
                toggleSidebarLoading(true);
                const originalIconHtml = fetchMoreBtn.innerHTML;
                fetchMoreBtn.innerHTML = '<span class="material-symbols-outlined text-[20px] animate-spin">refresh</span><span>Fetching...</span>';

                const res = await fetch(`${API_BASE}/sync`, { method: 'POST', headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify({ fetch_more: true }) });
                if (!res.ok) throw new Error('Fetch More failed');

                await loadReportList(currentSelectedId); // Refresh list
            } catch (error) {
                console.error('Fetch More failed:', error);
                alert("Failed to fetch more logs. Please check backend.");
            } finally {
                fetchMoreBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">download</span><span>Fetch More</span>';
                toggleSidebarLoading(false);
            }
        });
    }

    // Mark as done action
    if (markDoneBtn) {
        markDoneBtn.addEventListener('click', async () => {
            if (!currentSelectedId) return;

            try {
                toggleContentLoading(true);
                const originalBtnHtml = markDoneBtn.innerHTML;
                markDoneBtn.innerHTML = '<span class="material-symbols-outlined animate-spin">refresh</span><span>Saving...</span>';

                const res = await fetch(`${API_BASE}/reports/${currentSelectedId}/done`, { method: 'POST', headers: getAuthHeaders() });
                if (!res.ok) throw new Error('Failed to mark as done');

                // Reload list and stay on current report
                await loadReportList(currentSelectedId);
                await loadReportContent(currentSelectedId);
            } catch (error) {
                console.error('Failed to mark done:', error);
                alert('Failed to mark report as done.');
            } finally {
                markDoneBtn.innerHTML = '<span class="material-symbols-outlined">check</span><span>Mark as Done</span>';
                toggleContentLoading(false);
            }
        });
    }

    // Initial load
    loadReportList();
});
