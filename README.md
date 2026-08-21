# GameHub

Um site social de jogos feito em Python 3 + Flask + SQLite.

## Recursos incluídos

- Cadastro e login individual
- Senhas armazenadas com hash
- Perfil do usuário
- Biblioteca de jogos
- Avaliações de 1 a 10
- Comentários nas avaliações
- Feed estilo rede social
- Upload de imagens e vídeos
- Comentários nas publicações
- Área administrativa
- Configurações do nome, descrição e cor do site
- Cadastro de jogos pela área administrativa
- Banco SQLite, fácil de trocar por PostgreSQL depois

## Instalação

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
flask --app app init
python app.py
```

Depois abra:

http://127.0.0.1:5000

Admin inicial:

- E-mail: admin@gamehub.local
- Senha: admin123

**Troque essa senha antes de colocar o site na internet.**

## Próximas melhorias recomendadas

- Curtidas
- Seguir usuários
- Busca de jogos
- API externa de jogos (RAWG, IGDB etc.)
- Tags/gêneros
- Página de descoberta
- Notificações
- Moderação de conteúdo
- Recuperação de senha por e-mail
- CSRF
- Rate limiting
- PostgreSQL
- Armazenamento de mídia em S3/Cloudflare R2
