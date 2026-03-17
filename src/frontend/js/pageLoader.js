// Page Loader Utility
const PageLoader = {
    cache: {},
    
    async load(pageName) {
        try {
            // Check cache first
            if (this.cache[pageName]) {
                return this.cache[pageName];
            }
            
            // Fetch page content
            const response = await fetch(`pages/${pageName}.html`);
            if (!response.ok) {
                throw new Error(`Failed to load page: ${pageName}`);
            }
            
            const html = await response.text();
            this.cache[pageName] = html;
            return html;
        } catch (error) {
            console.error(`Error loading page ${pageName}:`, error);
            return `<div class="alert alert-danger">Failed to load page: ${pageName}</div>`;
        }
    },
    
    clearCache() {
        this.cache = {};
    }
};

// Make available globally
window.PageLoader = PageLoader;
