/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.TAURI_BUILD === "1" ? "export" : undefined,
  images: { unoptimized: true },
  trailingSlash: true,
  reactStrictMode: true,

  // Avoid scanning Tauri/Rust artifacts during build (can hang file tracing on Windows).
  experimental: {
    outputFileTracingExcludes: {
      "*": [
        "./src-tauri/**",
        "./node_modules/@tauri-apps/**",
      ],
    },
  },

  webpack: (config, { dev }) => {
    if (!dev) {
      config.watchOptions = {
        ...config.watchOptions,
        ignored: [
          "**/node_modules/**",
          "**/src-tauri/**",
          "**/.venv/**",
          "**/backend-pack/**",
        ],
      };
    }
    return config;
  },
};

export default nextConfig;
