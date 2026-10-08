const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const code=fs.readFileSync(path.join(__dirname,'../router.js'),'utf8');
const route=chatInput=>vm.runInNewContext(`(function(){${code}})()`,{$input:{first:()=>({json:{chatInput}})}})[0].json.output.route;
assert.equal(route('debug this python function'),'code');assert.equal(route('translate this into spanish'),'translate');assert.equal(route('summarize this text'),'summarize');assert.equal(route('explain how a cache works'),'reason');assert.equal(route('write a poem'),'creative');assert.equal(route('hello'),'simple');assert.equal(route('summarize this python code'),'summarize');console.log('7 routing checks passed');
