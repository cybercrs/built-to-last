import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {DATA} from '../content.js';
import * as e from '../engine.js';
const fixtures=JSON.parse(readFileSync(new URL('./python-oracles.json',import.meta.url)));
test('Asset balances, partial-year depreciation, sale and ratios match independent Python outcomes',()=>{
  assert.deepEqual(e.acquisitionTotals(),fixtures.calculations.acquisition);assert.deepEqual(e.lifecycleTotals(),fixtures.calculations.lifecycle);
  for(const g of DATA.numbers)assert.deepEqual(e.expectedNumbers(g.prefix),fixtures.calculations.expected[g.prefix]);
  for(const [n,expected] of [[.5,0],[1.5,2],[2.5,2],[-.5,0],[-1.5,-2],[-2.5,-2]])assert.equal(e.pyRound(n)||0,expected);
});
test('All original shuffle orders match exactly including 63-bit seeds',async()=>{for(const f of fixtures.shuffles)assert.deepEqual(await e.shuffled(f.input,BigInt(f.seed),f.salt),f.output);});
test('Old snapshots, choice/numeric drafts and both retired-disposal migrations match Python',async()=>{
  for(const f of fixtures.snapshots){const restored=await e.decodeState(f.token);assert.ok(restored);assert.deepEqual(restored,{...f.payload,z:BigInt(f.seed)});assert.deepEqual(await e.decodeState(await e.encodeState(restored)),restored);}
  for(const seed of [0n,9007199254740993n,9223372036854775807n]){const s=e.newState(seed);assert.equal((await e.decodeState(await e.encodeState(s))).z,seed);}
});
test('Invalid saved state and reasoning before calculation gates cannot unlock content',async()=>{
  for(const patch of [{s:7},{extra:1},{ds:1},{dv:{depreciable_cost:45000}},{z:2**53},{fp:{'choice:site_closing':true}}])assert.throws(()=>e.validateSnapshot({...e.newState(0n),...patch}));
  for(const token of ['', 'garbage', 'a'.repeat(20001)])assert.equal(await e.decodeState(token),null);
  const old=fixtures.snapshots.find(f=>f.payload.s===3);const s=await e.decodeState(old.token);s.ds=false;s.dv={};assert.throws(()=>e.validateSnapshot(s));
  const draft=fixtures.snapshots.find(f=>f.payload.nd.depreciation.depreciable_cost);const lesson=new e.Lesson(await e.decodeState(draft.token));assert.equal(lesson.draftChoice(lesson.context().item.correct),false);assert.equal(lesson.submitChoice(),false);assert.equal(lesson.advance(),false);
});
test('Complete lifecycle preserves all repeated numeric attempts and separate reasoning validations',()=>{
  const lesson=new e.Lesson(e.newState(42n));assert.ok(lesson.advance());
  while(lesson.state.s!==7){
    const g=lesson.numberGroup();if(g&&!lesson.numericLocked()){
      assert.equal(lesson.draftChoice(lesson.context().item.correct),false);
      for(const [k] of g.fields)lesson.draftNumber(k,'0');assert.ok(lesson.submitNumbers());assert.equal(lesson.advance(),false);
      const attempts=structuredClone(lesson.state.at);assert.ok(lesson.submitNumbers());for(const [k] of g.fields)assert.equal(lesson.state.at[`${g.prefix}:${k}`],attempts[`${g.prefix}:${k}`]+1);
      for(const [k,v] of Object.entries(e.expectedNumbers(g.prefix)))lesson.draftNumber(k,String(v));assert.ok(lesson.submitNumbers());assert.deepEqual(lesson.state.nd[g.draft],{});assert.equal(lesson.submitNumbers(),false);assert.equal(lesson.advance(),false);
    }
    const {group,item}=lesson.context();lesson.draftChoice(item.options.find(x=>x!==item.correct));assert.ok(lesson.submitChoice());assert.deepEqual(lesson.state.cd[group.draft],{});assert.equal(lesson.advance(),false);assert.ok(lesson.submitChoice());assert.equal(lesson.state.at[`choice:${item.id}`],2);lesson.draftChoice(item.correct);assert.ok(lesson.submitChoice());assert.equal(lesson.submitChoice(),false);assert.ok(lesson.advance());
  }
  assert.equal(e.scoreSummary(lesson.state).attempted,e.scoreKeys().size);const saved=e.canonicalJSON(lesson.state);
  while(lesson.move(-1)){assert.equal(lesson.submitChoice(),false);assert.equal(lesson.submitNumbers(),false);assert.equal(lesson.draftChoice('anything'),false);assert.equal(lesson.draftNumber('book_value','0'),false);assert.equal(lesson.reset(),false);assert.equal(lesson.advance(),false);assert.equal(e.canonicalJSON(lesson.state),saved);}while(lesson.move(1))assert.equal(e.canonicalJSON(lesson.state),saved);assert.equal(lesson.view,e.frontier(lesson.state));
});
test('View limits, units, numeric bounds and practice overflow retain original semantics',async()=>{
  const lesson=new e.Lesson(e.newState(0n),999);assert.equal(lesson.view,0);
  const [d,x,a]=DATA.numbers;assert.equal(e.parseNumber('$45,000',d,'depreciable_cost'),45000);assert.equal(e.parseNumber('45000.1',d,'depreciable_cost'),null);assert.equal(e.parseNumber('1,000,001',x,'book_value'),null);assert.equal(e.parseNumber('1.50',a,'asset_turnover'),1.5);assert.equal(e.parseNumber('1,50',a,'asset_turnover'),null);
  lesson.advance();const item=lesson.context().item;lesson.draftChoice(item.options.find(x=>x!==item.correct));for(let i=0;i<51;i++)lesson.submitChoice();assert.equal(lesson.state.v,4);assert.equal(e.scoreSummary(lesson.state).revisions,50);assert.deepEqual(await e.decodeState(await e.encodeState(lesson.state)),lesson.state);
});
test('Final titles and every generated teaching variant contain no provisional app branding',()=>{
  assert.match(readFileSync(new URL('../index.html',import.meta.url),'utf8'),/<title>Built to Last\?<\/title>/);assert.doesNotMatch(JSON.stringify({hero:DATA.hero,screens:DATA.screens,groups:DATA.groups,numbers:DATA.numbers}),/\b(?:pilot|preview|prototype|experimental)\b/i);assert.equal(DATA.screens.length,26);assert.equal(DATA.screens.reduce((n,x)=>n+Object.keys(x.variants).length,0),96);
});
