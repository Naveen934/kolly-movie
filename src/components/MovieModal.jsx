import { useEffect, useState, useRef } from 'react';
import { X, Play, Plus, ThumbsUp, ChevronDown, Download, Star, Calendar } from 'lucide-react';
import { getPalette, getMovieImageUrl, toSlug } from '../lib/utils';

const CardBg = ({ name, fontSize = "8rem" }) => {
  const [c1, c2] = getPalette(name);
  return (
    <div 
      className="absolute inset-0 flex items-center justify-center font-['Bebas_Neue'] text-white/10 select-none"
      style={{ background: `linear-gradient(135deg, ${c1}, ${c2})`, fontSize }}
    >
      {(name || "?")[0]}
    </div>
  );
};

const MovieModal = ({ movie, allMovies = [], onMovieClick, onClose }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const modalRef = useRef(null);

  useEffect(() => {
    if (movie) {
      fetchRecommendations();
      window.scrollTo({ top: 0, behavior: 'smooth' });
      // Disable body scroll
      document.body.style.overflow = 'hidden';
    }
    const handleEsc = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handleEsc);
    
    return () => {
      window.removeEventListener('keydown', handleEsc);
      // Re-enable body scroll
      document.body.style.overflow = 'unset';
    };
  }, [movie?.movie_name, onClose]);

  const fetchRecommendations = async () => {
    setLoadingRecs(true);
    try {
      const response = await fetch(
        `/api/recommend?movie=${encodeURIComponent(movie.movie_name)}`
      );
      const data = await response.json();
      if (data.recommendations) setRecommendations(data.recommendations);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoadingRecs(false);
    }
  };

  const handleRecommendationClick = (rec) => {
    const recName = rec.name;
    const needle = recName.toLowerCase().trim();
    const needleWords = needle.split(/\s+/);

    let found = allMovies.find(m => m.movie_name.toLowerCase().trim() === needle);

    if (!found) {
      let bestScore = 0;
      let bestMatch = null;
      for (const m of allMovies) {
        const hay = m.movie_name.toLowerCase().trim();
        const hayWords = hay.split(/\s+/);
        const shared = hayWords.filter(w => w.length > 1 && needleWords.includes(w)).length;
        const score = shared / hayWords.length;
        if (score > bestScore || (score === bestScore && hay.length > (bestMatch?.movie_name?.length || 0))) {
          bestScore = score;
          bestMatch = m;
        }
      }
      if (bestScore >= 0.5) found = bestMatch;
    }

    if (!found) {
      found = {
        id: `rec_stub_${recName}`,
        movie_name: recName,
        story: null,
        stars: null,
        director_name: null,
        gentre: null,
        genre: null,
        year: rec.year,
        poster: rec.poster
      };
    }
    onMovieClick(found);
  };

  const handlePlay = () => {
    const name = movie.movie_name;
    const cast = movie.stars || '';
    const castFirst = cast.split(',')[0].trim();
    const query = castFirst ? `${name} Full Tamil Movie ${castFirst}` : `${name} Full Tamil Movie`;
    window.open(`https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`, '_blank');
  };

  const handleDownload = () => {
    const slug = toSlug(movie.movie_name);
    const year = movie.release_year || movie.year || '';
    window.open(`https://moviesda18.com/${slug}-${year}-movie/`, '_blank');
  };

  if (!movie) return null;

  const genres = (movie.gentre || movie.genre || '').split(/[,|/]/).map(g => g.trim()).filter(Boolean);
  const fields = [
    { label: "Director", value: movie.director_name || movie.director },
    { label: "Writers", value: movie.writers_name || movie.writers },
    { label: "Stars", value: movie.stars || movie.cast },
    { label: "Release Year", value: movie.release_year || movie.year },
  ].filter(f => f.value);

  return (
    <div 
      className="fixed inset-0 z-[1000] flex items-center justify-center p-0 md:p-6 bg-black/95 backdrop-blur-md animate-in fade-in duration-300 overflow-y-auto no-scrollbar"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div 
        ref={modalRef}
        className="bg-[#090910] border-0 md:border md:border-white/10 rounded-0 md:rounded-2xl w-full max-w-5xl min-h-screen md:min-h-0 md:max-h-[92vh] overflow-y-auto no-scrollbar shadow-2xl animate-in zoom-in-95 duration-300 relative"
      >
        {/* Modal Hero */}
        <div className="relative h-[40vh] md:h-[450px] w-full overflow-hidden">
          <CardBg name={movie.movie_name} />
          
          <img 
            src={movie.poster || getMovieImageUrl(movie.movie_name, movie.release_year || movie.year)}
            alt={movie.movie_name}
            className="absolute inset-0 w-full h-full object-cover opacity-60"
            onError={(e) => { e.target.style.display = 'none'; }}
          />

          <div className="absolute inset-0 bg-gradient-to-t from-[#090910] via-[#090910]/40 to-transparent" />
          
          <button 
            onClick={onClose}
            className="fixed md:absolute top-6 right-6 z-50 w-12 h-12 rounded-full bg-black/60 border border-white/20 flex items-center justify-center text-white hover:bg-[#e8192c] transition-all group/close"
          >
            <X className="w-6 h-6 group-hover/close:rotate-90 transition-transform" />
          </button>

          <div className="absolute bottom-8 left-8 md:bottom-12 md:left-12 right-12">
             <div className="flex items-center gap-3 mb-4">
                <span className="text-[#f5c842] font-bold text-xs md:text-sm tracking-[4px] uppercase select-none">KOLLYWOOD Premium</span>
             </div>
            <h2 className="font-['Bebas_Neue'] text-5xl md:text-8xl tracking-[2px] text-[#f2efe8] drop-shadow-2xl leading-none">
              {movie.movie_name}
            </h2>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-8 md:p-16">
          <div className="grid lg:grid-cols-[1fr,320px] gap-16">
            <div className="space-y-10">
              <div className="flex flex-wrap gap-2">
                {genres.map(g => (
                  <span key={g} className="px-4 py-1.5 bg-[#e8192c]/10 border border-[#e8192c]/20 rounded text-[11px] font-bold uppercase tracking-wider text-[#ff5466]">
                    {g}
                  </span>
                ))}
              </div>

              <div className="space-y-6">
                <h3 className="text-[11px] font-bold uppercase tracking-[3px] text-[#7a7a8c] flex items-center gap-3">
                  <span className="w-6 h-[1px] bg-[#e8192c]" /> Storyline
                </h3>
                <p className="text-[#f2efe8]/80 leading-relaxed text-base md:text-lg">
                  {movie.story || "Experience the magic of Tamil cinema at its finest—blockbuster action, soul-stirring drama, and everything in between."}
                </p>
              </div>

              <div className="flex flex-wrap gap-4 pt-4">
                <button 
                  onClick={handlePlay}
                  className="inline-flex items-center gap-3 bg-[#e8192c] text-white px-10 py-5 rounded-xl font-bold hover:bg-[#ff1f35] hover:scale-105 transition-all shadow-xl text-lg uppercase tracking-widest"
                >
                  <Play className="w-5 h-5 fill-current" /> Play
                </button>
                <button 
                  onClick={handleDownload}
                  className="inline-flex items-center gap-3 bg-white/5 border border-white/10 text-[#f2efe8] px-10 py-5 rounded-xl font-bold hover:bg-white/10 transition-all text-lg uppercase tracking-widest"
                >
                  <Download className="w-5 h-5" /> Download
                </button>
              </div>
            </div>

            <div className="space-y-10 bg-white/[0.02] p-8 rounded-3xl border border-white/5">
              {fields.map((field, idx) => (
                <div key={idx} className="space-y-2 pb-6 border-b border-white/5 last:border-0 last:pb-0">
                  <h4 className="text-[10px] font-bold uppercase tracking-[3px] text-[#7a7a8c]">{field.label}</h4>
                  <p className="text-sm text-[#f2efe8] font-medium leading-relaxed">{field.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations Area */}
          <div className="mt-24 pt-16 border-t border-white/10">
              <h3 className="font-['Bebas_Neue'] text-3xl tracking-[3px] text-[#f2efe8] uppercase mb-12 flex items-center gap-4">
                 <Star className="w-6 h-6 text-[#f5c842] fill-[#f5c842]" />
                 More Like This
              </h3>
              
              {loadingRecs ? (
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-8">
                  {[...Array(8)].map((_, i) => <div key={i} className="skel h-64 rounded-2xl" />)}
                </div>
              ) : recommendations.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">
                  {recommendations.slice(0, 8).map((rec, i) => {
                    const [c1, c2] = getPalette(rec.name);
                    const poster = rec.poster || getMovieImageUrl(rec.name, rec.year);
                    return (
                      <div 
                        key={i}
                        onClick={() => handleRecommendationClick(rec)}
                        className="group cursor-pointer flex flex-col gap-4"
                      >
                         <div className="relative aspect-[2/3] rounded-2xl overflow-hidden border border-white/5 shadow-2xl group-hover:scale-105 transition-all duration-500 hover:shadow-[0_0_30px_rgba(232,25,44,0.2)]">
                            <div className="absolute inset-0 flex items-center justify-center font-['Bebas_Neue'] text-white/10 text-5xl" style={{ background: `linear-gradient(135deg, ${c1}, ${c2})` }}>
                              {rec.name[0]}
                            </div>
                            
                            {/* Recommendation Poster */}
                            {poster && (
                                <img 
                                  src={poster}
                                  alt={rec.name}
                                  className="absolute inset-0 w-full h-full object-cover transition-opacity duration-500 group-hover:opacity-40"
                                  loading="lazy"
                                  onError={(e) => { e.target.style.display = 'none'; }}
                                />
                            )}

                            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-transparent group-hover:bg-black/40 transition-all" />
                            <div className="absolute bottom-3 right-3 text-green-400 font-bold text-[11px] bg-black/70 px-2 py-1 rounded backdrop-blur-md border border-white/10">
                               {Math.round((1 - rec.similarity) * 100)}% Match
                            </div>
                         </div>
                         <div className="text-sm font-bold text-[#f2efe8] group-hover:text-[#e8192c] transition-colors truncate px-1">{rec.name}</div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-20 bg-white/5 rounded-3xl border border-dashed border-white/10">
                  <p className="text-[#7a7a8c] text-xs uppercase tracking-[4px] font-bold opacity-60">
                    Discovering similar titles...
                  </p>
                </div>
              )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MovieModal;
