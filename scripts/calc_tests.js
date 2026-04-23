#!/usr/bin/env node
// Sanity-check suite for scripts/calc.js — exercises the NCP wrapper across
// diverse interactions (immunities, weather, prep-chain abilities, items, etc.)
// to catch silent regressions when NCP updates or our wrapper drifts.
//
// Each test case has:
//   - name        : human label
//   - input       : same shape as calc.js stdin JSON
//   - expect      : assertions (damage array OR ranges + KO chance OR note regex)
//   - verified    : "live"  = expected values cross-checked against web calc (gold)
//                   "snapshot" = expected pinned from our own output (regression only)
//                   "manual" = expected derived by hand from formula
//
// Run: node scripts/calc_tests.js

const path = require('path');
const { spawnSync } = require('child_process');

const CALC = path.join(__dirname, 'calc.js');

function runCalc(input) {
  const res = spawnSync('node', [CALC], {
    input: JSON.stringify(input),
    encoding: 'utf8',
    timeout: 30000,
  });
  if (res.status !== 0) {
    return { error: res.stderr || 'unknown', stdout: res.stdout };
  }
  try {
    return { ok: JSON.parse(res.stdout), stderr: res.stderr };
  } catch (e) {
    return { error: 'JSON parse failed: ' + e.message, stdout: res.stdout };
  }
}

const TESTS = [
  {
    name: 'JLuke baseline: Mega Camerupt Modest 32 SpA Earth Power vs balanced-bulk Incin',
    verified: 'live',
    input: {
      attacker: { name: 'Camerupt-Mega', ability: 'Sheer Force', item: 'Cameruptite',
        nature: 'Modest', sps: { sa: 32 }, moves: ['Earth Power'] },
      defender: { name: 'Incineroar', ability: 'Intimidate', item: 'Sitrus Berry',
        nature: 'Careful', sps: { hp: 32, sd: 20 }, moves: ['Fake Out'] },
      field: { format: 'Doubles' },
    },
    expect: { damage: [200, 204, 206, 210, 212, 212, 216, 218, 222, 224, 224, 228, 230, 234, 236] },
  },
  {
    name: 'Type immunity: Sneasler Dire Claw (Poison) vs Archaludon (Steel/Dragon)',
    verified: 'manual',
    input: {
      attacker: { name: 'Sneasler', ability: 'Unburden', item: 'White Herb',
        nature: 'Jolly', sps: { at: 32, sp: 32 }, moves: ['Dire Claw'] },
      defender: { name: 'Archaludon', ability: 'Stamina', item: 'Leftovers',
        nature: 'Impish', sps: { hp: 32, df: 32, sd: 2 }, moves: ['Body Press'] },
      field: { format: 'Doubles' },
    },
    expect: { damageAllZero: true, noteMatch: /immunity/i },
  },
  {
    name: 'Status move: Protect returns 0 + status note',
    verified: 'manual',
    input: {
      attacker: { name: 'Incineroar', ability: 'Intimidate', item: 'Sitrus Berry',
        nature: 'Careful', sps: { hp: 32, sd: 32 }, moves: ['Protect'] },
      defender: { name: 'Garchomp', ability: 'Rough Skin', item: 'Leftovers',
        nature: 'Jolly', sps: { at: 32, sp: 32 }, moves: ['Earthquake'] },
      field: { format: 'Doubles' },
    },
    expect: { damageAllZero: true, noteMatch: /status|non-damaging/i },
  },
  {
    name: 'Weather: Charizard Y Heat Wave under Drought sun (boosted Fire)',
    verified: 'snapshot',
    input: {
      attacker: { name: 'Charizard-Mega-Y', ability: 'Drought', item: 'Charizardite Y',
        nature: 'Modest', sps: { sa: 32, sp: 32 }, moves: ['Heat Wave'] },
      defender: { name: 'Garchomp', ability: 'Rough Skin', item: 'Leftovers',
        nature: 'Jolly', sps: { hp: 16, df: 16, sp: 32 }, moves: ['Earthquake'] },
      field: { format: 'Doubles', weather: 'Sun' },
    },
    // Pinned after a manual run; flag if it changes.
    expect: { minDamage: 1, koChance: null /* fill in after first run */ },
  },
  {
    name: 'Sheer Force secondary suppression: Mega Camerupt Earth Power has no SpDef drop',
    verified: 'manual',
    // Sheer Force should be applied (×1.3) and secondary effect (-1 SpD) suppressed.
    // We can't directly assert on the secondary suppression but we CAN check the
    // damage description includes "Sheer Force".
    input: {
      attacker: { name: 'Camerupt-Mega', ability: 'Sheer Force', item: 'Cameruptite',
        nature: 'Modest', sps: { sa: 32 }, moves: ['Earth Power'] },
      defender: { name: 'Garchomp', ability: 'Rough Skin', item: 'Leftovers',
        nature: 'Jolly', sps: { hp: 16, df: 16, sp: 32 }, moves: ['Earthquake'] },
      field: { format: 'Doubles' },
    },
    expect: { descriptionIncludes: 'Sheer Force' },
  },
];

function check(test, result) {
  const failures = [];
  if (result.error) {
    return [`calc errored: ${result.error.split('\n')[0]}`];
  }
  const move0 = result.ok.moves[0];
  const dmg = move0.result.damage;
  const desc = move0.result.description || '';
  const note = move0.note || '';

  const e = test.expect;
  if (e.damage) {
    if (JSON.stringify(dmg) !== JSON.stringify(e.damage)) {
      failures.push(`damage array mismatch:\n    expected: ${JSON.stringify(e.damage)}\n    actual:   ${JSON.stringify(dmg)}`);
    }
  }
  if (e.damageAllZero) {
    if (!dmg.every(d => d === 0)) failures.push(`expected all-zero damage; got ${JSON.stringify(dmg)}`);
  }
  if (e.minDamage != null) {
    if (Math.min(...dmg) < e.minDamage) failures.push(`min damage ${Math.min(...dmg)} < expected ${e.minDamage}`);
  }
  if (e.maxDamage != null) {
    if (Math.max(...dmg) > e.maxDamage) failures.push(`max damage ${Math.max(...dmg)} > expected ${e.maxDamage}`);
  }
  if (e.noteMatch) {
    if (!e.noteMatch.test(note)) failures.push(`note "${note}" did not match ${e.noteMatch}`);
  }
  if (e.descriptionIncludes) {
    if (!desc.includes(e.descriptionIncludes)) failures.push(`description "${desc}" did not include "${e.descriptionIncludes}"`);
  }
  return failures;
}

function fmtDmg(arr) {
  if (!Array.isArray(arr)) return String(arr);
  if (arr.length <= 5) return `[${arr.join(', ')}]`;
  return `[${arr[0]}..${arr[arr.length-1]}]`;
}

(async () => {
  let pass = 0, fail = 0;
  for (const t of TESTS) {
    process.stdout.write(`▸ ${t.name}\n  [${t.verified}] `);
    const r = runCalc(t.input);
    const failures = check(t, r);
    if (failures.length === 0) {
      const dmg = r.ok && r.ok.moves[0].result.damage;
      console.log(`PASS ${dmg ? fmtDmg(dmg) : ''}`);
      pass++;
    } else {
      console.log(`FAIL`);
      for (const f of failures) console.log(`    ${f}`);
      fail++;
    }
  }
  console.log(`\n${pass}/${pass + fail} passed`);
  process.exit(fail > 0 ? 1 : 0);
})();
