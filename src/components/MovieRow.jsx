import { useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Play } from 'lucide-react';
import { getPalette, getMovieImageUrl } from '../lib/utils';

const CardBg = ({ name, fontSize = "3.5rem" }) => {
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

const MovieCard = ({ movie, onClick }) => {
  const [isHovered, setIsHovered] = useState(false);
  const genre1 = (movie.gentre || movie.genre || "").split(/[,|/]/)[0].trim();
  // Prioritize DB poster, then generated URL
  const posterUrl = movie.poster || getMovieImageUrl(movie.movie_name, movie.release_year || movie.year);

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="relative flex-none w-36 md:w-48 aspect-[2/3] cursor-pointer rounded-xl overflow-hidden transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)] hover:scale-[1.07] hover:-translate-y-2 hover:z-40 group/card shadow-lg hover:shadow-[0_20px_44px_rgba(0,0,0,0.8)]"
      style={{ boxShadow: isHovered ? "0 0 0 1.5px #e8192c" : "" }}
    >
      <CardBg name={movie.movie_name} />
      
      {posterUrl && (
        <img 
          src={posterUrl} 
          alt={movie.movie_name}
          className="absolute inset-0 w-full h-full object-cover transition-opacity duration-300 group-hover/card:opacity-40"
          loading="lazy"
          onError={(e) => { e.target.style.display = 'none'; }}
        />
      )}

      {/* Overlays */}
      <div className={`absolute inset-0 transition-all duration-300 ${isHovered ? 'bg-[#090910]/80' : 'bg-gradient-to-t from-[#090910] via-[#090910]/20 to-transparent opacity-90'}`} />

      {/* Default Content */}
      <div className={`absolute bottom-0 left-0 right-0 p-3 md:p-4 transition-all duration-300 ${isHovered ? 'opacity-0 translate-y-4' : 'opacity-100 translate-y-0'}`}>
        {genre1 && <div className="text-[9px] font-bold tracking-[2px] uppercase text-[#f5c842] mb-1">{genre1}</div>}
        <div className="text-xs md:text-sm font-bold text-[#f2efe8] line-clamp-2 leading-tight">{movie.movie_name}</div>
      </div>

      {/* Hover Content */}
      <div className={`absolute inset-0 flex flex-col items-center justify-center gap-3 p-4 text-center transition-all duration-300 ${isHovered ? 'opacity-100 scale-100' : 'opacity-0 scale-90 pointer-events-none'}`}>
        <div className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-[#e8192c] flex items-center justify-center shadow-lg transform transition-transform group-hover/card:scale-110">
          <Play className="w-5 h-5 fill-white text-white ml-1" />
        </div>
        <div>
          <div className="text-[10px] md:text-xs font-bold text-[#f2efe8] mb-1 line-clamp-2">{movie.movie_name}</div>
          {genre1 && <div className="text-[8px] font-bold tracking-[1.5px] uppercase text-[#f5c842]">{genre1}</div>}
        </div>
        {movie.story && (
          <p className="text-[9px] md:text-[10px] text-[#7a7a8c] leading-relaxed line-clamp-3 md:line-clamp-4">
            {movie.story}
          </p>
        )}
      </div>
    </div>
  );
};

const MovieRow = ({ title, movies, onMovieClick }) => {
  const rowRef = useRef(null);

  const handleScroll = (direction) => {
    if (rowRef.current) {
      const { scrollLeft, clientWidth } = rowRef.current;
      const scrollTo = direction === 'left' ? scrollLeft - clientWidth * 0.8 : scrollLeft + clientWidth * 0.8;
      rowRef.current.scrollTo({ left: scrollTo, behavior: 'smooth' });
    }
  };

  if (!movies || movies.length === 0) return null;

  return (
    <div className="py-6 md:py-10 group/row relative">
      <div className="flex items-center gap-3 mb-4 md:mb-6 px-1">
        <span className="w-1 h-6 bg-[#e8192c] rounded-full" />
        <h2 className="font-['Bebas_Neue'] text-xl md:text-2xl tracking-[2px] text-[#f2efe8] uppercase">{title}</h2>
      </div>
      
      <div className="relative group">
        <button 
          onClick={() => handleScroll('left')}
          className="absolute -left-4 md:-left-6 top-1/2 -translate-y-1/2 z-[45] bg-[#090910]/80 hover:bg-[#e8192c] w-10 h-10 md:w-12 md:h-12 hidden group-hover/row:flex items-center justify-center opacity-0 group-hover/row:opacity-100 transition-all duration-300 border border-white/10 rounded-full backdrop-blur-md shadow-2xl"
        >
          <ChevronLeft className="w-6 h-6 text-white" />
        </button>

        <div 
          ref={rowRef}
          className="flex gap-4 md:gap-6 overflow-x-auto no-scrollbar scroll-smooth pb-8 px-1"
        >
          {movies.map((movie, i) => (
            <MovieCard 
              key={movie.id || i} 
              movie={movie} 
              onClick={() => onMovieClick(movie)} 
            />
          ))}
        </div>

        <button 
          onClick={() => handleScroll('right')}
          className="absolute -right-4 md:-right-6 top-1/2 -translate-y-1/2 z-[45] bg-[#090910]/80 hover:bg-[#e8192c] w-10 h-10 md:w-12 md:h-12 hidden group-hover/row:flex items-center justify-center opacity-0 group-hover/row:opacity-100 transition-all duration-300 border border-white/10 rounded-full backdrop-blur-md shadow-2xl"
        >
          <ChevronRight className="w-6 h-6 text-white" />
        </button>
      </div>
    </div>
  );
};

export default MovieRow;
