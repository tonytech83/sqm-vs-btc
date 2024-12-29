let priceChart = new Chart(
    document.getElementById("priceChart").getContext("2d"),
    {
      type: "line",
      data: {
        labels: [],
        datasets: [
          {
            backgroundColor: "rgba(247, 147, 26, 1.0)",
            label: "Ratio sqm Price vs. BTC Price",
            data: [],
            borderColor: "rgba(247, 147, 26, 1.0)",
            borderWidth: 2,
            fill: false,
          },
        ],
      },
      options: {
        scales: {
          x: {
            title: {
              display: true,
              text: "Time",
              color: "#D8DEE9",
              font: { size: 18 },
            },
            ticks: {
              color: "rgba(216, 222, 233, 1.0)",
              font: { size: 14 },
            },
            grid: { color: "rgba(216, 222, 233, 1.0)" },
          },
          y: {
            title: {
              display: true,
              text: "Ratio",
              color: "#D8DEE9",
              font: { size: 18 },
            },
            ticks: {
              color: "rgba(216, 222, 233, 1.0)",
              font: { size: 14 },
            },
            grid: { color: "rgba(216, 222, 233, 1.0)" },
            min: 0,
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
        priceChart.data.datasets[0].data = [];

        // Populate the chart with data from the JSON response
        data.forEach((entry) => {
          priceChart.data.labels.push(entry.date);
          priceChart.data.datasets[0].data.push(entry.ratio);
        });

        // Update the chart
        priceChart.update();
      });
  }

  // Update the chart every minute
  setInterval(updateCharts, 6000);