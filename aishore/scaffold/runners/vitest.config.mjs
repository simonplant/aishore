// Runs acceptance and finding tests with the project's own vitest config, whatever its `include`.
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { mergeConfig } from "vitest/config";

const root = process.cwd();
const names = ["vitest.config", "vite.config"].flatMap((n) => ["ts", "mts", "js", "mjs", "cjs", "cts"].map((e) => `${n}.${e}`));
const found = names.map((n) => resolve(root, n)).find(existsSync);
let base = {};
if (found) {
  const mod = await import(pathToFileURL(found).href);
  const cfg = mod.default ?? {};
  base = typeof cfg === "function" ? await cfg({ command: "serve", mode: "test" }) : cfg;
}
export default mergeConfig(base, {
  root,
  test: { include: ["tests/{acceptance,_review}/**/*.{accept,test,spec}.?(c|m)[jt]s?(x)"] },
});
