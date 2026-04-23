#!/usr/bin/env node
// Headless wrapper around NCP-VGC-Damage-Calculator for Champions calcs.
//
// Approach:
//   - Load index.html into jsdom, inject NCP scripts so calc globals (pokedex, moves,
//     Pokemon ctor, Field ctor, CALCULATE_ALL_MOVES_SV, etc.) populate.
//   - Force gen=10 + vgcdex (Champions).
//   - Build Pokemon POJOs directly (avoids DOM-scraping ctor); reuse Field() ctor by
//     toggling DOM checkboxes (lightweight).
//   - Call CALCULATE_ALL_MOVES_SV(p1, p2, field) — runs the full prep chain
//     (Intimidate, weather abilities, paradox abilities, etc.) before damage math.
//
// Usage (CLI):
//   node scripts/calc.js < input.json
//   echo '{ ... }' | node scripts/calc.js
//
// Input JSON shape:
//   {
//     "attacker": { "name": "Camerupt-Mega", "ability": "Sheer Force", "item": "Charcoal",
//                   "nature": "Modest", "sps": {"sa": 32}, "moves": ["Earth Power"] },
//     "defender": { "name": "Incineroar", ... },
//     "field":    { "weather": "Sun", "tailwind": [false, false], "intimidate": false }
//   }

const { JSDOM, VirtualConsole } = require('jsdom');
const path = require('path');
const fs = require('fs');

const CALC_DIR = path.join(__dirname, '..', 'sim', 'ncp-calc');
const INDEX = path.join(CALC_DIR, 'index.html');

const STATS = ['hp', 'at', 'df', 'sa', 'sd', 'sp'];
const NATURE_MAP = {
  Adamant: ['at', 'sa'], Bold: ['df', 'at'], Brave: ['at', 'sp'], Calm: ['sd', 'at'],
  Careful: ['sd', 'sa'], Gentle: ['sd', 'df'], Hasty: ['sp', 'df'], Impish: ['df', 'sa'],
  Jolly: ['sp', 'sa'], Lax: ['df', 'sd'], Lonely: ['at', 'df'], Mild: ['sa', 'df'],
  Modest: ['sa', 'at'], Naive: ['sp', 'sd'], Naughty: ['at', 'sd'], Quiet: ['sa', 'sp'],
  Rash: ['sa', 'sd'], Relaxed: ['df', 'sp'], Sassy: ['sd', 'sp'], Timid: ['sp', 'at'],
  // Neutral: Hardy, Bashful, Docile, Quirky, Serious — handled via empty arrays
};

function natureMult(stat, nature) {
  const pair = NATURE_MAP[nature];
  if (!pair) return 1.0;
  if (pair[0] === stat) return 1.1;
  if (pair[1] === stat) return 0.9;
  return 1.0;
}

// Champions stat formula: level 50, IVs 31, EV = SP × 8.
function computeStat(stat, base, sp, nature) {
  const iv = 31;
  const ev = sp * 8;
  if (stat === 'hp') {
    return Math.floor(((2 * base + iv + Math.floor(ev / 4)) * 50) / 100) + 50 + 10;
  }
  const raw = Math.floor(((2 * base + iv + Math.floor(ev / 4)) * 50) / 100) + 5;
  return Math.floor(raw * natureMult(stat, nature));
}

let _bootstrap = null;

async function bootstrap() {
  if (_bootstrap) return _bootstrap;
  _bootstrap = (async () => {
    const html = fs.readFileSync(INDEX, 'utf8');
    const scriptSrcRegex = /<script[^>]*src=["']([^"']+)["'][^>]*>\s*<\/script>/gi;
    const scriptSrcs = [];
    let m;
    while ((m = scriptSrcRegex.exec(html)) !== null) scriptSrcs.push(m[1]);
    const stripped = html.replace(scriptSrcRegex, '');

    const vc = new VirtualConsole();
    vc.on('jsdomError', () => {});

    const dom = new JSDOM(stripped, {
      runScripts: 'dangerously',
      pretendToBeVisual: true,
      url: `file://${INDEX}`,
      virtualConsole: vc,
    });

    const w = dom.window;
    let loaded = 0, missing = 0;
    for (const src of scriptSrcs) {
      if (/^https?:/.test(src)) continue;
      const filePath = path.resolve(CALC_DIR, src);
      if (!fs.existsSync(filePath)) {
        console.error(`[calc bootstrap] MISSING script: ${src} — calc may produce wrong results`);
        missing++;
        continue;
      }
      const code = fs.readFileSync(filePath, 'utf8');
      const scriptEl = w.document.createElement('script');
      scriptEl.textContent = code;
      w.document.head.appendChild(scriptEl);
      loaded++;
    }
    if (missing > 0) {
      console.error(`[calc bootstrap] ${missing} script(s) missing of ${scriptSrcs.length}. Did the NCP submodule update?`);
    }
    await new Promise(r => setTimeout(r, 200));

    // Initialize gen 10 / Champions globals (mirrors the gen-change handler in ap_calc.js).
    try {
      w.eval(`
        gen = 10;
        pokedex = POKEDEX_CHAMPIONS;
        typeChart = TYPE_CHART_SV;
        moves = MOVES_CHAMPIONS;
        items = ITEMS_CHAMPIONS;
        abilities = ABILITIES_CHAMPIONS;
        STATS = STATS_GSC;
        calculateAllMoves = CALCULATE_ALL_MOVES_SV;
        calcHP = CALC_HP_CHAMP;
        calcStat = CALC_STAT_CHAMP;
      `);
    } catch (e) {
      throw new Error('Champions globals init failed (NCP may have changed shape): ' + e.message);
    }
    await new Promise(r => setTimeout(r, 50));

    // Sanity-check globals are all present and non-empty.
    const checks = {
      pokedex: w.pokedex && Object.keys(w.pokedex).length,
      moves: w.moves && Object.keys(w.moves).length,
      items: w.items && (Array.isArray(w.items) ? w.items.length : Object.keys(w.items).length),
      abilities: w.abilities && (Array.isArray(w.abilities) ? w.abilities.length : Object.keys(w.abilities).length),
      typeChart: w.typeChart && Object.keys(w.typeChart).length,
      Pokemon: typeof w.Pokemon === 'function',
      Field: typeof w.Field === 'function',
      CALCULATE_ALL_MOVES_SV: typeof w.CALCULATE_ALL_MOVES_SV === 'function',
    };
    for (const [k, v] of Object.entries(checks)) {
      if (!v) console.error(`[calc bootstrap] WARN: ${k} is missing/empty (${v})`);
    }
    return { dom, w };
  })();
  return _bootstrap;
}

function levenshtein(a, b) {
  const al = a.length, bl = b.length;
  if (!al) return bl; if (!bl) return al;
  const dp = Array.from({ length: al + 1 }, () => new Array(bl + 1));
  for (let i = 0; i <= al; i++) dp[i][0] = i;
  for (let j = 0; j <= bl; j++) dp[0][j] = j;
  for (let i = 1; i <= al; i++) {
    for (let j = 1; j <= bl; j++) {
      const cost = a[i - 1].toLowerCase() === b[j - 1].toLowerCase() ? 0 : 1;
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost);
    }
  }
  return dp[al][bl];
}

function suggestNames(target, candidates, n = 3) {
  return candidates
    .map(c => [c, levenshtein(target, c)])
    .sort((a, b) => a[1] - b[1])
    .slice(0, n)
    .filter(([, d]) => d <= Math.max(3, Math.floor(target.length / 2)))
    .map(([c]) => c);
}

function resolveSpecies(w, name) {
  if (w.pokedex[name]) return [name, w.pokedex[name]];
  // Showdown→NCP conversions for mega forms:
  //   Camerupt-Mega       → Mega Camerupt
  //   Charizard-Mega-X    → Mega Charizard X
  //   Charizard-Mega-Y    → Mega Charizard Y
  const megaXY = name.match(/^(.+)-Mega-([XY])$/);
  if (megaXY) {
    const k = `Mega ${megaXY[1]} ${megaXY[2]}`;
    if (w.pokedex[k]) return [k, w.pokedex[k]];
  }
  if (name.endsWith('-Mega')) {
    const k = `Mega ${name.slice(0, -5)}`;
    if (w.pokedex[k]) return [k, w.pokedex[k]];
  }
  // Other common variants
  const variants = [`Mega ${name}`];
  for (const v of variants) if (w.pokedex[v]) return [v, w.pokedex[v]];
  const suggestions = suggestNames(name, Object.keys(w.pokedex));
  const hint = suggestions.length ? `  Did you mean: ${suggestions.join(', ')}?` : '';
  throw new Error(`Unknown species: "${name}".${hint}`);
}

function typeEffectiveness(w, attackType, defType1, defType2) {
  if (!w.typeChart || !w.typeChart[attackType]) return 1;
  const t1 = w.typeChart[attackType][defType1];
  const t2 = defType2 ? w.typeChart[attackType][defType2] : 1;
  return (t1 == null ? 1 : t1) * (t2 == null ? 1 : t2);
}

function resolveMove(w, name) {
  if (w.moves[name]) return w.moves[name];
  const suggestions = suggestNames(name, Object.keys(w.moves));
  const hint = suggestions.length ? `  Did you mean: ${suggestions.join(', ')}?` : '';
  throw new Error(`Unknown move: "${name}".${hint}`);
}

function buildPokemon(w, spec) {
  if (!spec || typeof spec !== 'object') throw new Error(`Pokemon spec must be an object, got: ${typeof spec}`);
  if (!spec.name) throw new Error('Pokemon spec missing required "name" field');
  const [speciesKey, dexEntry] = resolveSpecies(w, spec.name);

  // SP validation: 0-32 per stat, 66 total.
  const totalSP = Object.values(spec.sps || {}).reduce((a, b) => a + b, 0);
  if (totalSP > 66) console.error(`[calc] WARN: ${spec.name} total SP = ${totalSP} (Champions max is 66)`);
  for (const [s, v] of Object.entries(spec.sps || {})) {
    if (v < 0 || v > 32) console.error(`[calc] WARN: ${spec.name} ${s} SP = ${v} (must be 0-32)`);
  }

  // Nature validation
  if (spec.nature && !(spec.nature in NATURE_MAP) && !['Hardy', 'Bashful', 'Docile', 'Quirky', 'Serious'].includes(spec.nature)) {
    console.error(`[calc] WARN: ${spec.name} nature "${spec.nature}" not recognized — treating as neutral`);
  }

  // Ability validation against Champions ability list
  if (spec.ability && Array.isArray(w.abilities) && w.abilities.length && !w.abilities.includes(spec.ability)) {
    const suggestions = suggestNames(spec.ability, w.abilities);
    const hint = suggestions.length ? ` Did you mean: ${suggestions.join(', ')}?` : '';
    console.error(`[calc] WARN: ${spec.name} ability "${spec.ability}" not in Champions ability list.${hint}`);
  }

  // Item validation against Champions item list
  if (spec.item && Array.isArray(w.items) && w.items.length && !w.items.includes(spec.item)) {
    const suggestions = suggestNames(spec.item, w.items);
    const hint = suggestions.length ? ` Did you mean: ${suggestions.join(', ')}?` : '';
    console.error(`[calc] WARN: ${spec.name} item "${spec.item}" not in Champions item list.${hint}`);
  }

  const sps = Object.fromEntries(STATS.map(s => [s, (spec.sps && spec.sps[s]) || 0]));
  const evs = Object.fromEntries(STATS.map(s => [s, sps[s] * 8]));
  const ivs = Object.fromEntries(STATS.map(s => [s, 31]));
  const nature = spec.nature || 'Hardy';
  const rawStats = Object.fromEntries(STATS.map(s =>
    [s, computeStat(s, dexEntry.bs[s], sps[s], nature)]
  ));
  const boosts = { at: 0, df: 0, sa: 0, sd: 0, sp: 0, ...(spec.boosts || {}) };

  // Build move objects: copy from moves dict + add defaults for fields the calc reads.
  const moves = (spec.moves || []).slice(0, 4).map(name => {
    const def = resolveMove(w, name);
    return Object.assign({}, def, {
      name,
      bp: def.bp || 0,
      type: def.type,
      category: def.category,
      isCrit: false,
      isZ: false,
      hits: def.hitRange ? (Array.isArray(def.hitRange) ? def.hitRange : 1) : 1,
      isDouble: 0,
      combinePledge: 0,
      timesAffected: 0,
      usedOppMoveIndex: 0,
      getsStellarBoost: false,
      isPlusMove: false,
    });
  });
  while (moves.length < 4) {
    moves.push({ name: '(No Move)', bp: 0, type: 'Normal', category: 'Other',
      isCrit: false, isZ: false, hits: 1, isDouble: 0, combinePledge: 0,
      timesAffected: 0, usedOppMoveIndex: 0, getsStellarBoost: false, isPlusMove: false });
  }

  const poke = {
    name: speciesKey,
    type1: dexEntry.t1,
    type2: dexEntry.t2 || '',
    tera_type: '',
    level: 50,
    maxHP: rawStats.hp,
    curHP: rawStats.hp,
    HPSPs: sps.hp, HPEVs: evs.hp, HPIVs: 31, HPraw: rawStats.hp,
    isDynamax: false, gmax_factor: false, isTerastalize: false,
    rawStats, boosts, stats: {}, sps, evs, ivs,
    nature,
    ability: spec.ability || dexEntry.ab || '',
    abilityOn: true,
    supremeOverlord: 0,
    rivalryGender: '',
    highestStat: -1,
    item: spec.item || '',
    status: spec.status || 'Healthy',
    toxicCounter: 0,
    moves,
    glaiveRushMod: false,
    weight: dexEntry.w || 100,
    canEvolve: dexEntry.canEvolve || false,
    isTransformed: false,
  };
  // hasType helper used by the calc
  poke.hasType = function (type) { return this.type1 === type || this.type2 === type; };
  return poke;
}

function configureField(w, fieldSpec) {
  const f = fieldSpec || {};
  const $ = w.$;
  // Format: Singles or Doubles (Champions = Doubles)
  $(`input:radio[name='format'][value='${f.format || 'Doubles'}']`).prop('checked', true);
  // Weather
  const weather = f.weather || '';
  $(`input:radio[name='weather'][value='${weather}']`).prop('checked', true);
  // Terrain
  const terrain = f.terrain || '';
  $(`input:radio[name='terrain'][value='${terrain}']`).prop('checked', true);
  // Tailwind per side
  const tw = f.tailwind || [false, false];
  $('#tailwindL').prop('checked', !!tw[0]);
  $('#tailwindR').prop('checked', !!tw[1]);
  return new w.Field();
}

async function calc(input) {
  const { w } = await bootstrap();
  const p1 = buildPokemon(w, input.attacker);
  const p2 = buildPokemon(w, input.defender);
  const field = configureField(w, input.field);
  if (process.env.CALC_DEBUG) {
    const orig = w.GET_DAMAGE_SV;
    w.GET_DAMAGE_SV = function(att, def, mv, fld) {
      console.error(`>>GET_DAMAGE_SV name=${mv.name} bp=${mv.bp} cat=${mv.category} type=${mv.type}`);
      return orig.call(this, att, def, mv, fld);
    };
  }
  let results;
  try {
    results = w.CALCULATE_ALL_MOVES_SV(p1, p2, field);
  } catch (e) {
    throw new Error(`CALCULATE_ALL_MOVES_SV threw: ${e.message}\n  attacker=${p1.name} defender=${p2.name}\n  This usually means a move/ability/item interaction the calc doesn't expect — check inputs.`);
  }
  // results[0] = attacker's 4 moves vs defender; results[1] = defender's vs attacker
  return {
    attacker: { name: p1.name, stats: p1.rawStats, ability: p1.ability },
    defender: { name: p2.name, stats: p2.rawStats, ability: p2.ability },
    moves: input.attacker.moves.map((mv, i) => {
      const r = results[0][i];
      const out = { move: mv, result: r };
      // Annotate "why is damage 0" so silent immunities are visible.
      if (r && Array.isArray(r.damage) && r.damage.every(d => d === 0)) {
        const moveDef = w.moves[mv];
        if (!moveDef) {
          out.note = `damage=0: move "${mv}" not found in Champions move data`;
        } else if (moveDef.bp === 0 || moveDef.category === 'Other' || moveDef.category === 'Status') {
          out.note = `damage=0: ${mv} is a status/non-damaging move`;
        } else {
          // Compute type effectiveness via the calc's own typeChart
          const eff = typeEffectiveness(w, moveDef.type, p2.type1, p2.type2);
          if (eff === 0) {
            out.note = `damage=0: ${moveDef.type} is 0× vs ${p2.type1}${p2.type2 ? '/' + p2.type2 : ''} (immunity)`;
          } else {
            out.note = `damage=0: unknown reason — check inputs (ability/item interaction?)`;
          }
        }
      }
      return out;
    }),
  };
}

async function main() {
  let raw = '';
  if (!process.stdin.isTTY) {
    for await (const chunk of process.stdin) raw += chunk;
  }
  if (!raw.trim()) {
    // No input — run a sanity check against the JLuke transcript example.
    raw = JSON.stringify({
      attacker: {
        name: 'Camerupt-Mega', ability: 'Sheer Force', item: 'Cameruptite',
        nature: 'Modest', sps: { sa: 32 }, moves: ['Earth Power'],
      },
      defender: {
        name: 'Incineroar', ability: 'Intimidate', item: 'Sitrus Berry',
        nature: 'Careful', sps: { hp: 32, sd: 32 }, moves: ['Fake Out'],
      },
      field: { weather: '', format: 'Doubles' },
    });
  }
  const input = JSON.parse(raw);
  try {
    const result = await calc(input);
    console.log(JSON.stringify(result, null, 2));
  } catch (e) {
    console.error('Calc error:', e.message);
    console.error(e.stack);
    process.exit(1);
  }
}

main();
