import type { MetadataRoute } from "next";

const productionUrl = "https://aster-research.shawn22587.chatgpt.site";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: productionUrl,
      lastModified: new Date("2026-07-29T00:00:00Z"),
      changeFrequency: "weekly",
      priority: 1,
    },
  ];
}
