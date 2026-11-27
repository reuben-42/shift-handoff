/**
 * Rule #1 for the frontend (docs/PLAN.md): dependencies point inward.
 *   domain          imports nothing (no React, no fetch, no npm packages)
 *   application     imports domain only
 *   presentation    never imports infrastructure
 *   infrastructure  is imported only by main.tsx (the composition root)
 * Test files are excluded: they may import vitest and testing-library.
 */
/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: "domain-imports-nothing",
      comment: "domain/ is pure TypeScript: it may only import other domain/ files.",
      severity: "error",
      from: { path: "^src/domain/" },
      to: { pathNot: "^src/domain/" },
    },
    {
      name: "application-imports-domain-only",
      comment: "application/ may import only application/ and domain/.",
      severity: "error",
      from: { path: "^src/application/" },
      to: { pathNot: "^src/(application|domain)/" },
    },
    {
      name: "presentation-never-imports-infrastructure",
      comment: "Components and hooks get gateways through GatewayProvider, never directly.",
      severity: "error",
      from: { path: "^src/presentation/" },
      to: { path: "^src/infrastructure/" },
    },
    {
      name: "only-main-imports-infrastructure",
      comment: "main.tsx is the composition root; nothing else may construct gateways.",
      severity: "error",
      from: { pathNot: "^src/(main\\.tsx|infrastructure/)" },
      to: { path: "^src/infrastructure/" },
    },
    {
      name: "infrastructure-never-imports-presentation",
      comment: "Gateways depend on application ports, not on UI.",
      severity: "error",
      from: { path: "^src/infrastructure/" },
      to: { path: "^src/presentation/" },
    },
    {
      name: "no-circular",
      severity: "error",
      from: {},
      to: { circular: true },
    },
  ],
  options: {
    doNotFollow: { path: "node_modules" },
    exclude: { path: "\\.(test|spec)\\.tsx?$|test-setup\\.ts$" },
    tsPreCompilationDeps: true,
    tsConfig: { fileName: "tsconfig.json" },
    enhancedResolveOptions: {
      exportsFields: ["exports"],
      conditionNames: ["import", "require", "node", "default", "types"],
    },
  },
};
