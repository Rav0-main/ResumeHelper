import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const extraArgs = process.argv.slice(2);

/** @param {string} cmd @param {string[]} cmdArgs @returns {number | null} */
function tryRun(cmd, cmdArgs) {
  const r = spawnSync(cmd, cmdArgs, { cwd: root, stdio: "inherit", env: process.env });
  if (r.error) {
    const code = r.error.code;
    if (code === "ENOENT") return null;
    console.error(r.error);
    process.exit(1);
  }
  if (r.signal) {
    process.exit(1);
  }
  return r.status ?? 0;
}

const scriptRel = path.join("scripts", "dev.py");
/** @type {Array<[string, string[]]>} */
const attempts = [];

if (process.env.PYTHON) {
  attempts.push([process.env.PYTHON, [scriptRel, ...extraArgs]]);
}
attempts.push(["python3", [scriptRel, ...extraArgs]]);
attempts.push(["python", [scriptRel, ...extraArgs]]);
if (process.platform === "win32") {
  attempts.push(["py", ["-3", scriptRel, ...extraArgs]]);
}

for (const [cmd, args] of attempts) {
  const code = tryRun(cmd, args);
  if (code !== null) {
    process.exit(code);
  }
}

console.error(
  "Не найден интерпретатор Python. Установите Python 3 или задайте переменную окружения PYTHON (путь к исполняемому файлу).",
);
process.exit(1);
