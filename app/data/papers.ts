export type Paper = {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  categories: string[];
  published: string;
  updated: string;
  citations: number;
  score: number;
  signal: string;
  source: string;
  sourceUrl?: string;
};

export const papers: Paper[] = [
  {
    id: "2402.19427",
    title: "The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery",
    authors: ["Chris Lu", "Cong Lu", "Robert T. Lange", "Jakob Foerster"],
    abstract:
      "A framework that enables foundation models to perform research ideation, experiment design, execution, and scientific writing in an iterative loop.",
    categories: ["cs.AI", "cs.LG"],
    published: "2024-08-12",
    updated: "2025-01-21",
    citations: 418,
    score: 0.94,
    signal: "Strong semantic match · active citation growth",
    source: "arXiv",
    sourceUrl: "https://arxiv.org/abs/2402.19427",
  },
  {
    id: "2310.11511",
    title: "SciBench: Evaluating College-Level Scientific Problem-Solving Abilities of Large Language Models",
    authors: ["Xiaoxuan Wang", "Zizhao Wang", "Jialong Liu", "Yangyi Chen"],
    abstract:
      "A benchmark of challenging scientific problems spanning mathematics, chemistry, physics, and biology, with fine-grained evaluation of reasoning quality.",
    categories: ["cs.CL", "cs.AI"],
    published: "2023-10-17",
    updated: "2024-05-29",
    citations: 152,
    score: 0.89,
    signal: "Matches evaluation intent · cited by saved work",
    source: "arXiv",
    sourceUrl: "https://arxiv.org/abs/2310.11511",
  },
  {
    id: "2304.05376",
    title: "Scientific Discovery in the Age of Artificial Intelligence",
    authors: ["Hanchen Wang", "Tianfan Fu", "Yue Zhao", "Jure Leskovec"],
    abstract:
      "A systematic review of how modern machine learning changes hypothesis generation, experimental design, simulation, and scientific communication.",
    categories: ["cs.LG", "stat.ML"],
    published: "2023-04-11",
    updated: "2024-02-08",
    citations: 367,
    score: 0.86,
    signal: "Foundational survey · broad field coverage",
    source: "arXiv",
    sourceUrl: "https://arxiv.org/abs/2304.05376",
  },
  {
    id: "2210.11416",
    title: "Galactica: A Large Language Model for Science",
    authors: ["Ross Taylor", "Marcin Kardas", "Guillem Cucurull", "Thomas Scialom"],
    abstract:
      "A large language model trained on scientific knowledge, including papers, reference material, knowledge bases, and many other scientific modalities.",
    categories: ["cs.CL", "cs.LG"],
    published: "2022-11-16",
    updated: "2022-11-16",
    citations: 1042,
    score: 0.82,
    signal: "High citation authority · model lineage match",
    source: "arXiv",
    sourceUrl: "https://arxiv.org/abs/2210.11416",
  },
  {
    id: "2302.04761",
    title: "Toolformer: Language Models Can Teach Themselves to Use Tools",
    authors: ["Timo Schick", "Jane Dwivedi-Yu", "Roberto Dessì", "Roberta Raileanu"],
    abstract:
      "A self-supervised approach for teaching language models which external tools to call, when to call them, and how to incorporate their results.",
    categories: ["cs.CL", "cs.AI"],
    published: "2023-02-09",
    updated: "2023-02-09",
    citations: 2891,
    score: 0.78,
    signal: "Method adjacency · strong downstream influence",
    source: "arXiv",
    sourceUrl: "https://arxiv.org/abs/2302.04761",
  },
  {
    id: "2110.08861",
    title: "A Generalist Agent",
    authors: ["Scott Reed", "Konrad Zolna", "Emilio Parisotto", "Sergio Gómez Colmenarejo"],
    abstract:
      "A single generalist sequence model trained across a wide variety of control, perception, and language tasks with shared representations.",
    categories: ["cs.AI", "cs.LG"],
    published: "2022-05-12",
    updated: "2022-05-19",
    citations: 934,
    score: 0.71,
    signal: "Exploratory connection · shared agent architecture",
    source: "arXiv",
    sourceUrl: "https://arxiv.org/abs/2110.08861",
  },
];

export const categoryOptions = [
  { value: "all", label: "All fields" },
  { value: "cs.AI", label: "Artificial intelligence" },
  { value: "cs.CL", label: "Computation & language" },
  { value: "cs.LG", label: "Machine learning" },
  { value: "stat.ML", label: "Statistical ML" },
];
