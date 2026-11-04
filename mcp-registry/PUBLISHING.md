# Publishing to the official MCP Registry

Publishes the hosted Webz.io MCP servers to
[registry.modelcontextprotocol.io](https://registry.modelcontextprotocol.io)
under the `io.webz` namespace.

Why it matters: the official registry is the upstream source for MCP
aggregators and client directories (PulseMCP, Glama, and others ingest it), so
one publish propagates everywhere.

## Servers

| Registry name | MCP URL | File |
|---------------|---------|------|
| `io.webz/news-search` | `https://news-search-mcp.webz.io/mcp` | `server.json` |
| `io.webz/news` | `https://news-mcp.webz.io/mcp` | `news/server.json` |
| `io.webz/blogs` | `https://blogs-mcp.webz.io/mcp` | `blogs/server.json` |
| `io.webz/forums` | `https://forums-mcp.webz.io/mcp` | `forums/server.json` |
| `io.webz/seg-news` | `https://seg-news-mcp.webz.io/mcp` | `seg-news/server.json` |
| `io.webz/seg-blogs` | `https://seg-blogs-mcp.webz.io/mcp` | `seg-blogs/server.json` |
| `io.webz/seg-forums` | `https://seg-forums-mcp.webz.io/mcp` | `seg-forums/server.json` |

The six `news` through `seg-forums` entries match the server cards those hosts
serve at `/mcp/server-card`. Keep names, titles, and descriptions in sync with
them. The registry caps `description` at 100 characters.

## What is in this folder

| File | Purpose | Commit? |
|------|---------|---------|
| `server.json`, `*/server.json` | Registry metadata, one file per server | Yes |
| `key.pem` | Ed25519 private key that proves ownership of `webz.io` | **No** (gitignored) |
| `mcp-registry-auth.txt` | Public-key proof record derived from `key.pem` | Yes |

## One-time setup: domain verification

The `io.webz/*` names require proving control of `webz.io`.
Two options; DNS is standard.

### Option A: DNS TXT record (recommended)

Ask whoever manages DNS for `webz.io` to add this TXT record **on the apex**
(`webz.io`, not a subdomain or selector — SPF-style placement):

```
webz.io. IN TXT "v=MCPv1; k=ed25519; p=<public key from mcp-registry-auth.txt>"
```

The exact value is the contents of `mcp-registry-auth.txt`. The record must
stay in place for future publishes (version bumps), so treat it as permanent.

### Option B: well-known file

Serve the contents of `mcp-registry-auth.txt` at
`https://webz.io/.well-known/mcp-registry-auth` (content type `text/plain`).

> The current keypair was generated on 2026-11-02 with OpenSSL 3.0 (Ed25519),
> replacing the 2026-09-16 key, which was lost. Keep a copy of `key.pem` in the
> team secrets store. If it is lost or leaked, regenerate with
> `openssl genpkey -algorithm Ed25519 -out key.pem`, refresh
> `mcp-registry-auth.txt` with
> `printf 'v=MCPv1; k=ed25519; p=%s' "$(openssl pkey -in key.pem -pubout -outform DER | tail -c 32 | base64)" > mcp-registry-auth.txt`,
> and replace (not add) the TXT record.

## Publish

From this directory, once the TXT record has propagated
(`dig +short TXT webz.io` should show the `v=MCPv1` record that matches
`mcp-registry-auth.txt`):

```bash
# 1. Login (proves domain ownership by signing with key.pem)
PRIVATE_KEY="$(openssl pkey -in key.pem -noout -text | grep -A3 'priv:' | tail -n +2 | tr -d ' :\n')"
mcp-publisher login dns --domain webz.io --private-key "${PRIVATE_KEY}"

# 2. Publish every server
mcp-publisher publish
for dir in news blogs forums seg-news seg-blogs seg-forums; do
  (cd "$dir" && mcp-publisher publish)
done

# 3. Verify
curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=io.webz"
```

If using Option B, replace step 1 with
`mcp-publisher login http --domain webz.io --private-key "${PRIVATE_KEY}"`.

## Updating a listing

Bump `version` in that server's `server.json` and run `mcp-publisher publish`
from its directory again (login is cached, but re-login with the same key works
any time). Validate first with `mcp-publisher validate`.

## Notes

- GitHub auth is not an option for the org namespace: it requires the
  **Owner** role in the `Webhose` GitHub org, and it would also force the
  unbranded name `io.github.<user>/...`. Domain auth additionally satisfies
  the registry rule that a remote URL's host must fall under the verified
  domain (`*.webz.io` ⊂ `webz.io`).
- Install `mcp-publisher` from the
  [registry releases page](https://github.com/modelcontextprotocol/registry/releases).
