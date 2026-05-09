(function () {
    window.StarMapApp = window.StarMapApp || {};

    const CONSTELLATION_NAMES = {
        "And": "Andromeda", "Ant": "Antlia", "Aps": "Apus", "Aqr": "Aquarius", "Aql": "Aquila", "Ara": "Ara", "Ari": "Aries", "Aur": "Auriga", "Boo": "Boötes", "Cae": "Caelum", "Cam": "Camelopardalis", "Cnc": "Cancer", "CVn": "Canes Venatici", "CMa": "Canis Major", "CMi": "Canis Minor", "Cap": "Capricornus", "Car": "Carina", "Cas": "Cassiopeia", "Cen": "Centaurus", "Cep": "Cepheus", "Cet": "Cetus", "Cha": "Chamaeleon", "Cir": "Circinus", "Col": "Columba", "Com": "Coma Berenices", "CrA": "Corona Australis", "CrB": "Corona Borealis", "Crv": "Corvus", "Crt": "Crater", "Cru": "Crux", "Cyg": "Cygnus", "Del": "Delphinus", "Dor": "Dorado", "Dra": "Draco", "Equ": "Equuleus", "Eri": "Eridanus", "For": "Fornax", "Gem": "Gemini", "Gru": "Grus", "Her": "Hercules", "Hor": "Horologium", "Hya": "Hydra", "Hyi": "Hydrus", "Ind": "Indus", "Lac": "Lacerta", "Leo": "Leo", "LMi": "Leo Minor", "Lep": "Lepus", "Lib": "Libra", "Lup": "Lupus", "Lyn": "Lynx", "Lyr": "Lyra", "Men": "Mensa", "Mic": "Microscopium", "Mon": "Monoceros", "Mus": "Musca", "Nor": "Norma", "Oct": "Octans", "Oph": "Ophiuchus", "Ori": "Orion", "Pav": "Pavo", "Peg": "Pegasus", "Per": "Perseus", "Phe": "Phoenix", "Pic": "Pictor", "Psc": "Pisces", "PsA": "Piscis Austrinus", "Pup": "Puppis", "Pyx": "Pyxis", "Ret": "Reticulum", "Sge": "Sagitta", "Sgr": "Sagittarius", "Sco": "Scorpius", "Scl": "Sculptor", "Sct": "Scutum", "Ser": "Serpens", "Sex": "Sextans", "Tau": "Taurus", "Tel": "Telescopium", "Tri": "Triangulum", "TrA": "Triangulum Australe", "Tuc": "Tucana", "UMa": "Ursa Major", "UMi": "Ursa Minor", "Vel": "Vela", "Vir": "Virgo", "Vol": "Volans", "Vul": "Vulpecula"
    };

    class StarData {
        constructor() {
            this.data = {};
            this.dataUrls = {
                constellations: 'https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/constellations.json',
                lines: 'https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/constellations.lines.json',
                stars: 'https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/stars.6.json',
                dsos: 'https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/dsos.bright.json',
                starnames: 'https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/starnames.json',
                planets: 'https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/planets.json',
                mw: 'https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/mw.json',
                constellationBorders: 'https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/constellations.borders.json',
                dsonames: 'https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/dsonames.json'
            };
        }

        async load() {
            const dataPromises = Object.entries(this.dataUrls).map(([key, url]) =>
                fetch(url).then(r => r.json()).then(d => [key, d])
            );
            this.data = Object.fromEntries(await Promise.all(dataPromises));
            return this.data;
        }

        getTranslatedName(id, type, language, data) {
            const lang = language === 'default' ? 'en' : language;

            if (type === 'star') {
                const starData = data.starnames[id];
                if (!starData) return null;
                return starData[lang] || starData.name || starData.proper;
            } else if (type === 'planet') {
                const planetData = data.planets[id] || Object.values(data.planets).find(p => p.id === id || p.name === id);
                if (!planetData) return id;
                return planetData[lang] || planetData.name || planetData.en;
            }
            return id;
        }
    }

    window.StarMapApp.CONSTELLATION_NAMES = CONSTELLATION_NAMES;
    window.StarMapApp.StarData = StarData;
})();