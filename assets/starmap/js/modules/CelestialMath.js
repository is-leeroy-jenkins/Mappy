(function () {
    window.StarMapApp = window.StarMapApp || {};

    class CelestialMath {
        static dateToJD(date) {
            return date.getTime() / 86400000 + 2440587.5;
        }

        static jdToGST(jd) {
            const T = (jd - 2451545.0) / 36525.0;
            let GST = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T * T - T * T * T / 38710000.0;
            return (GST % 360 + 360) % 360;
        }

        static jdToLST(jd, lon) {
            const gst = this.jdToGST(jd);
            let lst = gst + lon;
            return (lst % 360 + 360) % 360;
        }

        static getPlanetPosition(planet, jd) {
            if (!planet.elements || planet.elements.length === 0) return null;
            const e = planet.elements[0];
            const d = (jd - 2451545.0) / 36525.0;

            const a = e.a + (e.da || 0) * d;
            const ecc = e.e + (e.de || 0) * d;
            const incl = (e.i + (e.di || 0) * d) * Math.PI / 180;
            const L = (e.L + (e.dL || 0) * d) % 360 * Math.PI / 180;
            const w = (e.W + (e.dW || 0) * d) * Math.PI / 180;
            const N = (e.N + (e.dN || 0) * d) * Math.PI / 180;

            const M = L - w;
            let E = M;
            for (let i = 0; i < 5; i++) E = M + ecc * Math.sin(E);

            const xv = a * (Math.cos(E) - ecc);
            const yv = a * (Math.sqrt(1.0 - ecc * ecc) * Math.sin(E));

            const v = Math.atan2(yv, xv);
            const r = Math.sqrt(xv * xv + yv * yv);

            const lon = v + w;
            const xeclip = r * (Math.cos(N) * Math.cos(lon) - Math.sin(N) * Math.sin(lon) * Math.cos(incl));
            const yeclip = r * (Math.sin(N) * Math.cos(lon) + Math.cos(N) * Math.sin(lon) * Math.cos(incl));
            const zeclip = r * (Math.sin(lon) * Math.sin(incl));

            const eps = 23.439 * Math.PI / 180;
            const xeq = xeclip;
            const yeq = yeclip * Math.cos(eps) - zeclip * Math.sin(eps);
            const zeq = yeclip * Math.sin(eps) + zeclip * Math.cos(eps);

            const ra = Math.atan2(yeq, xeq) * 180 / Math.PI;
            const dec = Math.atan2(zeq, Math.sqrt(xeq * xeq + yeq * yeq)) * 180 / Math.PI;

            return { ra: (ra + 360) % 360, dec: dec };
        }

        static formatCoords(ra, dec) {
            const raHours = Math.floor(ra / 15);
            const raMin = Math.floor((ra / 15 - raHours) * 60);
            const decDeg = Math.floor(dec);
            const decMin = Math.abs(Math.floor((dec - decDeg) * 60));
            return `${raHours}h ${raMin}m, ${decDeg}° ${decMin}'`;
        }

        static getStarColor(bv) {
            const t = 4600 * ((1 / (0.92 * bv + 1.7)) + (1 / (0.92 * bv + 0.62)));
            if (t < 3000) return '#ffcc99';
            if (t < 5000) return '#ffddae';
            if (t < 6000) return '#ffffd4';
            if (t < 8000) return '#ffffff';
            return '#cad8ff';
        }

        static adjustColorOpacity(hex, opacity) {
            let c;
            if (/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)) {
                c = hex.substring(1).split('');
                if (c.length == 3) {
                    c = [c[0], c[0], c[1], c[1], c[2], c[2]];
                }
                c = '0x' + c.join('');
                return 'rgba(' + [(c >> 16) & 255, (c >> 8) & 255, c & 255].join(',') + ',' + opacity + ')';
            }
            return hex;
        }
    }

    window.StarMapApp.CelestialMath = CelestialMath;
})();