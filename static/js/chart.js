let priceChart = new Chart(
  document.getElementById("priceChart").getContext("2d"),
  {
    type: "line",
    data: {
      labels: [], // Dates will go here
      datasets: [
        {
          label: "Ratio sqm price vs. BTC price",
          data: [], // Ratios will go here
          borderColor: "rgba(54, 162, 235, 1.0)",
          backgroundColor: "rgba(54, 162, 235, 0.2)",
          borderWidth: 2,
          yAxisID: "yRatio", // Bind to left Y-axis
        },
        {
          label: "BTC Price",
          data: [], // BTC prices will go here
          borderColor: "rgba(247, 147, 26, 1.0)",
          backgroundColor: "rgba(247, 147, 26, 0.2)",
          borderWidth: 2,
          yAxisID: "yPrice", // Bind to right Y-axis
        },
        {
          label: "SQM Price",
          data: [], // SQM prices will go here
          borderColor: "rgba(163, 190, 140, 1.0)",
          backgroundColor: "rgba(163, 190, 140, 0.2)",
          borderWidth: 2,
          yAxisID: "yPrice", // Bind to right Y-axis
        },
      ],
    },
    options: {
      elements: {
        line: {
          tension: 0.4, // Smooth lines
        },
      },
      scales: {
        x: {
          title: {
            display: true,
            text: "Date",
            color: "#D8DEE9",
            font: { size: 18 },
          },
          ticks: {
            color: "rgba(216, 222, 233, 1.0)",
            font: { size: 14 },
          },
          grid: { color: "rgba(216, 222, 233, 0.5)" },
        },
        yRatio: {
          position: "left",
          title: {
            display: true,
            text: "Ratio",
            color: "#D8DEE9",
            font: { size: 18 },
          },
          ticks: {
            color: "rgba(54, 162, 235, 1.0)",
            font: { size: 14 },
          },
          grid: { color: "rgba(216, 222, 233, 0.5)" },
        },
        yPrice: {
          position: "right",
          title: {
            display: true,
            text: "Price (€)",
            color: "#D8DEE9",
            font: { size: 18 },
          },
          ticks: {
            color: "rgba(247, 147, 26, 1.0)",
            font: { size: 14 },
          },
          grid: { drawOnChartArea: false }, // Don't overlap grids with left Y-axis
        },
      },
    },
  }
);

function updateCharts() {
  fetch("/data")
    .then((response) => response.json())
    .then((data) => {
      // Clear existing chart data
      priceChart.data.labels = [];
      priceChart.data.datasets[0].data = []; // Ratios
      priceChart.data.datasets[1].data = []; // BTC Prices
      priceChart.data.datasets[2].data = []; // SQM Prices

      // Populate the chart with data from the JSON response
      data.forEach((entry) => {
        priceChart.data.labels.push(entry.date);
        priceChart.data.datasets[0].data.push(entry.ratio);
        priceChart.data.datasets[1].data.push(entry.btc_price);
        priceChart.data.datasets[2].data.push(entry.sqm_price);
      });

      // Update the chart
      priceChart.update();
    });
}

// Call updateCharts immediately to load data on page load
updateCharts();

// Update the chart every minute
setInterval(updateCharts, 60000);