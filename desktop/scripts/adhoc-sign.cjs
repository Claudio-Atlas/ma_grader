// electron-builder afterPack hook: ad-hoc sign the macOS app ("codesign -s -").
//
// We don't have an Apple Developer ID, so electron-builder skips signing
// (mac.identity = null). Left like that, the bundle keeps the stock Electron
// binary's signature, which no longer matches the renamed app — macOS then
// calls the downloaded app "damaged" and offers only "Move to Trash".
// An ad-hoc signature is free and makes the bundle consistent, so instead users
// get the normal "can't verify the developer" prompt, which System Settings →
// Privacy & Security → "Open Anyway" gets past.
//
// Runs after the .app is assembled and before the .dmg is built.

const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const MACHO_MAGICS = new Set([
  0xfeedface, 0xfeedfacf, 0xcefaedfe, 0xcffaedfe, // thin 32/64-bit, either endian
  0xcafebabe, 0xbebafeca,                         // universal (fat)
]);

function isMachO(file) {
  const fd = fs.openSync(file, "r");
  try {
    const buf = Buffer.alloc(4);
    if (fs.readSync(fd, buf, 0, 4, 0) < 4) return false;
    return MACHO_MAGICS.has(buf.readUInt32BE(0));
  } finally {
    fs.closeSync(fd);
  }
}

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(p, out);
    else if (entry.isFile()) out.push(p);
  }
  return out;
}

function sign(target, deep = false) {
  const args = ["--force", "--sign", "-"];
  if (deep) args.push("--deep");
  execFileSync("codesign", [...args, target], { stdio: "inherit" });
}

exports.default = async function adhocSign(context) {
  if (context.electronPlatformName !== "darwin") return;

  const appPath = path.join(
    context.appOutDir,
    `${context.packager.appInfo.productFilename}.app`
  );

  // 1) The bundled Python engine (PyInstaller) lives in Resources, where
  //    `codesign --deep` doesn't reach. Sign each of its executables/libraries
  //    so they're allowed to run on Apple Silicon.
  const engineDir = path.join(appPath, "Contents", "Resources", "engine");
  if (fs.existsSync(engineDir)) {
    for (const file of walk(engineDir)) {
      if (isMachO(file)) sign(file);
    }
  }

  // 2) The app itself, including Electron's frameworks and helper apps.
  sign(appPath, true);

  execFileSync("codesign", ["--verify", "--deep", "--strict", appPath], { stdio: "inherit" });
  console.log(`  • ad-hoc signed ${appPath}`);
};
