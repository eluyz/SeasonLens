/* Fixed-model, observed-step walk-forward comparisons. No price forecasts are
   converted into trading claims or invented future session dates. */
(function (root, factory) {
 'use strict';
 const common = root.SeasonLensScienceCommon ||
  (typeof module === 'object' && module.exports ? require('./science_common.js') : null);
 const api = factory(common);
 root.SeasonLensForecasts = api;
 if (typeof module === 'object' && module.exports) module.exports = api;
})(globalThis, function (common) {
 'use strict';
 if (!common) throw Error('Forecast comparison requires the scientific common module.');
 const definitions = Object.freeze([
  {id:'naive', label:'Last observed price'},
  {id:'drift', label:'Expanding-history drift'},
  {id:'mean20', label:'Trailing 20-observation mean'}
 ]);
 function checked(value, purpose) {
  if (!Number.isFinite(value)) throw Error(purpose + ' exceeded the arithmetic range.');
  return value;
 }
 function integer(value, lower, upper, label) {
  if (!Number.isInteger(value) || value < lower || value > upper)
   throw Error(label + ' must be an integer from ' + lower + ' to ' + upper + '.');
  return value;
 }
 function rootMeanSquare(errors) {
  const scale = errors.reduce((maximum, error) => Math.max(maximum, Math.abs(error)), 0);
  if (!scale) return 0;
  return checked(Math.sqrt(common.mean(errors.map(error => (error / scale) ** 2))) * scale, 'RMSE');
 }
 function emptyHorizon(horizon, reason) {
  return {
   horizon, count:0, eligibleOriginCount:0, limitedOriginCount:0, reason,
   firstOriginDate:null, lastOriginDate:null, firstTargetDate:null, lastTargetDate:null,
   models:definitions.map(model => ({...model, count:0, mae:null, rmse:null, maeSkill:null, rmseSkill:null})),
   rows:[]
  };
 }
 function evaluate(input, options) {
  const opts = options || {};
  // Validation deliberately precedes selection, even for excluded future rows.
  const rows = common.validateRows(input, opts.asOf);
  const minTraining = integer(opts.minTraining === undefined ? 200 : opts.minTraining, 20, 20000, 'Minimum training observations');
  const maxOrigins = integer(opts.maxOrigins === undefined ? 252 : opts.maxOrigins, 1, 1000, 'Maximum evaluation origins');
  const horizons = opts.horizons === undefined ? [1,5,20] : opts.horizons;
  if (!Array.isArray(horizons) || !horizons.length || horizons.length > 3 ||
      horizons.some(horizon => ![1,5,20].includes(horizon)) || new Set(horizons).size !== horizons.length)
   throw Error('Forecast horizons must be distinct observed-step values selected from 1, 5 and 20.');
  const startDate = opts.startDate === undefined || opts.startDate === null ? null : opts.startDate;
  if (startDate !== null) {
   // The common validator also checks the calendar independently of the cutoff.
   common.validateRows([{date:startDate, value:0}], opts.asOf);
   if (startDate > opts.asOf) throw Error('Evaluation start date must not be after the analysis cutoff.');
  }
  const output = {asOf:opts.asOf, startDate, visibleCount:rows.length, minTraining, maxOrigins, horizons:[]};
  for (const horizon of horizons) {
   const eligible = [];
   for (let origin = minTraining - 1; origin + horizon < rows.length; origin++) {
    if (startDate !== null && (rows[origin].date < startDate || rows[origin+horizon].date < startDate)) continue;
    eligible.push(origin);
   }
   if (!eligible.length) {
    output.horizons.push(emptyHorizon(horizon,
     'No eligible origin and later target: need at least ' + (minTraining+horizon) +
     ' cutoff-visible observations and an origin inside the selected evaluation period.'));
    continue;
   }
   const chosen = eligible.slice(-maxOrigins), evaluated = [];
   try {
    for (const origin of chosen) {
     const current = rows[origin].value, actual = rows[origin+horizon].value;
     const predictions = {
      naive:current,
      // Includes the first and current quote, never an observation after origin.
      drift:checked(current + (current-rows[0].value) / origin * horizon, 'Drift prediction'),
      mean20:checked(common.mean(rows.slice(origin-19, origin+1).map(row => row.value)), 'Trailing mean prediction')
     };
     evaluated.push({originDate:rows[origin].date, targetDate:rows[origin+horizon].date, actual, predictions});
    }
    const models = definitions.map(model => {
     const errors = evaluated.map(row => checked(row.predictions[model.id]-row.actual, 'Prediction error'));
     return {...model, count:evaluated.length, mae:checked(common.mean(errors.map(Math.abs)), 'MAE'),
      rmse:rootMeanSquare(errors), maeSkill:null, rmseSkill:null};
    });
    const baseline = models[0];
    for (const model of models) {
     model.maeSkill = baseline.mae === 0 ? null : checked(1-model.mae/baseline.mae, 'MAE skill');
     model.rmseSkill = baseline.rmse === 0 ? null : checked(1-model.rmse/baseline.rmse, 'RMSE skill');
    }
    output.horizons.push({
     horizon, count:evaluated.length, eligibleOriginCount:eligible.length,
     limitedOriginCount:eligible.length-evaluated.length, reason:null,
     firstOriginDate:evaluated[0].originDate, lastOriginDate:evaluated[evaluated.length-1].originDate,
     firstTargetDate:evaluated[0].targetDate, lastTargetDate:evaluated[evaluated.length-1].targetDate,
     models, rows:evaluated
    });
   } catch (error) {
    // A numerical limitation affects all models for this horizon equally. The
    // dashboard can show the reason without silently dropping hard origins.
    const unavailable = emptyHorizon(horizon, 'Numerical comparison unavailable: ' + error.message);
    unavailable.eligibleOriginCount = eligible.length;
    unavailable.limitedOriginCount = eligible.length-chosen.length;
    output.horizons.push(unavailable);
   }
  }
  return output;
 }
 return Object.freeze({evaluate});
});
