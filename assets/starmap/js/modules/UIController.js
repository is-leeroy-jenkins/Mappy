(function () {
    window.StarMapApp = window.StarMapApp || {};

    class UIController {
        constructor(callbacks) {
            this.callbacks = callbacks;
            this.form = document.getElementById('inputForm');
            this.setupEventListeners();
        }

        setupEventListeners() {
            this.form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.callbacks.onSubmit();
            });

            document.getElementById('date').addEventListener('input', () => this.callbacks.onInputChange());

            document.querySelectorAll('.toggle-group input[type="checkbox"]').forEach(cb => {
                cb.addEventListener('input', () => this.callbacks.onInputChange());
            });

            ['starBrightness', 'starSize', 'zoomScale'].forEach(id => {
                document.getElementById(id).addEventListener('input', (e) => {
                    this.callbacks.onSliderChange(id, parseFloat(e.target.value));
                });
            });

            document.getElementById('labelLanguage').addEventListener('change', (e) => {
                this.callbacks.onLanguageChange(e.target.value);
            });

            document.getElementById('whatUpTonightBtn').addEventListener('click', () => this.callbacks.onWhatUpTonight());
            document.getElementById('playAnimationBtn').addEventListener('click', () => this.callbacks.onPlayAnimation());
            document.getElementById('pauseAnimationBtn').addEventListener('click', () => this.callbacks.onPauseAnimation());

            const dateInput = document.getElementById('date');
            const dateLabel = document.querySelector('label[for="date"]');
            if (dateLabel && dateInput) {
                dateLabel.addEventListener('click', () => {
                    try { dateInput.showPicker(); } catch (e) { }
                });
            }
        }

        getFormData() {
            const formData = new FormData(this.form);
            const options = {};
            for (let [key, value] of formData.entries()) {
                options[key] = value === 'on' ? true : value;
            }
            const checkboxes = this.form.querySelectorAll('input[type="checkbox"]');
            checkboxes.forEach(cb => {
                options[cb.name] = cb.checked;
            });
            return options;
        }

        setDateTime(date) {
            const year = date.getFullYear();
            const month = (date.getMonth() + 1).toString().padStart(2, '0');
            const day = date.getDate().toString().padStart(2, '0');
            const hours = date.getHours().toString().padStart(2, '0');
            const minutes = date.getMinutes().toString().padStart(2, '0');
            document.getElementById('date').value = `${year}-${month}-${day}T${hours}:${minutes}`;
        }

        getDateTime() {
            const dateStr = document.getElementById('date').value;
            const date = new Date(dateStr);
            if (isNaN(date)) throw new Error('Invalid date format.');
            return date;
        }

        updateLocationDisplay(lat, lon) {
            document.getElementById('selectedLocation').textContent = `${lat.toFixed(4)}°, ${lon.toFixed(4)}°`;
            document.getElementById('lat').textContent = lat.toFixed(4);
            document.getElementById('lon').textContent = lon.toFixed(4);
        }

        updateLSTDisplay(lst) {
            document.getElementById('lst').textContent = `${lst.toFixed(2)}h`;
            document.getElementById('locationInfo').classList.remove('hidden');
        }

        toggleLoading(show) {
            document.querySelector('.loading-overlay').classList.toggle('hidden', !show);
            document.querySelector('.generate-btn .btn-text').style.visibility = show ? 'hidden' : 'visible';
            document.querySelector('.generate-btn .spinner').classList.toggle('hidden', !show);
        }

        showError(message, elementId = 'locationError') {
            const errEl = document.getElementById(elementId);
            if (errEl) errEl.textContent = message;
        }

        setAnimationState(playing) {
            document.getElementById('playAnimationBtn').disabled = playing;
            document.getElementById('pauseAnimationBtn').disabled = !playing;
        }

        getTimeStep() {
            return document.getElementById('timeStep').value;
        }
    }

    window.StarMapApp.UIController = UIController;
})();