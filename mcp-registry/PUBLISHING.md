# Publishing to the official MCP Registry

Publishes the hosted server `https://news-search-mcp.webz.io/mcp` to
[registry.modelcontextprotocol.io](https://registry.modelcontextprotocol.io) as
**`io.webz/news-search`**.

Why it matters: the official registry is the upstream source for MCP
aggregators and client directories (PulseMCP, Glama, and others ingest it), so
one publish propagates everywhere.

## What is in this folder

| File | Purpose | Commit? |
|------|---------|---------|
| `server.json` | Registry metadata (validated against the live schema) | Yes |
| `key.pem` | Ed25519 private key that proves ownership of `webz.io` | **No** (gitignored) |
| `mcp-registry-auth.txt` | Public-key proof record derived from `key.pem` | Yes |

## One-time setup: domain verification

The name `io.webz/news-search` requires proving control of `webz.io`.
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

> The keypair was generated on 2026-09-16 with OpenSSL 3.0 (Ed25519). If
> `key.pem` is ever lost or leaked, regenerate with
> `openssl genpkey -algorithm Ed25519 -out key.pem`, refresh
> `mcp-registry-auth.txt`, and replace (not add) the TXT record.

## Publish

From this directory, once the TXT record has propagated
(`dig +short TXT webz.io` should show the `v=MCPv1` record):

```bash
# 1. Login (proves domain ownership by signing with key.pem)
PRIVATE_KEY="$(openssl pkey -in key.pem -noout -text | grep -A3 'priv:' | tail -n +2 | tr -d ' :\n')"
~/.local/bin/mcp-publisher login dns --domain webz.io --private-key "${PRIVATE_KEY}"

# 2. Publish
~/.local/bin/mcp-publisher publish

# 3. Verify
curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=io.webz/news-search"
```

If using Option B, replace step 1 with
`mcp-publisher login http --domain webz.io --private-key "${PRIVATE_KEY}"`.

## Updating the listing

Bump `version` in `server.json` and run `mcp-publisher publish` again
(login is cached, but re-login with the same key works any time).
Validate first with `mcp-publisher validate`.

## Notes

- GitHub auth is not an option for the org namespace: it requires the
  **Owner** role in the `Webhose` GitHub org, and it would also force the
  unbranded name `io.github.<user>/...`. Domain auth additionally satisfies
  the registry rule that a remote URL's host must fall under the verified
  domain (`news-search-mcp.webz.io` ⊂ `webz.io`).
- `mcp-publisher` binary is installed at `~/.local/bin/mcp-publisher`
  (from the [registry releases page](https://github.com/modelcontextprotocol/registry/releases)).
