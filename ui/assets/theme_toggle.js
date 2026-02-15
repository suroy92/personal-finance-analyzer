// Clientside callbacks for theme toggling
// Registered in app.py via app.clientside_callback

window.dash_clientside = Object.assign({}, window.dash_clientside, {
    theme: {
        // Fires only on button click. Reads current theme from State, toggles it.
        toggle: function(n_clicks, currentTheme) {
            if (!n_clicks) {
                return window.dash_clientside.no_update;
            }
            var newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('pfa-theme', newTheme);
            return newTheme;
        },

        // Fires on page load (url change). Restores theme from localStorage.
        initTheme: function(pathname) {
            var saved = localStorage.getItem('pfa-theme') || 'light';
            document.documentElement.setAttribute('data-theme', saved);
            return saved;
        },

        // Updates the toggle button label when theme-store changes.
        updateButtonLabel: function(theme) {
            if (theme === 'dark') {
                return '☀️  Light Mode';
            }
            return '🌙  Dark Mode';
        },

        // Applies data-theme attribute whenever theme-store value changes.
        applyTheme: function(theme) {
            document.documentElement.setAttribute('data-theme', theme || 'light');
            return window.dash_clientside.no_update;
        }
    }
});
