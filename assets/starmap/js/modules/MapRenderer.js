(function () {
    window.StarMapApp = window.StarMapApp || {};
    const { CelestialMath, CONSTELLATION_NAMES } = window.StarMapApp;

    class MapRenderer {
        constructor(containerId) {
            this.container = document.getElementById(containerId);
            this.currentMap = null;
        }

        createProjection(lat, lon, date, zoomScale) {
            const width = this.container.clientWidth;
            const height = this.container.clientHeight;
            const radius = Math.min(width, height) / 2;

            const jd = CelestialMath.dateToJD(date);
            const GST_deg = CelestialMath.jdToGST(jd);
            let LST_deg = (GST_deg + lon) % 360;
            if (LST_deg < 0) LST_deg += 360;

            return d3.geoStereographic()
                .rotate([-LST_deg, -lat, 0])
                .scale(radius * zoomScale)
                .clipAngle(90)
                .translate([0, 0]);
        }

        clearMap(backgroundColor) {
            d3.select(this.container).select('svg').remove();

            const width = this.container.clientWidth;
            const height = this.container.clientHeight;
            const radius = Math.min(width, height) / 2;

            const svg = d3.select(this.container)
                .append('svg')
                .attr('width', '100%')
                .attr('height', '100%')
                .style('background', backgroundColor);

            svg.append('defs')
                .append('clipPath')
                .attr('id', 'circle-clip')
                .append('circle')
                .attr('cx', 0)
                .attr('cy', 0)
                .attr('r', radius);

            this.currentMap = svg.append('g')
                .attr('clip-path', 'url(#circle-clip)')
                .attr('transform', `translate(${width / 2}, ${height / 2})`);

            return this.currentMap;
        }

        renderMilkyWay(projection, mwData) {
            if (!mwData) return;
            const path = d3.geoPath(projection);
            this.currentMap.append("path")
                .datum(mwData)
                .attr("d", path)
                .attr("class", "milky-way");
        }

        renderConstellationBorders(projection, bordersData) {
            if (!bordersData) return;
            const path = d3.geoPath(projection);
            this.currentMap.append("path")
                .datum(bordersData)
                .attr("d", path)
                .attr("class", "constellation-border");
        }

        renderGraticule(projection, color) {
            if (!d3.geoGraticule) return;
            const graticule = d3.geoGraticule().step([15, 10]);
            const path = d3.geoPath(projection);

            this.currentMap.append("path")
                .datum(graticule)
                .attr("d", path)
                .style("fill", "none")
                .style("stroke", color)
                .style("stroke-width", 0.5);
        }

        renderStars(projection, starsData, appearance, callbacks) {
            if (!starsData || !starsData.features) return;
            starsData.features.forEach(star => {
                const coords = star.geometry?.coordinates;
                if (!coords) return;
                const [x, y] = projection(coords);
                if (!x || !y) return;

                const magnitude = star.properties.mag;
                const size = Math.max(0.5, (3.5 - magnitude / 2) * appearance.sizeScale);
                const color = d3.color(CelestialMath.getStarColor(star.properties.bv || 0))
                    .brighter(appearance.brightness - 1);

                this.currentMap.append('circle')
                    .attr('cx', x).attr('cy', y).attr('r', size)
                    .style('fill', color).style('opacity', 0.9)
                    .style('cursor', 'pointer')
                    .on('mouseover', (e) => callbacks.onMouseOver(e, star))
                    .on('mouseout', () => callbacks.onMouseOut())
                    .on('click', (e) => {
                        e.stopPropagation();
                        callbacks.onClick(star);
                    });
            });
        }

        renderConstellations(projection, linesData, color) {
            if (!linesData || !linesData.features) return;
            const path = d3.geoPath(projection);
            linesData.features.forEach(lineFeature => {
                this.currentMap.append("path")
                    .datum(lineFeature)
                    .attr("d", path)
                    .style('stroke', color)
                    .style('stroke-width', 1)
                    .style('fill', 'none')
                    .style('opacity', 0.8);
            });
        }

        renderLabels(projection, data, options) {
            const { constellations, stars, planets, starnames } = data;
            const { labelLanguage, constellationColor, planetsColor, showPlanets, date } = options;

            if (constellations && constellations.features) {
                constellations.features.forEach(constellation => {
                    const coords = constellation.properties.display;
                    const [x, y] = projection(coords);
                    if (!x || !y) return;

                    let labelText;
                    const props = constellation.properties;
                    switch (labelLanguage) {
                        case 'en': labelText = props.name; break;
                        case 'ar': labelText = props.ar; break;
                        case 'es': labelText = props.es; break;
                        case 'de': labelText = props.de; break;
                        case 'fr': labelText = props.fr; break;
                        default: labelText = props.desig;
                    }

                    this.currentMap.append('text')
                        .attr('x', x).attr('y', y).attr('text-anchor', 'middle')
                        .style('fill', constellationColor)
                        .style('font-size', '12px').style('opacity', 0.7)
                        .text(labelText || props.desig);
                });
            }

            if (stars && stars.features) {
                stars.features.forEach(star => {
                    if (star.properties.mag > 2.5) return;
                    const [x, y] = projection(star.geometry.coordinates);
                    if (!x || !y) return;

                    const name = this.getTranslatedStarName(star, labelLanguage, starnames);
                    if (!name) return;

                    this.currentMap.append('text')
                        .attr('x', x).attr('y', y + 10)
                        .attr('text-anchor', 'middle')
                        .style('fill', 'rgba(255, 255, 255, 0.5)')
                        .style('font-size', '10px')
                        .style('pointer-events', 'none')
                        .text(name);
                });
            }

            if (planets && showPlanets) {
                const jd = CelestialMath.dateToJD(date);
                Object.values(planets).forEach(planet => {
                    if (planet.id === 'sol' || planet.id === 'ter' || !planet.elements) return;
                    const pos = CelestialMath.getPlanetPosition(planet, jd);
                    if (!pos) return;
                    const [x, y] = projection([pos.ra, pos.dec]);
                    if (!x || !y) return;

                    const name = planet[labelLanguage === 'default' ? 'en' : labelLanguage] || planet.name || planet.en;

                    this.currentMap.append('text')
                        .attr('x', x).attr('y', y - 10)
                        .attr('text-anchor', 'middle')
                        .style('fill', planetsColor)
                        .style('font-size', '11px')
                        .style('font-weight', 'bold')
                        .style('pointer-events', 'none')
                        .text(name);
                });
            }
        }

        getTranslatedStarName(star, language, starnames) {
            const id = star.id || star.properties.hip;
            const lang = language === 'default' ? 'en' : language;
            const data = starnames[id];
            if (!data) return null;
            return data[lang] || data.name || data.proper;
        }

        renderDSOs(projection, dsosData, color, callbacks) {
            if (!dsosData || !dsosData.features) return;
            dsosData.features.forEach(dso => {
                const coords = dso.geometry?.coordinates;
                if (!coords) return;
                const [x, y] = projection(coords);
                if (!x || !y) return;

                this.currentMap.append('circle')
                    .attr('cx', x).attr('cy', y).attr('r', 3)
                    .style('fill', color).style('opacity', 0.8)
                    .on('mouseover', (e) => callbacks.onMouseOver(e, dso))
                    .on('mouseout', () => callbacks.onMouseOut());
            });
        }

        renderPlanets(projection, planetsData, date, color, callbacks) {
            if (!planetsData) return;
            const jd = CelestialMath.dateToJD(date);

            Object.values(planetsData).forEach(planet => {
                if (planet.id === 'sol' || planet.id === 'ter' || !planet.elements) return;
                const pos = CelestialMath.getPlanetPosition(planet, jd);
                if (!pos) return;
                const [x, y] = projection([pos.ra, pos.dec]);
                if (!x || !y) return;

                this.currentMap.append('circle')
                    .attr('cx', x).attr('cy', y).attr('r', 5)
                    .style('fill', color)
                    .on('mouseover', (e) => callbacks.onMouseOver(e, planet))
                    .on('mouseout', () => callbacks.onMouseOut());
            });
        }
    }

    window.StarMapApp.MapRenderer = MapRenderer;
})();