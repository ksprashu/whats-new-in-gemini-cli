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

    // Configure marked with syntax highlighting
    marked.setOptions({
        highlight: function (code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        }
    });

    // Helper loading states
    const toggleSidebarLoading = (isLoading) => {
        if (isLoading) {
            sidebarLoading.classList.remove('hidden');
            syncBtn.disabled = true;
            syncBtn.classList.add('opacity-50', 'cursor-not-allowed');
        } else {
            sidebarLoading.classList.add('hidden');
            syncBtn.disabled = false;
            syncBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    };

    const toggleContentLoading = (isLoading) => {
        if (isLoading) {
            contentLoading.classList.remove('hidden');
            markDoneBtn.disabled = true;
        } else {
            contentLoading.classList.add('hidden');
            // evaluate enable/disable later based on report status
        }
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

        return `
            <div class="${cardClasses}" data-id="${report.id}">
                ${checkmarkHtml}
                <div class="flex items-center gap-2">
                    <span class="${pillClass}">
                        ${report.version || 'v?.?.?'}
                    </span>
                    <span class="text-xs text-slate-500 dark:text-slate-400">${isDone ? 'Finished' : 'Pending'}</span>
                </div>
                <h3 class="${titleClass}">${report.title}</h3>
                <p class="text-sm text-slate-500 dark:text-slate-400 line-clamp-2">Click to view details and changelog breakdown.</p>
            </div>
        `;
    };

    const loadReportList = async (selectedId = null) => {
        try {
            toggleSidebarLoading(true);
            const res = await fetch(`${API_BASE}/reports`);
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

    const updateStatusDetails = (status) => {
        if (status === 'Done') {
            statusIndicator.className = 'ml-auto flex items-center gap-1 text-green-500 text-sm font-medium bg-green-500/10 px-2 py-1 rounded';
            statusIndicator.innerHTML = '<span class="material-symbols-outlined text-[16px]">check_circle</span> Done';
            markDoneBtn.disabled = true;
        } else {
            statusIndicator.className = 'ml-auto flex items-center gap-1 text-amber-500 text-sm font-medium bg-amber-500/10 px-2 py-1 rounded';
            statusIndicator.innerHTML = '<span class="material-symbols-outlined text-[16px]">pending</span> Pending';
            markDoneBtn.disabled = false;
        }
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
            const res = await fetch(`${API_BASE}/reports/${reportId}`);
            if (!res.ok) throw new Error('Report not found');
            const data = await res.json();

            // Populate content area
            reportTitle.textContent = data.title;
            reportVersion.textContent = data.version || 'v?.?.?';
            contentViewer.innerHTML = marked.parse(data.content);
            footerStatusText.textContent = `Reading ${data.title}`;

            updateStatusDetails(data.status);

            // Show content and footer
            contentContainer.classList.remove('hidden');
            actionFooter.classList.remove('hidden');

        } catch (error) {
            console.error('Failed to load report:', error);
            contentViewer.innerHTML = `<div class="text-red-500 p-4 border border-red-500 rounded bg-red-500/10">Failed to load report.</div>`;
            actionFooter.classList.add('hidden');
        } finally {
            toggleContentLoading(false);
        }
    };

    // Sync Action
    syncBtn.addEventListener('click', async () => {
        try {
            toggleSidebarLoading(true);
            const originalIconHtml = syncBtn.innerHTML;
            syncBtn.innerHTML = '<span class="material-symbols-outlined text-[20px] animate-spin">refresh</span><span>Syncing...</span>';

            const res = await fetch(`${API_BASE}/sync`, { method: 'POST' });
            if (!res.ok) throw new Error('Sync failed');

            await loadReportList(currentSelectedId); // Refresh list
        } catch (error) {
            console.error('Sync failed:', error);
            alert("Failed to sync with changelog. Please check backend.");
        } finally {
            syncBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">sync</span><span>Sync with Changelog</span>';
            toggleSidebarLoading(false);
        }
    });

    // Mark as done action
    markDoneBtn.addEventListener('click', async () => {
        if (!currentSelectedId) return;

        try {
            toggleContentLoading(true);
            const originalBtnHtml = markDoneBtn.innerHTML;
            markDoneBtn.innerHTML = '<span class="material-symbols-outlined animate-spin">refresh</span><span>Saving...</span>';

            const res = await fetch(`${API_BASE}/reports/${currentSelectedId}/done`, { method: 'POST' });
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

    // Initial load
    loadReportList();
});
