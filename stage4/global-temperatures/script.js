// script.js — adds a clip‑path, bottom x‑axis, dashed 0‑line
(async function () {
  const margin = { top: 20, right: 20, bottom: 70, left: 60 };
  const width  = 960 - margin.left - margin.right;
  const height = 400 - margin.top - margin.bottom;

  /* ─── SVG scaffold ─────────────────────────────────────────────────── */
  const svg = d3.select('#chart')
    .append('svg')
    .attr('viewBox', [0, 0, width + margin.left + margin.right, height + margin.top + margin.bottom])
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);

  /* ─── Clip path so bars & line stay inside the plot area ─────────────── */
  svg.append('defs')
      .append('clipPath')
        .attr('id', 'plot‑clip')
      .append('rect')
        .attr('width',  width)
        .attr('height', height);

  /* ─── Data load & tidy ──────────────────────────────────────────────── */
  const raw = await d3.csv('temperatures.csv', d3.autoType);

  const data = raw
    .filter(d => Number.isFinite(d['J-D']))
    .map(d => ({ year: d.Year, value: d['J-D'] }));

  const domainX = d3.extent(data, d => d.year);
  const domainY = d3.extent(data, d => d.value);

  const x = d3.scaleLinear()
    .domain([domainX[0] - 0.5, domainX[1] + 0.5])
    .range([0, width]);

  const barWidth = x(domainX[0] + 1) - x(domainX[0]) - 1;

  const y = d3.scaleLinear()
    .domain([domainY[0], domainY[1]]).nice()
    .range([height, 0]);

  const color = d3.scaleSequential()
    .domain([domainY[1], domainY[0]])
    .interpolator(d3.interpolateRdBu);

  /* ─── Plotting groups (clipped!) ────────────────────────────────────── */
  const plotG = svg.append('g')
      .attr('clip-path', 'url(#plot‑clip)');

  /* ─── Bars ──────────────────────────────────────────────────────────── */
  const barsG = plotG.append('g').attr('class', 'bars');

  barsG.selectAll('rect')
      .data(data)
      .join('rect')
        .attr('x',  d => x(d.year))
        .attr('y',  d => y(Math.max(0, d.value)))
        .attr('height', d => Math.abs(y(d.value) - y(0)))
        .attr('width',  barWidth)
        .attr('fill',  d => color(d.value));

  /* ─── 5‑year running average line ───────────────────────────────────── */
  const running = data.map((d, i) => {
      const slice = data.slice(Math.max(0, i - 2), Math.min(data.length, i + 3));
      return { year: d.year, avg: d3.mean(slice, s => s.value) };
  });

  const line = d3.line()
      .x(d => x(d.year) + barWidth / 2)
      .y(d => y(d.avg));

  const linePath = plotG.append('path')
      .datum(running)
      .attr('class', 'running-average')
      .attr('fill', 'none')
      .attr('stroke', '#000')
      .attr('stroke-width', 2)
      .attr('d', line);

  /* ─── 0‑anomaly reference line ──────────────────────────────── */
  svg.append('line')
      .attr('class', 'zero-line')
      .attr('x1', 0)
      .attr('x2', width)
      .attr('y1', y(0))
      .attr('y2', y(0));

  /* ─── Axes ──────────────────────────────────────────────────────────── */
  const xAxisG = svg.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x).ticks(10).tickFormat(d3.format('d')));

  const yAxisG = svg.append('g')
      .attr('class', 'y-axis')
      .call(d3.axisLeft(y).ticks(6));

  /* ─── Zoom (x‑axis only) ───────────────────────────────────────────── */
  const zoom = d3.zoom()
      .scaleExtent([1, (domainX[1] - domainX[0]) / 10])
      .translateExtent([[0, 0], [width, height]])
      .extent([[0, 0], [width, height]])
      .on('zoom', zoomed);

  svg.append('rect')
      .attr('class', 'zoom-rect')
      .attr('width', width)
      .attr('height', height)
      .style('fill', 'none')
      .style('pointer-events', 'all')
      .call(zoom);

  function zoomed({ transform }) {
      const zx = transform.rescaleX(x);
      const bw = zx(domainX[0] + 1) - zx(domainX[0]) - 1;

      barsG.selectAll('rect')
          .attr('x', d => zx(d.year))
          .attr('width', bw);

      const newLine = d3.line()
          .x(d => zx(d.year) + bw / 2)
          .y(d => y(d.avg));
      linePath.attr('d', newLine);

      xAxisG.call(d3.axisBottom(zx).ticks(10).tickFormat(d3.format('d')));
  }

  /* ─── Color legend ─────────────────────────────────────── */
  const legendW = 200, legendH = 10;
  const legendG = svg.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${width - legendW - 20},${height + 40})`);

  const defs = svg.select('defs');               // reuse existing <defs>
  const gradient = defs.append('linearGradient')
      .attr('id', 'tempGradient');

  d3.range(0, 1.01, 0.01).forEach(t => {
      gradient.append('stop')
          .attr('offset', `${t * 100}%`)
          .attr('stop-color', color(domainY[0] + t * (domainY[1] - domainY[0])));
  });

  legendG.append('rect')
      .attr('width', legendW)
      .attr('height', legendH)
      .style('fill', 'url(#tempGradient)');

  const legendScale = d3.scaleLinear()
      .domain([domainY[0], domainY[1]])
      .range([0, legendW]);

  legendG.append('g')
      .attr('transform', `translate(0,${legendH})`)
      .call(d3.axisBottom(legendScale).ticks(5).tickFormat(d3.format('.1f')));

  legendG.append('text')
      .attr('x', legendW / 2)
      .attr('y', -5)
      .attr('text-anchor', 'middle')
      .text('Anomaly (°C)');
})();