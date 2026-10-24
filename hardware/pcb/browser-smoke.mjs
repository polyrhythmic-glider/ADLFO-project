// Local offline viewer verification via Chrome DevTools pipe; no npm dependencies.
import {spawn} from 'node:child_process';
import {writeFile, mkdir, readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('.',import.meta.url));
const child=spawn(process.env.CHROME_BIN || 'google-chrome',['--headless','--no-sandbox','--disable-dev-shm-usage','--disable-gpu',
 '--no-first-run','--user-data-dir=/tmp/adlfo-cdp','--remote-debugging-pipe'],{stdio:['ignore','ignore','ignore','pipe','pipe']});
let seq=0, buffer='';const pending=new Map();
child.stdio[4].on('data',chunk=>{buffer+=chunk.toString();let k;while((k=buffer.indexOf('\0'))>=0){
 const packet=JSON.parse(buffer.slice(0,k));buffer=buffer.slice(k+1);if(pending.has(packet.id)){
 const {resolve,reject}=pending.get(packet.id);pending.delete(packet.id);packet.error?reject(packet.error):resolve(packet.result)}}});
const send=(method,params={},sessionId)=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});child.stdio[3].write(JSON.stringify({id,method,params,sessionId})+'\0')});
const timer=setTimeout(()=>{child.kill();console.error('Chrome smoke timed out');process.exit(1)},25000);
try{
 const {targetId}=await send('Target.createTarget',{url:'about:blank'});
 const {sessionId}=await send('Target.attachToTarget',{targetId,flatten:true});
 const call=(m,p)=>send(m,p,sessionId);
 await call('Page.enable');await call('Runtime.enable');
 await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1200,deviceScaleFactor:1,mobile:false});
 const {frameTree}=await call('Page.getFrameTree');
 await call('Page.setDocumentContent',{frameId:frameTree.frame.id,html:await readFile(new URL('./output/index.html',import.meta.url),'utf8')});
 const evalJS=async(expression)=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
 await evalJS(`new Promise((resolve,reject)=>{const deadline=Date.now()+10000;const poll=()=>{if(document.querySelectorAll('tbody tr').length)resolve(true);else if(Date.now()>deadline)reject(Error('Viewer did not load: '+location.href));else setTimeout(poll,50)};poll()})`);
 const design=JSON.parse(await readFile(new URL('./output/design.json',import.meta.url),'utf8'));
 assert.equal(await evalJS('document.querySelectorAll("tbody tr").length'),design.parts.length);
 assert.equal(await evalJS('document.body.textContent.includes("20 HP")'),true);
 for(const view of ['assembly','front','back','cut','pair']){
  assert.equal(await evalJS(`document.querySelector('[data-view="${view}"]').click(); document.querySelector('.view.active').id`),'view-'+view);
 }
 assert.equal(await evalJS(`document.querySelector('[data-view="back"]').click();document.querySelector('#rats').click();!document.querySelector('#board-rats').classList.contains('hidden')`),true);
 assert.equal(await evalJS(`const s=document.querySelector('#search');s.value='TL074';s.dispatchEvent(new Event('input'));document.querySelectorAll('tbody tr:not([hidden])').length`),1);
 await evalJS(`document.querySelector('[data-view="assembly"]').click(); const e=document.querySelector('#explode');e.value=170;e.dispatchEvent(new Event('input'))`);
 assert.equal(await evalJS(`document.querySelector('.assembly').style.getPropertyValue('--separation')`),'170px');
 await mkdir('/tmp/adlfo-viewer-checks',{recursive:true});
 let shot=await call('Page.captureScreenshot',{format:'png'});await writeFile('/tmp/adlfo-viewer-checks/exploded.png',Buffer.from(shot.data,'base64'));
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 await evalJS(`document.querySelector('[data-view="pair"]').click()`);
 assert.equal(await evalJS('document.documentElement.scrollWidth<=innerWidth'),true);
 shot=await call('Page.captureScreenshot',{format:'png'});await writeFile('/tmp/adlfo-viewer-checks/mobile.png',Buffer.from(shot.data,'base64'));
 console.log('PASS: all five tabs, ratsnest, BOM search, exploded slider, mobile width.');
 await send('Browser.close');
}finally{clearTimeout(timer);child.kill()}

