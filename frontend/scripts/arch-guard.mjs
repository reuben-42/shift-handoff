// Rule #1 guard: prove dependency-cruiser actually fails on layer violations.
// Plants one bad file at a time, runs depcruise, expects a failure, cleans up.
import { execFileSync } from "node:child_process";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";

const cases = [
  ["src/domain/__guard__.ts", 'import { useState } from "react";\nexport const x = useState;\n', "domain-imports-nothing"],
  ["src/application/__guard__.ts", 'import { App } from "../presentation/App";\nexport const x = App;\n', "application-imports-domain-only"],
  ["src/presentation/__guard__.ts", 'import { x } from "../infrastructure/http/__guard_target__";\nexport const y = x;\n', "presentation-never-imports-infrastructure"],
];
const target = "src/infrastructure/http/__guard_target__.ts";

function depcruise() {
  try {
    execFileSync("npx", ["depcruise", "src", "--config", ".dependency-cruiser.cjs"], { stdio: "pipe" });
    return { ok: true, out: "" };
  } catch (err) {
    return { ok: false, out: String(err.stdout) };
  }
}

let failed = false;
writeFileSync(target, "export const x = 1;\n");
try {
  if (!depcruise().ok) {
    console.error("✗ the real tree should pass dependency-cruiser");
    failed = true;
  }
  for (const [file, body, rule] of cases) {
    mkdirSync(dirname(file), { recursive: true });
    writeFileSync(file, body);
    try {
      const res = depcruise();
      if (res.ok || !res.out.includes(rule)) {
        console.error(`✗ ${file}: expected rule "${rule}" to fail`);
        failed = true;
      } else {
        console.log(`✓ ${rule} catches ${file}`);
      }
    } finally {
      rmSync(file);
    }
  }
} finally {
  rmSync(target);
}
process.exit(failed ? 1 : 0);
