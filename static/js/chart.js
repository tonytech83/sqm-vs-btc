// Each series reads one value from a data row.
const SERIES = {
  btc: { label: "BTC Price (€)", color: "rgba(247, 147, 26, 1.0)", value: (r) => r.btc },
  sqm: { label: "SQM Price (€)", color: "rgba(163, 190, 140, 1.0)", value: (r) => r.sqm },
  ratio: { label: "Ratio SQM / BTC", color: "rgba(54, 162, 235, 1.0)", value: (r) => r.ratio },
  m2: { label: "m² per 1 BTC", color: "rgba(180, 142, 173, 1.0)", value: (r) => r.btc / r.sqm },
};

// Each tab shows one or two series. With two, the second gets its own right-hand axis,
// unless `rebase` puts both on one axis as growth from the first day (= 100).
const VIEWS = {
  btc: { series: ["btc"] },
  sqm: { series: ["sqm"] },
  ratio: { series: ["ratio"] },
  m2: { series: ["m2"] },
  btcRatio: { series: ["btc", "ratio"] },
  sqmRatio: { series: ["sqm", "ratio"] },
  growth: { series: ["btc", "sqm"], rebase: true },
};

const TEXT_COLOR = "rgba(216, 222, 233, 1.0)";
const GRID_COLOR = "rgba(216, 222, 233, 0.3)";

let rows = [];
let currentView = "btc";
let currentRange = "all";

const chart = new Chart(document.getElementById("priceChart").getContext("2d"), {
  type: "line",
  data: { labels: [], datasets: [] },
  options: {},
});

function rowsInRange() {
  if (currentRange === "all" || rows.length === 0) return rows;
  const last = new Date(rows[rows.length - 1].date);
  const cutoff = new Date(last);
  cutoff.setDate(cutoff.getDate() - Number(currentRange));
  return rows.filter((r) => new Date(r.date) >= cutoff);
}

function axis(position, title, color, drawGrid) {
  return {
    position,
    title: { display: true, text: title, color: TEXT_COLOR, font: { size: 16 } },
    ticks: { color, font: { size: 13 } },
    grid: drawGrid ? { color: GRID_COLOR } : { drawOnChartArea: false },
  };
}

function render() {
  const view = VIEWS[currentView];
  const visible = rowsInRange();

  const datasets = view.series.map((key, i) => {
    const s = SERIES[key];
    let values = visible.map(s.value);
    if (view.rebase && values.length) {
      const first = values[0];
      values = values.map((v) => (v / first) * 100);
    }
    return {
      label: s.label,
      data: values,
      borderColor: s.color,
      backgroundColor: s.color.replace("1.0)", "0.2)"),
      borderWidth: 2,
      pointRadius: 0,
      yAxisID: i === 0 || view.rebase ? "y" : "y1",
    };
  });

  const first = SERIES[view.series[0]];
  const scales = {
    x: {
      ticks: { color: TEXT_COLOR, font: { size: 13 }, maxTicksLimit: 12 },
      grid: { color: GRID_COLOR },
    },
    y: view.rebase
      ? axis("left", "Growth (first day = 100)", TEXT_COLOR, true)
      : axis("left", first.label, first.color, true),
  };
  if (view.series.length > 1 && !view.rebase) {
    const second = SERIES[view.series[1]];
    scales.y1 = axis("right", second.label, second.color, false);
  }

  chart.data.labels = visible.map((r) => r.date);
  chart.data.datasets = datasets;
  chart.options = {
    elements: { line: { tension: 0.3 } },
    interaction: { mode: "index", intersect: false },
    plugins: { legend: { labels: { color: TEXT_COLOR } } },
    scales,
  };
  chart.update();
}

function bindButtons(selector, onSelect) {
  const buttons = document.querySelectorAll(selector);
  buttons.forEach((button) =>
    button.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.toggle("active", b === button));
      onSelect(button.dataset.value);
      render();
    })
  );
}

bindButtons(".tab", (value) => (currentView = value));
bindButtons(".range", (value) => (currentRange = value));

function updateCharts() {
  fetch("/data")
    .then((response) => response.json())
    .then((data) => {
      // NUMERIC columns arrive as strings, so convert them to numbers once here.
      rows = data.map((e) => ({
        date: e.date,
        btc: Number(e.btc_price),
        sqm: Number(e.sqm_price),
        ratio: Number(e.ratio),
      }));
      render();
    });
}

// Call updateCharts immediately to load data on page load
updateCharts();

// Update the chart every minute
setInterval(updateCharts, 60000);
