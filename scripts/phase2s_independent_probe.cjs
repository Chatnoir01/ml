/**
 * Phase 2S independent cross-language ToySPN one-bit baseline.
 *
 * Node.js implementation independent of the Python baseline: own xorshift32
 * sampler, own 32-bit ToySPN, own feature counts, own train/held-out split.
 * Purpose: corroborate a structural trend, NOT prove cryptographic security.
 * Post-hoc, selected following the published Phase 2A-T results.
 */
"use strict";
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const ROOT = path.join(__dirname, "..");
const panelPath = path.join(ROOT, "src/adversarial_sbox/phase2a_candidates.py");
const keysPath = path.join(ROOT, "src/adversarial_sbox/neural_heterogeneity.py");
const resultPath = path.join(ROOT, "research/PHASE2AT_RESULT.md");
const PANEL_DIGEST = "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30";
const DEPTHS = [3, 4, 5], DELTAS = [1, 256];
const rotl = (x, n) => ((x << n) | (x >>> (32 - n))) >>> 0;

function sources() {
  const panelText = fs.readFileSync(panelPath, "utf8");
  assert.ok(panelText.includes(PANEL_DIGEST));
  const fingerprints = [...panelText.matchAll(/'fingerprint': '([0-9a-f]{64})'/g)]
    .map(x => x[1]);
  const boxes = [...panelText.matchAll(/'sbox':\s*\(\s*([\s\S]*?)\n\s*\),/g)]
    .map(m => m[1].split(/[\s,]+/).filter(Boolean).map(Number));
  assert.equal(boxes.length, 6);
  assert.equal(fingerprints.length, 6);
  boxes.forEach((box, i) => {
    assert.equal(box.length, 256);
    assert.equal(new Set(box).size, 256);
    assert.ok(box.every(v => Number.isInteger(v) && v >= 0 && v <= 255));
    assert.equal(crypto.createHash("sha3-256").update(Buffer.from(box)).digest("hex"),
                 fingerprints[i]);
  });
  const keysText = fs.readFileSync(keysPath, "utf8");
  const match = /ROUND_KEYS\s*=\s*\(\s*([\s\S]*?)\n\s*\)/.exec(keysText);
  assert.ok(match);
  const keys = match[1].split(/[\s,]+/).filter(Boolean).map(v => Number(v) >>> 0);
  assert.equal(keys.length, 6);
  const scoreText = fs.readFileSync(resultPath, "utf8");
  assert.ok(scoreText.includes("phase2at_depth4_peak_replicated"));
  const neural = {};
  for (const m of scoreText.matchAll(/^Depth ([345]):\s*\n[^\n]*?(\[[^\n]+\])/gm)) {
    neural[Number(m[1])] = JSON.parse(m[2]);
  }
  assert.deepEqual(Object.keys(neural).map(Number).sort((a,b)=>a-b), DEPTHS);
  for (const d of DEPTHS) assert.equal(neural[d].length, 6);
  return {boxes, fingerprints, keys, neural, sha256: crypto.createHash("sha256")
    .update(panelText).update(keysText).update(scoreText).digest("hex")};
}

function schedules(keys) {
  return {
    historical: keys,
    xor_perturbed: keys.map((v, i) => (v ^ ((0x01020408 + i * 0x01010101) >>> 0)) >>> 0),
    rotated_perturbed: keys.map((v, i) => rotl(v ^ 0x9E3779B9, 3 + i))
  };
}

function encrypt(box, keys, p) {
  let v = p >>> 0;
  for (let i = 0; i < keys.length - 1; i++) {
    v = (v ^ keys[i]) >>> 0;
    v = ((box[v >>> 24] << 24) | (box[(v >>> 16) & 255] << 16) |
         (box[(v >>> 8) & 255] << 8) | box[v & 255]) >>> 0;
    if (i !== keys.length - 2) v = rotl(v, 11);
  }
  return (v ^ keys[keys.length - 1]) >>> 0;
}
function xorshift32(seed) {
  let state = seed >>> 0;
  if (state === 0) throw new Error("xorshift32 seed cannot be zero");
  return () => {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return state >>> 0;
  };
}
function samples(delta, trainN, testN) {
  const next = xorshift32(0x52010471 ^ delta);
  const seen = new Set(), positive = [], negative = [], total = trainN + testN;
  while (positive.length < total) {
    const x = next(), y = (x ^ delta) >>> 0;
    if (seen.has(x) || seen.has(y)) continue;
    seen.add(x); seen.add(y); positive.push([x, y]);
  }
  while (negative.length < total) {
    const x = next(), y = next();
    if (x === y || ((x ^ y) >>> 0) === delta || seen.has(x) || seen.has(y)) continue;
    seen.add(x); seen.add(y); negative.push([x, y]);
  }
  assert.equal(seen.size, 4 * total);
  return {trp:positive.slice(0, trainN), trn:negative.slice(0, trainN),
          tsp:positive.slice(trainN), tsn:negative.slice(trainN)};
}
function counts(box, keys, pairs) {
  const bits = new Uint32Array(32);
  for (const [a,b] of pairs) {
    const diff = (encrypt(box, keys, a) ^ encrypt(box, keys, b)) >>> 0;
    for (let i = 0; i < 32; i++) bits[i] += (diff >>> i) & 1;
  }
  return bits;
}
function oneBit(box, keys, p) {
  const a = counts(box, keys, p.trp), b = counts(box, keys, p.trn);
  let selected = 0, gap = -1;
  for (let i = 0; i < 32; i++) {
    const distance = Math.abs(a[i] - b[i]);
    if (distance > gap) { gap = distance; selected = i; }
  }
  const sign = a[selected] >= b[selected] ? 1 : -1;
  const c = counts(box, keys, p.tsp), d = counts(box, keys, p.tsn);
  return {bit: selected, test_signed_advantage:
    sign * (c[selected] - d[selected]) / p.tsp.length};
}
function pearson(a,b) {
  const am = a.reduce((x,y)=>x+y,0)/a.length;
  const bm = b.reduce((x,y)=>x+y,0)/b.length;
  let xy = 0, xx = 0, yy = 0;
  for (let i = 0; i < a.length; i++) {
    const x = a[i] - am, y = b[i] - bm;
    xy += x*y; xx += x*x; yy += y*y;
  }
  return xx > 0 && yy > 0 ? xy / Math.sqrt(xx * yy) : null;
}
function main() {
  const smoke = process.argv.includes("--smoke");
  const trainN = smoke ? 64 : 1536;
  const testN = smoke ? 128 : 3072;
  const data = sources();
  const pairs = new Map(DELTAS.map(d => [d, samples(d,trainN,testN)]));
  const results = [], summary = [];
  for (const [scheme, sixKeys] of Object.entries(schedules(data.keys))) {
    for (const depth of DEPTHS) {
      for (const delta of DELTAS) {
        const candidate = data.boxes.map((box, i) => ({
          index:i, ...oneBit(box, sixKeys.slice(0,depth+1), pairs.get(delta))
        }));
        const scores = candidate.map(r => r.test_signed_advantage);
        results.push(...candidate.map(c => ({schedule:scheme,depth,delta,...c})));
        summary.push({
          schedule:scheme,depth,delta,
          mean_signed_advantage:scores.reduce((x,y)=>x+y,0)/scores.length,
          range:Math.max(...scores)-Math.min(...scores),
          pearson_vs_frozen_neural:pearson(scores,data.neural[depth]),
        });
      }
    }
  }
  assert.equal(results.length, 108);
  const output={
    experiment:"phase2s_independent_xorshift32_js_posthoc", schema_version:1,
    actual_neural_training:0, findings_are_confirmatory:false,
    sbox_count:6, train_per_label:trainN,test_per_label:testN,
    source_input_sha256:data.sha256, results, summary,
    warnings:["ToySPN only","new pseudo-random generator",
              "n=6 candidate correlations descriptive only",
              "not a replication of Python random.Random dataset",
              "not a production cipher or security result"],
  };
  process.stdout.write(JSON.stringify(output,null,2)+"\n");
}
main();
