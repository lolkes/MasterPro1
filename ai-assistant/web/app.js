let conversationId=null;
const $=s=>document.querySelector(s);
async function api(url,opt={}){const r=await fetch(url,{headers:{'Content-Type':'application/json'},...opt});return r.json()}
async function init(){let cs=await api('/api/conversations');if(!cs.length){const c=await api('/api/conversations',{method:'POST'});conversationId=c.id}else conversationId=cs[0].id;loadMessages();loadTasks();loadMemories();}
function addMsg(role,text){const d=document.createElement('div');d.className='msg '+role;d.textContent=text;$('#messages').appendChild(d);$('#messages').scrollTop=$('#messages').scrollHeight}
async function loadMessages(){const ms=await api(`/api/conversations/${conversationId}/messages`);$('#messages').innerHTML='';if(!ms.length)addMsg('assistant','Привет! Я My AI ✦\n\nЯ уже умею хранить историю, задачи и память. Напиши мне что-нибудь.');else ms.forEach(m=>addMsg(m.role==='user'?'user':'assistant',m.content));}
async function send(){const input=$('#input'),text=input.value.trim();if(!text)return;input.value='';addMsg('user',text);const r=await api('/api/chat',{method:'POST',body:JSON.stringify({conversation_id:conversationId,message:text})});addMsg('assistant',r.answer)}
$('#send').onclick=send;$('#input').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
async function loadTasks(){const ts=await api('/api/tasks');$('#taskList').innerHTML=ts.map(t=>`<div class="item task"><button onclick="toggleTask(${t.id})">${t.completed?'↩':'✓'}</button><span class="${t.completed?'done':''}">${escapeHtml(t.title)}</span></div>`).join('')}
async function toggleTask(id){await api('/api/tasks/'+id,{method:'PATCH'});loadTasks()}
$('#addTask').onclick=async()=>{const i=$('#taskInput'),v=i.value.trim();if(!v)return;await api('/api/tasks',{method:'POST',body:JSON.stringify({title:v})});i.value='';loadTasks()};
async function loadMemories(){const ms=await api('/api/memories');$('#memoryList').innerHTML=ms.map(m=>`<div class="item">🧠 ${escapeHtml(m.content)}</div>`).join('')}
$('#addMemory').onclick=async()=>{const i=$('#memoryInput'),v=i.value.trim();if(!v)return;await api('/api/memories',{method:'POST',body:JSON.stringify({content:v})});i.value='';loadMemories()};
function escapeHtml(s){return s.replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\':'&#92;','"':'&quot;'}[c]))}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.screen').forEach(x=>x.classList.remove('active'));$('#'+b.dataset.screen).classList.add('active');});
init();