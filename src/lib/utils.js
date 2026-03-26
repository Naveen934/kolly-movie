export const PALETTES = [
  ["#b71c2c","#7b0e1a"],["#c45e10","#7a3a08"],["#1a6b5a","#0d3d32"],
  ["#5c3dbf","#321e80"],["#0d7a6e","#054d46"],["#8b2252","#4d1030"],
  ["#8b5e0a","#4d3306"],["#1a4d8b","#0a2852"],["#2d6e1a","#143d08"],
];

export function getPalette(name = "") {
  const n = String(name || "");
  const idx = ((n.charCodeAt(0)||0)+(n.charCodeAt(1)||0)) % PALETTES.length;
  return PALETTES[idx];
}

export const toSlug = (name) => (name || '')
  .toLowerCase()
  .replace(/[^a-z0-9\s]/g, '')
  .replace(/\s+/g, '-');

export const getMovieImageUrl = (name, year) => {
  if (!name || !year) return null;
  const slug = toSlug(name);
  return `https://moviesda18.com/uploads/images/${slug}-${year}.webp`;
};
