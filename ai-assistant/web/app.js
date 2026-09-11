let conversationId=null;
let sending=false;
const $=s=>document.querySelector(s);
async function api(url,opt={}){const r=await fetch(url,{headers:{'Content-Type':'application/json',...(opt.headers||{})},...opt});let data;try{data=await r.json()}catch{data={}}if(!r.ok)throw new Error(data.detail||data.error||`HTTP ${r.status}`);return data}
function escapeHtml(s){return String(s).replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\':'&#92;','"':'&quot;'}[c]))}
function scrollMessages(){const m=$('#messages');m.scrollTop=m.scrollHeight}
function addMsg(role,text,extra=''){const d=document.createElement('div');d.className=`msg ${role} ${extra}`;d.textContent=text;$('#messages').appendChild(d);scrollMessages();return d}
function showTyping(){const d=document.createElement('div');d.className='msg assistant typing';d.id='typing';d.innerHTML='<i></i><i></i><i></i>';$('#messages').appendChild(d);scrollMessages()}
function hideTyping(){$('#typing')?.remove()}
async function init(){try{const cs=await api('/api/conversations');if(!cs.length){const c=await api('/api/conversations',{method:'POST'});conversationId=c.id}else conversationId=cs[0].id;await Promise.all([loadMessages(),loadTasks(),loadMemories()])}catch(e){addMsg('assistant','Не удалось загрузить данные. Проверь соединение с сервером.','error')}}
async function loadMessages(){const ms=await api(`/api/conversations/${conversationId}/messages`);$('#messages').innerHTML='';if(!ms.length)addMsg('assistant','Привет! Я My AI ✦\n\nЯ могу хранить историю, задачи и память. Напиши, что нужно сделать.');else ms.forEach(m=>addMsg(m.role==='user'?'user':'assistant',m.content))}
async function send(){if(sending)return;const input=$('#input'),text=input.value.trim();if(!text)return;sending=true;$('#send').disabled=true;input.value='';autoResize();addMsg('user',text);showTyping();try{const r=await api('/api/chat',{method:'POST',body:JSON.stringify({conversation_id:conversationId,message:text})});hideTyping();addMsg('assistant',r.answer||'Пустой ответ от модели.')}catch(e){hideTyping();addMsg('assistant',`Не удалось получить ответ. ${e.message}`,'error')}finally{sending=false;$('#send').disabled=false;input.focus()}}
function autoResize(){const i=$('#input');i.style.height='auto';i.style.height=Math.min(i.scrollHeight,125)+'px'}
$('#send').onclick=send;
$('#input').addEventListener('input',autoResize);
$('#input').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
async function loadTasks(){const ts=await api('/api/tasks');const list=$('#taskList');list.innerHTML='';$('#emptyTasks').classList.toggle('hidden',ts.length>0);ts.forEach(t=>{const d=document.createElement('div');d.className='item task';d.innerHTML=`<button class="task-toggle" aria-label="Изменить задачу">${t.completed?'✓':'○'}</button><span class="task-title ${t.completed?'done':''}">${escapeHtml(t.title)}</span>`;d.querySelector('button').onclick=async()=>{await api('/api/tasks/'+t.id,{method:'PATCH'});loadTasks()};list.appendChild(d)})}
async function addTask(){const i=$('#taskInput'),v=i.value.trim();if(!v)return;try{await api('/api/tasks',{method:'POST',body:JSON.stringify({title:v})});i.value='';loadTasks()}catch(e){alert(e.message)}}
$('#addTask').onclick=addTask;$('#taskInput').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();addTask()}});
async function loadMemories(){const ms=await api('/api/memories');const list=$('#memoryList');list.innerHTML='';$('#emptyMemory').classList.toggle('hidden',ms.length>0);ms.forEach(m=>{const d=document.createElement('div');d.className='item memory-item';d.innerHTML=`<span class="memory-mark">✦</span>${escapeHtml(m.content)}`;list.appendChild(d)})}
async function addMemory(){const i=$('#memoryInput'),v=i.value.trim();if(!v)return;try{await api('/api/memories',{method:'POST',body:JSON.stringify({content:v})});i.value='';loadMemories()}catch(e){alert(e.message)}}
$('#addMemory').onclick=addMemory;$('#memoryInput').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();addMemory()}});
function switchScreen(name){document.querySelectorAll('.screen').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.nav-item').forEach(x=>x.classList.remove('active'));$('#'+name).classList.add('active');document.querySelector(`[data-screen="${name}"]`).classList.add('active');window.scrollTo(0,0)}
document.querySelectorAll('.nav-item').forEach(b=>b.onclick=()=>switchScreen(b.dataset.screen));
$('#newChat').onclick=async()=>{try{const c=await api('/api/conversations',{method:'POST'});conversationId=c.id;await loadMessages();switchScreen('chat');$('#input').focus()}catch(e){addMsg('assistant',e.message,'error')}};
init();