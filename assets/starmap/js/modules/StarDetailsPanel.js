(function () {
    window.StarMapApp = window.StarMapApp || {};
    const { CelestialMath, CONSTELLATION_NAMES } = window.StarMapApp;

    class StarDetailsPanel {
        constructor(callbacks) {
            this.panel = document.getElementById('sidePanel');
            this.closeBtn = document.getElementById('closeSidePanel');
            this.callbacks = callbacks;
            this.setupEventListeners();
        }

        setupEventListeners() {
            this.closeBtn.addEventListener('click', () => this.close());
            window.addEventListener('click', (e) => {
                if (this.panel && !this.panel.contains(e.target) && !e.target.closest('circle')) {
                    this.close();
                }
            });
        }

        async show(star, language) {
            const hip = star.properties?.hip || star.id;
            const nameData = this.callbacks.getStarNames(hip);
            const properName = nameData?.name || nameData?.proper;
            const translatedName = this.callbacks.getTranslatedName(hip, 'star');
            const desig = nameData?.desig || star.properties?.desig || '';
            const con = nameData?.c || star.properties?.con || '';

            const fullName = translatedName || (desig ? `${desig} ${CONSTELLATION_NAMES[con] || con}` : `HIP ${hip}`);
            const searchName = properName || (desig ? `${desig} ${CONSTELLATION_NAMES[con] || con}` : fullName);

            this.panel.classList.remove('hidden');
            document.getElementById('starName').textContent = fullName;
            document.getElementById('starMagnitude').textContent = star.properties.mag != null ? star.properties.mag.toFixed(2) : '-';
            document.getElementById('starConstellation').textContent = CONSTELLATION_NAMES[con] || con || '-';

            const coords = star.geometry.coordinates;
            document.getElementById('starCoords').textContent = CelestialMath.formatCoords(coords[0], coords[1]);

            this.resetContent();

            try {
                const lang = language === 'default' ? 'en' : language;
                const data = await this.fetchWikipediaData(searchName, lang);
                if (data) {
                    document.getElementById('starSummary').textContent = data.extract;
                    if (data.thumbnail) {
                        const img = document.getElementById('starImage');
                        img.src = data.thumbnail.source;
                        img.classList.remove('hidden');
                        document.getElementById('starImagePlaceholder').classList.add('hidden');
                    }

                    const wikiLink = document.getElementById('wikiLink');
                    wikiLink.href = data.content_urls.desktop.page;
                    wikiLink.classList.remove('hidden');

                    this.extractDetails(data.extract);
                } else {
                    document.getElementById('starSummary').textContent = "No Wikipedia entry found for this star.";
                }
            } catch (error) {
                document.getElementById('starSummary').textContent = "Error fetching details from Wikipedia.";
            }
        }

        resetContent() {
            document.getElementById('starSummary').innerHTML = '<div class="spinner central"></div> Searching Wikipedia...';
            document.getElementById('starImage').classList.add('hidden');
            document.getElementById('starImagePlaceholder').classList.remove('hidden');
            document.getElementById('wikiLink').classList.add('hidden');
            document.getElementById('starDistance').textContent = '-';
        }

        async fetchWikipediaData(title, lang = 'en') {
            try {
                const response = await fetch(`https://${lang}.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title.replace(/ /g, '_'))}`);
                if (!response.ok) return null;
                return await response.json();
            } catch (e) {
                return null;
            }
        }

        extractDetails(summary) {
            const distMatch = summary.match(/(\d+(\.\d+)?)\s*(light-years|ly|parsecs|pc)/i);
            if (distMatch) {
                document.getElementById('starDistance').textContent = distMatch[0];
            }
        }

        close() {
            this.panel.classList.add('hidden');
        }
    }

    window.StarMapApp.StarDetailsPanel = StarDetailsPanel;
})();