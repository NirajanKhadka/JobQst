// Custom JavaScript for JobLens Dashboard

document.addEventListener('DOMContentLoaded', function() {
    // Function to make external links open in new tab
    function makeExternalLinksOpenInNewTab() {
        const tableContainer = document.querySelector('.dash-table-container');
        if (tableContainer) {
            const externalLinks = tableContainer.querySelectorAll('a[href]:not([href^="#"])');
            externalLinks.forEach(link => {
                link.setAttribute('target', '_blank');
                link.setAttribute('rel', 'noopener noreferrer');
            });
        }
    }

    // Run on initial load
    makeExternalLinksOpenInNewTab();

    // Run whenever the table updates (using MutationObserver)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                makeExternalLinksOpenInNewTab();
            }
        });
    });

    // Observe changes to the entire document body
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // Enhanced tooltip functionality for job summaries
    function enhanceTooltips() {
        const summaryLinks = document.querySelectorAll('a[href="#"]');
        summaryLinks.forEach(link => {
            if (link.textContent.includes('📋 Summary')) {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const title = link.getAttribute('title');
                    if (title) {
                        // Create a better looking popup
                        alert(title.replace(/\\n/g, '\n'));
                    }
                });
            }
        });
    }

    // Run tooltip enhancements
    enhanceTooltips();

    // Re-run when content changes
    const tooltipObserver = new MutationObserver(function() {
        enhanceTooltips();
    });

    tooltipObserver.observe(document.body, {
        childList: true,
        subtree: true
    });
});
