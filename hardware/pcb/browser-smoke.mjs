import {spawn} from 'node:child_process';
import {readFile,mkdir,writeFile,access} from 'node:fs/promises';
import assert from 'node:assert/strict';
const child=spawn(process.env.CHROME_BIN||'chromium',['--headless','--no-sandbox','--disable-dev-shm-usage','--disable-gpu','--no-first-run','--user-data-dir=/tmp/adolfo-cdp','--remote-debugging-pipe'],{stdio:['ignore','ignore','ignore','pipe','pipe']});
let seq=0,buffer='';const pending=new Map();
child.stdio[4].on('data',c=>{buffer+=c;let k;while((k=buffer.indexOf('\0'))>=0){const p=JSON.parse(buffer.slice(0,k));buffer=buffer.slice(k+1);if(pending.has(p.id)){const {resolve,reject}=pending.get(p.id);pending.delete(p.id);p.error?reject(p.error):resolve(p.result)}}});
const send=(method,params={},sessionId)=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});child.stdio[3].write(JSON.stringify({id,method,params,sessionId})+'\0')});
const timer=setTimeout(()=>{child.kill();process.exit(1)},25000);
try {
 const {targetId}=await send('Target.createTarget',{url:'about:blank'});
 const {sessionId}=await send('Target.attachToTarget',{targetId,flatten:true});const call=(m,p)=>send(m,p,sessionId);
 await call('Page.enable');await call('Runtime.enable');
 await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
 const {frameTree}=await call('Page.getFrameTree');await call('Page.setDocumentContent',{frameId:frameTree.frame.id,html:await readFile(new URL('./output/index.html',import.meta.url),'utf8')});
 const evaluate=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
 const design=JSON.parse(await readFile(new URL('./output/design.json',import.meta.url),'utf8'));
 assert.equal(await evaluate('document.querySelectorAll("tbody tr").length'),design.parts.length);
 for(const name of ['main','panel','drill','front'])assert.equal(await evaluate(`document.querySelector('[data-view="${name}"]').click();document.querySelector('.view.active').id`),name);
 assert.equal(await evaluate(`document.querySelector('#search').value='DAC8568B';document.querySelector('#search').dispatchEvent(new Event('input'));document.querySelectorAll('tbody tr:not([hidden])').length`),1);
 const links=await evaluate('[...document.querySelectorAll("a")].map(a=>a.getAttribute("href"))');for(const href of links)await access(new URL('./output/'+href,import.meta.url));
 await mkdir('/tmp/adolfo-viewer-checks',{recursive:true});
 let shot=await call('Page.captureScreenshot',{format:'png'});await writeFile('/tmp/adolfo-viewer-checks/desktop.png',Buffer.from(shot.data,'base64'));
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});assert.equal(await evaluate('document.documentElement.scrollWidth<=innerWidth'),true);
 shot=await call('Page.captureScreenshot',{format:'png'});await writeFile('/tmp/adolfo-viewer-checks/mobile.png',Buffer.from(shot.data,'base64'));
 console.log('PASS four views, BOM search, local links, mobile width');await send('Browser.close');
}finally{clearTimeout(timer);child.kill()}
