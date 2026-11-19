# Publishing @webz.io/freellmapi to npm

## Prerequisites

- npm account with access to the `@webz.io` scope
- A clean `packages/freellmapi` directory (no `node_modules` leftover from a failed install)

## Build

```bash
cd packages/freellmapi
npm install
npm test
npm run build
```

`prepublishOnly` runs the tests and the build again.

## Upload

```bash
npm publish --access public
```

## Verify

```bash
npm install @webz.io/freellmapi
node -e "import('@webz.io/freellmapi').then((m) => console.log(m.WebzSearchProvider.name))"
```
