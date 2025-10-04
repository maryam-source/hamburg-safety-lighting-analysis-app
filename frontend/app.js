// Configuration
const BACKEND_URL = "http://localhost:8000";

// Map initialization
const map = L.map("map").setView([53.55, 9.99], 12); // Hamburg

// Basemap
const osm = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors",
  maxZoom: 19,
}).addTo(map);

// Raster tile layer (COG overlay)
const rasterLayer = L.tileLayer(`${BACKEND_URL}/lighting/tiles/{z}/{x}/{y}.png`, {
  attribution: "Raster Lighting Data",
  maxZoom: 20,
  opacity: 0.7,
}).addTo(map);

rasterLayer.on("tileerror", (e) =>
  console.error("Raster tile error", e?.tile?.src || e)
);

// Histogram bins & color scale
const bins = [
  0, 0.002727, 0.005454, 0.008181, 0.010909, 0.013636, 0.016363, 0.01909,
  0.021817, 0.024544, 0.027272, 0.029999, 0.032726, 0.035453, 0.03818, 0.040907,
  0.043635, 0.046362, 0.049089, 0.051816, 0.054543, 0.05727, 0.059998, 0.062725,
  0.065452, 0.068179, 0.070906, 0.073633, 0.076361, 0.079088,
];

const colors = [
  "#FFEDA0", "#FED976", "#FEB24C", "#FD8D3C",
  "#FC4E2A", "#E31A1C", "#BD0026", "#800026",
];

function getColor(value) {
  if (value == null) return "#ffffff";
  for (let i = bins.length - 1; i >= 0; i--) {
    if (value >= bins[i]) return colors[i % colors.length];
  }
  return "#ffffff";
}

// Vector tile layer (auto-detect source-layer)
let detectedSourceLayer = null;

const vectorLayer = L.vectorGrid.protobuf(
  `${BACKEND_URL}/vector/tiles/{z}/{x}/{y}.pbf`,
  {
    vectorTileLayerStyles: {
      default: { color: "red", weight: 1, fill: false },
    },
    interactive: true,
  }
);

vectorLayer.on("tileload", (event) => {
  if (!detectedSourceLayer) {
    const vt = event.tile._tileLayer;
    const tiles = vt?._vectorTiles ?? {};
    const firstTile = Object.values(tiles)[0];
    const layers = Object.keys(firstTile?.layers ?? {});
    if (layers.length > 0) {
      detectedSourceLayer = layers[0];
      console.log("Detected vector source-layer:", detectedSourceLayer);

      vectorLayer.options.vectorTileLayerStyles = {
        [detectedSourceLayer]: (props) => ({
          fillColor: getColor(props?.mean_intensity ?? 0),
          fillOpacity: 0.6,
          color: "#333",
          weight: 0.4,
        }),
      };
      vectorLayer.redraw();
    }
  }
});

vectorLayer.on("mouseover", (e) => {
  const props = e.layer?.properties ?? e.properties;
  if (!props) return;
  const v = props.mean_intensity ?? "N/A";
  if (e.latlng) {
    L.popup({ closeButton: false, offset: [0, -10] })
      .setLatLng(e.latlng)
      .setContent(
        `Mean intensity: ${typeof v === "number" ? v.toPrecision(6) : v}`
      )
      .openOn(map);
  }
});
vectorLayer.on("mouseout", () => map.closePopup());
vectorLayer.on("click", (e) =>
  console.log("Vector feature:", e.layer?.properties ?? e.properties)
);
vectorLayer.on("tileerror", (e) =>
  console.warn("Vector tile missing:", e?.tile?.src || e)
);

// Leaflet Draw Control
const drawnItems = new L.FeatureGroup().addTo(map);
const drawControl = new L.Control.Draw({
  draw: { polygon: true, rectangle: false, polyline: false, circle: false, marker: false, circlemarker: false },
  edit: { featureGroup: drawnItems },
});
map.addControl(drawControl);

// Histogram chart
let histogramChart = new Chart(document.getElementById("histogram"), {
  type: "bar",
  data: { labels: [], datasets: [{ label: "Lighting Intensity Distribution", data: [], backgroundColor: "#0078d7" }] },
  options: {
    responsive: true,
    plugins: { tooltip: { callbacks: { label: (ctx) => `Count: ${ctx.raw}` } } },
    scales: { x: { title: { display: true, text: "Bins" } }, y: { type: "logarithmic", title: { display: true, text: "Count (log scale)" }, ticks: { callback: (v) => Number(v) } } },
  },
});

// Helper functions
function showLoading(isLoading) { document.getElementById("loading").style.display = isLoading ? "block" : "none"; }
function updateHistogram(binsStart, binsEnd, counts) {
  const labels = binsStart.map((start, i) => `${start.toPrecision(3)} - ${binsEnd[i].toPrecision(3)}`);
  histogramChart.data.labels = labels;
  histogramChart.data.datasets[0].data = counts;
  histogramChart.update();
}
async function fetchStats(geojson) {
  try {
    showLoading(true);
    document.getElementById("stats").innerHTML = "Loading stats...";
    const res = await fetch(`${BACKEND_URL}/lighting/stats?return_histogram=true&return_values=true`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ geojson }) });
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    const data = await res.json();
    showLoading(false);
    return data;
  } catch (err) {
    showLoading(false);
    console.error(err);
    document.getElementById("stats").innerHTML = "Error fetching stats.";
    return null;
  }
}
async function exportCSV(geojson) {
  try {
    const res = await fetch(`${BACKEND_URL}/lighting/export?return_histogram=true&return_values=true`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ geojson }) });
    if (!res.ok) throw new Error(`Export request failed: ${res.status}`);
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "lighting_stats.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) { console.error("CSV export error", err); }
}

// Polygon draw event
map.on(L.Draw.Event.CREATED, async (e) => {
  const layer = e.layer;
  drawnItems.clearLayers();
  drawnItems.addLayer(layer);

  const geojson = layer.toGeoJSON();
  const data = await fetchStats(geojson);
  if (!data) return;

  const vectorStats = data.vector_stats ?? {};
  const rasterStats = data.raster_stats ?? {};

  const statsHTML = `
    <h4>Vector Stats (grid)</h4>
    <p><b>Mean:</b> ${vectorStats.mean?.toPrecision(6) ?? "N/A"}</p>
    <p><b>Min:</b> ${vectorStats.min?.toPrecision(6) ?? "N/A"}</p>
    <p><b>Max:</b> ${vectorStats.max?.toPrecision(6) ?? "N/A"}</p>
    <p><b>Count:</b> ${vectorStats.count ?? "N/A"}</p>

    <h4>Raster Stats (clipped)</h4>
    <p><b>Mean:</b> ${rasterStats.mean?.toPrecision(6) ?? "N/A"}</p>
    <p><b>Min:</b> ${rasterStats.min?.toPrecision(6) ?? "N/A"}</p>
    <p><b>Max:</b> ${rasterStats.max?.toPrecision(6) ?? "N/A"}</p>
  `;
  document.getElementById("stats").innerHTML = statsHTML;

  if (rasterStats.histogram) updateHistogram(rasterStats.histogram.bins_start, rasterStats.histogram.bins_end, rasterStats.histogram.counts);
  else { histogramChart.data.labels = []; histogramChart.data.datasets[0].data = []; histogramChart.update(); }

  const exportBtn = document.getElementById("exportBtn");
  exportBtn.disabled = false;
  exportBtn.onclick = () => exportCSV(geojson);
});

// Layer control (no vector checkbox, vector still added to map)
const baseMaps = { OpenStreetMap: osm };
const overlayMaps = { "Raster Lighting": rasterLayer };
L.control.layers(baseMaps, overlayMaps).addTo(map);
vectorLayer.addTo(map); // vector grid still visible but not in control

// Legend (raster only)
const legend = L.control({ position: "bottomright" });
legend.onAdd = function () {
  const div = L.DomUtil.create("div", "legend");
  div.innerHTML = `
    <label><b>Raster Opacity</b></label><br>
    <input type="range" id="rasterOpacity" min="0" max="1" step="0.1" value="${rasterLayer.options.opacity}">
  `;
  return div;
};
legend.addTo(map);

document.addEventListener("input", (e) => {
  if (e.target.id === "rasterOpacity") rasterLayer.setOpacity(parseFloat(e.target.value));
});

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("stats").innerHTML = "Draw a polygon on the map to see results.";
  showLoading(false);
});
