# Create a Flutter + Supabase boilerplate as a downloadable zip

import os, json, textwrap, zipfile, pathlib

base = "/mnt/data/insta_diff_flutter_supabase"
os.makedirs(base, exist_ok=True)

# Directory structure
dirs = [
    "lib/pages",
    "lib/services",
    "lib/utils",
    "lib/models",
    "assets",
    "supabase",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# pubspec.yaml
pubspec = """
name: insta_diff
description: App para comparar seguidores do Instagram via export oficial (sem scraping).
publish_to: "none"
version: 0.1.0+1

environment:
  sdk: ">=3.3.0 <4.0.0"

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.8
  supabase_flutter: ^2.5.6
  file_picker: ^8.0.3
  archive: ^3.6.1
  path: ^1.9.0
  intl: ^0.19.0
  flutter_dotenv: ^5.1.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^4.0.0

flutter:
  uses-material-design: true
  assets:
    - assets/
    - .env
"""

# .env.example
env_example = """
SUPABASE_URL=coloque_sua_url_aqui
SUPABASE_ANON_KEY=coloque_seu_anon_key_aqui
"""

# README.md
readme = """
# Insta Diff — Flutter + Supabase (MVP)

App legal com assinatura para detectar **quem entrou** e **quem saiu** dos seus seguidores do Instagram, usando apenas o **arquivo oficial de exportação** (sem scraping).

## Como rodar
1. Instale Flutter (3.22+).
2. Crie um projeto no **Supabase** e copie **URL** e **anon key**.
3. Duplique `.env.example` para `.env` e preencha `SUPABASE_URL` e `SUPABASE_ANON_KEY`.
4. Rode as migrações SQL do diretório `supabase/` (Tables + Policies).
5. `flutter pub get`
6. `flutter run`

## Fluxo
- Login por e-mail (Supabase Magic Link).
- Upload do ZIP/JSON exportado do Instagram.
- Parser extrai lista de seguidores (`followers_*.json` ou CSV) e cria um **snapshot**.
- Comparação com snapshot anterior => eventos **follow/unfollow**.
- Telas:
  - Home (resumo),
  - Upload,
  - Mudanças (Entraram/Saíram).

> Observação: Sem scraping. O app depende do envio de novos arquivos pelo usuário (ex.: lembrete semanal).

## Próximos passos
- Paywall (In-App Purchases).
- Push Notifications.
- Relatórios e gráficos.
"""

# lib/main.dart
main_dart = r"""
import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'pages/login_page.dart';
import 'pages/home_page.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: ".env");

  final url = dotenv.env['SUPABASE_URL'];
  final anonKey = dotenv.env['SUPABASE_ANON_KEY'];

  if (url == null || anonKey == null) {
    throw Exception("Defina SUPABASE_URL e SUPABASE_ANON_KEY no .env");
  }

  await Supabase.initialize(
    url: url,
    anonKey: anonKey,
    authOptions: const FlutterAuthClientOptions(
      authFlowType: AuthFlowType.pkce,
    ),
  );

  runApp(const InstaDiffApp());
}

class InstaDiffApp extends StatelessWidget {
  const InstaDiffApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Insta Diff',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
        useMaterial3: true,
      ),
      debugShowCheckedModeBanner: false,
      home: const Root(),
    );
  }
}

class Root extends StatefulWidget {
  const Root({super.key});

  @override
  State<Root> createState() => _RootState();
}

class _RootState extends State<Root> {
  @override
  Widget build(BuildContext context) {
    return StreamBuilder<AuthState>(
      stream: Supabase.instance.client.auth.onAuthStateChange,
      builder: (context, snapshot) {
        final session = Supabase.instance.client.auth.currentSession;
        if (session == null) {
          return const LoginPage();
        } else {
          return const HomePage();
        }
      },
    );
  }
}
"""

# lib/pages/login_page.dart
login_page = r"""
import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _emailController = TextEditingController();
  bool _loading = false;
  String? _message;

  Future<void> _signIn() async {
    setState(() {
      _loading = true;
      _message = null;
    });

    try {
      await Supabase.instance.client.auth.signInWithOtp(
        email: _emailController.text.trim(),
        emailRedirectTo: null,
      );
      setState(() {
        _message = "Verifique seu e-mail para entrar (Magic Link).";
      });
    } on AuthException catch (e) {
      setState(() => _message = e.message);
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text("Insta Diff", style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
                const SizedBox(height: 12),
                const Text("Entre com seu e-mail para receber um link mágico."),
                const SizedBox(height: 24),
                TextField(
                  controller: _emailController,
                  decoration: const InputDecoration(labelText: "E-mail"),
                  keyboardType: TextInputType.emailAddress,
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: _loading ? null : _signIn,
                    child: _loading ? const CircularProgressIndicator() : const Text("Entrar"),
                  ),
                ),
                if (_message != null)...[
                  const SizedBox(height: 12),
                  Text(_message!, textAlign: TextAlign.center),
                ]
              ],
            ),
          ),
        ),
      ),
    );
  }
}
"""

# lib/pages/home_page.dart
home_page = r"""
import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:intl/intl.dart';
import 'upload_page.dart';
import 'diff_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int followerCount = 0;
  int newCount = 0;
  int lostCount = 0;
  bool loading = true;

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    final supa = Supabase.instance.client;
    final uid = supa.auth.currentUser!.id;

    final followersResp = await supa
        .from('followers')
        .select('*', const FetchOptions(count: CountOption.exact))
        .eq('user_id', uid);
    final eventsResp = await supa
        .from('events')
        .select('type', const FetchOptions(count: CountOption.exact))
        .eq('user_id', uid);

    setState(() {
      followerCount = (followersResp as List).length;
      newCount = (eventsResp as List).where((e) => e['type'] == 'follow').length;
      lostCount = (eventsResp as List).where((e) => e['type'] == 'unfollow').length;
      loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final df = DateFormat('dd/MM/yyyy HH:mm');

    return Scaffold(
      appBar: AppBar(
        title: const Text('Insta Diff'),
        actions: [
          IconButton(
            tooltip: 'Sair',
            onPressed: () async {
              await Supabase.instance.client.auth.signOut();
            },
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Card(
                    child: ListTile(
                      title: const Text('Seguidores atuais'),
                      subtitle: const Text('Total estimado pelo último arquivo processado'),
                      trailing: Text('$followerCount', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: Card(
                          child: ListTile(
                            title: const Text('Entraram'),
                            trailing: Text('$newCount', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Card(
                          child: ListTile(
                            title: const Text('Saíram'),
                            trailing: Text('$lostCount', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      icon: const Icon(Icons.upload_file),
                      label: const Text('Enviar arquivo do Instagram'),
                      onPressed: () async {
                        await Navigator.push(context, MaterialPageRoute(builder: (_) => const UploadPage()));
                        await _loadStats();
                      },
                    ),
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.compare),
                      label: const Text('Ver mudanças (diff)'),
                      onPressed: () {
                        Navigator.push(context, MaterialPageRoute(builder: (_) => const DiffPage()));
                      },
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
"""

# lib/pages/upload_page.dart
upload_page = r"""
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:archive/archive_io.dart';
import 'package:path/path.dart' as p;
import 'package:supabase_flutter/supabase_flutter.dart';
import '../utils/parser.dart';

class UploadPage extends StatefulWidget {
  const UploadPage({super.key});

  @override
  State<UploadPage> createState() => _UploadPageState();
}

class _UploadPageState extends State<UploadPage> {
  String? _status;
  bool _working = false;

  Future<void> _processFile() async {
    final res = await FilePicker.platform.pickFiles(
      withData: false,
      allowMultiple: false,
      type: FileType.custom,
      allowedExtensions: ['zip', 'json', 'csv'],
    );

    if (res == null) return;
    setState(() { _working = true; _status = "Lendo arquivo..."; });

    final supa = Supabase.instance.client;
    final uid = supa.auth.currentUser!.id;

    List<String> usernames = [];

    final path = res.files.single.path!;
    final ext = p.extension(path).toLowerCase();

    try {
      if (ext == '.zip') {
        final inputStream = InputFileStream(path);
        final archive = ZipDecoder().decodeBuffer(inputStream);
        usernames = await InstagramExportParser.extractFollowersFromArchive(archive);
      } else if (ext == '.json' || ext == '.csv') {
        usernames = await InstagramExportParser.extractFollowersFromFile(File(path));
      } else {
        throw Exception("Formato não suportado");
      }

      usernames = usernames.map((e) => e.trim().toLowerCase()).where((e) => e.isNotEmpty).toSet().toList();
      setState(() { _status = "Encontrados ${usernames.length} seguidores. Gravando snapshot..."; });

      // Create an import record
      final importResp = await supa.from('imports').insert({
        'user_id': uid,
        'source': 'instagram_export',
      }).select().single();

      final importId = importResp['id'] as int;

      // Load previous followers
      final currentFollowers = await supa
          .from('followers')
          .select('username')
          .eq('user_id', uid);

      final prev = (currentFollowers as List).map((e) => e['username'] as String).toSet();
      final now = usernames.toSet();

      final entered = now.difference(prev).toList();
      final left = prev.difference(now).toList();

      // Upsert followers table
      final toUpsert = now.map((u) => {
        'user_id': uid,
        'username': u,
        'first_seen': DateTime.now().toIso8601String(),
        'last_seen': DateTime.now().toIso8601String(),
        'last_status': 'current',
      }).toList();

      // Mark left as last_status=left and update last_seen
      final updates = left.map((u) => {
        'user_id': uid,
        'username': u,
        'last_seen': DateTime.now().toIso8601String(),
        'last_status': 'left',
      }).toList();

      if (toUpsert.isNotEmpty) {
        await supa.from('followers').upsert(toUpsert, onConflict: 'user_id,username');
      }
      for (final upd in updates) {
        await supa.from('followers').update({
          'last_seen': upd['last_seen'],
          'last_status': 'left',
        }).match({'user_id': uid, 'username': upd['username']});
      }

      // Insert events
      final eventRows = [
        ...entered.map((u) => {
              'user_id': uid,
              'username': u,
              'type': 'follow',
              'happened_at': DateTime.now().toIso8601String(),
              'import_id': importId,
            }),
        ...left.map((u) => {
              'user_id': uid,
              'username': u,
              'type': 'unfollow',
              'happened_at': DateTime.now().toIso8601String(),
              'import_id': importId,
            }),
      ];

      if (eventRows.isNotEmpty) {
        await supa.from('events').insert(eventRows);
      }

      setState(() {
        _status = "Processo concluído. Entraram: ${entered.length} | Saíram: ${left.length}";
      });

    } catch (e) {
      setState(() { _status = "Erro: $e"; });
    } finally {
      setState(() { _working = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Upload do arquivo Instagram")),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("Envie o ZIP/JSON/CSV que você baixou em 'Suas informações' no Instagram."),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _working ? null : _processFile,
                icon: const Icon(Icons.file_upload),
                label: const Text("Selecionar arquivo"),
              ),
            ),
            const SizedBox(height: 16),
            if (_status != null) Text(_status!),
          ],
        ),
      ),
    );
  }
}
"""

# lib/pages/diff_page.dart
diff_page = r"""
import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class DiffPage extends StatefulWidget {
  const DiffPage({super.key});

  @override
  State<DiffPage> createState() => _DiffPageState();
}

class _DiffPageState extends State<DiffPage> {
  List<Map<String, dynamic>> entered = [];
  List<Map<String, dynamic>> left = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final supa = Supabase.instance.client;
    final uid = supa.auth.currentUser!.id;

    final events = await supa
        .from('events')
        .select('username,type,happened_at')
        .eq('user_id', uid)
        .order('happened_at', ascending: false);

    setState(() {
      entered = (events as List).where((e) => e['type'] == 'follow').cast<Map<String, dynamic>>().toList();
      left = (events as List).where((e) => e['type'] == 'unfollow').cast<Map<String, dynamic>>().toList();
      loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Mudanças")),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : DefaultTabController(
              length: 2,
              child: Column(
                children: [
                  const TabBar(tabs: [
                    Tab(text: "Entraram"),
                    Tab(text: "Saíram"),
                  ]),
                  Expanded(
                    child: TabBarView(
                      children: [
                        _list(entered),
                        _list(left),
                      ],
                    ),
                  )
                ],
              ),
            ),
    );
  }

  Widget _list(List<Map<String, dynamic>> items) {
    if (items.isEmpty) {
      return const Center(child: Text("Sem eventos ainda. Faça upload de um arquivo."));
    }
    return ListView.separated(
      itemCount: items.length,
      itemBuilder: (context, i) {
        final e = items[i];
        return ListTile(
          title: Text(e['username'] ?? ''),
          subtitle: Text(e['happened_at'] ?? ''),
        );
      },
      separatorBuilder: (_, __) => const Divider(height: 1),
    );
  }
}
"""

# lib/utils/parser.dart
parser_dart = r"""
import 'dart:convert';
import 'dart:io';
import 'package:archive/archive.dart';

class InstagramExportParser {
  /// Tenta extrair a lista de seguidores de um ZIP de exportação oficial.
  static Future<List<String>> extractFollowersFromArchive(Archive archive) async {
    // Possíveis caminhos do JSON/CSV nos exports (vários formatos ao longo do tempo)
    final candidates = [
      // JSONs comuns
      RegExp(r'followers_.*\.json$', caseSensitive: false),
      RegExp(r'followers\.json$', caseSensitive: false),
      // CSV
      RegExp(r'followers_.*\.csv$', caseSensitive: false),
      RegExp(r'followers\.csv$', caseSensitive: false),
      // Alguns exports usam "connections" ou "followers_and_following"
      RegExp(r'connections/followers_.*\.json$', caseSensitive: false),
      RegExp(r'connections/followers\.json$', caseSensitive: false),
    ];

    for (final file in archive) {
      final name = file.name.replaceAll("\\", "/");
      if (file.isFile && candidates.any((rx) => rx.hasMatch(name))) {
        final data = file.content as List<int>;
        if (name.toLowerCase().endsWith('.json')) {
          return _parseFollowersJson(utf8.decode(data));
        } else if (name.toLowerCase().endsWith('.csv')) {
          return _parseFollowersCsv(utf8.decode(data));
        }
      }
    }

    // Fallback: tentar following caso o usuário queira comparar "que eu sigo"
    for (final file in archive) {
      final name = file.name.replaceAll("\\", "/");
      if (file.isFile && name.toLowerCase().contains('following') && name.toLowerCase().endsWith('.json')) {
        final data = file.content as List<int>;
        return _parseFollowersJson(utf8.decode(data));
      }
    }

    throw Exception("Não encontrei arquivo de seguidores no ZIP.");
  }

  /// Extrai de um arquivo solto (JSON ou CSV)
  static Future<List<String>> extractFollowersFromFile(File file) async {
    final content = await file.readAsString();
    if (file.path.toLowerCase().endsWith('.json')) {
      return _parseFollowersJson(content);
    } else if (file.path.toLowerCase().endsWith('.csv')) {
      return _parseFollowersCsv(content);
    }
    throw Exception("Formato não suportado (apenas JSON/CSV/ZIP).");
  }

  static List<String> _parseFollowersJson(String content) {
    final data = json.decode(content);
    final List<String> usernames = [];

    if (data is List) {
      // Alguns exports são lista de objetos com "string_list_data" -> [{"href": ".../username/", "value": "Username", "timestamp": 123}]
      for (final item in data) {
        if (item is Map && item['string_list_data'] is List && item['string_list_data'].isNotEmpty) {
          final first = item['string_list_data'][0];
          if (first is Map && first['href'] is String) {
            final href = first['href'] as String;
            final u = _usernameFromHref(href);
            if (u != null) usernames.add(u);
          } else if (first is Map && first['value'] is String) {
            usernames.add((first['value'] as String).toLowerCase());
          }
        } else if (item is Map && item['username'] is String) {
          usernames.add((item['username'] as String).toLowerCase());
        }
      }
    } else if (data is Map && data['followers'] is List) {
      for (final item in (data['followers'] as List)) {
        if (item is Map && item['username'] is String) {
          usernames.add((item['username'] as String).toLowerCase());
        }
      }
    }

    return usernames;
  }

  static List<String> _parseFollowersCsv(String content) {
    final lines = const LineSplitter().convert(content);
    final usernames = <String>[];
    for (var i = 1; i < lines.length; i++) {
      final row = lines[i].split(',');
      if (row.isNotEmpty) {
        final candidate = row[0].replaceAll('"', '').trim();
        if (candidate.isNotEmpty) {
          usernames.add(candidate.toLowerCase());
        }
      }
    }
    return usernames;
  }

  static String? _usernameFromHref(String href) {
    // Ex.: https://www.instagram.com/username/
    final uri = Uri.tryParse(href);
    if (uri == null) return null;
    final segments = uri.pathSegments.where((s) => s.isNotEmpty).toList();
    if (segments.isEmpty) return null;
    return segments.first.toLowerCase();
  }
}
"""

# lib/services/supabase_client.dart (optional helper)
services_supa = r"""
// Placeholder para serviços adicionais do Supabase se necessário futuramente.
"""

# supabase/schema.sql
schema_sql = r"""
-- Tables
create table if not exists public.imports (
  id bigserial primary key,
  user_id uuid not null,
  source text not null default 'instagram_export',
  imported_at timestamptz not null default now()
);

create table if not exists public.followers (
  id bigserial primary key,
  user_id uuid not null,
  username text not null,
  first_seen timestamptz,
  last_seen timestamptz,
  last_status text check (last_status in ('current','left')) default 'current',
  unique (user_id, username)
);

create table if not exists public.events (
  id bigserial primary key,
  user_id uuid not null,
  username text not null,
  type text check (type in ('follow','unfollow')) not null,
  happened_at timestamptz not null default now(),
  import_id bigint references public.imports(id) on delete set null
);

-- RLS
alter table public.imports enable row level security;
alter table public.followers enable row level security;
alter table public.events enable row level security;

-- Policies (owner-based: user_id = auth.uid())
create policy "imports own rows" on public.imports
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

create policy "followers own rows" on public.followers
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

create policy "events own rows" on public.events
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());
"""

# supabase/README.sql.md
supabase_readme = """
# Supabase SQL

1. No dashboard do Supabase, vá em **SQL** > **New query** e cole o conteúdo de `schema.sql`.
2. Execute.
3. Em **Authentication** > **Providers**, deixe **Email** habilitado (Magic Link).
"""

# Write files
files = {
    "pubspec.yaml": pubspec,
    ".env.example": env_example,
    "README.md": readme,
    "lib/main.dart": main_dart,
    "lib/pages/login_page.dart": login_page,
    "lib/pages/home_page.dart": home_page,
    "lib/pages/upload_page.dart": upload_page,
    "lib/pages/diff_page.dart": diff_page,
    "lib/utils/parser.dart": parser_dart,
    "lib/services/supabase_client.dart": services_supa,
    "supabase/schema.sql": schema_sql,
    "supabase/README.sql.md": supabase_readme,
}

for path, content in files.items():
    full = os.path.join(base, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(content).lstrip())

# Zip it
zip_path = "/mnt/data/insta_diff_flutter_supabase.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, filenames in os.walk(base):
        for fn in filenames:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, base)
            z.write(full, arcname=f"insta_diff_flutter_supabase/{rel}")

zip_path
