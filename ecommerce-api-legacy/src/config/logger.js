function timestamp() {
    return new Date().toISOString();
}

const logger = {
    info: (msg) => console.log(`[INFO] ${timestamp()} ${msg}`),
    warn: (msg) => console.warn(`[WARN] ${timestamp()} ${msg}`),
    error: (msg, err) => console.error(`[ERROR] ${timestamp()} ${msg}`, err ? (err.stack || err) : ''),
};

module.exports = logger;
