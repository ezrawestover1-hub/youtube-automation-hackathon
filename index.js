const fs = require("node:fs/promises");
const path = require("node:path");
const http = require("node:http");

const PORT = Number(process.env.PORT || 3000);
const ROOT = __dirname;
const ENCODING = "utf8";

async function readAsset(filePath, res) {
  const fullPath = path.join(ROOT, filePath);

  try {
    const contents = await fs.readFile(fullPath, ENCODING);
    const ext = path.extname(fullPath).toLowerCase();
    const mime =
      ext === ".css"
        ? "text/css"
        : ext === ".js"
          ? "application/javascript"
          : ext === ".json"
            ? "application/json"
            : "text/html";

    res.writeHead(200, { "Content-Type": `${mime}; charset=utf-8` });
    res.end(contents);
    return;
  } catch (err) {
    if (err.code !== "ENOENT") {
      console.error("Asset read failed:", err);
    }
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Not found");
  }
}

async function handleRequest(req, res) {
  const cleanPath = decodeURIComponent(req.url || "/").split("?")[0] || "/";

  if (cleanPath === "/" || cleanPath === "/index.html") {
    await readAsset("index.html", res);
    return;
  }

  const sanitized = cleanPath.replace(/^\/+/, "");
  if (sanitized.startsWith(".") || /\\/\\.\\./.test(sanitized)) {
    res.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Bad request");
    return;
  }

  const file = path.join(ROOT, sanitized);
  if (file.startsWith(ROOT) && (file.endsWith(".html") || file.endsWith(".css") || file.endsWith(".js") || file.endsWith(".json") || file.endsWith(".txt") || file.endsWith(".md"))) {
    await readAsset(sanitized, res);
    return;
  }

  res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
  res.end("Not found");
}

if (require.main === module) {
  const server = http.createServer((req, res) => {
    handleRequest(req, res).catch((err) => {
      console.error("Unhandled request error:", err);
      res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("Server error");
    });
  });

  server.listen(PORT, () => {
    console.log(`DropFix landing page running on http://localhost:${PORT}`);
  });
}

module.exports = async function handler(req, res) {
  await handleRequest(req, res);
};
