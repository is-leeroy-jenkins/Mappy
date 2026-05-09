(function () {
    window.StarMapApp = window.StarMapApp || {};
    const { CelestialMath } = window.StarMapApp;

    class ImageExporter {
        constructor(callbacks) {
            this.callbacks = callbacks;
            this.modal = document.getElementById('downloadModal');
            this.previewContainer = document.getElementById('canvasPreviewContainer');
            this.currentTemplate = 'clean';
            this.previewCanvas = null;
            this.setupEventListeners();
        }

        setupEventListeners() {
            const btn = document.getElementById('downloadBtn');
            const closeSpan = document.querySelector('.close-modal');
            const finalBtn = document.getElementById('finalDownloadBtn');
            const templates = document.querySelectorAll('.template-option');

            btn.addEventListener('click', () => {
                this.modal.classList.remove('hidden');
                const date = this.callbacks.getDateTime();
                document.getElementById('mapDateLabel').value = date.toLocaleDateString(undefined, {
                    year: 'numeric', month: 'long', day: 'numeric'
                });
                this.updatePreview();
            });

            closeSpan.addEventListener('click', () => this.modal.classList.add('hidden'));
            window.addEventListener('click', (e) => {
                if (e.target === this.modal) this.modal.classList.add('hidden');
            });

            templates.forEach(t => {
                t.addEventListener('click', (e) => {
                    templates.forEach(opt => opt.classList.remove('active'));
                    e.currentTarget.classList.add('active');
                    this.currentTemplate = e.currentTarget.dataset.template;

                    const bgInput = document.getElementById('templateBgColor');
                    const textInput = document.getElementById('templateTextColor');

                    if (this.currentTemplate === 'polaroid') {
                        bgInput.value = '#ffffff';
                        textInput.value = '#000000';
                    } else if (this.currentTemplate === 'poster') {
                        bgInput.value = '#0a0b17';
                        textInput.value = '#ffffff';
                    }

                    this.updatePreview();
                });
            });

            ['mapTitle', 'mapDateLabel', 'templateFont', 'templateBgColor', 'templateTextColor'].forEach(id => {
                document.getElementById(id).addEventListener('input', () => this.updatePreview());
            });

            finalBtn.addEventListener('click', () => this.download());
        }

        updatePreview() {
            this.previewContainer.innerHTML = '';
            const title = document.getElementById('mapTitle').value;
            const subtitle = document.getElementById('mapDateLabel').value;
            const coordsText = document.getElementById('selectedLocation').textContent;
            const font = document.getElementById('templateFont').value;
            const bgColor = document.getElementById('templateBgColor').value;
            const textColor = document.getElementById('templateTextColor').value;

            const svgElement = document.getElementById('map').querySelector('svg');
            if (!svgElement) return;

            const { width, height } = svgElement.getBoundingClientRect();
            const mapDiameter = Math.min(width, height);
            const clonedSvg = svgElement.cloneNode(true);
            clonedSvg.setAttribute('width', width);
            clonedSvg.setAttribute('height', height);
            const svgData = new XMLSerializer().serializeToString(clonedSvg);
            const scale = 2;
            const baseDiameter = mapDiameter * scale;

            let finalWidth, finalHeight, mapCenterX, mapCenterY, mapRadius;
            if (this.currentTemplate === 'polaroid') {
                finalWidth = baseDiameter * 1.2;
                finalHeight = baseDiameter * 1.5;
                mapRadius = baseDiameter / 2;
                mapCenterX = finalWidth / 2;
                mapCenterY = finalWidth / 2;
            } else if (this.currentTemplate === 'poster') {
                finalWidth = baseDiameter * 1.2;
                finalHeight = baseDiameter * 1.6;
                mapRadius = baseDiameter / 2;
                mapCenterX = finalWidth / 2;
                mapCenterY = finalHeight * 0.4;
            } else {
                finalWidth = baseDiameter;
                finalHeight = baseDiameter;
                mapRadius = baseDiameter / 2;
                mapCenterX = finalWidth / 2;
                mapCenterY = finalHeight / 2;
            }

            const canvas = document.createElement('canvas');
            canvas.width = finalWidth;
            canvas.height = finalHeight;
            const ctx = canvas.getContext('2d');

            if (this.currentTemplate !== 'clean') {
                ctx.fillStyle = bgColor;
                ctx.fillRect(0, 0, finalWidth, finalHeight);
            }

            const img = new Image();
            img.onload = () => {
                ctx.save();
                ctx.beginPath();
                ctx.arc(mapCenterX, mapCenterY, mapRadius, 0, Math.PI * 2);
                ctx.closePath();
                ctx.clip();

                ctx.fillStyle = this.callbacks.getBackgroundColor();
                ctx.fillRect(mapCenterX - mapRadius, mapCenterY - mapRadius, mapRadius * 2, mapRadius * 2);

                const sX = (width - mapDiameter) / 2;
                const sY = (height - mapDiameter) / 2;

                ctx.drawImage(img, sX, sY, mapDiameter, mapDiameter,
                    mapCenterX - mapRadius, mapCenterY - mapRadius, mapRadius * 2, mapRadius * 2);
                ctx.restore();

                if (this.currentTemplate !== 'clean') {
                    ctx.textAlign = 'center';
                    ctx.fillStyle = textColor;

                    if (this.currentTemplate === 'polaroid') {
                        const textStartY = mapCenterY + mapRadius + (finalHeight * 0.05);
                        ctx.font = `bold ${baseDiameter * 0.06}px ${font}`;
                        ctx.fillText(title || "THE NIGHT SKY", mapCenterX, textStartY + (baseDiameter * 0.05));
                        ctx.fillStyle = CelestialMath.adjustColorOpacity(textColor, 0.7);
                        ctx.font = `${baseDiameter * 0.035}px ${font}`;
                        ctx.fillText(subtitle, mapCenterX, textStartY + (baseDiameter * 0.1));
                        ctx.fillText(coordsText, mapCenterX, textStartY + (baseDiameter * 0.14));
                    } else if (this.currentTemplate === 'poster') {
                        ctx.font = `300 ${baseDiameter * 0.1}px ${font}`;
                        if (font.includes('Montserrat')) ctx.letterSpacing = '5px';
                        ctx.fillText((title || "STARS").toUpperCase(), mapCenterX, finalHeight * 0.75);
                        ctx.beginPath();
                        ctx.moveTo(mapCenterX - 50, finalHeight * 0.78);
                        ctx.lineTo(mapCenterX + 50, finalHeight * 0.78);
                        ctx.strokeStyle = CelestialMath.adjustColorOpacity(textColor, 0.5);
                        ctx.stroke();
                        ctx.letterSpacing = '0px';
                        ctx.font = `${baseDiameter * 0.03}px ${font}`;
                        ctx.fillStyle = CelestialMath.adjustColorOpacity(textColor, 0.8);
                        ctx.fillText(subtitle, mapCenterX, finalHeight * 0.82);
                        ctx.fillText(coordsText, mapCenterX, finalHeight * 0.85);
                    }
                }

                this.previewContainer.appendChild(canvas);
                this.previewCanvas = canvas;
            };
            img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgData);
        }

        download() {
            if (!this.previewCanvas) return;
            const link = document.createElement('a');
            const timestamp = new Date().toISOString().slice(0, 10);
            link.download = `starmap-${this.currentTemplate}-${timestamp}.png`;
            link.href = this.previewCanvas.toDataURL('image/png');
            link.click();
        }
    }

    window.StarMapApp.ImageExporter = ImageExporter;
})();