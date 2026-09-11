import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';

const defaultApi = String.fromEnvironment('API_BASE_URL', defaultValue: '');

void main() => runApp(const MyAIApp());

class MyAIApp extends StatelessWidget {
  const MyAIApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    debugShowCheckedModeBanner: false,
    title: 'My AI',
    theme: ThemeData(useMaterial3: true, brightness: Brightness.dark, scaffoldBackgroundColor: const Color(0xFF08090D), colorSchemeSeed: const Color(0xFF9B8CFF)),
    home: const HomePage(),
  );
}

class Api {
  String base = defaultApi;
  Future<dynamic> request(String path, {String method='GET', Map<String,dynamic>? body}) async {
    if (base.isEmpty) throw Exception('Укажи адрес сервера в настройках.');
    final client = HttpClient();
    try {
      final req = await client.openUrl(method, Uri.parse(base.replaceFirst(RegExp(r'/$'), '') + path));
      req.headers.contentType = ContentType.json;
      if (body != null) req.write(jsonEncode(body));
      final res = await req.close();
      final text = await res.transform(utf8.decoder).join();
      if (res.statusCode < 200 || res.statusCode >= 300) throw Exception('Сервер: ${res.statusCode} ${text.length > 200 ? text.substring(0,200) : text}');
      return text.isEmpty ? {} : jsonDecode(text);
    } finally { client.close(force: true); }
  }
}

class HomePage extends StatefulWidget { const HomePage({super.key}); @override State<HomePage> createState()=>_HomePageState(); }
class _HomePageState extends State<HomePage> {
  final api = Api(); final input = TextEditingController(); final taskInput = TextEditingController(); final memoryInput = TextEditingController();
  final messages = <Map<String,dynamic>>[]; List<dynamic> tasks=[]; List<dynamic> memories=[]; int tab=0; int? conversationId; bool loading=true; bool sending=false;
  @override void initState(){super.initState(); _init();}
  Future<void> _init() async { if(api.base.isEmpty){setState(()=>loading=false); return;} try { final cs=await api.request('/api/conversations'); if(cs.isEmpty){final c=await api.request('/api/conversations',method:'POST'); conversationId=c['id'];} else conversationId=cs[0]['id']; await Future.wait([_loadMessages(),_loadTasks(),_loadMemories()]); } catch(e){messages.add({'role':'assistant','content':'Не удалось подключиться: $e'});} setState(()=>loading=false); }
  Future<void> _loadMessages() async {final ms=await api.request('/api/conversations/$conversationId/messages'); messages..clear()..addAll(List<Map<String,dynamic>>.from(ms));}
  Future<void> _loadTasks() async {tasks=await api.request('/api/tasks');}
  Future<void> _loadMemories() async {memories=await api.request('/api/memories');}
  Future<void> _send() async {final text=input.text.trim(); if(text.isEmpty||sending||conversationId==null)return; setState((){sending=true;messages.add({'role':'user','content':text});input.clear();}); try {final r=await api.request('/api/chat',method:'POST',body:{'conversation_id':conversationId,'message':text}); setState(()=>messages.add({'role':'assistant','content':r['answer']??'Пустой ответ'}));}catch(e){setState(()=>messages.add({'role':'assistant','content':'Ошибка: $e'}));}setState(()=>sending=false);}
  Future<void> _newChat() async {try{final c=await api.request('/api/conversations',method:'POST');setState((){conversationId=c['id'];messages.clear();tab=0;});}catch(e){_snack('$e');}}
  Future<void> _addTask() async {final v=taskInput.text.trim();if(v.isEmpty)return;try{await api.request('/api/tasks',method:'POST',body:{'title':v});taskInput.clear();await _loadTasks();setState((){});}catch(e){_snack('$e');}}
  Future<void> _toggle(dynamic t) async {try{await api.request('/api/tasks/${t['id']}',method:'PATCH');await _loadTasks();setState((){});}catch(e){_snack('$e');}}
  Future<void> _addMemory() async {final v=memoryInput.text.trim();if(v.isEmpty)return;try{await api.request('/api/memories',method:'POST',body:{'content':v});memoryInput.clear();await _loadMemories();setState((){});}catch(e){_snack('$e');}}
  void _snack(String s)=>ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(s)));
  @override Widget build(BuildContext context){return Scaffold(body:SafeArea(child:Column(children:[_top(),Expanded(child:loading?const Center(child:CircularProgressIndicator()):_body()),_nav()])),);}
  Widget _top()=>Padding(padding:const EdgeInsets.fromLTRB(18,14,18,10),child:Row(children:[Container(width:42,height:42,decoration:BoxDecoration(borderRadius:BorderRadius.circular(14),gradient:const LinearGradient(colors:[Color(0xFF9B8CFF),Color(0xFF5E9BFF)])),child:const Icon(Icons.auto_awesome,color:Colors.white)),const SizedBox(width:12),const Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('My AI',style:TextStyle(fontSize:20,fontWeight:FontWeight.w800)),Text('Твой личный ассистент',style:TextStyle(color:Colors.white54,fontSize:12))])),IconButton(onPressed:_newChat,icon:const Icon(Icons.add_circle_outline,size:29))]));
  Widget _body(){if(tab==0)return _chat();if(tab==1)return _tasks();return _memory();}
  Widget _chat()=>Column(children:[Expanded(child:messages.isEmpty?const Center(child:Text('Привет!\nНапиши, что нужно сделать.',textAlign:TextAlign.center,style:TextStyle(fontSize:19,fontWeight:FontWeight.w600))):ListView.builder(padding:const EdgeInsets.fromLTRB(14,8,14,12),itemCount:messages.length,itemBuilder:(c,i){final m=messages[i];final user=m['role']=='user';return Align(alignment:user?Alignment.centerRight:Alignment.centerLeft,child:Container(margin:const EdgeInsets.only(bottom:9),padding:const EdgeInsets.symmetric(horizontal:15,vertical:11),constraints:const BoxConstraints(maxWidth:330),decoration:BoxDecoration(color:user?const Color(0xFF685CCB):const Color(0xFF171922),borderRadius:BorderRadius.circular(18)),child:Text('${m['content']}',style:const TextStyle(fontSize:15,height:1.35)));})),Container(padding:const EdgeInsets.fromLTRB(12,7,12,10),child:Row(crossAxisAlignment:CrossAxisAlignment.end,children:[Expanded(child:TextField(controller:input,minLines:1,maxLines:5,decoration:InputDecoration(hintText:'Напиши сообщение...',filled:true,fillColor:const Color(0xFF15171F),border:OutlineInputBorder(borderRadius:BorderRadius.circular(20),borderSide:BorderSide.none),contentPadding:const EdgeInsets.symmetric(horizontal:16,vertical:12)),onSubmitted:(_)=>_send())),const SizedBox(width:8),IconButton(onPressed:sending?null:_send,style:IconButton.styleFrom(backgroundColor:const Color(0xFF7668E8)),icon:const Icon(Icons.arrow_upward))]))]);
  Widget _tasks()=>_page('Задачи','То, что нужно сделать.',TextField(controller:taskInput,onSubmitted:(_)=>_addTask(),decoration:_dec('Новая задача',Icons.add_task),textInputAction:TextInputAction.done),Column(children:tasks.map((t)=>ListTile(onTap:()=>_toggle(t),leading:Icon(t['completed']==true?Icons.check_circle:Icons.radio_button_unchecked),title:Text('${t['title']}',style:TextStyle(decoration:t['completed']==true?TextDecoration.lineThrough:null))).toList()));
  Widget _memory()=>_page('Память','Важные вещи для ассистента.',TextField(controller:memoryInput,onSubmitted:(_)=>_addMemory(),decoration:_dec('Что запомнить?',Icons.bookmark_add_outlined),textInputAction:TextInputAction.done),Column(children:memories.map((m)=>ListTile(leading:const Icon(Icons.auto_awesome),title:Text('${m['content']}'))).toList()));
  Widget _page(String title,String sub,Widget add,Widget list)=>ListView(padding:const EdgeInsets.all(18),children:[Text(title,style:const TextStyle(fontSize:30,fontWeight:FontWeight.w800)),Text(sub,style:const TextStyle(color:Colors.white54)),const SizedBox(height:20),add,const SizedBox(height:12),list]);
  InputDecoration _dec(String hint,IconData icon)=>InputDecoration(hintText:hint,prefixIcon:Icon(icon),filled:true,fillColor:const Color(0xFF15171F),border:OutlineInputBorder(borderRadius:BorderRadius.circular(18),borderSide:BorderSide.none));
  Widget _nav()=>NavigationBar(selectedIndex:tab,onDestinationSelected:(i)=>setState(()=>tab=i),backgroundColor:const Color(0xFF0D0E13),indicatorColor:const Color(0xFF29243F),destinations:const [NavigationDestination(icon:Icon(Icons.chat_bubble_outline),selectedIcon:Icon(Icons.chat_bubble),label:'Чат'),NavigationDestination(icon:Icon(Icons.checklist),label:'Задачи'),NavigationDestination(icon:Icon(Icons.auto_awesome),label:'Память')]);
}
