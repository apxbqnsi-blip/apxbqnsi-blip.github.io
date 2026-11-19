import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateCatalog, MODULES } from '../_site/catalog-validation.js';
import { activeCatalog, setupAt } from '../_site/catalog-store.js';
import { RV_LEVELS, MAX_HOME_LEVEL, MODULE_MAX_LEVELS, FACILITIES } from '../_site/facility-config.js';

const original = JSON.parse(readFileSync(new URL('../data/game-data.json', import.meta.url), 'utf8'));
const last = [...original.rv_levels].sort((a, b) => a.level - b.level).at(-1);
const clone = () => structuredClone(original);

test('published levels, modules and facility tiers derive from the catalog', () => {
    assert.deepEqual(RV_LEVELS, original.rv_levels.map(r => r.level).sort((a, b) => a - b));
    assert.equal(MAX_HOME_LEVEL, last.level);
    for (const module of MODULES) assert.equal(MODULE_MAX_LEVELS[module][last.level - 1], last.modules[module]);
    for (const f of FACILITIES) {
        const expected = {};
        for (const row of [...original.rv_levels].sort((a, b) => a.level - b.level)) {
            const tier = row.facilities[f.name];
            if (tier.count) expected[tier.level] ??= row.level;
        }
        assert.deepEqual(f.unlocks, expected);
    }
});

test('future RV levels, facility levels and module requirements have no release-specific ceiling', () => {
    const data = clone();
    for (const offset of [1, 15, 100]) {
        const row = structuredClone(last);
        row.level += offset;
        row.facilities.Farmland.count += offset;
        row.facilities.Farmland.level += offset;
        row.modules.ecological_module += offset;
        data.rv_levels.unshift(row);
    }
    const recipe = {...structuredClone(data.recipes[0]), name:'future_test_recipe',
        min_rv_level:last.level + 100, facility_level:last.facilities.Farmland.level + 100,
        module_requirement:['ecological_module', last.modules.ecological_module + 100]};
    data.recipes.push(recipe);
    assert.equal(validateCatalog(data), data);
    const setup = setupAt(data, last.level + 100);
    assert.equal(setup.facilities.Farmland[0].count, last.facilities.Farmland.count + 100);
    assert.equal(setup.modules.ecological_module, last.modules.ecological_module + 100);
    assert.throws(() => setupAt(data, last.level + 2), /No published data/);
});

test('invalid or duplicate RV levels are rejected rather than silently clipped', () => {
    for (const value of [0, -1, 1.5, '23', NaN, Infinity]) {
        const data = clone(); data.rv_levels.push({...structuredClone(last), level:value});
        assert.throws(() => validateCatalog(data), /invalid RV level/);
    }
    const data = clone(); data.rv_levels.push(structuredClone(last));
    assert.throws(() => validateCatalog(data), /duplicate/);
});

test('an added RV needs complete facility and module data', () => {
    for (const change of [row => delete row.facilities.Farmland,
        row => { row.facilities.Farmland.count = -1; },
        row => delete row.modules.kitchen_module, row => { row.aniimo_max = 0; }]) {
        const data = clone(), row = {...structuredClone(last), level:last.level + 1};
        change(row); data.rv_levels.push(row);
        assert.throws(() => validateCatalog(data), /Invalid game data/);
    }
});

test('new recipes must use existing ingredients and valid requirements', () => {
    const missing = clone();
    missing.recipes[0].raw_materials = ['missing_test_ingredient'];
    missing.recipes[0].required_amount = [1];
    assert.throws(() => validateCatalog(missing), /missing ingredient/);
    const cyclic = clone();
    cyclic.recipes[0].raw_materials = [cyclic.recipes[0].name];
    cyclic.recipes[0].required_amount = [1];
    assert.throws(() => validateCatalog(cyclic), /cyclic ingredients/);
    const invalid = clone(); invalid.recipes[0].module_requirement = ['kitchen_module', 0];
    assert.throws(() => validateCatalog(invalid), /module requirement/);
});

test('the public loader remains immutable and ignores saved editor catalogs', async () => {
    let reads = 0;
    Object.defineProperty(globalThis, 'localStorage', {configurable:true,
        value:{getItem() { reads++; return '{"rv_levels":[{"level":999}]}'; }}});
    try {
        const module = await import('../_site/catalog-store.js?test=readonly');
        assert.equal(reads, 0);
        assert.equal(module.saveCatalog, undefined);
        assert.equal(module.activeCatalog, module.defaultCatalog);
        assert(Object.isFrozen(module.activeCatalog.rv_levels[0].facilities));
        assert.throws(() => module.activeCatalog.rv_levels.push({level:999}), TypeError);
        assert.equal(activeCatalog.rv_levels.length, original.rv_levels.length);
    } finally { delete globalThis.localStorage; }
});
