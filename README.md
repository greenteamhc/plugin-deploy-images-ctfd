# Challenge Deployer - CTFd Plugin

Plugin para CTFd que automatiza o processo de criação e deploy de desafios usando o chall-manager.

## 🚀 Funcionalidades

- ✅ Interface web para criar desafios via formulário
- ✅ Copia automaticamente os arquivos do template `example`
- ✅ Modifica `Pulumi.yaml`, `build.sh` e `main.go` com as configurações fornecidas
- ✅ Executa o `build.sh` automaticamente
- ✅ Envia o desafio para o registry usando ORAS
- ✅ Retorna a URL do registry onde o desafio foi salvo
- ✅ Lista todos os desafios deployados
- ✅ Permite deletar desafios (apenas diretório local)

## 📋 Pré-requisitos

### No ambiente do chall-manager:

1. **Diretório base**: `/opt/ctfd-chall-manager/hack/desafios/`
2. **Diretório example**: `/opt/ctfd-chall-manager/hack/desafios/example/` contendo:
   - `Pulumi.yaml`
   - `build.sh`
   - `main.go`
   - `go.mod`
   - `go.sum`

3. **Ferramentas necessárias**:
   - `go` (Golang)
   - `yq` (YAML processor)
   - `oras` (OCI Registry As Storage)
   - `bash`

4. **Registry**: Registry OCI rodando e acessível (ex: `localhost:5000`)

### No CTFd:

- CTFd 3.x
- Acesso ao diretório `/opt/ctfd-chall-manager/hack/desafios/` (via volume mount ou mesmo host)

## 📦 Instalação

### Opção 1: Instalação Manual

1. Copie a pasta `challenge_deployer` para o diretório de plugins do CTFd:

```bash
cp -r challenge_deployer /opt/CTFd/CTFd/plugins/
```

2. Reinicie o CTFd:

```bash
docker-compose restart ctfd
```

### Opção 2: Via Docker Compose

Adicione o volume mount no seu `docker-compose.yml`:

```yaml
services:
  ctfd:
    image: ctfd/ctfd:3.8.1
    volumes:
      - ./plugins/challenge_deployer:/opt/CTFd/CTFd/plugins/challenge_deployer
      - /opt/ctfd-chall-manager/hack:/opt/ctfd-chall-manager/hack
```

## 🎯 Uso

### 1. Acessar a interface

Faça login como admin e acesse:

```
https://seu-ctfd.com/admin/challenge-deployer
```

### 2. Criar um novo desafio

Preencha o formulário com:

- **Nome do Desafio**: Nome único (ex: `web01`, `pwn_easy`)
  - Apenas letras, números, `-` e `_`
  
- **Imagem Docker**: Imagem do Docker Hub (ex: `lukerking/sqli:latest`)
  
- **Porta Interna**: Porta que o container expõe (ex: `80`)
  
- **Protocolo**: `tcp` ou `udp` (padrão: `tcp`)
  
- **Hostname**: Domínio onde os desafios serão acessíveis (ex: `desafios.ctfgthc.com.br`)
  
- **Registry URL**: URL do registry (ex: `localhost:5000/`)

### 3. Deploy

Clique em **Criar e Deploy**. O plugin irá:

1. ✅ Criar pasta `/opt/ctfd-chall-manager/hack/desafios/{nome_desafio}/`
2. ✅ Copiar arquivos do `example`
3. ✅ Modificar `Pulumi.yaml` com o nome do desafio
4. ✅ Modificar `build.sh` com nome e registry
5. ✅ Modificar `main.go` com imagem Docker, porta, hostname e protocolo
6. ✅ Executar `build.sh`
7. ✅ Retornar a URL do registry: `localhost:5000/gthc/{nome_desafio}:latest`

### 4. Resultado

Após o deploy bem-sucedido, você verá:

- ✅ Mensagem de sucesso
- ✅ URL do registry (pode copiar com um clique)
- ✅ Output do build script
- ✅ Desafio aparece na lista de "Desafios Deployados"

## 🔧 Estrutura de Arquivos

```
challenge_deployer/
├── __init__.py              # Registro do plugin
├── routes.py                # Rotas da API e lógica de deploy
├── templates/
│   └── challenge_deployer_admin.html  # Interface web
└── assets/
    └── challenge_deployer.js          # JavaScript do frontend
```

## 📝 Endpoints da API

### GET `/admin/challenge-deployer/`
Interface web de administração

### GET `/admin/challenge-deployer/api/challenges`
Lista todos os desafios deployados

**Resposta:**
```json
{
  "success": true,
  "challenges": [
    {
      "name": "web01",
      "path": "/opt/ctfd-chall-manager/hack/desafios/web01"
    }
  ]
}
```

### POST `/admin/challenge-deployer/api/deploy`
Cria e faz deploy de um novo desafio

**Request:**
```json
{
  "challenge_name": "web01",
  "docker_image": "lukerking/sqli:latest",
  "internal_port": "80",
  "protocol": "tcp",
  "hostname": "desafios.ctfgthc.com.br",
  "registry": "localhost:5000/"
}
```

**Resposta (sucesso):**
```json
{
  "success": true,
  "message": "Desafio criado e enviado para o registry com sucesso!",
  "registry_url": "localhost:5000/gthc/web01:latest",
  "output": "... build output ..."
}
```

### DELETE `/admin/challenge-deployer/api/delete/<challenge_name>`
Deleta o diretório de um desafio

**Resposta:**
```json
{
  "success": true,
  "message": "Desafio 'web01' deletado com sucesso"
}
```

## 🐛 Troubleshooting

### Erro: "Diretório example não encontrado"

Verifique se o caminho `/opt/ctfd-chall-manager/hack/desafios/example/` existe e está acessível pelo container do CTFd.

**Solução**: Monte o volume corretamente no `docker-compose.yml`.

### Erro: "Timeout: Build script demorou mais de 5 minutos"

O build.sh está demorando muito (provavelmente pull de imagem grande).

**Solução**: Ajuste o timeout em `routes.py`, linha com `timeout=300`.

### Erro ao executar build.sh

Verifique se as ferramentas estão instaladas:

```bash
docker exec -it ctfd bash
which go yq oras
```

**Solução**: Instale as dependências no container ou use um container customizado.

### Registry não acessível

Verifique se o registry está rodando:

```bash
curl http://localhost:5000/v2/_catalog
```

**Solução**: Configure corretamente o registry ou ajuste a URL no formulário.

## 🔒 Segurança

⚠️ **IMPORTANTE**: Este plugin executa comandos shell e cria arquivos no sistema. Use apenas em ambiente confiável e com acesso restrito a administradores.

- ✅ Apenas administradores podem acessar (`@admins_only`)
- ✅ Validação de nome do desafio (apenas `[a-zA-Z0-9_-]+`)
- ✅ Não permite deletar o diretório `example`
- ⚠️ Não valida o conteúdo das imagens Docker
- ⚠️ Executa `build.sh` com permissões do container CTFd

## 📄 Licença

MIT License - Veja arquivo LICENSE para detalhes.

## 🤝 Contribuindo

Pull requests são bem-vindos! Para mudanças maiores, abra uma issue primeiro.

## 🙏 Créditos

Desenvolvido para integração com [chall-manager](https://github.com/ctfer-io/chall-manager) da ctfer.io.
