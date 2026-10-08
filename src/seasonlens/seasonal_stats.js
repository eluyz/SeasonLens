/* Descriptive completed-year seasonality. Invented/public or private rows use the same pure API. */
(function (root) {
 'use strict';
 const common = root.SeasonLensScienceCommon || (typeof require === 'function' ? require('./science_common.js') : null);
 if (!common) throw Error('SeasonLensScienceCommon must load before seasonal statistics.');

 function rng(seed) {
  let state = seed >>> 0;
  return function () {
   state = (state + 0x6D2B79F5) >>> 0;
   let value = Math.imul(state ^ (state >>> 15), state | 1);
   value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
   return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
 }
 function previousMonth(key) {
  const year = Number(key.slice(0, 4)), month = Number(key.slice(5, 7));
  return String(month === 1 ? year - 1 : year).padStart(4, '0') + '-' + String(month === 1 ? 12 : month - 1).padStart(2, '0');
 }
 function finite(value) {
  if (value !== null && !Number.isFinite(value)) throw Error('Seasonal statistics exceed the supported numeric range.');
  return value;
 }
 function analyze(rows, options) {
  options = options || {};
  const {asOf, windowYears = 5, bootstrapReplicates = 1000, seed = 20261008} = options;
  if (![5, 10, 'all'].includes(windowYears)) throw Error('Seasonal windowYears must be 5, 10 or all.');
  if (!Number.isInteger(bootstrapReplicates) || bootstrapReplicates < 1 || bootstrapReplicates > 2000) throw Error('Bootstrap replicates must be an integer from 1 through 2000.');
  if (!Number.isInteger(seed) || seed < 0 || seed > 4294967295) throw Error('Bootstrap seed must be an unsigned 32-bit integer.');
  const visible = common.validateRows(rows, asOf);
  const cutoffYear = Number(asOf.slice(0, 4)), endYear = cutoffYear - 1;
  const completed = visible.filter(row => Number(row.date.slice(0, 4)) < cutoffYear);
  const startYear = windowYears === 'all' ? (completed.length ? Number(completed[0].date.slice(0, 4)) : cutoffYear) : cutoffYear - windowYears;
  if (startYear < 1) throw Error('The declared seasonal window starts before supported calendar year 1.');
  const yearCount = Math.max(0, endYear - startYear + 1);
  if (yearCount > 100) throw Error('Seasonal analysis supports at most 100 declared completed calendar years.');
  // Split by the declared calendar vector, never by whichever years have observations.
  const splitYear = startYear + Math.floor(yearCount / 2) - 1;
  const last = new Map();
  visible.forEach(row => last.set(row.date.slice(0, 7), row));
  const omissions = {futureRows: rows.length - visible.length, currentYearRows: visible.length - completed.length, missingMonthClose: 0, missingPreviousMonth: 0, nonpositiveMonthEndpoints: 0};
  const yearly = [];
  for (let year = startYear; year <= endYear; year++) {
   const returns = [];
   for (let month = 1; month <= 12; month++) {
    const key = String(year).padStart(4, '0') + '-' + String(month).padStart(2, '0');
    const current = last.get(key), previous = last.get(previousMonth(key));
    let change = null;
    if (!current) omissions.missingMonthClose++;
    else if (!previous) omissions.missingPreviousMonth++;
    else if (!(current.value > 0 && previous.value > 0)) omissions.nonpositiveMonthEndpoints++;
    else change = finite(common.pctChange(current.value, previous.value));
    returns.push(change);
   }
   yearly.push({year, returns});
  }
  const months = Array.from({length: 12}, (_, index) => {
   const values = yearly.map(row => row.returns[index]).filter(value => value !== null);
   const early = yearly.filter(row => row.year <= splitYear).map(row => row.returns[index]).filter(value => value !== null);
   const late = yearly.filter(row => row.year > splitYear).map(row => row.returns[index]).filter(value => value !== null);
   const leaveOut = values.length < 2 ? [] : values.map((_, omitted) => finite(common.mean(values.filter((_, i) => i !== omitted))));
   const positiveCount = values.filter(value => value > 0).length;
   return {month: index + 1, mean: finite(common.mean(values)), median: finite(common.quantile(values, .5)), yearCount: values.length,
    positiveCount, positiveFraction: values.length ? positiveCount / values.length : null,
    minimum: values.length ? Math.min(...values) : null, maximum: values.length ? Math.max(...values) : null,
    earlyMean: finite(common.mean(early)), earlyCount: early.length, lateMean: finite(common.mean(late)), lateCount: late.length,
    leaveOneOutMinimum: leaveOut.length ? Math.min(...leaveOut) : null, leaveOneOutMaximum: leaveOut.length ? Math.max(...leaveOut) : null,
    bootstrapLow: null, bootstrapHigh: null, bootstrapValidReplicates: 0,
    bootstrapReason: values.length < 8 ? 'At least 8 contributing completed years are required.' : null};
  });
  const eligible = months.filter(month => month.yearCount >= 8);
  if (eligible.length) {
   const random = rng(seed), samples = Array.from({length: 12}, () => []);
   for (let replicate = 0; replicate < bootstrapReplicates; replicate++) {
    const vector = [];
    while (vector.length < yearCount) {
     // Each draw is a contiguous two-year vector block; the final block is truncated.
     const start = Math.floor(random() * (yearCount - 1));
     vector.push(yearly[start].returns);
     if (vector.length < yearCount) vector.push(yearly[start + 1].returns);
    }
    eligible.forEach(month => {
     const values = vector.map(row => row[month.month - 1]).filter(value => value !== null);
     const average = finite(common.mean(values));
     if (average !== null) samples[month.month - 1].push(average);
    });
   }
   eligible.forEach(month => {
    const sample = samples[month.month - 1];
    month.bootstrapValidReplicates = sample.length;
    if (sample.length < .9 * bootstrapReplicates) month.bootstrapReason = 'Fewer than 90% of bootstrap replicates contain an observed monthly change.';
    else {
     month.bootstrapLow = finite(common.quantile(sample, .025));
     month.bootstrapHigh = finite(common.quantile(sample, .975));
    }
   });
  }
  return {asOf, windowYears, startYear, endYear, yearCount, splitYear,
   earlyYears: {startYear, endYear: splitYear}, lateYears: {startYear: splitYear + 1, endYear},
   months, yearly, omissions,
   bootstrap: {seed, replicates: bootstrapReplicates, blockLength: 2, confidence: .95,
    method: 'non-circular moving two-year block vectors', minimumContributors: 8,
    interpretation: 'Approximate percentile interval for the historical monthly mean, not a future-price interval or significance verdict.'}};
 }
 const api = {analyze};
 root.SeasonLensSeasonalStats = api;
 if (typeof module === 'object' && module.exports) module.exports = api;
})(typeof globalThis === 'object' ? globalThis : this);
