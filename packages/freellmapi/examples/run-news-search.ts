import { WebzSearchProvider } from "../src/index.js";

const provider = new WebzSearchProvider();
const response = await provider.search({
  query: "recent developments on EU AI regulation",
  max_results: 5,
  topic: "news",
});

for (const hit of response.results) {
  console.log(hit.score ?? "-", hit.title);
  console.log(hit.url);
}
